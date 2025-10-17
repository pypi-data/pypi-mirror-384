from pydantic import BaseModel, RootModel
from typing import Any, Optional, List
from datetime import datetime as dt


class Clocking(BaseModel):
    id: int
    center: str
    ss: str
    datetime: dt
    action: Optional[str] = None


class ClockingList(RootModel[Any]):
    root: List[Clocking]
