import aiohttp
import arrow
import asyncio
import json
import os
import pathlib
import redis
import secrets
import shutil

from aiohttp import web
from pymongo import MongoClient
from web3 import Web3
from Crypto.Hash import keccak as sha3


ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
TESTNET = 'https://kovan.infura.io/v3/7e078b78f3ba433c8c5c8715a612487b'
INFURA = TESTNET
FANTICA_DAPP_ADDRESS = '0x610706d8f743cB0C33268178905D81cC02aF665B'
web3 = Web3(Web3.HTTPProvider(TESTNET))
rs_0 = redis.StrictRedis(decode_responses=True, db=5)  # TODO set to 0
client = MongoClient()
db = client['fantica:{}'.format(FANTICA_DAPP_ADDRESS)]
free_workers = asyncio.Semaphore(20)


ALLOWED_HEADERS = ','.join((
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-requested-with',
    'x-csrftoken',
))

PROFILE_KEYS = ['username', 'about', 'location', 'website']
POST_KEYS = ['message', 'media_count']


def set_cors_headers(request, response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get(
        'Origin', '*')
    response.headers['Access-Control-Allow-Methods'] = request.method
    response.headers['Access-Control-Allow-Headers'] = ALLOWED_HEADERS
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@web.middleware
async def md_cors_factory(request, handler):
    if request.method == 'OPTIONS':
        return set_cors_headers(request, web.Response())
    else:
        response = await handler(request)
        return set_cors_headers(request, response)


def keccak(seed):
    k = sha3.new(digest_bits=256)
    k.update(seed.encode('utf8'))
    return k.hexdigest()


def encode_func(func_name, hex_prefix=False) -> str:
    function_hex = keccak(func_name)[:8]  # first 4 bytes
    if hex_prefix:
        function_hex = '0x{}'.format(function_hex)
    return function_hex


def encode_data(func, params, value_wei=0):
    assert isinstance(value_wei, int)
    if params:
        assert len(func.split(',')) == len(params)
    hex_params = [str(hex(int(str(p), 16))[2:]).zfill(64)
                  for p in params]  # without 0x, int64
    value_wei_hex = str(hex(value_wei)[2:]).zfill(64)  # without 0x, int64
    return '0x{}{}{}'.format(encode_func(func), ''.join(hex_params), value_wei_hex)


def build_query(func, params, _id=1):
    tx_data = {
        'to': FANTICA_DAPP_ADDRESS,
        'data': encode_data(func, params),
    }
    return {"jsonrpc": "2.0", "method": "eth_call", "id": _id, "params": [tx_data] }


def verify_message(message, signature):
    from eth_account.messages import encode_defunct
    signer = web3.eth.account.recover_message(
        encode_defunct(text=message), signature=signature)
    return signer


def mongo_get(collection, key):
    return db[collection].find_one({'_id': key})


def mongo_set(collection, obj):
    return db[collection].update_one({'_id': obj['_id']}, {'$set': obj}, upsert=True)


def mongo_del(collection, obj_id):
    return db[collection].delete_one({'_id': obj_id})


def mongo_find_one(collection, **kwargs):
    return db[collection].find_one(kwargs)


def mongo_find_posts(collection, skip=0, limit=10, filter=None):
    return db[collection].find(filter=filter, skip=skip, limit=limit).sort('ts', -1)


def create_profile(address):
    profile = {
        '_id': address,
        'username': address,
        'about': '',
        'location': '',
        'website': '',
    }
    mongo_set('profile', profile)
    return profile


async def api_auth(req):
    data = await req.json()
    required_keys = set(['msg', 'sign'])
    if len(set(data.keys()) - required_keys) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(required_keys)}, status=400)
    if len(data['msg']) != len('Address: 0x0000000000000000000000000000000000000000'):
        return web.json_response({'msg': 'Invalid length of the msg parameter.'}, status=400)
    try:
        signer = verify_message(data['msg'], data['sign'])
    except:
        return web.json_response({'msg': 'Signature error.'}, status=401)
    if 'Address: ' + signer != data['msg']:
        return web.json_response({'msg': 'Invalid signature.'}, status=403)
    secret_token = secrets.token_hex(32)
    rs_0.set('token:' + secret_token, signer, ex=ONE_DAY * 7)
    rs_0.set('address:' + signer, secret_token, ex=ONE_DAY * 7)
    return web.json_response({'token': secret_token, 'expires': 7})


