from base64 import b64encode, b64decode
from os import environ, urandom

def _try_parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except ValueError:  # pragma: no cover
        return default


IS_DEBUG = str(environ.get("IS_DEBUG")).lower() in ("true", "1")

if IS_DEBUG:  # pragma: no cover
    DB_CONNECTION_STRING = environ.get("DB_CONNECTION_STRING", "sqlite://:memory:")
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 6)
    DONT_CREATE_TEST_DATA = str(environ.get("DONT_CREATE_TEST_DATA")).lower() in ("true", "1")
else:  # pragma: no cover
    DB_CONNECTION_STRING = environ["DB_CONNECTION_STRING"]
    BCRYPT_ROUNDS = environ.get("BCRYPT_ROUNDS", 12)
    DONT_CREATE_TEST_DATA = True

JWT_KEY = b64decode(environ.get("JWT_KEY", b64encode(urandom(32)).decode("utf8")))

RECAPTCHA_SECRET = environ.get("RECAPTCHA_SECRET")
if RECAPTCHA_SECRET is None:  # pragma: no cover
    import warnings
    warnings.warn("RECAPTCHA_SECRET is not set!")

AUTH_JWT_TTL = _try_parse_int(environ.get("AUTH_JWT_TTL", 86400), 86400)
AUTH_REFRESH_JWT_TTL = _try_parse_int(environ.get("AUTH_JWT_TTL", AUTH_JWT_TTL * 7), AUTH_JWT_TTL * 7)

SMTP_HOST = environ.get("SMTP_HOST", "127.0.0.1")
SMTP_PORT = _try_parse_int(environ.get("SMTP_PORT", 0), 0)

PUBLIC_HOST = environ.get("PUBLIC_HOST", "https://127.0.0.1:8080")

if IS_DEBUG:  # pragma: no cover
    PAYPAL_ID = environ.get("PAYPAL_ID", "PAYPAL_ID")
    if not PAYPAL_ID or PAYPAL_ID == "PAYPAL_ID":
        import warnings
        warnings.warn("PAYPAL_ID is not set!")
    PAYPAL_SECRET = environ.get("PAYPAL_SECRET", "PAYPAL_SECRET")
    if not PAYPAL_SECRET or PAYPAL_SECRET == "PAYPAL_SECRET":
        import warnings
        warnings.warn("PAYPAL_SECRET is not set!")
else:  # pragma: no cover
    PAYPAL_ID = environ["PAYPAL_ID"]
    PAYPAL_SECRET = environ["PAYPAL_SECRET"]
