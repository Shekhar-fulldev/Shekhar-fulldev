from pydantic import BaseModel, EmailStr, ConfigDict, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# -----------------------------------------------------------
# ENUMS (Same as SQLAlchemy enums)
# -----------------------------------------------------------
class UserRole(str, Enum):
    Admin = "Admin"
    Supervisor = "Supervisor"
    Maintainer = "Maintainer"


class MaintenanceType(str, Enum):
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    SixMonthly = "SixMonthly"
    Yearly = "Yearly"
    Unscheduled = "Unscheduled"


class MaintenanceStatus(str, Enum):
    Scheduled = "Scheduled"
    Completed = "Completed"
    Overdue = "Overdue"
    Breakdown = "Breakdown"


# -----------------------------------------------------------
# BASE SCHEMAS
# -----------------------------------------------------------
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TimestampMixin(BaseSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SoftDeleteMixin(BaseSchema):
    is_active: Optional[bool] = True


# -----------------------------------------------------------
# AUTH SCHEMAS
# -----------------------------------------------------------
class UserBase(BaseSchema):
    first_name: str = Field(..., max_length=50)
    last_name: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.Maintainer
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None
    is_maintainer: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None
    is_maintainer: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin, SoftDeleteMixin):
    id: int


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class Token(BaseSchema):
    access_token: str
    token_type: str
    user: UserResponse


# -----------------------------------------------------------
# MAKES, CAPACITIES, REFRIGERANTS SCHEMAS
# -----------------------------------------------------------
class MakeBase(BaseSchema):
    name: str = Field(..., max_length=70)


class MakeCreate(MakeBase):
    pass


class MakeUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=70)


class MakeResponse(MakeBase, TimestampMixin, SoftDeleteMixin):
    id: int


class CapacityBase(BaseSchema):
    tonnage: float = Field(..., ge=0.5, le=100.0)


class CapacityCreate(CapacityBase):
    pass


class CapacityUpdate(BaseSchema):
    tonnage: Optional[float] = Field(None, ge=0.5, le=100.0)


class CapacityResponse(CapacityBase, TimestampMixin, SoftDeleteMixin):
    id: int
    tonnage:float


class RefrigerantBase(BaseSchema):
    type: str = Field(..., max_length=255)


class RefrigerantCreate(RefrigerantBase):
    pass


class RefrigerantUpdate(BaseSchema):
    type: Optional[str] = Field(None, max_length=255)


class RefrigerantResponse(RefrigerantBase, TimestampMixin, SoftDeleteMixin):
    id: int
    type:str


# -----------------------------------------------------------
# DIVISION & SUBDIVISION SCHEMAS
# -----------------------------------------------------------
class DivisionBase(BaseSchema):
    name: str = Field(..., max_length=100)


class DivisionCreate(DivisionBase):
    pass


class DivisionUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)


class DivisionResponse(DivisionBase):
    id: int
    name:str


class SubDivisionBase(BaseSchema):
    name: str = Field(..., max_length=100)
    division_id: int


class SubDivisionCreate(SubDivisionBase):
    pass


class SubDivisionUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    division_id: Optional[int] = None


class SubDivisionResponse(SubDivisionBase):
    id: int
    name:str


class StationBase(BaseSchema):
    name: str = Field(..., max_length=100)


class StationCreate(DivisionBase):
    pass


class StationUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)


class StationResponse(DivisionBase):
    id: int
    name:str


# -----------------------------------------------------------
# MAINTAINER SCHEMAS
# -----------------------------------------------------------
class MaintainerBase(BaseSchema):
    name: str = Field(..., max_length=255)
    contact: Optional[str] = Field(None, max_length=100)
    subdivision_id: int
    user_id: Optional[int] = None


class MaintainerCreate(MaintainerBase):
    pass


class MaintainerUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    contact: Optional[str] = Field(None, max_length=100)
    subdivision_id: Optional[int] = None
    user_id: Optional[int] = None


class MaintainerResponse(MaintainerBase, TimestampMixin, SoftDeleteMixin):
    id: int
    subdivision: Optional[SubDivisionResponse] = None
    user: Optional[UserResponse] = None


# -----------------------------------------------------------
# AIR CONDITIONER SCHEMAS
# -----------------------------------------------------------
class AirConditionerBase(BaseSchema):
    serial_number: str = Field(..., max_length=255)
    station: str = Field(..., max_length=255)
    model: str = Field(..., max_length=255)
    precise_location: str
    install_date: date
    manufacturing_date: date
    make_id: int
    capacity_id: int
    refrigerant_id: int
    maintainer_id: Optional[int] = None
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None

    @validator('manufacturing_date')
    def validate_dates(cls, v, values):
        if 'install_date' in values and v > values['install_date']:
            raise ValueError('Manufacturing date must be before installation date')
        return v


class AirConditionerCreate(AirConditionerBase):
    pass


