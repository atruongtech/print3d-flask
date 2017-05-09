from flask import request, Response
from functools import wraps
from configs.allowedkeys import Allowed_Keys

def required_apikey(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        apikey = request.headers.get('ApiKey')
        if apikey not in Allowed_Keys:
            return not_authorized()
        return f(*args, **kwargs)
    return decorated

def not_authorized():
    return Response('A valid API key is required to access this endpoint.', 403)