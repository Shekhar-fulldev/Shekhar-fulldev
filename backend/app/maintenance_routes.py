from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models import MaintenanceRecord, User
from schemas import MaintenanceOut, MaintenanceCreate
from backend.app.api.auth_utils import get_current_user, require_role

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=List[MaintenanceOut])
def get_maintenance_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MaintenanceRecord)

    # 🧠 Role-based data filtering
    if current_user.role == "DivisionManager":
        query = query.filter(
            MaintenanceRecord.division_id == current_user.division_id
        )
    elif current_user.role == "SubDivisionMaintainer":
        query = query.filter(
            MaintenanceRecord.subdivision_id == current_user.subdivision_id
        )

    records = query.all()
    return records


@router.post("/", response_model=MaintenanceOut)
def create_maintenance_record(
    record: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 🧠 Enforce jurisdiction for creation
    if current_user.role == "SubDivisionMaintainer":
        if record.subdivision_id != current_user.subdivision_id:
            raise HTTPException(
                status_code=403,
                detail="You can only add records for your own sub-division.",
            )

    if current_user.role == "DivisionManager":
        # Division Manager can add for their division or its sub-divisions
        if record.division_id != current_user.division_id:
            raise HTTPException(
                status_code=403,
                detail="You can only add records for your own division.",
            )

    db_record = MaintenanceRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record
