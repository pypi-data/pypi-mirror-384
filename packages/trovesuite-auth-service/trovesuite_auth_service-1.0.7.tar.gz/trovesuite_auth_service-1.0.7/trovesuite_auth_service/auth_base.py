from pydantic import BaseModel

class AuthBase(BaseModel):
    token: str
