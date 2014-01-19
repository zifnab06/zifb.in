__author__ = 'zifnab'
from database import User, Paste
from flask import abort, current_app
from flask_superadmin import Admin, model, base
from flask_login import current_user


def is_admin():
    if (current_user.is_anonymous()):
        abort(403)
    else:
        return current_user.admin

class BaseModel(model.ModelAdmin):
    def is_accessible(self):
        return is_admin()

class UserModel(BaseModel):
    list_display = ('username', 'email', 'admin', 'registration_date')
    search_fields = ('username', 'email')
    can_create = False
    can_edit = True
    can_delete = True
    exclude = ('hash')

class PasteModel(BaseModel):
    list_display = ('name', 'paste', 'time', 'expire', 'user', 'views', 'language')

admin = Admin(current_app)

admin.register(User, UserModel)
admin.register(Paste, PasteModel)