import hashlib
from dotenv import load_dotenv
import os
from database.storage import query
from flask import request, jsonify
from utils.jwtToken import generateToken

load_dotenv()

def hashPassword(passwordPlain):
    password = hashlib.pbkdf2_hmac(
        'sha256',
        passwordPlain.encode('utf-8'),
        bytes(os.environ.get('HASH_PASS'), 'utf-8'),
        100000,
        dklen=128
    )
    return password

def checkLogin(json: dict):
    try:
        user_name:str = json['login']
        password:str = json['password']
        resultUserName = query('SELECT password from users where login = %s LIMIT 1',(user_name,))
        print(resultUserName[0][0])
        if (len(resultUserName) == 0 ):
            return {'message': 'User or password is invalid!', 'status': 400}
        hashedpass = hashPassword(password)
        print(str(hashedpass))
        if (resultUserName[0][0] == str(hashedpass)):

            return {'message': 'User Logged succesfully!', 'status': 200}
        else:
            return {'message': "User or password in invalid!", 'status': 400}
    except Exception as error:
        print(error)
        return {"message": "There was an error in your request", 'status': 500}


# def newuser(jsonIN):
#     try:
#         if (len(jsonIN['password']) < 6):
#             return 'Password must be at least 6 Digits', 400
#         returnQuery = query(
#             'INSERT INTO users(user_name, password, email, applications) VALUES(%s, %s, %s, %s)', 
#             (
#                 jsonIN['login'], 
#                 str(hashPassword(jsonIN['password'])), 
#                 jsonIN['email'],
#                 jsonIN['applications']
#             )
#         )

#         return jsonify({ "message": returnQuery}), 201

#     except:
#         return 'There was an error in your request, contact the support or try again later', 500

    