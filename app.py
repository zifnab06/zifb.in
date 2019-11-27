from flask import (
    Flask,
    redirect,
    request,
    render_template,
    abort,
    Response,
    url_for,
)
from flask_mongoengine import MongoEngine
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import (
    current_user,
    fresh_login_required,
)
from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, SelectField, SubmitField
from wtforms.validators import Required
from datetime import datetime

import pygments
from pygments.lexers import guess_lexer, get_lexer_by_name, get_all_lexers
from markdown2 import markdown
from util import random_string

import database
import html
import pendulum

from hashlib import sha1

from werkzeug.routing import BaseConverter

app = Flask(__name__)


class SHA1Converter(BaseConverter):
    def __init__(self, map):
        super(SHA1Converter, self).__init__(map)
        self.regex = "[A-Za-z0-9]{40}"


app.url_map.converters["sha1"] = SHA1Converter

with app.app_context():

    @app.route("/<string:id>")
    @app.route("/<sha1:digest>")
    def get(id=None, digest=None):
        if id:
            paste = database.Paste.objects(name__exact=id).first()
        if digest:
            paste = database.Paste.objects(digest__exact=digest).first()

        if not paste:
            abort(404)
        elif paste.expire and paste.expire < pendulum.now("utc").naive():
            paste.delete()
            abort(404)
        else:
            return render_paste(paste, title=paste.id)

    import auth  # noqa: F401
    import config

    app.config.from_object(config)
    app.config["DEBUG_TB_PANELS"] = [
        "flask_debugtoolbar.panels.versions.VersionDebugPanel",
        "flask_debugtoolbar.panels.timer.TimerDebugPanel",
        "flask_debugtoolbar.panels.headers.HeaderDebugPanel",
        "flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel",
        "flask_debugtoolbar.panels.template.TemplateDebugPanel",
        "flask_debugtoolbar.panels.logger.LoggingPanel",
        "flask_debugtoolbar.panels.profiler.ProfilerDebugPanel",
        "flask_mongoengine.panels.MongoDebugPanel",
    ]

    @app.template_filter("prettytime")
    def format_datetime(value, format="medium"):
        return pendulum.instance(value).to_datetime_string()

    @app.template_filter("humanize")
    def humanize_date(value):
        return pendulum.instance(value).diff_for_humans()

    db = MongoEngine(app)
    import admin  # noqa: F401

    toolbar = DebugToolbarExtension(app)

    from api import v1  # noqa: F401

    def get_lexers():
        yield ("none", "Automatically Detect")
        yield ("markdown", "markdown")
        for lexer in sorted(get_all_lexers()):
            yield (lexer[1][0], lexer[0])

    class PasteForm(FlaskForm):
        text = TextAreaField("Paste Here", validators=[Required()])
        expiration = SelectField(
            "Expiration",
            choices=[
                ("0", "Never"),
                ("1", "Fifteen Minutes"),
                ("2", "Thirty Minutes"),
                ("3", "One Hour"),
                ("4", "Six Hours"),
                ("5", "Twelve Hours"),
                ("6", "One Day"),
                ("7", "One Week"),
                ("8", "One Month"),
            ],
            default="6",
        )

        language = SelectField("Language", choices=[i for i in get_lexers()])

    class PasteFormNoAuth(PasteForm):
        expiration = SelectField(
            "Expiration",
            choices=[
                ("1", "Fifteen Minutes"),
                ("2", "Thirty Minutes"),
                ("3", "One Hour"),
                ("4", "Six Hours"),
                ("5", "Twelve Hours"),
                ("6", "One Day"),
                ("7", "One Week"),
                ("8", "One Month"),
            ],
            default="6",
        )

    class ConfirmForm(FlaskForm):
        confirm = SubmitField("Click here to confirm deletion", validators=[Required()])

    @app.route("/", methods=("POST", "GET"))
    @app.route("/new", methods=("POST", "GET"))
    def main():
        if current_user.is_authenticated:
            form = PasteForm(request.form)
        else:
            form = PasteFormNoAuth(request.form)

        if form.validate_on_submit():

            times = {
                "0": None,
                "1": {"minutes": +15},
                "2": {"minutes": +30},
                "3": {"hours": +1},
                "4": {"hours": +6},
                "5": {"hours": +12},
                "6": {"days": +1},
                "7": {"weeks": +1},
                "8": {"months": +1},
            }
            paste = database.Paste()

            paste.paste = form.text.data
            paste.digest = sha1(paste.paste.encode("utf-8")).hexdigest()

            if current_user.is_authenticated:
                paste.user = current_user.to_dbref()
            # Create a name and make sure it doesn't exist
            paste.name = random_string()
            collision_check = database.Paste.objects(name__exact=paste.name).first()
            while collision_check:
                paste.name = random_string()
                collision_check = database.Paste.objects(name__exact=paste.name).first()

            if form.language.data:
                paste.language = form.language.data
            else:
                try:
                    paste.language = guess_lexer(form.text.data).name
                except pygments.util.ClassNotFound:
                    paste.language = "text"
            paste.time = datetime.utcnow()

            if times.get(form.expiration.data):
                paste.expire = pendulum.now("utc").add(
                    **times.get(form.expiration.data)
                )
            if (
                not times.get(form.expiration.data)
                and not current_user.is_authenticated
            ):
                paste.expire = pendulum.now("utc").add(**times.get(7))

            paste.save()
            return redirect("/{id}".format(id=paste.name))

        return render_template("new_paste.html", form=form)

    @app.route("/my")
    def my():
        if not current_user.is_authenticated:
            abort(403)
        pastes = database.Paste.objects(user=current_user.to_dbref()).order_by(
            "-expire", "-time"
        )
        if pastes.count() == 0:
            pastes = None
        return render_template("my_pastes.html", pastes=pastes, title="My Pastes")

    @app.route("/raw/<string:id>")
    @app.route("/raw/<sha1:digest>")
    def raw(id=None, digest=None):
        if id:
            paste = database.Paste.objects(name__exact=id).first()
        if digest:
            paste = database.Paste.objects(digest__exact=digest).first()

        if not paste:
            abort(404)
        else:
            return Response(paste.paste, mimetype="text/plain")

    @app.route("/settings")
    @fresh_login_required
    def settings():
        keys = database.ApiKey.objects(user=current_user.to_dbref())
        return render_template("settings.html", keys=keys)

    @app.route("/settings/new_api_key", methods=("POST",))
    @fresh_login_required
    def new_api_key():
        key = random_string(size=32)
        api_key = database.ApiKey(user=current_user.to_dbref(), key=key)
        api_key.save()
        return redirect(url_for("settings"))

    @app.route("/settings/delete_api_key/<string:key>", methods=("POST",))
    @fresh_login_required
    def delete_api_key(key):
        api_key = database.ApiKey.objects(key=key).first()
        if api_key and api_key.user.to_dbref() == current_user.to_dbref():
            api_key.delete()
        else:
            abort(403)
        return redirect(url_for("settings"))

    @app.route("/<string:id>/delete", methods=("POST",))
    def delete(id):
        paste = database.Paste.objects(name=id).first()
        if not paste:
            abort(404)
        if paste.user.to_dbref() != current_user.to_dbref():
            abort(403)
        paste.delete()
        return redirect("/my")

    def htmlify(string, language=None):
        """
        Takes a string, and returns an html encoded string with color formatting
        """
        if not language:
            try:
                lexer = guess_lexer(string)
            except pygments.util.ClassNotFound:
                lexer = get_lexer_by_name("text")
        else:
            try:
                lexer = get_lexer_by_name(language)
            except pygments.util.ClassNotFound:
                lexer = get_lexer_by_name("text")

        format = pygments.formatters.HtmlFormatter(linenos="inline")
        return pygments.highlight(string, lexer, format)

    def render_paste(paste, title=None):
        if not title:
            title = paste.id
        text = paste.paste
        text = text.rstrip("\n")
        text += "\n"
        lines = len(text.split("\n"))
        if paste.language == "none" or not paste.language:
            try:
                paste.language = guess_lexer(text).name
            except pygments.util.ClassNotFound:
                paste.language = "text"
            text = htmlify(text, paste.language)
        elif paste.language == "markdown":
            text = markdown(html.escape(text.replace("!", "\\!")))
        else:
            text = htmlify(text, paste.language)
        paste.views += 1
        paste.save()

        return render_template(
            "paste.html", paste=paste, title=title, text=text, lines=lines
        )


@app.cli.command()
def remove_expired():
    for paste in database.Paste.objects(expire__lt=pendulum.now("utc")):
        print(f"delete {paste.name}")
        paste.delete()


app.debug = app.config["DEBUG"]


def run():
    app.run()
