__author__ = 'zifnab'
from app import app
from flask import current_app, request, abort, flash, redirect, render_template
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_wtf import Form
from database import User

from wtforms.fields import StringField, BooleanField, PasswordField
from wtforms.validators import Required, Length, EqualTo, Email
from util import authenticate_user, create_user, lookup_user

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return User.objects(username__iexact=user_id).first()

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
class ForgotPasswordForm(Form):
    username = RegForm.username
    def validate(self):
        user = lookup_user(self.username.data)
        if user is None:
            self.username.errors.append("Username does not exist")
            return False
        if user.email is None:
            self.username.errors.append("No email on file, cannot be recovered")
            return False
        return True

@app.route('/auth/login', methods=('POST', 'GET'))
def login():
    form = AuthForm(request.form)
    if current_user.is_authenticated():
        return redirect('/')
    if request.method == 'POST' and form.validate():
        user = form.user
        login_user(user, remember=form.remember)
        return redirect('/')
    return render_template('login.html', form=form, title='Login')

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect('/')

@app.route('/auth/register', methods=('POST','GET'))
def register():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        create_user(**form.data)
        flash('Thanks for registering!')
        return redirect('/')
    return render_template('register.html', form=form, title='Register')
#@app.route('/auth/forgotpassword', methods=('POST', 'GET'))
def pwreset():
    form = ForgotPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        #Email Link to reset password
        pass


    return render_template('pwreset.html', form=form, title='Forgot Passowrd')
    pass