class AirConditionerUpdate(BaseSchema):
    serial_number: Optional[str] = Field(None, max_length=255)
    station: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    precise_location: Optional[str] = None
    install_date: Optional[date] = None
    manufacturing_date: Optional[date] = None
    make_id: Optional[int] = None
    capacity_id: Optional[int] = None
    refrigerant_id: Optional[int] = None
    maintainer_id: Optional[int] = None
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None


class AirConditionerResponse(AirConditionerBase, TimestampMixin, SoftDeleteMixin):
    id: int
    make: Optional[MakeResponse] = None
    capacity: Optional[CapacityResponse] = None
    refrigerant: Optional[RefrigerantResponse] = None
    maintainer: Optional[MaintainerResponse] = None
    subdivision: Optional[SubDivisionResponse] = None
    division: Optional[DivisionResponse] = None
    maintenance_records: List["MaintenanceRecordResponse"] = []
    maintenance_dates: List["MaintenanceDatesResponse"] = []


# -----------------------------------------------------------
# MAINTENANCE DATES SCHEMAS
# -----------------------------------------------------------
class MaintenanceDatesBase(BaseSchema):
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    ac_id: int

    @validator('next_maintenance')
    def validate_next_maintenance(cls, v, values):
        if v and 'last_maintenance' in values and values['last_maintenance']:
            if v < values['last_maintenance']:
                raise ValueError('Next maintenance date must be after last maintenance date')
        return v


class MaintenanceDatesCreate(MaintenanceDatesBase):
    pass


class MaintenanceDatesUpdate(BaseSchema):
    last_maintenance: Optional[date] = None
    next_maintenance: Optional[date] = None
    ac_id: Optional[int] = None


class MaintenanceDatesResponse(MaintenanceDatesBase, TimestampMixin, SoftDeleteMixin):
    id: int
    ac: Optional[AirConditionerResponse] = None


# -----------------------------------------------------------
# CHECKLIST SCHEMAS
# -----------------------------------------------------------
class ChecklistItemBase(BaseSchema):
    description: str = Field(..., max_length=200)
    maintenance_type: MaintenanceType


class ChecklistItemCreate(ChecklistItemBase):
    pass


class ChecklistItemUpdate(BaseSchema):
    description: Optional[str] = Field(None, max_length=200)
    maintenance_type: Optional[MaintenanceType] = None


class ChecklistItemResponse(ChecklistItemBase, TimestampMixin, SoftDeleteMixin):
    id: int


# -----------------------------------------------------------
# MAINTENANCE RECORD SCHEMAS
# -----------------------------------------------------------
class MaintenanceRecordBase(BaseSchema):
    ac_id: int
    maintainer_id: int
    maintenance_type: MaintenanceType
    maintenance_date: date = Field(default_factory=date.today)
    next_due_date: Optional[date] = None
    work_done: Optional[str] = None
    status: MaintenanceStatus = MaintenanceStatus.Scheduled
    is_completed: bool = False

    @validator('next_due_date')
    def validate_due_date(cls, v, values):
        if v and 'maintenance_date' in values and v < values['maintenance_date']:
            raise ValueError('Next due date must be after maintenance date')
        return v


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordUpdate(BaseSchema):
    ac_id: Optional[int] = None
    maintainer_id: Optional[int] = None
    maintenance_type: Optional[MaintenanceType] = None
    maintenance_date: Optional[date] = None
    next_due_date: Optional[date] = None
    work_done: Optional[str] = None
    status: Optional[MaintenanceStatus] = None
    is_completed: Optional[bool] = None


class MaintenanceRecordResponse(MaintenanceRecordBase, TimestampMixin, SoftDeleteMixin):
    id: int
    ac: Optional[AirConditionerResponse] = None
    maintainer: Optional[MaintainerResponse] = None
    checklist_records: List["MaintenanceChecklistRecordResponse"] = []
    parts_replaced: List["PartsReplacedResponse"] = []


# -----------------------------------------------------------
# MAINTENANCE CHECKLIST RECORD SCHEMAS
# -----------------------------------------------------------
class MaintenanceChecklistRecordBase(BaseSchema):
    maintenance_id: int
    checklist_item_id: int
    done: bool = False


class MaintenanceChecklistRecordCreate(MaintenanceChecklistRecordBase):
    pass


class MaintenanceChecklistRecordUpdate(BaseSchema):
    maintenance_id: Optional[int] = None
    checklist_item_id: Optional[int] = None
    done: Optional[bool] = None


class MaintenanceChecklistRecordResponse(MaintenanceChecklistRecordBase, TimestampMixin, SoftDeleteMixin):
    id: int
    maintenance: Optional[MaintenanceRecordResponse] = None
    checklist_item: Optional[ChecklistItemResponse] = None


# -----------------------------------------------------------
# PARTS REPLACED SCHEMAS
# -----------------------------------------------------------
class PartsReplacedBase(BaseSchema):
    maintenance_id: int
    part_name: str = Field(..., max_length=255)
    quantity: int = Field(..., gt=0)
    remarks: Optional[str] = None


class PartsReplacedCreate(PartsReplacedBase):
    pass


