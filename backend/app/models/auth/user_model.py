from pydantic import BaseModel, EmailStr
from uuid import uuid4

class User(BaseModel):
    id: str = str(uuid4())
    username: str
    email: EmailStr
    full_name: str
    password: str