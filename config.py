import os

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False") == "True"
MONGODB_SETTINGS = { "db": os.environ.get("MONGODB_DB", "zifbin") }
