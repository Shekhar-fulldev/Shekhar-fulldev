from sqlalchemy import (
    Integer, String, Text, Date, Boolean, ForeignKey, DECIMAL
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from datetime import date
import enum
from sqlalchemy import Enum as SQLEnum


# -----------------------------------------------------------
# BASE CLASS
# -----------------------------------------------------------
class Base(DeclarativeBase):
    pass


# -----------------------------------------------------------
# ENUMS
# -----------------------------------------------------------
class UserRole(str, enum.Enum):
    Admin = "Admin"
    Supervisor = "Supervisor"
    Maintainer = "Maintainer"


class MaintenanceType(str, enum.Enum):
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    SixMonthly = "SixMonthly"
    Yearly = "Yearly"
    Unscheduled = "Unscheduled"  # breakdown


class MaintenanceStatus(str, enum.Enum):
    Scheduled = "Scheduled"
    Completed = "Completed"
    Overdue = "Overdue"
    Breakdown = "Breakdown"


# -----------------------------------------------------------
# CORE TABLES
# -----------------------------------------------------------
class Make(Base):
    __tablename__ = "makes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(70), nullable=False)

    air_conditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="make", cascade="all, delete-orphan"
    )


class Capacity(Base):
    __tablename__ = "capacities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tonnage: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=False)

    air_conditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="capacity", cascade="all, delete-orphan"
    )


class Refrigerant(Base):
    __tablename__ = "refrigerants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)

    air_conditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="refrigerant", cascade="all, delete-orphan"
    )


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    subdivisions: Mapped[list["SubDivision"]] = relationship(
        "SubDivision", back_populates="division", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="division")


class SubDivision(Base):
    __tablename__ = "subdivisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    division_id: Mapped[int] = mapped_column(Integer, ForeignKey("divisions.id"), nullable=False)

    division: Mapped["Division"] = relationship("Division", back_populates="subdivisions")
    maintainers: Mapped[list["Maintainer"]] = relationship("Maintainer", back_populates="subdivision")
    air_conditioners: Mapped[list["AirConditioner"]] = relationship("AirConditioner", back_populates="subdivision")
    users: Mapped[list["User"]] = relationship("User", back_populates="subdivision")


class Maintainer(Base):
    __tablename__ = "maintainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subdivision_id: Mapped[int] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="maintainers")
    user: Mapped["User"] = relationship("User", back_populates="maintainer")
    air_conditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="maintainer", cascade="all, delete-orphan"
    )
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="maintainer", cascade="all, delete-orphan"
    )


class AirConditioner(Base):
    __tablename__ = "air_conditioners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    station: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    precise_location: Mapped[str] = mapped_column(Text, nullable=False)
    install_date: Mapped[date] = mapped_column(Date, nullable=False)
    manufacturing_date: Mapped[date] = mapped_column(Date, nullable=False)

    make_id: Mapped[int] = mapped_column(Integer, ForeignKey("makes.id"))
    capacity_id: Mapped[int] = mapped_column(Integer, ForeignKey("capacities.id"))
    refrigerant_id: Mapped[int] = mapped_column(Integer, ForeignKey("refrigerants.id"))
    maintainer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("maintainers.id"), nullable=True)
    division_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("divisions.id"), nullable=True)
    subdivision_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=True)

    make: Mapped["Make"] = relationship("Make", back_populates="air_conditioners")
    capacity: Mapped["Capacity"] = relationship("Capacity", back_populates="air_conditioners")
    refrigerant: Mapped["Refrigerant"] = relationship("Refrigerant", back_populates="air_conditioners")
    maintainer: Mapped["Maintainer"] = relationship("Maintainer", back_populates="air_conditioners")
    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="air_conditioners")

    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="ac", cascade="all, delete-orphan"
    )
    maintenance_dates: Mapped[list["MaintenanceDates"]] = relationship(
        "MaintenanceDates", back_populates="ac", cascade="all, delete-orphan"
    )


class MaintenanceDates(Base):
    __tablename__ = "maintenance_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    last_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    ac_id: Mapped[int] = mapped_column(Integer, ForeignKey("air_conditioners.id"), nullable=False)

    ac: Mapped["AirConditioner"] = relationship("AirConditioner", back_populates="maintenance_dates")


# -----------------------------------------------------------
# USER TABLE
# -----------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    designation: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.Maintainer
    )
    division_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("divisions.id"), nullable=True)
    subdivision_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=True)
    is_maintainer: Mapped[bool] = mapped_column(Boolean, default=False)

    division: Mapped["Division"] = relationship("Division", back_populates="users")
    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="users")
    maintainer: Mapped["Maintainer"] = relationship("Maintainer", back_populates="user", uselist=False)


# -----------------------------------------------------------
# MAINTENANCE TABLES
# -----------------------------------------------------------
class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType, name="maintenance_type_enum", native_enum=False)
    )

    records: Mapped[list["MaintenanceChecklistRecord"]] = relationship(
        "MaintenanceChecklistRecord", back_populates="checklist_item", cascade="all, delete-orphan"
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ac_id: Mapped[int] = mapped_column(Integer, ForeignKey("air_conditioners.id"))
    maintainer_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintainers.id"))
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType, name="maintenance_type_enum", native_enum=False)
    )
    maintenance_date: Mapped[date] = mapped_column(Date, default=date.today)
    next_due_date: Mapped[date | None] = mapped_column(Date)
    work_done: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MaintenanceStatus] = mapped_column(
        SQLEnum(MaintenanceStatus, name="maintenance_status_enum", native_enum=False),
        default=MaintenanceStatus.Scheduled
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    ac: Mapped["AirConditioner"] = relationship("AirConditioner", back_populates="maintenance_records")
    maintainer: Mapped["Maintainer"] = relationship("Maintainer", back_populates="maintenance_records")
    checklist_records: Mapped[list["MaintenanceChecklistRecord"]] = relationship(
        "MaintenanceChecklistRecord", back_populates="maintenance", cascade="all, delete-orphan"
    )
    parts_replaced: Mapped[list["PartsReplaced"]] = relationship(
        "PartsReplaced", back_populates="maintenance", cascade="all, delete-orphan"
    )


class MaintenanceChecklistRecord(Base):
    __tablename__ = "maintenance_checklist_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maintenance_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintenance_records.id"))
    checklist_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklist_items.id"))
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    maintenance: Mapped["MaintenanceRecord"] = relationship("MaintenanceRecord", back_populates="checklist_records")
    checklist_item: Mapped["ChecklistItem"] = relationship("ChecklistItem", back_populates="records")


class PartsReplaced(Base):
    __tablename__ = "parts_replaced"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maintenance_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintenance_records.id"))
    part_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer)
    remarks: Mapped[str | None] = mapped_column(Text)

    maintenance: Mapped["MaintenanceRecord"] = relationship("MaintenanceRecord", back_populates="parts_replaced")
