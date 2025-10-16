from __future__ import annotations

from typing import Optional, List, Union
from pydantic import BaseModel
from datetime import date, datetime


class ListModel(BaseModel):
    count: Optional[int]
    next: Optional[str]
    previous: Optional[str]
    msg: Optional[str]
    code: int
    data: Optional[List]


class Company(BaseModel):
    id: Optional[int]
    company_code: Optional[str]
    company_name: Optional[str]


class CompanyList(ListModel):
    data: Optional[List[Company]]


class Area(BaseModel):
    id: Optional[int]
    area_code: Optional[str]
    area_name: Optional[str]
    parent_area: Optional[Union[Area, int]]
    parent_area_name: Optional[str]
    company: Optional[Union[Company, int]]


class AreaList(ListModel):
    data: Optional[List[Area]]


class Department(BaseModel):
    id: Optional[int]
    dept_code: Optional[str]
    dept_name: Optional[str]
    parent_dept: Optional[Union[Department, int]]
    parent_dept_name: Optional[str]
    company: Optional[Union[Company, int]]


class DepartmentList(ListModel):
    data: Optional[List[Department]]


class Terminal(BaseModel):
    id: Optional[int]
    sn: Optional[str]
    ip_address: Optional[str]
    alias: Optional[str]
    terminal_name: Optional[str]
    fw_ver: Optional[str]
    push_ver: Optional[str]
    company: Optional[Union[Company, int]]
    company_code: Optional[str]
    company_name: Optional[str]
    state: Optional[int]
    state_name: Optional[str]
    terminal_tz: Optional[int]
    area: Optional[Union[Area, int]]
    area_name: Optional[str]
    last_activity: Optional[Union[date, datetime, str]]
    user_count: Optional[int]
    fp_count: Optional[int]
    face_count: Optional[int]
    palm_count: Optional[int]
    transaction_count: Optional[int]
    push_time: Optional[Union[date, datetime, str]]
    transfer_time: Optional[str]
    transfer_interval: Optional[int]
    is_attendance: Optional[bool]


class TerminalList(ListModel):
    data: Optional[List[Terminal]]


class Position(BaseModel):
    id: Optional[int]
    position_code: Optional[str]
    position_name: Optional[str]
    parent_position: Optional[Union[Position, int]]
    parent_position_name: Optional[str]
    company: Optional[Union[Company, int]]


class PositionList(ListModel):
    data: Optional[List[Position]]


class Employee(BaseModel):
    id: Optional[int]
    emp_code: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    nickname: Optional[str]
    device_password: Optional[str]
    card_no: Optional[str]
    department: Optional[Union[Department, int]]
    company: Optional[Union[Company, int]]
    dept_name: Optional[str]
    position: Optional[Union[Position, int]]
    position_name: Optional[str]
    hire_date: Optional[Union[date, datetime, str]]
    gender: Optional[str]
    birthday: Optional[Union[date, datetime]]
    verify_mode: Optional[Union[str, int]]
    emp_type: Optional[Union[str, int]]
    contact_tel: Optional[str]
    office_tel: Optional[str]
    mobile: Optional[str]
    national: Optional[str]
    city: Optional[str]
    address: Optional[str]
    postcode: Optional[str]
    email: Optional[str]
    enroll_sn: Optional[str]
    ssn: Optional[str]
    religion: Optional[str]
    enable_att: Optional[bool]
    enable_overtime: Optional[bool]
    enable_holiday: Optional[bool]
    dev_privilege: Optional[Union[bool, str]]
    self_password: Optional[str]
    flow_role: Optional[list]
    area: Optional[List[Union[Area, int]]]
    area_name: Optional[str]
    app_status: Optional[int]
    app_role: Optional[Union[str, int]]
    update_time: Optional[Union[date, datetime, str]]
    fingerprint: Optional[str]
    face: Optional[str]
    palm: Optional[str]
    v1_face: Optional[str]


class EmployeeList(ListModel):
    data: Optional[List[Employee]]


class WorkCode(BaseModel):
    id: Optional[int]
    code: Optional[str]
    alias: Optional[str]
    last_activity: Optional[Union[date, datetime, str]]


class WorkCodeList(ListModel):
    data: Optional[List[WorkCode]]


class Transaction(BaseModel):
    id: Optional[int]
    emp_code: Optional[str]
    punch_time: Optional[str]
    punch_state: Optional[Union[str, int]]
    verify_type: Optional[int]
    work_code: Optional[Union[str, int]]
    terminal_sn: Optional[str]
    terminal_alias: Optional[str]
    area_alias: Optional[str]
    longitude: Optional[str]
    latitude: Optional[str]
    gps_location: Optional[str]
    mobile: Optional[str]
    source: Optional[int]
    purpose: Optional[int]
    crc: Optional[str]
    is_attendance: Optional[int]
    reserved: Optional[bool]
    upload_time: Optional[Union[date, datetime, str]]
    sync_status: Optional[int]
    sync_time: Optional[Union[date, datetime, str]]
    is_mask: Optional[Union[bool, int, str]]
    temperature: Optional[Union[float, int, str]]
    emp: Optional[Union[int, Employee]]
    terminal: Optional[Union[int, Terminal]]


class TransactionList(ListModel):
    data: Optional[List[Transaction]]


class Message(BaseModel):
    id: Optional[int]
    terminal: Optional[Union[Terminal, int]]
    start_time: Optional[Union[date, datetime, str]]
    duration: Optional[int]
    content: Optional[str]
    company_name: Optional[str]
    last_send: Optional[Union[date, datetime, str]]
    terminal_sn: Optional[str]
    terminal_alias: Optional[str]


class PublicMessage(BaseModel):
    id: Optional[int]
    terminal: Optional[Union[Terminal, int]]


class PublicMessageList(ListModel):
    data: Optional[List[PublicMessage]]


class PrivateMessage(Message):
    employee: Optional[Union[Employee, int]]
    emp_code: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class PrivateMessageList(ListModel):
    data: Optional[List[PrivateMessage]]
