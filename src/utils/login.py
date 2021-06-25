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

def checkLogin(json):
    try:
        user_name:str = json.login
        password:str = json.password

        resultUserName = query('SELECT password from users where login = %s LIMIT 1',(user_name,))
        if (len(resultUserName) == 0 ):
            return jsonify({ 'message': 'User or password is invalid!'}), 400
        hashedpass = hashPassword(password)
        if (resultUserName[0][0] == str(hashedpass)):
            jwtToken = generateToken(json.login)
            returnVar = jsonify({'message': 'User Logged succesfully!'})
            return returnVar
        else:
            return jsonify({ 'message': "User or password in invalid!"}), 400
    except Exception as error:
        print(error)
        return jsonify({ "message": "There was an error in your request"}), 500


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

    