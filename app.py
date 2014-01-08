__author__ = 'zifnab'
from flask import Flask

app = Flask(__name__)


with app.app_context():
    from config import local_config
    app.config.from_object(local_config)
    from config import blueprint_config
    app.config.from_object(blueprint_config)

for blueprint in app.config['BLUEPRINTS']:
    app.register_blueprint(**blueprint)

with app.app_context():
    from blueprints import base

app.debug = app.config['DEBUG']


def run():
    app.run(
        host=app.config.get('HOST', None),
        port=app.config.get('PORT', None)
    )


