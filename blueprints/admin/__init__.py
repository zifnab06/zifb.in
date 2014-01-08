__author__ = 'zifnab'
from blueprints.base import admin
from blueprints.auth.models import User
from blueprints.paste.models import Paste
from flask import abort
from flask_admin.contrib import mongoengine
from flask_admin import BaseView, AdminIndexView
from flask_login import current_user


def is_admin():
    if (current_user.is_anonymous()):
        abort(403)
    else:
        return current_user.username == 'zif'

class AdminIndexView(AdminIndexView):
    def is_accessible(self):
        return is_admin()


class ModelView(mongoengine.ModelView):
    def is_accessible(self):
        return is_admin()

class UserView(ModelView):
    column_exclude_list= ('hash')
class PasteView(ModelView):
    pass

admin.add_view(UserView(User))
admin.add_view(PasteView(Paste))
