from base64 import b64encode, b64decode
from os import environ, urandom

IS_DEBUG = str(environ.get("IS_DEBUG")).lower() in ("true", "1")

if IS_DEBUG:
    DB_CONNECTION_STRING = environ.get("DB_CONNECTION_STRING", "sqlite://:memory:")
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 6)
else:
    DB_CONNECTION_STRING = environ["DB_CONNECTION_STRING"]
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 12)

JWT_KEY = b64decode(environ.get("JWT_KEY", b64encode(urandom(32)).decode("utf8")))
