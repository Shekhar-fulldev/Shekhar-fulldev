from sqlalchemy import (
    Integer, String, Text, Date, Boolean, ForeignKey, DECIMAL, 
    DateTime, Index, CheckConstraint, event, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, Session
from datetime import date, datetime
import enum
from sqlalchemy.sql import func 

from .db.database import get_db as db
from sqlalchemy import Numeric


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

maintenance_type_enum = SQLEnum(
    MaintenanceType, name="maintenance_type_enum", native_enum=False
)
maintenance_status_enum = SQLEnum(
    MaintenanceStatus, name="maintenance_status_enum", native_enum=False
)
# -----------------------------------------------------------
# CORE TABLES
# -----------------------------------------------------------
class Make(Base):
    __tablename__ = "makes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(70), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    airconditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="make", cascade="all, delete-orphan"
    )


class Capacity(Base):
    __tablename__ = "capacities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tonnage: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    airconditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="capacity", cascade="all, delete-orphan"
    )


class Refrigerant(Base):
    __tablename__ = "refrigerants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    airconditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="refrigerant", cascade="all, delete-orphan"
    )


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    subdivisions: Mapped[list["SubDivision"]] = relationship(
        "SubDivision", back_populates="division", cascade="all, delete-orphan"
    )
    stations: Mapped[list["Station"]] = relationship("Station", back_populates="division")
    users: Mapped[list["User"]] = relationship("User", back_populates="division")
    airconditioners: Mapped[list["AirConditioner"]] = relationship("AirConditioner", back_populates="division")


class SubDivision(Base):
    __tablename__ = "subdivisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    division_id: Mapped[int] = mapped_column(Integer, ForeignKey("divisions.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    division: Mapped["Division"] = relationship("Division", back_populates="subdivisions")
    maintainers: Mapped[list["Maintainer"]] = relationship("Maintainer", back_populates="subdivision")
    airconditioners: Mapped[list["AirConditioner"]] = relationship("AirConditioner", back_populates="subdivision")
    users: Mapped[list["User"]] = relationship("User", back_populates="subdivision")
    stations: Mapped[list["Station"]] = relationship("Station", back_populates="subdivision")


class Maintainer(Base):
    __tablename__ = "maintainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subdivision_id: Mapped[int] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="maintainers")
    user: Mapped["User"] = relationship("User", back_populates="maintainer")
    airconditioners: Mapped[list["AirConditioner"]] = relationship(
        "AirConditioner", back_populates="maintainer", cascade="all, delete-orphan"
    )
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="maintainer", cascade="all, delete-orphan"
    )


