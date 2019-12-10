from database import User, Paste, ApiKey
from flask import abort, current_app
from flask_login import current_user
from flask_admin import BaseView, Admin
from flask_admin.contrib.mongoengine import ModelView


def is_admin():
    if current_user.is_anonymous:
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
    column_exclude_list = "hash"
    column_searchable_list = ("username", "email")
    can_create = False
    can_edit = True
    can_delete = True


class PasteModel(SecureModelView):
    list_display = ("name", "paste", "time", "expire", "user", "views", "language")
    column_searchable_list = ("name", "paste")


class ApiKeyModel(SecureModelView):
    pass


admin = Admin(current_app)

admin.add_view(UserModel(User))
admin.add_view(PasteModel(Paste))
admin.add_view(ApiKeyModel(ApiKey))
