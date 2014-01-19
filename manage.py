__author__ = 'zifnab'
from flask_script import Manager, Server
from app import app
from database import Paste
import arrow

manager=Manager(app)

manager.add_command('runserver', Server(host=app.config.get('HOST', '0.0.0.0'), port=app.config.get('PORT', 5000)))

@manager.command
def print_routes():
    for rule in app.url_map.iter_rules():
        print rule
@manager.command
def remove_expired():
    for paste in Paste.objects(expire__lt=arrow.now().datetime, user=None):
        print 'delete {0}'.format(paste.name)
        paste.delete()

if __name__ == '__main__':
    manager.run()