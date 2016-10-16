___author__ = 'zifnab'
from flask import Flask, redirect, request, render_template, flash, abort, Response, url_for
from flask_mongoengine import MongoEngine
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, fresh_login_required
from flask_wtf import FlaskForm, RecaptchaField
from wtforms.fields import *
from wtforms.validators import *
from passlib.hash import sha512_crypt
from datetime import datetime, timedelta, date
from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from markdown2 import markdown
from simplecrypt import encrypt, decrypt
from binascii import hexlify
from util import random_string
import database
import arrow
import cgi
import string

from hashlib import sha1

from werkzeug.routing import BaseConverter

app = Flask(__name__)

class SHA1Converter(BaseConverter):
    def __init__(self, map):
        super(SHA1Converter, self).__init__(map)
        self.regex = '[A-Za-z0-9]{40}'

app.url_map.converters['sha1'] = SHA1Converter

with app.app_context():

    @app.route('/<string:id>')
    @app.route('/<sha1:digest>')
    def get(id=None, digest=None):
        if id:
            paste = database.Paste.objects(name__exact=id).first()
        if digest:
            paste = database.Paste.objects(digest__exact=digest).first()

        if paste is None:
            abort(404)
        elif paste.expire is not None and arrow.get(paste.expire) < arrow.utcnow():
            paste.delete()
            abort(404)
        else:
            return render_paste(paste, title=paste.id)

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
        'flask_mongoengine.panels.MongoDebugPanel'
        ]
    @app.template_filter('prettytime')
    def format_datetime(value, format='medium'):
        return arrow.get(value).format('YYYY-MM-DD HH:mm')

    @app.template_filter('humanize')
    def humanize_date(value):
        return arrow.get(value).humanize()



    db = MongoEngine(app)
    import admin
    toolbar = DebugToolbarExtension(app)

    from api import v1

    def get_lexers():
        yield ('none', 'Automatically Detect')
        yield ('markdown', 'markdown')
        for lexer in sorted(get_all_lexers()):
            yield (lexer[1][0], lexer[0])

    class PasteForm(FlaskForm):
        text = TextAreaField('Paste Here', validators=[Required()])
        expiration = SelectField('Expiration', choices=[('0', 'Expires Never'),
                                                        ('1', 'Expires In Fifteen Minutes'),
                                                        ('2', 'Expires In Thirty Minutes'),
                                                        ('3', 'Expires In One Hour'),
                                                        ('4', 'Expires In Six Hours'),
                                                        ('5', 'Expires in Twelve Hours'),
                                                        ('6', 'Expires In One Day'),
                                                        ('7', 'Expires in One Week'),
                                                        ('8', 'Expires in One Month')], default='6')

        language = SelectField('Language', choices=[i for i in get_lexers()])

    class PasteFormNoAuth(PasteForm):
        expiration = SelectField('Expiration', choices=[('1', 'Expires In Fifteen Minutes'),
                                                        ('2', 'Expires In Thirty Minutes'),
                                                        ('3', 'Expires In One Hour'),
                                                        ('4', 'Expires In Six Hours'),
                                                        ('5', 'Expires in Twelve Hours'),
                                                        ('6', 'Expires In One Day'),
                                                        ('7', 'Expires in One Week'),
                                                        ('8', 'Expires in One Month')], default='6')


    class ConfirmForm(FlaskForm):
        confirm = SubmitField('Click here to confirm deletion', validators=[Required()])

    @app.route('/', methods=('POST', 'GET'))
    @app.route('/new', methods=('POST', 'GET'))
    def main():
        if current_user.is_authenticated():
            form = PasteForm(request.form)
        else:
            print 'test'
            form = PasteFormNoAuth(request.form)

        if form.validate_on_submit():

            times = {
                '0':None,
                '1':{'minutes':+15},
                '2':{'minutes':+30},
                '3':{'hours':+1},
                '4':{'hours':+6},
                '5':{'hours':+12},
                '6':{'days':+1},
                '7':{'weeks':+1},
                '8':{'months':+1}
            }
            paste = database.Paste()

            paste.paste = form.text.data
            paste.digest = sha1(paste.paste.encode('utf-8')).hexdigest()

            if (current_user.is_authenticated()):
                paste.user = current_user.to_dbref()
            #Create a name and make sure it doesn't exist
            paste.name = random_string()
            collision_check = database.Paste.objects(name__exact=paste.name).first()
            while collision_check is not None:
                paste.name = random_string()
                collision_check = database.Paste.objects(name__exact=paste.name).first()

            if form.language.data is not None:
                paste.language = form.language.data
            else:
                try:
                    paste.language = guess_lexer(form.text.data).name
                except:
                    paste.language = 'text'
            paste.time = datetime.utcnow()

            if times.get(form.expiration.data) is not None:
                paste.expire = arrow.utcnow().replace(**times.get(form.expiration.data)).datetime
            if times.get(form.expiration.data) is None and not current_user.is_authenticated():
                paste.expire = arrow.utcnow.replace(**times.get(7))

            paste.save()
            return redirect('/{id}'.format(id=paste.name))


        return render_template('new_paste.html', form=form)

    @app.route('/my')
    def my():
        if not current_user.is_authenticated():
            abort(403)
        pastes = database.Paste.objects(user=current_user.to_dbref()).order_by('-expire', '-time')
        if pastes.count() == 0:
            pastes = None
        return render_template("my_pastes.html", pastes=pastes, title="My Pastes")


    @app.route('/raw/<string:id>')
    @app.route('/raw/<sha1:digest>')
    def raw(id=None, digest=None):
        if id:
            paste = database.Paste.objects(name__exact=id).first()
        if digest:
            paste = database.Paste.objects(digest__exact=digest).first()

        if paste is None:
            abort(404)
        else:
            return Response(paste.paste, mimetype="text/plain")

    @app.route('/settings')
    @fresh_login_required
    def settings():
        keys = database.ApiKey.objects(user=current_user.to_dbref())
        return render_template('settings.html', keys=keys)

    @app.route('/settings/new_api_key', methods=('POST',))
    @fresh_login_required
    def new_api_key():
        key = random_string(size=32)
        api_key = database.ApiKey(user=current_user.to_dbref(), key=key)
        api_key.save()
        return redirect(url_for('settings'))

    @app.route('/settings/delete_api_key/<string:key>', methods=('POST',))
    @fresh_login_required
    def delete_api_key(key):
        api_key = database.ApiKey.objects(key=key).first()
        print not api_key
        print api_key.user == current_user.to_dbref()
        if api_key and api_key.user.to_dbref() == current_user.to_dbref():
            api_key.delete()
        else:
            abort(403)
        return redirect(url_for('settings'))

    @app.route('/<string:id>/delete', methods=('POST',))
    def delete(id):
        paste = database.Paste.objects(name=id).first()
        if not paste:
            abort(404)
        if paste.user.to_dbref() != current_user.to_dbref():
            abort(403)
        paste.delete()
        return redirect('/my')


    def htmlify(string, language=None):
        '''
        Takes a string, and returns an html encoded string with color formatting
        '''
        if language is None:
            try:
                lexer = guess_lexer(string)
            except:
                lexer = get_lexer_by_name('text')
        else:
            try:
                lexer = get_lexer_by_name(language)
            except:
                lexer = get_lexer_by_name('text')

        format = HtmlFormatter()
        return highlight(string, lexer, format)

    def render_paste(paste, title=None):
        if not title:
            title = paste.id
        text = paste.paste
        text = text.rstrip('\n')
        text += '\n'
        lines = len(text.split('\n'))
        if paste.language == 'none' or paste.language is None:
            try:
                paste.language = guess_lexer(text).name
            except:
                paste.language = 'text'
            text=htmlify(text, paste.language)
        elif paste.language == 'markdown':
            text=markdown(cgi.escape(text.replace('!','\\!')))
        else:
            text=htmlify(text, paste.language)
        paste.views += 1
        paste.save()



        return render_template("paste.html", paste=paste, title=title, text=text, lines=lines)

@app.cli.command()
def remove_expired():
    for paste in database.Paste.objects(expire__lt=arrow.now().datetime):
        print 'delete {0}'.format(paste.name)
        paste.delete()


app.debug = app.config['DEBUG']

def run():
    app.run()
