from datetime import datetime

from mongoengine import Document
from mongoengine import (
    StringField,
    DateTimeField,
    ReferenceField,
    IntField,
    BooleanField,
)
from flask_login import UserMixin


class User(Document, UserMixin, object):
    username = StringField(required=True, unique=True, max_length=16, min_length=3)
    hash = StringField(required=True)
    email = StringField(required=False)
    registration_date = DateTimeField(default=datetime.now)
    admin = BooleanField(default=False)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    meta = {"index": ["username"], "collection": "users"}

    def __str__(self):
        return self.username


class Paste(Document):
    name = StringField(required=True, unique=True)
    paste = StringField(required=True)
    digest = StringField(required=False)
    time = DateTimeField(required=True)
    expire = DateTimeField(required=False)
    user = ReferenceField(User, required=False)
    views = IntField(required=False, default=0)
    language = StringField(required=False)
    address = StringField(required=False)

    def __str__(self):
        return self.name


class ApiKey(Document):
    key = StringField(required=True, unique=True, max_length=32, min_length=32)
    user = ReferenceField(User, required=True)

    def __str__(self):
        return "{0}:{1}".format(self.user, self.key)
