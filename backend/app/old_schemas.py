from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum
from .models import MaintenanceStatus

# ============================================================
# ENUMS
# ============================================================
class MaintenanceType(str, Enum):
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    SixMonthly = "SixMonthly"
    Yearly = "Yearly"
    Unscheduled = "Unscheduled"


class UserRole(str, Enum):
    Admin = "Admin"
    Supervisor = "Supervisor"
    Maintainer = "Maintainer"


# ============================================================
# COMMON BASE CONFIG
# ============================================================
class ORMBase(BaseModel):
    class Config:
        from_attributes = True


# ============================================================
# BASIC MASTER SCHEMAS
# ============================================================
class MakeBase(ORMBase):
    name: str


class MakeCreate(MakeBase):
    pass


class MakeResponse(MakeBase):
    id: int


class CapacityBase(ORMBase):
    tonnage: Decimal


class CapacityCreate(CapacityBase):
    pass


class CapacityResponse(CapacityBase):
    id: int


class RefrigerantBase(ORMBase):
    type: str


class RefrigerantCreate(RefrigerantBase):
    pass


class RefrigerantResponse(RefrigerantBase):
    id: int


# ============================================================
# DIVISION / SUBDIVISION
# ============================================================
class DivisionBase(ORMBase):
    name: str


class DivisionRead(DivisionBase):
    id: int


class SubDivisionBase(ORMBase):
    name: str
    division_id: int


class SubDivisionRead(SubDivisionBase):
    id: int


# ============================================================
# MAINTAINER
# ============================================================
class MaintainerBase(ORMBase):
    name: str
    contact: Optional[str] = None
    email: Optional[EmailStr] = None
    subdivision_id: int


class MaintainerCreate(MaintainerBase):
    pass


class MaintainerRead(MaintainerBase):
    id: int


# ============================================================
# AIR CONDITIONER
# ============================================================
class AirConditionerBase(ORMBase):
    serial_number: str
    precise_location:str
    make_id: int
    capacity_id: int
    refrigerant_id: int
    subdivision_id: int
    division_id: int
    install_date: date
    manufacturing_date: date
    model: str
    station: str
    maintainer_id: Optional[int] = None


class AirConditionerCreate(AirConditionerBase):
    pass


class AirConditionerResponse(AirConditionerBase):
    id: int
    make: Optional[MakeResponse] = None
    capacity: Optional[CapacityResponse] = None
    refrigerant: Optional[RefrigerantResponse] = None
    maintainer: Optional[MaintainerRead] = None


# ============================================================
# MAINTENANCE DATES
# ============================================================
class MaintenanceDatesBase(ORMBase):
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    ac_id: Optional[int] = None


class MaintenanceDatesCreate(MaintenanceDatesBase):
    pass


class MaintenanceDatesResponse(MaintenanceDatesBase):
    id: int


# ============================================================
# CHECKLIST ITEMS
# ============================================================
class ChecklistItemBase(ORMBase):
    description: str
    maintenance_type: MaintenanceType


class ChecklistItemRead(ChecklistItemBase):
    id: int


# ============================================================
# MAINTENANCE RECORD
# ============================================================
class MaintenanceRecordBase(ORMBase):
    ac_id: int
    maintainer_id: int
    maintenance_type: MaintenanceType
    maintenance_date: Optional[date] = None
    next_due_date: Optional[date] = None
    work_done: Optional[str] = None
    parts_replaced: Optional[str] = None
    is_completed: bool = False
    status: Optional[MaintenanceStatus] = MaintenanceStatus.Scheduled


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordRead(MaintenanceRecordBase):
    id: int


# ============================================================
# USER & AUTHENTICATION
# ============================================================
class UserBase(ORMBase):
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    role: Optional[UserRole] = UserRole.Maintainer


class UserCreate(UserBase):
    password: str
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None


class UserOut(UserBase):
    id: int
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
