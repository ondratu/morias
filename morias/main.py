from poorwsgi import app

from core.config import config

config.load(app.get_options())
application = app
