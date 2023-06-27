from pydantic import BaseModel


class OnlyFansUserAccount(BaseModel):
    id: int
    name: str
    username: str
    email: str
