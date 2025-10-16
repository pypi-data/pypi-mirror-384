# https://shiriev.ru/pydantic-two-way-mapping/
# https://docs.pydantic.dev/latest/migration/#changes-to-dataclasses
# https://docs.pydantic.dev/latest/concepts/dataclasses/#dataclass-config
# https://docs.pydantic.dev/latest/migration/#changes-to-config
# https://www.youtube.com/watch?app=desktop&v=Z0a0Vjd992I

from typing import Optional

from pydantic import BaseModel, Field


class UserInfoVO(BaseModel):
    name: Optional[str] = ""
    given_name: Optional[str] = ""
    family_name: Optional[str] = ""
    preferred_username: Optional[str] = ""
    email: Optional[str] = ""
    email_verified: Optional[bool] = False
    resource_access: dict = {}
    sub: str = ""


class TokenInfoVO(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    scope: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    session_state: str


class AuthorizeInfoVO(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    scope: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    user_info: UserInfoVO = Field(alias="userinfo")
