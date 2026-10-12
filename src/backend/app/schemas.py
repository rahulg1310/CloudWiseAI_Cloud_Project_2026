from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    username: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
