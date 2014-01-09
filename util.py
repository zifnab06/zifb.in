__author__ = 'zifnab'

import string
from passlib.hash import sha512_crypt
import database

def random_string(size=10, chars=string.ascii_letters + string.digits):
    import random
    return ''.join(random.choice(chars) for x in range(size))

def create_user(**kwargs):
    username = kwargs.get('username')
    password = kwargs.get('password')
    email = kwargs.get('email')
    hash = sha512_crypt.encrypt(password)
    user = database.User(username=username,
                hash=hash,
                email=email)
    user.save()

def authenticate_user(username, password):
    user = database.User.objects(username__iexact=username).first()
    if (sha512_crypt.verify(password, user.hash)):
        return user
    else:
        return None
def lookup_user(username):
    user = database.User.objects(username__iexact=username).first()
    return user