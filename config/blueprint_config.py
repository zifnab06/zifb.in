from blueprints import (auth, admin, paste)
BLUEPRINTS = [
    dict(blueprint=auth.blueprint),
    dict(blueprint=paste.blueprint)
]