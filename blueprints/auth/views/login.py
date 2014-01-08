__author__ = 'zifnab'
from flask import redirect, request, url_for, render_template, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import Form
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt

from blueprints.auth.models import User
from blueprints.auth import blueprint

class AuthForm(Form):
    username = StringField('Username*', validators=[Required(message='Please enter your username'), Length(min=3, max=16)])
    password = PasswordField('Password*', validators=[Required(message='Please enter your password'), Length(min=8)])
    remember = BooleanField("Remember Account?", validators=[], default=True)

    def validate(self):
        rv = Form.validate(self)
        if rv is None:
            return False

        user = authenticate_user(self.username.data, self.password.data)
        if user is None:
            self.username.errors.append("Invalid username or password")
            return False
        else:
            self.user = user
            return True

@blueprint.route('/auth/login', methods=('POST', 'GET'))
def login():
    form = AuthForm(request.form)
    if current_user.is_authenticated():
        return redirect('/')
    if request.method == 'POST' and form.validate():
        user = form.user
        login_user(user, remember=form.remember)
    return render_template('login.html', form=form, title='Login')

@blueprint.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect('/')


def authenticate_user(username, password):
    user = User.objects(username__iexact=username).first()
    if (sha512_crypt.verify(password, user.hash)):
        return user
    else:
        return None
