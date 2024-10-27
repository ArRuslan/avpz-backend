from base64 import b64encode, b64decode
from os import environ, urandom

IS_DEBUG = str(environ.get("IS_DEBUG")).lower() in ("true", "1")

if IS_DEBUG:  # pragma: no cover
    DB_CONNECTION_STRING = environ.get("DB_CONNECTION_STRING", "sqlite://:memory:")
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 6)
else:  # pragma: no cover
    DB_CONNECTION_STRING = environ["DB_CONNECTION_STRING"]
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 12)

JWT_KEY = b64decode(environ.get("JWT_KEY", b64encode(urandom(32)).decode("utf8")))

RECAPTCHA_SECRET = environ.get("RECAPTCHA_SECRET")
if RECAPTCHA_SECRET is None:  # pragma: no cover
    import warnings
    warnings.warn("RECAPTCHA_SECRET is not set!")

try:
    AUTH_JWT_TTL = int(environ.get("AUTH_JWT_TTL", 86400))
except ValueError:  # pragma: no cover
    AUTH_JWT_TTL = 86400

try:
    AUTH_REFRESH_JWT_TTL = int(environ.get("AUTH_REFRESH_JWT_TTL", AUTH_JWT_TTL * 7))
except ValueError:  # pragma: no cover
    AUTH_REFRESH_JWT_TTL = AUTH_JWT_TTL * 7
