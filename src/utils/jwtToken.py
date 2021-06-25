from functools import wraps
import jwt
import datetime
from dotenv import load_dotenv
import os
from flask import request, jsonify

load_dotenv()

def generateToken(user_name):
    key = os.environ.get('JWTKEY')
    return jwt.encode({'username': user_name, 'exp': datetime.datetime.now() + datetime.timedelta(hours=12) }, key, algorithm="HS256")


def checkToken(token):
    @wraps(token)
    def decorated(*args, **kwargs):
        try: 
            print(request.cookies)
            tokenIn = request.cookies.get('token')
        except:
            return jsonify({ 'message': 'Token is missing', 'data': []}), 401
        if len(tokenIn) == 0:
            return jsonify({'message': 'token is missing', 'data': []}), 401
        try:
            data = jwt.decode(tokenIn, os.environ.get('JWTKEY'), algorithms=["HS256"])
        except:
            return jsonify({'message': 'token is invalid or expired', 'data': []}), 401
        return token(*args, **kwargs)
    return decorated
