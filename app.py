__author__ = 'zifnab'
from flask import Flask, redirect, request, render_template, flash, abort, Response
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
from pygments import highlight
from pygments.lexers import guess_lexer, get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from markdown2 import markdown
import cgi
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
        return arrow.get(value).format('YYYY-MM-DD HH:mm')

    @app.template_filter('humanize')
    def humanize_date(value):
        return arrow.get(value).humanize()



    db = connect('zifbin')
    import admin
    toolbar = DebugToolbarExtension(app)

    def get_lexers():
        yield ('none', 'Automatically Detect')
        yield ('markdown', 'markdown')
        for lexer in sorted(get_all_lexers()):
            yield (lexer[1][0], lexer[0])

    class PasteForm(Form):
        text = TextAreaField('Paste Here', validators=[Required()])
        expiration = SelectField('Expiration', choices=[('0', 'Expires Never'),
                                                        ('1', 'Expires In Fifteen Minutes'),
                                                        ('2', 'Expires In Thirty Minutes'),
                                                        ('3', 'Expires In One Hour'),
                                                        ('4', 'Expires In Six Hours'),
                                                        ('5', 'Expires in Twelve Hours'),
                                                        ('6', 'Expires In One Day')], default='0')
        language = SelectField('Language', choices=[i for i in get_lexers()])


    class PasteFormRecaptcha(PasteForm):
        recaptcha = RecaptchaField()
        expiration = SelectField('Expiration', choices=[('1', 'Expires In Fifteen Minutes'),
                                                        ('2', 'Expires In Thirty Minutes'),
                                                        ('3', 'Expires In One Hour'),
                                                        ('4', 'Expires In Six Hours'),
                                                        ('5', 'Expires in Twelve Hours'),
                                                        ('6', 'Expires In One Day')], default='6')


    class ConfirmForm(Form):
        confirm = SubmitField('Click here to confirm deletion', validators=[Required()])

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
                '5':{'hours':+12},
                '6':{'days':+1}
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

            if form.language.data is not None:
                paste.language = form.language.data
            else:
                paste.language = guess_lexer(paste.paste).name
            paste.time = datetime.utcnow()

            if times.get(form.expiration.data) is not None:
                paste.expire = arrow.utcnow().replace(**times.get(form.expiration.data)).datetime
            paste.save()
            return redirect('/{id}'.format(id=paste.name))


        return render_template('new_paste.html', form=form)

    @app.route('/my')
    def my():
        if not current_user.is_authenticated():
            abort(403)
        pastes = database.Paste.objects(user=current_user.to_dbref())
        if pastes.count() == 0:
            pastes = None
        return render_template("my_pastes.html", pastes=pastes, title="My Pastes")

    @app.route('/<string:id>/delete', methods=('POST', 'GET'))
    def delete(id):
        paste = database.Paste.objects(name__exact=id).first()
        if paste is None:
            abort(404)
        if paste.user is None:
            abort(403)
        if not paste.user.username == current_user.username:
            abort(403)
        #confirm action
        form = ConfirmForm(request.form)

        if request.method == 'POST' and form.confirm.data:
            paste.delete()
            flash('Paste was removed', 'info')
            return redirect('/')
        return render_paste(paste, current_user.is_authenticated() and paste.user and paste.user.username == current_user.username, title='Delete Post', form=form)
#        return render_template("paste.html", form=form, paste=paste, title='Delete Paste')


    @app.route('/<string:id>/raw')
    def raw(id):
        paste = database.Paste.objects(name__exact=id).first()
        if paste is None:
            abort(404)
        else:
            return Response(paste.paste, mimetype="text/plain")

    #THIS ROUTE NEEDS TO BE LAST
    @app.route('/<string:id>')
    def get(id):
        paste = database.Paste.objects(name__exact=id).first()

        if paste is None:
            abort(404)
        elif paste.expire is not None and arrow.get(paste.expire) < arrow.utcnow():
            paste.delete()
            abort(404)
        else:
            return render_paste(paste, current_user.is_authenticated() and paste.user and paste.user.username == current_user.username)


    def htmlify(string, language=None):
        '''
        Takes a string, and returns an html encoded string with color formatting
        '''
        if language is None:
            lexer = guess_lexer(string)
        else:
            try:
                lexer = get_lexer_by_name(language)
            except:
                lexer = guess_lexer(string)

        format = HtmlFormatter()
        return highlight(string, lexer, format)

    def render_paste(paste, owned, title=None, form=None):
        if not title:
            title = paste.id
        if paste.language == 'none' or paste.language is None:
            paste.language = guess_lexer(paste.paste).name
            text=htmlify(paste.paste, paste.language)
        elif paste.language == 'markdown':
            text=markdown(cgi.escape(paste.paste.replace('!','\\!')))
        else:
            text=htmlify(paste.paste, paste.language)
        paste.views += 1
        paste.save()
        return render_template("paste.html", paste=paste, title=title, text=text, form=form, owned=owned, markdown=markdown)





app.debug = app.config['DEBUG']

def run():
    app.run()



