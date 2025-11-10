from typing import Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ConfigDict,
    StringConstraints,
)


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    area_id: int | None = Field(None, gt=0)
    empresa_id: int = Field(..., gt=0)
    first_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]

    # noinspection PyDecorato
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    # noinspection PyDecorator
    @field_validator("first_name", "last_name")
    @classmethod
    def names_without_digits(cls, v: str) -> str:
        if any(ch.isdigit() for ch in v):
            raise ValueError("El nombre no debe contener números.")
        return v

    # noinspection PyDecorator
    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_symbol = any(not c.isalnum() for c in v)
        if not (has_upper and has_lower and has_digit and has_symbol):
            raise ValueError(
                "La contraseña debe incluir mayúsculas, minúsculas, números y símbolos."
            )
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
