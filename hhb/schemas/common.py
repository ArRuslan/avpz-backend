from pydantic import BaseModel

from hhb import config


class CaptchaExpectedRequest(BaseModel):
    captcha_key: str | None = (
        "for-now-this-field-is-not-empty-for-backward-compatibility-reasons" if config.IS_DEBUG else None
    )
