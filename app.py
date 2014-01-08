__author__ = 'zifnab'
from flask import Flask
from mongoengine import connect
from flask_admin import Admin
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask import redirect, request, render_template, flash, current_app as app, abort
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import Form
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt
from datetime import datetime
import database
from util import create_user, authenticate_user




app = Flask(__name__)

with app.app_context():
    from config import local_config
    app.config.from_object(local_config)

    db = connect('zifbin')
    admin = Admin(app)
    toolbar = DebugToolbarExtension(app)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id):
        return database.User.objects(username__iexact=user_id).first()

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

    class PasteForm(Form):
        text = TextAreaField('Paste Here', validators=[Required()])
        expiration = SelectField('Expiration', choices=[('0', 'Never'), ('1', 'Fifteen Minutes'), ('2', 'Thirty Minutes'), ('3', 'One Hour'), ('4', 'Six Hours'), ('5', 'One Day')])

    @app.route('/', methods=('POST', 'GET'))
    @app.route('/new', methods=('POST', 'GET'))
    def main():
        form = PasteForm(request.form)
        if form.validate_on_submit():
            paste = database.Paste(paste=form.text.data)
            if (current_user.is_authenticated()):
                paste.user = current_user.to_dbref()
            paste.save()
            return redirect('/{id}'.format(id=paste.name))
        return render_template('new_paste.html', form=form)

    @app.route('/<string:id>')
    def get(id):
        paste = database.Paste.objects(name__exact=id).first()
        if paste is None:
            abort(404)
        elif paste.expire > datetime.utcnow:
            abort(404)
        else:
            return render_template("paste.html", paste=paste, title=paste.id)

    @app.route('/auth/login', methods=('POST', 'GET'))
    def login():
        form = AuthForm(request.form)
        if current_user.is_authenticated():
            return redirect('/')
        if request.method == 'POST' and form.validate():
            user = form.user
            login_user(user, remember=form.remember)
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




app.debug = app.config['DEBUG']

def run():
    app.run(
        host=app.config.get('HOST', None),
        port=app.config.get('PORT', None)
    )



