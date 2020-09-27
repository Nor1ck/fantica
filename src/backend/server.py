import aiohttp
import arrow
import asyncio
import json
import os
import pathlib
import redis
import secrets

from aiohttp import web
from pymongo import MongoClient
from web3 import Web3


ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
TESTNET = 'https://kovan.infura.io/v3/7e078b78f3ba433c8c5c8715a612487b'
web3 = Web3(Web3.HTTPProvider(TESTNET))
rs_0 = redis.StrictRedis(decode_responses=True, db=5)  # TODO set to 0
client = MongoClient()
db = client['fantica']


ALLOWED_HEADERS = ','.join((
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-requested-with',
    'x-csrftoken',
))

PROFILE_KEYS = ['username', 'about', 'location', 'website']
POST_KEYS = ['message', 'media']


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
        return web.json_response({'msg': 'Signature error.'}, status=400)
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
        return web.json_response({'msg': 'Invalid token.'}, status=400)
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
        return web.json_response({'msg': 'Invalid token.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    if len(set(POST_KEYS) - set(data.keys())) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(POST_KEYS)}, status=400)
    if type(data['media']) is not list:
        return web.json_response({'msg': 'Invalid media format.'}, status=400)
    if not data['message']:  # forced identification of user posts
        return web.json_response({'msg': 'Message is empty.'}, status=400)
    profile = json.loads(rs_0.get('profile:' + address))
    ts = arrow.utcnow().timestamp
    user_post = {
        '_id': '{}:{}'.format(address, ts),
        'username': profile['username'],
        'address': address,
        'message': data['message'],
        'media': data['media'],
        'media_path': secrets.token_hex(32),
        'ts': ts,
    }
    mongo_set('posts', user_post)
    return web.json_response({})


async def api_delete_post(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    post_id = (await req.json()).get('post_id')
    if not post_id:
        return web.json_response({'msg': 'Post not found.'}, status=404)
    if not post_id.startswith(address):
        return web.json_response({'msg': 'Only owner.'}, status=403)
    # TODO delete media
    mongo_del('posts', post_id)
    return web.json_response({})



async def api_upload_file(req):
    token = req.cookies.get('token')
    if not token or len(token) != 64:
        return web.json_response({'msg': 'Invalid token.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    file_type = req.match_info['file_type']
    if file_type not in ['cover', 'avatar']: # TODO add a media ?
        return web.json_response({'msg': 'Invalid type of file.'}, status=400)


    reader = await req.multipart()
    field = await reader.next()
    extension = field.filename.split('.')[-1]

    if extension not in ['jpg', 'png', 'jpeg', 'bmp']:
        return web.json_response({'msg': 'Invalid file format.'}, status=400)

    file_name = secrets.token_hex(32) + '.jpg' if file_type == 'media' else file_type + '.jpg'
    directory = '/opt/fantica/{}/{}'.format(file_type, address)
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(directory, file_name)

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
        return web.json_response({'msg': 'Invalid token.'}, status=400)
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
    address = req.match_info['address']
    try:
        skip = int(req.rel_url.query.get('skip', 0))
    except:
        return web.json_response({'msg': 'Invalid skip parameter type.'}, status=400)
    posts = [x for x in mongo_find_posts('posts', skip=skip, filter={'address': address})]
    if not posts:
        return web.json_response({'msg': 'Posts not found.'}, status=404)
    return web.json_response({'posts': posts})


async def api_recent_posts(req):
    try:
        skip = int(req.rel_url.query.get('skip', 0))
    except:
        return web.json_response({'msg': 'Invalid skip parameter type.'}, status=400)
    posts = [x for x in mongo_find_posts('posts', skip=skip)]
    if not posts:
        return web.json_response({'msg': 'Posts not found.'}, status=404)
    return web.json_response({'posts': posts})


app = web.Application(middlewares=[md_cors_factory])

app.router.add_route('POST', '/api/auth', api_auth)
app.router.add_route('POST', '/api/update_profile', api_update_profile)
app.router.add_route('POST', '/api/new_post', api_new_post)
app.router.add_route('POST', '/api/upload/{file_type}', api_upload_file)
app.router.add_route('POST', '/api/profile', api_get_or_create_profile)
app.router.add_route('POST', '/api/posts/delete', api_delete_post)

app.router.add_route('GET', '/api/profile/{address}', api_user_profile)
app.router.add_route('GET', '/api/posts/recent', api_recent_posts)
app.router.add_route('GET', '/api/posts/{address}', api_user_posts)

app.add_routes([web.static('/static', '/opt/fantica')])

# TODO save purchased posts

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=3005)
