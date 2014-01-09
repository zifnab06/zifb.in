__author__ = 'zifnab'
from flask import Flask, redirect, request, render_template, flash, current_app as app, abort
from mongoengine import connect
from flask_admin import Admin
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import Form
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt
from datetime import datetime, timedelta, date
import database
import arrow

from util import random_string




app = Flask(__name__)

with app.app_context():
    import auth
    from config import local_config
    app.config.from_object(local_config)

    db = connect('zifbin')
    admin = Admin(app)
    import admin
    toolbar = DebugToolbarExtension(app)

    class PasteForm(Form):
        text = TextAreaField('Paste Here', validators=[Required()])
        expiration = SelectField('Expiration', choices=[('0', 'Never'), ('1', 'Fifteen Minutes'), ('2', 'Thirty Minutes'), ('3', 'One Hour'), ('4', 'Six Hours'), ('5', 'One Day')])

    @app.route('/', methods=('POST', 'GET'))
    @app.route('/new', methods=('POST', 'GET'))
    def main():
        form = PasteForm(request.form)
        if form.validate_on_submit():

            times = {
                '0':None,
                '1':{'minutes':+15},
                '2':{'minutes':+30},
                '3':{'hours':+1},
                '4':{'hours':+6},
                '5':{'days':+1}
            }
            paste = database.Paste(paste=form.text.data)
            if (current_user.is_authenticated()):
                paste.user = current_user.to_dbref()
            paste.name = random_string()
            if times.get(form.expiration.data) is not None:
                paste.expire = arrow.utcnow().replace(**times.get(form.expiration.data)).datetime
            paste.save()
            return redirect('/{id}'.format(id=paste.name))
        return render_template('new_paste.html', form=form)

    @app.route('/<string:id>')
    def get(id):
        paste = database.Paste.objects(name__exact=id).first()
        if paste is None:
            abort(404)
        elif paste.expire is not None and arrow.get(paste.expire) < arrow.utcnow():
            abort(404)
        else:
            return render_template("paste.html", paste=paste, title=paste.id)



app.debug = app.config['DEBUG']

def run():
    app.run(
        host=app.config.get('HOST', None),
        port=app.config.get('PORT', None)
    )



