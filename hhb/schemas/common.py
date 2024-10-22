from pydantic import BaseModel


class CaptchaExpectedRequest(BaseModel):
    captcha_key: str | None = None
