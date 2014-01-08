__author__ = 'zifnab'
from flask import abort, render_template, request, redirect
from datetime import datetime
from flask_login import current_user
from flask_wtf import Form
from wtforms import TextAreaField, SelectField
from wtforms.validators import *

from blueprints.auth.models import User

from blueprints.paste import blueprint
from blueprints.paste.models import Paste

class PasteForm(Form):
    text = TextAreaField('Paste Here', validators=[Required()])
    expiration = SelectField('Expiration', choices=[('0', 'Never'), ('1', 'Fifteen Minutes'), ('2', 'Thirty Minutes'), ('3', 'One Hour'), ('4', 'Six Hours'), ('5', 'One Day')])

@blueprint.route('/')
def main():
    return render_template('index.html', title='zifb.in')
@blueprint.route('/new', methods=('POST', 'GET'))
def new():
    form = PasteForm(request.form)
    if form.validate_on_submit():
        paste = Paste(paste=form.text.data)
        if (current_user.is_authenticated()):
            paste.user = current_user.to_dbref()
        paste.save()
        return redirect('/{id}'.format(id=paste.name))
    return render_template('new_paste.html', form=form)

@blueprint.route('/<string:id>')
def get(id):
    paste = Paste.objects(name__exact=id).first()
    if paste is None:
        abort(404)
    elif paste.expire > datetime.utcnow:
        abort(404)
    else:
        return render_template("paste.html", paste=paste, title=paste.id)
