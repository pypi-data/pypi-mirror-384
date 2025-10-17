from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field, field_validator


ModelType = TypeVar("ModelType", bound=BaseModel)


class BearerToken(BaseModel):
    model_config = ConfigDict(extra="allow")
    token: str = Field(alias="Bearer")
    token_format: str = Field(alias="BearerFormat")
    token_creation: datetime = Field(alias="BearerCreation")
    token_expires_in: int = Field(alias="BearerExpiresIn")


class SingleResponse(BaseModel, Generic[ModelType]):
    model_config = ConfigDict(extra="allow")
    status: bool
    code: int
    date: datetime
    elapsed: str
    message: str
    data: ModelType


class LoginResponse(SingleResponse[BearerToken]): ...


class ListResponse(BaseModel, Generic[ModelType]):
    model_config = ConfigDict(extra="allow")
    status: bool
    code: int
    date: datetime
    elapsed: str
    message: str
    data: List[ModelType]


class Worker(BaseModel):
    model_config = ConfigDict(extra="allow")

    kind: str = Field(alias="type")
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    num_id: Optional[str] = Field(default=None)
    tax_id: Optional[str] = Field(default=None)
    gender: Optional[str] = Field(default=None)
    img_name: Optional[str] = Field(default=None)
    birthday: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    legal_address: Optional[str] = Field(default=None)
    active: Optional[str] = Field(default=None)
    approved: Optional[str] = Field(default=None)
    create_dt: datetime
    update_dt: datetime
    supplier_tax_id: Optional[str] = Field(default=None)
    company_tax_id: Optional[str] = Field(default=None)
    company_ext_id: Optional[str] = Field(default=None)

    @field_validator("create_dt", "update_dt", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value


class Supplier(BaseModel):
    model_config = ConfigDict(extra="allow")

    business_name: Optional[str] = Field(default=None)
    tax_id: Optional[str] = Field(default=None)
    star_dt: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    legal_address: Optional[str] = Field(default=None)
    active: Optional[str] = Field(default=None)
    approved: Optional[str] = Field(default=None)
    create_dt: datetime
    update_dt: datetime
    company_tax_id: Optional[str] = Field(default=None)
    company_ext_id: Optional[str] = Field(default=None)
    sap_vendor_id: Optional[str] = Field(default=None)

    @field_validator("create_dt", "update_dt", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return value


class WorkersListResponse(ListResponse[Worker]): ...


class SuppliersListResponse(ListResponse[Supplier]): ...
