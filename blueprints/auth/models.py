__author__ = 'zifnab'

from mongoengine import Document
from mongoengine import StringField, IntField, BooleanField, DateTimeField
from datetime import datetime
from flask_login import UserMixin

class User(Document, UserMixin, object):
    username = StringField(required=True, unique=True, max_length=16, min_length=3)
    hash = StringField(required=True)
    email = StringField(required=False)
    registration_date = DateTimeField(default=datetime.now)


    def is_authenticated(self):
        return True
    def is_anonymous(self):
        return False
    def is_active(self):
        return True
    def get_id(self):
        return self.username

    meta = {
        'index': ['username'],
        'collection': 'users'
    }

