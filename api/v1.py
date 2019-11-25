import json

from app import app, database
from util import random_string
from flask import request
from hashlib import sha1

import pendulum

@app.route('/api/v1/paste', methods=('POST',))
def paste():
    paste = None
    language = None
    user = None
    expiration = None
    domain = 'https://zifb.in/'
    try:
        data = json.loads(request.data)
    except ValueError:
        return json.dumps({'error': 'invalid json'}), 400

    #Get Paste
    if not data.has_key('paste'):
        return json.dumps({'error': 'paste not found'}), 400
    paste = data.get('paste')

    #Get Language
    if data.has_key('language'):
        language = data.get('language')

    #Get API_KEY/User
    if data.has_key('api_key'):
        user = database.ApiKey.objects(key=data.get('api_key')).first().user

    #Get Expiration
    if data.has_key('expiration'):
        s = data.get('expiration')
        try:
            s = int(s)
        except ValueError:
            return json.dumps({'error': 'invalid expiration format, should be number of seconds'})
        if s is None or s == 0:
            expiration = None
        else:
            expiration = pendulum.now("UTC").add(seconds=s)

    if not user and not expiration:
        expiration = pendulum.now("UTC").add(hours=1)

    #Get Domain
    if data.has_key('domain'):
        domain = 'https://{0}/'.format(data.get('domain'))

    paste = database.Paste(name='testing', paste=paste, digest=sha1(paste.encode('utf-8')).hexdigest(), time=pendulum.now('utc'),
                           expire=expiration, user=user, language=language)
    paste.name = random_string()
    while database.Paste.objects(name=paste.name).first():
        paste.name = random_string()

    paste.save()
    return json.dumps({'paste': '{0}{1}'.format(domain, paste.name),
                       'expires': pendulum.instance(paste.expire).to_datetime_string()})
