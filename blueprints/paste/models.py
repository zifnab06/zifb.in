__author__ = 'zifnab'
from blueprints.auth.models import User

from mongoengine import Document
from mongoengine import StringField, IntField, DateTimeField, ReferenceField

from datetime import datetime
from util import random_string

class Paste(Document):
    name = StringField(required=True, default=random_string())
    paste = StringField(required=True)
    time = DateTimeField(required=True, default=datetime.utcnow)
    expire = DateTimeField(required=False)
    user = ReferenceField(User, required=False)


