from pydantic import BaseModel

class KeyWithTTL(BaseModel):
    key: str
    ttl: int