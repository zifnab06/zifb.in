__author__ = 'zifnab'

from flask import redirect, request, url_for, render_template, flash
from flask_login import login_user
from flask_wtf import Form
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt

from blueprints.auth.models import User
from blueprints.auth import blueprint

class RegForm(Form):
    username = StringField('Username*', validators=[Required(message='Please enter your username'), Length(min=3, max=16)])
    email = StringField('Email', validators=[Email()])
    password = PasswordField('Password*', validators=[Required(message='Please enter your password'), Length(min=8)])
    password2 = PasswordField('Repeat Password*', validators=[EqualTo('password', message='Passwords do not match'), Required()])

    def validate(self):
        rv = Form.validate(self)
        if rv is None:
            return False

        user = User.objects(username__iexact=self.username.data).first()
        if user is None:
            return True

        else:
            self.username.errors.append("Username is already taken - try again")
            return False

@blueprint.route('/auth/register', methods=('POST','GET'))
def register():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        create_user(**form.data)
        flash('Thanks for registering!')
        return redirect('/')
    return render_template('register.html', form=form, title='Register')


def create_user(**kwargs):
    username = kwargs.get('username')
    password = kwargs.get('password')
    email = kwargs.get('email')
    hash = sha512_crypt.encrypt(password)
    user = User(username=username,
                hash=hash,
                email=email)
    user.save()