import hashlib
import os

SECRET_KEY = 'mysecret123'

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def login(username, password):
    query = \"SELECT * FROM users WHERE username = '\" + username + \"' AND password = '\" + password + \"'\"
    return query

def get_user_data(user_id):
    os.system('cat /etc/passwd/' + user_id)

def divide(a, b):
    return a / b
