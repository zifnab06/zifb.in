from app import app, database
from util import random_string
from flask import request
from flask.views import MethodView
from hashlib import sha1

import arrow

import json

class PasteAPI(MethodView):

    def get(self, digest=None, name=None):
        '''get a paste and turn it to json
           flask deals with digest/name routing'''
        if digest:
            paste = database.Paste.objects(digest__exact=digest).first()
        if name:
            paste = database.Paste.objects(name__exact=name).first()
        return json.dumps({'name': paste.name, 'paste': paste.paste, 'digest': paste.digest,
                           'time': str(paste.time), 'expire': str(paste.expire) if paste.expire else None,
                           'user': str(paste.user), 'views': paste.views, 'language': paste.language})
    def post(self):
        ''make a new paste''
        try:
            data = json.loads(request.data)
        except ValueError:
            #json.loads throws ValueError if json can't be decoded
            return json.dumps({'error': 'invalid json'})
        if not 'paste' in data:
            #make sure a paste actually exists
            return json.dumps({'error': 'paste required'})

        paste = database.Paste()
        paste.name = random_string()
        #deduplicate paste name
        while database.Paste.objects(name=paste.name).first():
            paste.name = random_string()
        paste.paste = data['paste']
        paste.language = data['language'] if 'language' in data else None #TODO: autodetect language here
        paste.user = database.ApiKey.objects(key=data['api_key']).first().user if 'api_key' in data else None #TODO errors if api_key is invalid, need to catch
        paste.digest = sha1(paste.paste.encode('utf-8')).hexdigest()
        paste.time = arrow.utcnow().datetime
        if 'expiration' in data:
            #expiration needs to be a time in seconds, >0
            try:
                seconds = int(data['expiration'])
                if seconds < 0:
                    return json.dumps({'error': 'cannot expire in the past'})
                if seconds > 0:
                    paste.expire = arrow.utcnow().replace(seconds=+seconds)
            except ValueError:
                return json.dumps({'error': 'invalid expiration format, should be number of seconds'})

        paste.save()
        #domain is optional, no validation done. if you feel like using one of the alternatives (vomitb.in, not-pasteb.in), set the domain before sending the paste
        return 'https://{domain}/{name}'.format(domain=data['domain'] if 'domain' in data else 'zifb.in', name=paste.name)

    def delete(self, digest=None, name=None):
        '''delete a paste, either by name or digest. verify user is owner'''
        try:
            data = json.loads(request.data)
        except ValueError:
            return json.dumps({'error': 'invalid json'})
        if not 'api_key' in data:
            #require an api key
            return json.dumps({'error': 'api_key required'})
        user = database.ApiKey.objects(key=data['api_key']).first().user
        if digest:
            paste = database.Paste.objects(user=user, digest=digest).first()
        elif name:
            paste = database.Paste.objects(user=user, name=name).first()
        if not paste:
            return json.dumps({'error': 'paste not found'})
        #paste is guaranteed to be owned by the same user as the apikey at this point
        paste.delete()
        return json.dumps({'sucess': 1})

class UserAPI(MethodView):
   
    def get(self):
        '''get stats about the user. requires API key'''
        pass
    def post(self):
        '''creates a new user'''
        pass

class APIKeyAPI(MethodView):

    def get(self):
        '''get stats about the user the API key is attached to'''
        pass
    def post(self):
        '''creates a new api key. requires username/password'''
        pass
    def delete(self):
        '''deletes an apikey. requires username/password'''
        pass

paste_api_view = PasteAPI.as_view('paste-api')
app.add_url_rule('/api/v2/paste/', view_func=paste_api_view, methods=['POST'])
app.add_url_rule('/api/v2/paste/<sha1:digest>/', view_func=paste_api_view, methods=['GET', 'DELETE'])
app.add_url_rule('/api/v2/paste/<string:name>/', view_func=paste_api_view, methods=['GET', 'DELETE'])
app.add_url_rule('/api/v2/user/', view_func=UserAPI.as_view('user_api'))
app.add_url_rule('/api/v2/key/', view_func=APIKeyAPI.as_view('apikey-api'))
