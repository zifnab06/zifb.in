import string
from passlib.hash import sha512_crypt
from random import SystemRandom
import database
from flask_login import login_user

_random = SystemRandom()


def random_string(size=10, chars=string.ascii_letters + string.digits):
    return "".join(_random.choice(chars) for x in range(size))


def create_user(**kwargs):
    username = kwargs.get("username")
    password = kwargs.get("password")
    email = kwargs.get("email")
    hash = sha512_crypt.encrypt(password)
    user = database.User(username=username, hash=hash, email=email)
    if database.User.objects().count() == 0:
        user.admin = True
    user.save()
    login_user(user)


def authenticate_user(username, password):
    user = database.User.objects(username__iexact=username).first()
    if user is None:
        return None
    if sha512_crypt.verify(password, user.hash):
        return user
    else:
        return None


def lookup_user(username):
    user = database.User.objects(username__iexact=username).first()
    return user
