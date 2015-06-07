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
        paste.views += 1
        paste.save() 
        return json.dumps({'name': paste.name, 'paste': paste.paste, 'digest': paste.digest,
                           'time': str(paste.time), 'expire': str(paste.expire) if paste.expire else None,
                           'user': str(paste.user), 'views': paste.views, 'language': paste.language})
    def post(self):
        '''make a new paste'''
        if not 'paste' in request.form:
            return json.dumps({'error':'paste required'})
        if 'api_key' in request.form:
            user = database.ApiKey.objects(key=request.form['api_key']).first()
            if user:
                user = user.user
            else:
                return json.dumps({'error': 'invalid api_key'})
        paste = database.Paste()
        paste.name = random_string()
        #deduplicate paste name
        while database.Paste.objects(name=paste.name).first():
            paste.name = random_string()
        paste.paste = request.form['paste']
        paste.language = request.form['language'] if 'language' in request.form else None #TODO: autodetect language here
        paste.user = user
        paste.digest = sha1(paste.paste.encode('utf-8')).hexdigest()
        paste.time = arrow.utcnow().datetime
        if 'expiration' in request.form:
            #expiration needs to be a time in seconds, >0
            try:
                seconds = int(request.form['expiration'])
                if seconds < 0:
                    return json.dumps({'error': 'cannot expire in the past'})
                if seconds > 0:
                    paste.expire = arrow.utcnow().replace(seconds=+seconds)
            except ValueError:
                return json.dumps({'error': 'invalid expiration format, should be number of seconds'})

        paste.save()
        #domain is optional, no validation done. if you feel like using one of the alternatives (vomitb.in, not-pasteb.in), set the domain before sending the paste
        return json.dumps({'success': 1, 'url': 'https://{domain}/{name}'.format(domain=request.form['domain'] if 'domain' in request.form else 'zifb.in', name=paste.name)})

    def delete(self, digest=None, name=None):
        '''delete a paste, either by name or digest. verify user is owner'''
        if not 'api_key' in request.form:
            return json.dumps({'error': 'api_key required'})
        user = database.ApiKey.objects(key=request.form['api_key']).first()
        
        if not user:
            return json.dumps({'error': 'invalid api_key'})
        else:
            user = user.user
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
