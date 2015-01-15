__author__ = 'zifnab'
from database import User, Paste
from flask import abort, current_app
from flask_login import current_user
from flask_admin import BaseView, Admin
from flask_admin.contrib.mongoengine import ModelView

def is_admin():
    if (current_user.is_anonymous()):
        abort(403)
    else:
        return current_user.admin

class ProtectedView(BaseView):
    def is_accessible(self):
        return is_admin()

class SecureModelView(ModelView):
    def is_accessible(self):
        return is_admin()

class UserModel(SecureModelView):
    list_display = ('username', 'email', 'admin', 'registration_date')
    search_fields = ('username', 'email')
    can_create = False
    can_edit = True
    can_delete = True
    exclude = ('hash')

class PasteModel(SecureModelView):
    list_display = ('name', 'paste', 'time', 'expire', 'user', 'views', 'language')

admin = Admin(current_app)

admin.add_view(UserModel(User))
admin.add_view(PasteModel(Paste))
