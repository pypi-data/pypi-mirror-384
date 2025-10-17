from typing import Optional, Union
from pydantic import BaseModel


class JWT(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[Union[str, int]] = None


class KwargRelation(BaseModel):
    inner: str
    outer: str
    pop_inner: Optional[bool] = True
