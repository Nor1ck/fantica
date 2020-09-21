import aiohttp
import arrow
import asyncio
import json
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

PROFILE_KEYS = ['displayname', 'about', 'location', 'website']
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


def mongo_find_one(collection, **kwargs):
    return db[collection].find_one(kwargs)


def mongo_find_posts(collection, skip=0, limit=10, **kwargs):
    return db[collection].find(kwargs, skip=skip, limit=limit).sort('ts', -1)


def create_profile(address):
    profile = {
        '_id': address,
        'displayname': address,
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
    except Exception as e:
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
    if len(token) != 64:
        return web.json_response({'msg': 'Invalid token length.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    if len(set(PROFILE_KEYS) - set(data.keys())) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(PROFILE_KEYS)}, status=400)
    if len(data['displayname']) < 5:
        return web.json_response({'msg': 'The min length for displayname is 5 letters.'}, status=400)
    if '0x' in data['displayname'] and len(data['displayname']) >= 42 and data['displayname'] != address:
        return web.json_response({'msg': "It is forbidden to use other people's addresses."}, status=403)
    profile = {key: data[key] for key in data.keys() if key in PROFILE_KEYS}
    profile['_id'] = address
    mongo_set('profile', profile)
    return web.json_response({})


async def api_new_post(req):
    token = req.cookies.get('token')
    data = await req.json()
    if len(token) != 64:
        return web.json_response({'msg': 'Invalid token length.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    if len(set(POST_KEYS) - set(data.keys())) > 0:
        return web.json_response({'msg': 'Invalid keys. Required: {}'.format(POST_KEYS)}, status=400)
    if type(data['media']) is not list:
        return web.json_response({'msg': 'Invalid media format.'}, status=400)
    if not data['message']:  # forced identification of user posts
        return web.json_response({'msg': 'Message is empty.'}, status=400)
    ts = arrow.utcnow().timestamp
    user_post = {
        '_id': '{}:{}'.format(address, ts),
        'address': address,
        'message': data['message'],
        'media': data['media'],
        'ts': ts,
    }
    mongo_set('posts', user_post)
    return web.json_response({})


async def api_upload_file(req):
    pass


async def api_profile(req):
    token = req.cookies.get('token')
    if len(token) != 64:
        return web.json_response({'msg': 'Invalid token length.'}, status=400)
    address = rs_0.get('token:' + token)
    if not address:
        return web.json_response({'msg': 'Token not found.'}, status=404)
    # TODO profile
    profile = mongo_get('profile', address)
    if not profile:
        create_profile(address)
    return web.json_response({'profile': profile})


async def api_user_posts(req):
    address = req.match_info['address']
    try:
        skip = int(req.rel_url.query.get('skip', 0))
    except:
        return web.json_response({'msg': 'Invalid skip parameter type.'}, status=400)
    posts = [x for x in mongo_find_posts('posts', skip=skip, kwargs={'address': address})]
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
app.router.add_route('POST', '/api/upload_file', api_upload_file)
app.router.add_route('GET', '/api/profile', api_profile)
app.router.add_route('GET', '/api/posts', api_recent_posts)
app.router.add_route('GET', '/api/posts/{address}', api_user_posts)

if __name__ == '__main__':
    web.run_app(app, host='localhost', port=3005)
