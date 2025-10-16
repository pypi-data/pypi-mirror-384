from __future__ import annotations

from typing import Optional, List, Union
from pydantic import BaseModel
from datetime import date, datetime


class Transaction(BaseModel):
    id: Optional[int]
    emp_code: Optional[int]
    punch_time: Optional[Union[datetime, date]]
    punch_state: Optional[str]
    verify_type: Optional[int]
    work_code: Optional[str]
    terminal_sn: Optional[str]
    terminal_alias: Optional[str]
    area_alias: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    gps_location: Optional[str]
    mobile: Optional[str]
    source: Optional[int]
    purpose: Optional[int]
    crc: Optional[str]
    is_attendance: Optional[int]
    reserved: Optional[str]
    upload_time: Optional[Union[datetime, date]]
    sync_status: Optional[int]
    sync_time: Optional[Union[datetime, date]]
    is_mask: Optional[int]
    temperature: Optional[float]
    emp_id: Optional[int]
    terminal_id: Optional[int]


class TransactionPage(BaseModel):
    items: Optional[List[Transaction]]
    total: Optional[int]
    page: Optional[int]
    size: Optional[int]
    pages: Optional[int]
