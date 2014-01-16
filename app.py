__author__ = 'zifnab'
from flask import Flask, redirect, request, render_template, flash, abort
from mongoengine import connect
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import Form, RecaptchaField
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt
from datetime import datetime, timedelta, date
import database
import arrow
import babel

from util import random_string




app = Flask(__name__)

with app.app_context():
    import auth
    from config import local_config
    app.config.from_object(local_config)
    app.config['DEBUG_TB_PANELS'] = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'flask_debugtoolbar_mongo.panel.MongoDebugPanel'
        ]
    @app.template_filter('prettytime')
    def format_datetime(value, format='medium'):
        return arrow.get(value).format('YYYY-MM-DD HH:MM')

    @app.template_filter('humanize')
    def humanize_date(value):
        return arrow.get(value).humanize()



    db = connect('zifbin')
    import admin
    toolbar = DebugToolbarExtension(app)

    class PasteForm(Form):
        text = TextAreaField('Paste Here', validators=[Required()])
        expiration = SelectField('Expiration', choices=[('0', 'Forever Visible'),
                                                        ('1', 'Visible For Fifteen Minutes'),
                                                        ('2', 'Visible For Thirty Minutes'),
                                                        ('3', 'Visible For One Hour'),
                                                        ('4', 'Visible For Six Hours'),
                                                        ('5', 'Visible For One Day')], default='4')
    class PasteFormRecaptcha(PasteForm):
        recaptcha = RecaptchaField()
        expiration = SelectField('Expiration', choices=[('0', 'Expires Never'),
                                                        ('1', 'Expires In Fifteen Minutes'),
                                                        ('2', 'Expires In Thirty Minutes'),
                                                        ('3', 'Expires In One Hour'),
                                                        ('4', 'Expires In Six Hours'),
                                                        ('5', 'Expires In One Day')], default='4')

    class ConfirmForm(Form):
        confirm = SubmitField('Click here to confirm deletion', validators=[Required()])


    @app.route('/', methods=('POST', 'GET'))
    @app.route('/new', methods=('POST', 'GET'))
    def main():
        if current_user.is_authenticated():
            form = PasteForm(request.form)
        else:
            form = PasteFormRecaptcha(request.form)
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
            #Create a name and make sure it doesn't exist
            paste.name = random_string()
            collision_check = database.Paste.objects(name__exact=paste.name).first()
            while collision_check is not None:
                paste.name = random_string()
                collision_check = database.Paste.objects(name__exact=paste.name).first()

            paste.time = datetime.utcnow()

            if times.get(form.expiration.data) is not None:
                paste.expire = arrow.utcnow().replace(**times.get(form.expiration.data)).datetime
            paste.save()
            return redirect('/{id}'.format(id=paste.name))
        return render_template('new_paste.html', form=form)
    @login_required
    @app.route('/my')
    def my():
        pastes = database.Paste.objects(user=current_user.to_dbref())
        if pastes.count() == 0:
            pastes = None
        return render_template("my_pastes.html", pastes=pastes, title="My Pastes")

    @login_required
    @app.route('/<string:id>/delete', methods=('POST', 'GET'))
    def delete(id):
        paste = database.Paste.objects(name__exact=id).first()
        if paste is None:
            abort(404)
        if not paste.user.username == current_user.username:
            abort(403)
        #confirm action
        form = ConfirmForm(request.form)

        if request.method == 'POST' and form.confirm.data:
            paste.delete()
            flash('Paste was removed', 'info')
            return redirect('/')
        return render_template("paste.html", form=form, paste=paste, title='Delete Paste')


    #THIS ROUTE NEEDS TO BE LAST
    @app.route('/<string:id>')
    def get(id):
        paste = database.Paste.objects(name__exact=id).first()

        if paste is None:
            abort(404)
        elif paste.user.username == current_user.username:
            return render_template("paste.html", paste=paste, title=paste.id, owned=True)
        elif paste.expire is not None and arrow.get(paste.expire) < arrow.utcnow():
            if paste.user is None:
                paste.delete()
            abort(404)
        else:
            paste.views = paste.views + 1
            paste.save()
            return render_template("paste.html", paste=paste, title=paste.id)




app.debug = app.config['DEBUG']

def run():
    app.run(
        host=app.config.get('HOST', None),
        port=app.config.get('PORT', None)
    )



