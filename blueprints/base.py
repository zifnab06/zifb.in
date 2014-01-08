__author__ = 'zifnab'
from flask import current_app
from mongoengine import connect
from flask_admin import Admin
from flask_debugtoolbar import DebugToolbarExtension

db = connect('zifbin')

admin = Admin(current_app)

toolbar = DebugToolbarExtension(current_app)