class PartsReplacedUpdate(BaseSchema):
    maintenance_id: Optional[int] = None
    part_name: Optional[str] = Field(None, max_length=255)
    quantity: Optional[int] = Field(None, gt=0)
    remarks: Optional[str] = None


class PartsReplacedResponse(PartsReplacedBase, TimestampMixin, SoftDeleteMixin):
    id: int
    maintenance: Optional[MaintenanceRecordResponse] = None


# -----------------------------------------------------------
# BULK OPERATION SCHEMAS
# -----------------------------------------------------------
class BulkChecklistUpdate(BaseSchema):
    checklist_records: List[MaintenanceChecklistRecordCreate]


class BulkPartsUpdate(BaseSchema):
    parts_replaced: List[PartsReplacedCreate]


class MaintenanceCompleteRequest(BaseSchema):
    work_done: Optional[str] = None
    next_due_date: Optional[date] = None
    checklist_updates: List[MaintenanceChecklistRecordUpdate]
    parts_replaced: List[PartsReplacedCreate]


# -----------------------------------------------------------
# FILTER AND QUERY SCHEMAS
# -----------------------------------------------------------
class MaintenanceFilter(BaseSchema):
    status: Optional[MaintenanceStatus] = None
    maintenance_type: Optional[MaintenanceType] = None
    maintainer_id: Optional[int] = None
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_completed: Optional[bool] = None


class AirConditionerFilter(BaseSchema):
    make_id: Optional[int] = None
    capacity_id: Optional[int] = None
    division_id: Optional[int] = None
    subdivision_id: Optional[int] = None
    maintainer_id: Optional[int] = None
    station: Optional[str] = None


class PaginationParams(BaseSchema):
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# -----------------------------------------------------------
# DASHBOARD AND REPORTING SCHEMAS
# -----------------------------------------------------------
class MaintenanceStats(BaseSchema):
    total_maintenance: int
    completed_maintenance: int
    overdue_maintenance: int
    scheduled_maintenance: int
    breakdown_maintenance: int


class DivisionStats(BaseSchema):
    division_id: int
    division_name: str
    total_acs: int
    maintenance_due: int
    maintenance_overdue: int


class MaintainerPerformance(BaseSchema):
    maintainer_id: int
    maintainer_name: str
    total_assigned: int
    completed_on_time: int
    completed_late: int
    pending: int
    completion_rate: float


# -----------------------------------------------------------
# FORWARD REFERENCES FOR CIRCULAR IMPORTS
# -----------------------------------------------------------
DivisionResponse.model_rebuild()
SubDivisionResponse.model_rebuild()
MaintainerResponse.model_rebuild()
AirConditionerResponse.model_rebuild()
MaintenanceDatesResponse.model_rebuild()
MaintenanceRecordResponse.model_rebuild()
MaintenanceChecklistRecordResponse.model_rebuild()
PartsReplacedResponse.model_rebuild()


# -----------------------------------------------------------
# API RESPONSE SCHEMAS
# -----------------------------------------------------------
class PaginatedResponse(BaseSchema):
    items: List[BaseSchema]
    total: int
    skip: int
    limit: int


class SuccessResponse(BaseSchema):
    success: bool = True
    message: str
    data: Optional[BaseSchema] = None


class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    details: Optional[str] = None


class ChecklistItemSchema(BaseSchema):
    id: int
    description: str
    done: bool

    model_config = {
        "from_attributes": True
    }

class PartReplacedSchema(BaseSchema):
    id: int
    part_name: str
    quantity: int
    remarks: Optional[str]

    model_config = {
        "from_attributes": True
    }

class MaintenanceRecordDetailedSchema(BaseSchema):
    maintenance_date: date
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    remarks: Optional[str]
    checklist: List[ChecklistItemSchema] = []
    parts_replaced: List[PartReplacedSchema] = []

    model_config = {
        "from_attributes": True
    }

class AirConditionerMaintenanceDetailedSchema(BaseSchema):
    id: int
    serial_number: str
    maintenance_records: List[MaintenanceRecordDetailedSchema] = []

    model_config = {
        "from_attributes": True
    }

class MaintenanceRecordSummarySchema(BaseSchema):
    maintenance_date: date
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    remarks: str | None = None

    model_config = {
        "from_attributes": True
    }

class AirConditionerMaintenanceSummarySchema(BaseSchema):
    id: int
    serial_number: str
    maintenance_history: List[MaintenanceRecordSummarySchema] = []

    model_config = {
        "from_attributes": True
    }

class DashboardResponseSchema(BaseModel):
    users: List[UserResponse] = []
    maintainers: List[MaintainerResponse] = []
    divisions: List[DivisionResponse] = []
    subdivisions: List[SubDivisionResponse] = []
    air_conditioners: List[AirConditionerResponse] = []

class DropDownResponseSchema(BaseSchema):
    makes:List[MakeResponse]
    capacities:List[CapacityResponse]
    divisions:List[DivisionResponse]
    subdivisions:List[SubDivisionResponse]
    refrigerants:List[RefrigerantResponse]
