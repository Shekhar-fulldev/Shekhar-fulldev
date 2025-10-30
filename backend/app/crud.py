from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app import models, schemas
from app.core.security import hash_password
from typing import Optional, List
from datetime import datetime, timedelta

# --- Users ---
async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(str(user_in.password).strip),
        role=user_in.role,
        supervisor_id=user_in.supervisor_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    q = await db.execute(select(models.User).where(models.User.email == email))
    return q.scalars().first()

async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    q = await db.execute(select(models.User).where(models.User.id == user_id))
    return q.scalars().first()

# --- Vehicles ---
async def create_vehicle(db: AsyncSession, v: schemas.VehicleCreate) -> models.Vehicle:
    vehicle = models.Vehicle(
        vin=v.vin,
        registration_no=v.registration_no,
        model=v.model,
        assigned_driver_id=v.assigned_driver_id,
        service_period_days=v.service_period_days
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle

async def assign_vehicle(db: AsyncSession, vehicle_id: int, driver_id: Optional[int]) -> Optional[models.Vehicle]:
    q = await db.execute(select(models.Vehicle).where(models.Vehicle.id == vehicle_id))
    vehicle = q.scalars().first()
    if not vehicle:
        return None
    vehicle.driver_id = driver_id
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle

async def transfer_vehicle(db: AsyncSession, vehicle_id: int, new_driver_id: int, previous_driver_id:int) -> Optional[models.Vehicle]:
    # Business rules can be enforced here (e.g., only certain roles can transfer)
    transfer = models.TransferLog(vehicle_id=vehicle_id, from_driver_id=previous_driver_id, to_driver_id=new_driver_id) #action_by=by_user_id)
    db.add(transfer)
    await db.commit()
    return transfer
    

# --- Daily runs ---
async def create_daily_run(db: AsyncSession, r: schemas.DailyRunCreate) -> models.DailyRun:
    run = models.DailyRun(
        vehicle_id=r.vehicle_id,
        driver_id=r.driver_id,
        date=r.date or datetime.utcnow(),
        run_duration_minutes=r.run_duration_minutes,
        notes=r.notes
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run

async def get_vehicle_runs(db: AsyncSession, vehicle_id: int, limit: int = 100) -> List[models.DailyRun]:
    q = await db.execute(select(models.DailyRun).where(models.DailyRun.vehicle_id == vehicle_id).order_by(models.DailyRun.date.desc()).limit(limit))
    return q.scalars().all()

# --- Service ---
async def create_service_record(db: AsyncSession, sr: schemas.ServiceRecordCreate, service_period_days_override: Optional[int] = None) -> models.ServiceRecord:
    # compute next_service_due
    serviced_at = sr.serviced_at or datetime.utcnow()
    vehicle_q = await db.execute(select(models.Vehicle).where(models.Vehicle.id == sr.vehicle_id))
    vehicle = vehicle_q.scalars().first()
    period_days = service_period_days_override or (vehicle.service_period_days if vehicle else 90)
    next_due = serviced_at + timedelta(days=period_days)
    rec = models.ServiceRecord(
        vehicle_id=sr.vehicle_id,
        serviced_at=serviced_at,
        service_duration_minutes=sr.service_duration_minutes,
        notes=sr.notes,
        next_service_due=next_due
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec

# --- Reports / comparative ---
async def get_vehicle_total_run_minutes(db: AsyncSession, vehicle_id: int, days: int = 30) -> int:
    since = datetime.utcnow() - timedelta(days=days)
    q = await db.execute(
        select(func.coalesce(func.sum(models.DailyRun.run_duration_minutes), 0))
        .where(models.DailyRun.vehicle_id == vehicle_id)
        .where(models.DailyRun.date >= since)
    )
    return int(q.scalar() or 0)

async def comparative_vehicle_report(db: AsyncSession, days: int = 30, limit: int = 50):
    since = datetime.utcnow() - timedelta(days=days)
    q = await db.execute(
        select(
            models.Vehicle.id,
            models.Vehicle.vin,
            models.Vehicle.registration_no,
            func.coalesce(func.sum(models.DailyRun.run_duration_minutes), 0).label("total_minutes")
        ).join(models.DailyRun, models.DailyRun.vehicle_id == models.Vehicle.id, isouter=True)
         .where(models.DailyRun.date >= since)
         .group_by(models.Vehicle.id)
         .order_by(func.coalesce(func.sum(models.DailyRun.run_duration_minutes), 0).desc())
         .limit(limit)
    )
    rows = q.all()
    # convert to structured list
    return [{"vehicle_id": r[0], "vin": r[1], "reg": r[2], "total_minutes": int(r[3])} for r in rows]