class AirConditioner(Base):
    __tablename__ = "airconditioners"
    __table_args__ = (
        Index('ix_air_conditioner_serial', 'serial_number'),
        Index('ix_air_conditioner_station', 'station'),
        Index('ix_airconditioners_div_sub', 'division_id', 'subdivision_id'),
        Index('ix_air_conditioner_install_date', 'install_date'),
        CheckConstraint('manufacturing_date <= install_date', 
                    name='manufacturing_before_install'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    station: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    precise_location: Mapped[str] = mapped_column(Text, nullable=False)
    install_date: Mapped[date] = mapped_column(Date, nullable=False)
    manufacturing_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    make_id: Mapped[int] = mapped_column(Integer, ForeignKey("makes.id"))
    capacity_id: Mapped[int] = mapped_column(Integer, ForeignKey("capacities.id"))
    refrigerant_id: Mapped[int] = mapped_column(Integer, ForeignKey("refrigerants.id"))
    maintainer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("maintainers.id"), nullable=True)
    division_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("divisions.id", ondelete="SET NULL"), nullable=True)
    subdivision_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=True)

    make: Mapped["Make"] = relationship("Make", back_populates="airconditioners")
    capacity: Mapped["Capacity"] = relationship("Capacity", back_populates="airconditioners")
    refrigerant: Mapped["Refrigerant"] = relationship("Refrigerant", back_populates="airconditioners")
    maintainer: Mapped["Maintainer"] = relationship("Maintainer", back_populates="airconditioners")
    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="airconditioners")
    division: Mapped["Division"] = relationship("Division", back_populates="airconditioners")

    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="ac", cascade="all, delete-orphan"
    )
    maintenance_dates: Mapped[list["MaintenanceDates"]] = relationship(
        "MaintenanceDates", back_populates="ac", cascade="all, delete-orphan"
    )

    last_maintenance_type: Mapped[MaintenanceType | None] = mapped_column(
        maintenance_type_enum, nullable=True)
    last_maintenance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class MaintenanceDates(Base):
    __tablename__ = "maintenance_dates"
    __table_args__ = (
        Index('ix_maintenance_dates_last', 'last_maintenance'),
        Index('ix_maintenance_dates_next', 'next_maintenance'),
        CheckConstraint('last_maintenance <= next_maintenance', 
                    name='last_before_next_maintenance'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    last_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance: Mapped[date | None] = mapped_column(Date, nullable=True)
    ac_id: Mapped[int] = mapped_column(Integer, ForeignKey("airconditioners.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    ac: Mapped["AirConditioner"] = relationship("AirConditioner", back_populates="maintenance_dates")


# -----------------------------------------------------------
# USER TABLE
# -----------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_role', 'role'),
        Index('ix_users_division', 'division_id'),
        Index('ix_users_subdivision', 'subdivision_id'),
        Index('ix_users_div_sub_role', 'division_id', 'subdivision_id', 'role'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    designation: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.Maintainer
    )
    division_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("divisions.id"), nullable=True)
    subdivision_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subdivisions.id"), nullable=True)
    is_maintainer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    division: Mapped["Division"] = relationship("Division", back_populates="users")
    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="users")
    maintainer: Mapped["Maintainer"] = relationship("Maintainer", back_populates="user", uselist=False)


# -----------------------------------------------------------
# MAINTENANCE TABLES
# -----------------------------------------------------------
class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    __table_args__ = (
        Index('ix_checklist_maintenance_type', 'maintenance_type'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(maintenance_type_enum)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    records: Mapped[list["MaintenanceChecklistRecord"]] = relationship(
        "MaintenanceChecklistRecord", back_populates="checklist_item", cascade="all, delete-orphan"
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        Index('ix_maintenance_record_ac', 'ac_id'),
        Index('ix_maintenance_record_date', 'maintenance_date'),
        Index('ix_maintenance_record_status', 'status'),
        Index('ix_maintenance_record_type', 'maintenance_type'),
        Index('ix_maintenance_record_due_date', 'next_due_date'),
        Index('ix_maintenance_record_completed', 'is_completed'),
        CheckConstraint('maintenance_date <= COALESCE(next_due_date, maintenance_date)', 
                    name='maintenance_before_due'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ac_id: Mapped[int] = mapped_column(Integer, ForeignKey("airconditioners.id"))
    maintainer_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintainers.id"))
    maintenance_type: Mapped[MaintenanceType] = mapped_column(maintenance_type_enum)
    maintenance_date: Mapped[date] = mapped_column(Date, default=date.today)
    next_due_date: Mapped[date | None] = mapped_column(Date)
    work_done: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MaintenanceStatus] = mapped_column(maintenance_status_enum,
        default=MaintenanceStatus.Scheduled
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

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
    __table_args__ = (
        Index('ix_checklist_record_maintenance', 'maintenance_id'),
        Index('ix_checklist_record_item', 'checklist_item_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maintenance_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintenance_records.id"))
    checklist_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklist_items.id"))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    maintenance: Mapped["MaintenanceRecord"] = relationship("MaintenanceRecord", back_populates="checklist_records")
    checklist_item: Mapped["ChecklistItem"] = relationship("ChecklistItem", back_populates="records")


class PartsReplaced(Base):
    __tablename__ = "parts_replaced"
    __table_args__ = (
        Index('ix_parts_maintenance', 'maintenance_id'),
        CheckConstraint('quantity > 0', name='positive_quantity'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maintenance_id: Mapped[int] = mapped_column(Integer, ForeignKey("maintenance_records.id"))
    part_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer)
    remarks: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    maintenance: Mapped["MaintenanceRecord"] = relationship("MaintenanceRecord", back_populates="parts_replaced")

class Station(Base):
    __tablename__ = "stations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    division_id: Mapped[int] = mapped_column(ForeignKey("divisions.id"))
    subdivision_id: Mapped[int] = mapped_column(ForeignKey("subdivisions.id"))

    division: Mapped["Division"] = relationship("Division", back_populates="stations")
    subdivision: Mapped["SubDivision"] = relationship("SubDivision", back_populates="stations")

    
    
    
# -----------------------------------------------------------
# EVENT LISTENERS FOR AUTO-UPDATES
# -----------------------------------------------------------
# -----------------------------------------------------------
# EVENT LISTENERS FOR AUTO-UPDATES
# -----------------------------------------------------------

from sqlalchemy import select
from sqlalchemy.event import listens_for

from sqlalchemy import select, update, func
from sqlalchemy.event import listens_for

from sqlalchemy import select, func
from sqlalchemy.event import listens_for
from sqlalchemy.sql import insert, update

# -----------------------------------------------------------
# EVENT LISTENERS FOR AUTO-UPDATES
# -----------------------------------------------------------

@listens_for(MaintenanceRecord, "before_update")
def sync_maintenance_dates(mapper, connection, target):
    """
    Sync MaintenanceDates table when maintenance is completed.
    Ensures only one active MaintenanceDates per AC.
    """
    if not target.is_completed:
        return

    # Only trigger when status actually changes to Completed
    if target.status != MaintenanceStatus.Completed:
        target.status = MaintenanceStatus.Completed
        target.updated_at = func.now()

        if not target.ac_id or not target.next_due_date:
            return

        # Deactivate any existing active MaintenanceDates for same AC
        connection.execute(
            update(MaintenanceDates.__table__)
            .where(MaintenanceDates.ac_id == target.ac_id)
            .where(MaintenanceDates.is_active.is_(True))
            .values(is_active=False, updated_at=func.now())
        )

        # Insert new MaintenanceDates record
        connection.execute(
            insert(MaintenanceDates.__table__).values(
                ac_id=target.ac_id,
                last_maintenance=target.maintenance_date,
                next_maintenance=target.next_due_date,
                is_active=True,
                created_at=func.now(),
                updated_at=func.now(),
            )
        )


@listens_for(MaintenanceRecord, "after_insert")
@listens_for(MaintenanceRecord, "after_update")
def update_airconditioner_summary(mapper, connection, target):
    """
    Update AirConditioner summary fields (last maintenance type/date/next due).
    Triggered after insert/update.
    """
    if not target.is_completed or not target.ac_id:
        return

    latest_completed = (
        select(
            MaintenanceRecord.maintenance_type,
            MaintenanceRecord.maintenance_date,
            MaintenanceRecord.next_due_date,
        )
        .where(MaintenanceRecord.ac_id == target.ac_id)
        .where(MaintenanceRecord.is_completed.is_(True))
        .order_by(MaintenanceRecord.maintenance_date.desc())
        .limit(1)
    )

    result = connection.execute(latest_completed).fetchone()
    if not result:
        return

    connection.execute(
        update(AirConditioner.__table__)
        .where(AirConditioner.id == target.ac_id)
        .values(
            last_maintenance_type=result.maintenance_type,
            last_maintenance_date=result.maintenance_date,
            next_due_date=result.next_due_date,
            updated_at=func.now(),
        )
    )


@listens_for(MaintenanceRecord, "after_delete")
def cleanup_after_delete(mapper, connection, target):
    """
    If a completed maintenance record is deleted, re-sync AC summary and MaintenanceDates.
    """
    if not target.ac_id:
        return

    latest_completed = (
        select(
            MaintenanceRecord.maintenance_type,
            MaintenanceRecord.maintenance_date,
            MaintenanceRecord.next_due_date,
        )
        .where(MaintenanceRecord.ac_id == target.ac_id)
        .where(MaintenanceRecord.is_completed.is_(True))
        .order_by(MaintenanceRecord.maintenance_date.desc())
        .limit(1)
    )

    result = connection.execute(latest_completed).fetchone()

    if result:
        # Reassign based on most recent completed record
        connection.execute(
            update(AirConditioner.__table__)
            .where(AirConditioner.id == target.ac_id)
            .values(
                last_maintenance_type=result.maintenance_type,
                last_maintenance_date=result.maintenance_date,
                next_due_date=result.next_due_date,
                updated_at=func.now(),
            )
        )
    else:
        # If no completed records remain
        connection.execute(
            update(AirConditioner.__table__)
            .where(AirConditioner.id == target.ac_id)
            .values(
                last_maintenance_type=None,
                last_maintenance_date=None,
                next_due_date=None,
                updated_at=func.now(),
            )
        )

        # Deactivate all maintenance dates
        connection.execute(
            update(MaintenanceDates.__table__)
            .where(MaintenanceDates.ac_id == target.ac_id)
            .values(is_active=False, updated_at=func.now())
        )
