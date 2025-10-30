from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app import schemas, crud, models
from app.db.session import get_db
from app.api.deps import require_roles, get_current_user

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

@router.post("/", response_model=schemas.VehicleOut)
async def create_vehicle(v: schemas.VehicleCreate, db: AsyncSession = Depends(get_db),
                         current_user: models.User = Depends(require_roles("executive", "field_officer"))):
    # both executive and field officer can create vehicles
    vehicle = await crud.create_vehicle(db, v)
    return vehicle

@router.post("/{vehicle_id}/assign", response_model=schemas.VehicleOut)
async def assign_vehicle(vehicle_id: int, assign_to: int, db: AsyncSession = Depends(get_db),
                         current_user: models.User = Depends(require_roles("executive", "field_officer"))):
    # field_officer/executive assign vehicle to driver
    veh = await crud.assign_vehicle(db, vehicle_id, assign_to)
    if not veh:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return veh

@router.post("/transfer", response_model=schemas.VehicleOut)
async def transfer_vehicle(transfer: schemas.TransferRequest, db: AsyncSession = Depends(get_db),
                           current_user: models.User = Depends(require_roles("executive","field_officer"))):
    veh = await crud.transfer_vehicle(db, transfer.vehicle_id, transfer.new_driver_id)
    if not veh:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    # you can log the transfer reason in a TransferLog table (left as exercise)
    return veh

@router.post("/run", response_model=schemas.DailyRunOut)
async def create_run(run_in: schemas.DailyRunCreate, db: AsyncSession = Depends(get_db),
                     current_user: models.User = Depends(require_roles("driver","field_officer","executive"))):
    # drivers can report their runs; field_officer/executive can also create runs
    # you may want to restrict driver to only report runs for vehicles assigned to them
    run = await crud.create_daily_run(db, run_in)
    return run

@router.post("/service", response_model=schemas.ServiceRecordOut)
async def create_service(sr: schemas.ServiceRecordCreate, db: AsyncSession = Depends(get_db),
                         current_user: models.User = Depends(require_roles("field_officer","executive"))):
    rec = await crud.create_service_record(db, sr)
    return rec