async def api_update_profile(req):
    token = req.cookies.get('token')
    data = await req.json()
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    if len(set(PROFILE_KEYS) - set(data.keys())) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(PROFILE_KEYS)}, status=400)
    data['username'] = data['username'].strip()
    if len(data['username']) < 5:
        return web.json_response({'msg': 'The min length for username is 5 letters.'}, status=400)
    if '0x' in data['username'] and len(data['username']) >= 42 and data['username'] != address:
        return web.json_response({'msg': "It is forbidden to use other people's addresses."}, status=403)
    profile = {key: data[key] for key in data.keys() if key in PROFILE_KEYS}
    profile['_id'] = address
    mongo_set('profile', profile)
    rs_0.set('profile:' + address, json.dumps(profile), ex=ONE_DAY * 7)
    return web.json_response({})


async def api_new_post(req):
    token = req.cookies.get('token')
    data = await req.json()
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    if len(set(POST_KEYS) - set(data.keys())) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(POST_KEYS)}, status=400)
    if type(data['media_count']) is not int:
        return web.json_response({'msg': 'Invalid media count.'}, status=400)
    if not data['message']:  # forced identification of user posts
        return web.json_response({'msg': 'Message is empty.'}, status=400)
    profile = json.loads(rs_0.get('profile:' + address))
    ts = arrow.utcnow().timestamp
    user_post = {
        '_id': '{}:{}'.format(address, ts),
        'username': profile['username'],
        'address': address,
        'message': data['message'],
        'secret': secrets.token_hex(16),
        'media_count': data['media_count'],
        'ts': ts,
    }
    rs_0.set('secret:' + user_post['secret'], address, ex=ONE_MINUTE * 5)
    mongo_set('posts', user_post) # TODO cache it
    if data['media_count'] > 0:
        return web.json_response({'secret': user_post['secret']})
    return web.json_response({})


async def api_delete_post(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    post_id = (await req.json()).get('post_id')
    if not post_id:
        return web.json_response({'msg': 'Post not found.'}, status=404)
    if not post_id.startswith(address):
        return web.json_response({'msg': 'Only owner.'}, status=403)

    post = mongo_get('posts', post_id)
    shutil.rmtree('/opt/fantica/media/{}/{}'.format(address, post['secret']), ignore_errors=True)
    mongo_del('posts', post_id)
    return web.json_response({})


async def api_upload_file(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    file_type = req.match_info['file_type']
    if file_type not in ['cover', 'avatar']:
        return web.json_response({'msg': 'Invalid file type.'}, status=400)

    reader = await req.multipart()
    field = await reader.next()
    extension = field.filename.split('.')[-1]

    if extension not in ['jpg', 'png', 'jpeg', 'bmp']:
        return web.json_response({'msg': 'Invalid file format.'}, status=400)

    directory = '/opt/fantica/{}/{}'.format(file_type, address)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(directory, '{}.jpg'.format(file_type))

    with open(filepath, 'wb') as f:
        size = 0
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    return web.json_response({})


async def api_upload_media(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    secret = req.match_info['secret']
    if rs_0.get('secret:' + secret) != address:
        return web.json_response({'msg': 'Unauthorized.'}, status=401)

    index = req.match_info['index']

    try:
        index = int(index)
    except ValueError:
        return web.json_response({'msg': 'Invalid index type.'}, status=400)

    reader = await req.multipart()
    field = await reader.next()
    extension = field.filename.split('.')[-1]

    if extension not in ['jpg', 'png', 'jpeg', 'bmp']:
        return web.json_response({'msg': 'Invalid file format.'}, status=400)

    directory = '/opt/fantica/media/{}/{}'.format(address, secret)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(directory, '{}.jpg'.format(index))

    with open(filepath, 'wb') as f:
        size = 0
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)

    return web.json_response({})


async def api_get_or_create_profile(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    profile = mongo_get('profile', address)
    if not profile:
        profile = create_profile(address)
    rs_0.set('profile:' + address, json.dumps(profile), ex=ONE_DAY * 7)
    return web.json_response({'profile': profile})


async def api_user_profile(req):
    address = req.match_info['address']
    profile = rs_0.get('profile:' + address)
    if profile:
        profile = json.loads(profile)
    else:
        profile = mongo_get('profile', address)
    if not profile:
        return web.json_response({'profile': profile}, status=404)
    rs_0.expire('profile:' + address, ONE_DAY * 7)
    return web.json_response({'profile': profile})


async def api_user_posts(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=401)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)

    creator = req.match_info['address']
    try:
        skip = int(req.rel_url.query.get('skip', 0))
    except:
        return web.json_response({'msg': 'Invalid skip parameter type.'}, status=400)
    posts = [x for x in mongo_find_posts(
        'posts', skip=skip, filter={'address': creator})]
    if not posts:
        return web.json_response({'msg': 'Posts not found.'}, status=404)

    can_view = rs_0.exists('subscribtion:{}:{}'.format(address, creator)) == 1 or creator == address
    if not can_view:
        can_view = await dapp_can_view(address, creator) # TODO track the events instead of calls

    if not can_view:
        query = []
        for i, p in enumerate(posts):
            content_id_hex = format(int(p['_id'].split(':')[-1]), 'x')
            query.append(build_query('contentPurchased(address,address,uint256)', [address, creator, content_id_hex], _id=i))
        resp = await rpc_call(query)
        for r in resp:
            content_purchaised = int(r['result'], 16) == 1
            if not content_purchaised:
                posts[r['id']].pop('secret')
    else:
        expires = await dapp_subscription_expires(address, creator)
        expires = expires - arrow.utcnow().timestamp
        if expires > 0:
            rs_0.set('subscribtion:{}:{}'.format(address, creator), '', ex=expires)
    return web.json_response({'posts': posts})


async def api_recent_posts(req):
    try:
        skip = int(req.rel_url.query.get('skip', 0))
    except:
        return web.json_response({'msg': 'Invalid skip parameter type.'}, status=400)
    posts = [x for x in mongo_find_posts('posts', skip=skip)]
    [p.pop('secret') for p in posts]
    if not posts:
        return web.json_response({'msg': 'Posts not found.'}, status=404)
    return web.json_response({'posts': posts})


async def rpc_call(query):
    async with free_workers:
        async with aiohttp.ClientSession() as sess:
            async with sess.request('POST', INFURA, json=query, timeout=5, ssl=False) as resp:
                try:
                    return json.loads(await resp.text())
                except Exception as e:
                    print(e)
                    print('rpc_call {} {}'.format(resp.status, await resp.text()))


async def dapp_subscription_expires(consumer, creator):
    query = build_query('subscriptionExpires(address,address)', [consumer, creator])
    resp = await rpc_call(query)
    return int(resp['result'], 16)


async def dapp_can_view(consumer, creator):
    query = build_query('canView(address,address)', [consumer, creator])
    resp = await rpc_call(query)
    return int(resp['result'], 16) == 1


async def dapp_contentPurchased(consumer, creator, content_id):
    query = build_query('contentPurchased(address,address,uint256)', [consumer, creator, format(int(content_id), 'x')])
    resp = await rpc_call(query)
    return int(resp['result'], 16) == 1


async def event_scan():
    pass


async def api_ping(req):
    return web.json_response({'msg': 'pong'})


app = web.Application(middlewares=[md_cors_factory])

app.router.add_route('POST', '/api/auth', api_auth)
app.router.add_route('POST', '/api/update_profile', api_update_profile)
app.router.add_route('POST', '/api/new_post', api_new_post)
app.router.add_route('POST', '/api/upload/media/{secret}/{index}', api_upload_media)
app.router.add_route('POST', '/api/upload/{file_type}', api_upload_file)
app.router.add_route('POST', '/api/profile', api_get_or_create_profile)
app.router.add_route('POST', '/api/posts/delete', api_delete_post)

app.router.add_route('GET', '/api/ping', api_ping)
app.router.add_route('GET', '/api/profile/{address}', api_user_profile)
app.router.add_route('GET', '/api/posts/recent', api_recent_posts)
app.router.add_route('GET', '/api/posts/{address}', api_user_posts)

app.add_routes([web.static('/static', '/opt/fantica')])


if __name__ == '__main__':
    web.run_app(app, host='localhost', port=3005)
