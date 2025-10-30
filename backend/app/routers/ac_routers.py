from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.api.auth_utils import get_current_user
from app.models import *
from app.schemas import *
from datetime import timedelta

router = APIRouter(prefix="/ac",  tags=["AC Routs"])

@router.get("/dashboard", response_model=DashboardResponseSchema)
def get_dashboard(db: Session = Depends(get_db)):
    users = db.query(User).all()
    maintainers = db.query(Maintainer).all()
    divisions = db.query(Division).all()
    subdivisions = db.query(SubDivision).all()
    air_conditioners = db.query(AirConditioner).all()

    return {
        "users": [UserResponse.model_validate(u) for u in users],
        "maintainers": [MaintainerResponse.model_validate(m) for m in maintainers],
        "divisions": [DivisionResponse.model_validate(d) for d in divisions],
        "subdivisions": [SubDivisionResponse.model_validate(s) for s in subdivisions],
        "air_conditioners": [AirConditionerResponse.model_validate(ac) for ac in air_conditioners],
    }

@router.get("/dropdowndata", response_model=DropDownResponseSchema)
def get_dropdowndata(db: Session = Depends(get_db)):
    makes= db.query(Make).all()
    capacities=db.query(Capacity).all()
    refrigerants= db.query(Refrigerant).all()
    divisions = db.query(Division).all()
    subdivisions = db.query(SubDivision).all()
    return{
            "makes": [MakeResponse.model_validate(m) for m in makes],
            "capacities": [CapacityResponse.model_validate(c) for c in capacities],
            "divisions": [DivisionResponse.model_validate(d) for d in divisions],
            "subdivisions": [SubDivisionResponse.model_validate(s) for s in subdivisions],
            "refrigerants": [RefrigerantResponse.model_validate(r) for r in refrigerants],
        }
    
    

@router.get("/subdivisions/{div_id}", response_model=list[SubDivisionResponse])
def get_subdivisions_by_division_id(div_id:int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SubDivision).filter(SubDivision.division_id==div_id).all()

@router.post("/maintenance/", response_model=MaintenanceRecordResponse)
def add_maintenance(r: MaintenanceRecordBase, 
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):

    ac = db.query(AirConditioner).get(r.ac_id)
    if not ac:
        raise HTTPException(404, "AC not found")

    if not r.maintenance_date:
        r.maintenance_date = date.today()

    next_due = None
    status = MaintenanceStatus.Scheduled

    if r.maintenance_type == MaintenanceType.Monthly:
        next_due = r.maintenance_date + timedelta(days=30)
    elif r.maintenance_type == MaintenanceType.Quarterly:
        next_due = r.maintenance_date + timedelta(days=90)
    elif r.maintenance_type == MaintenanceType.SixMonthly:
        next_due = r.maintenance_date + timedelta(days=180)
    elif r.maintenance_type == MaintenanceType.Yearly:
        next_due = r.maintenance_date + timedelta(days=365)
    elif r.maintenance_type == MaintenanceType.Unscheduled:
        status = MaintenanceStatus.Breakdown

    if r.is_completed and status != MaintenanceStatus.Breakdown:
        status = MaintenanceStatus.Completed

    # Auto-check for overdue
    if next_due and date.today() > next_due and not r.is_completed:
        status = MaintenanceStatus.Overdue

    record = MaintenanceRecord(
        ac_id=r.ac_id,
        maintainer_id=r.maintainer_id,
        maintenance_type=r.maintenance_type,
        maintenance_date=r.maintenance_date,
        next_due_date=next_due,
        work_done=r.work_done,
        parts_replaced=r.parts_replaced,
        is_completed=r.is_completed,
        status=status
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/reports/division/{div_id}")
def division_report(div_id: int, db: Session = Depends(get_db)):
    div = db.query(Division).get(div_id)
    if not div:
        raise HTTPException(404, "Division not found")

    records = db.query(MaintenanceRecord).join(AirConditioner).join(SubDivision).filter(
        SubDivision.division_id == div_id
    ).all()

    status_counts = {
        "Scheduled": 0,
        "Completed": 0,
        "Overdue": 0,
        "Breakdown": 0
    }

    for r in records:
        status_counts[r.status.value] += 1

    return {
        "division": div.name,
        "total_records": len(records),
        "status_counts": status_counts
    }



@router.get("/all-ac", response_model=List[AirConditionerResponse])
def list_acs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.Admin:
        return db.query(AirConditioner).all()
    elif current_user.role == UserRole.Maintainer:
        maint = current_user.maintainer
        return db.query(AirConditioner).filter(AirConditioner.subdivision_id == maint.subdivision_id).all()
    else:
        raise HTTPException(403, "Access not allowed for your role")
    
@router.get("/reports/divisional/{div_id}")
def divisional_report(div_id: int, db: Session = Depends(get_db)):
    div = db.query(Division).get(div_id)
    if not div:
        raise HTTPException(404, "Division not found")

    records = db.query(MaintenanceRecord).join(AirConditioner).join(SubDivision).filter(
        SubDivision.division_id == div_id
    ).all()

    today = date.today()
    due_soon = [r for r in records if r.next_due_date and 0 <= (r.next_due_date - today).days <= 10]
    overdue = [r for r in records if r.next_due_date and r.next_due_date < today and not r.is_completed]
    breakdowns = [r for r in records if r.maintenance_type == MaintenanceType.Unscheduled]

    return {
        "division": div.name,
        "total_records": len(records),
        "due_soon": len(due_soon),
        "overdue": len(overdue),
        "breakdowns": len(breakdowns),
    }

@router.post("/acs/", response_model=AirConditionerResponse)
def add_ac(a: AirConditionerBase, db: Session = Depends(get_db)):
    if not db.query(SubDivision).get(a.subdivision_id):
        raise HTTPException(404, "SubDivision not found")
    ac = AirConditioner(**a.dict())
    db.add(ac); db.commit(); db.refresh(ac)
    return ac

@router.get("/capacities", response_model=list[CapacityResponse])
def get_capacities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Capacity).all()

@router.get("/refrigerants", response_model=list[RefrigerantResponse])
def get_refrigerants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Refrigerant).all()

@router.get("/maintenance_dates", response_model=list[MaintenanceDatesResponse])
def get_maintenance_dates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(MaintenanceDates).all()



@router.post("/add-ac", response_model=AirConditionerResponse)
def add_ac(ac:AirConditionerCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db_ac= AirConditioner(
        serial_number=ac.serial_number,
        precise_location=ac.precise_location,
        make_id= ac.make_id,
        capacity_id= ac.capacity_id,
        refrigerant_id= ac.refrigerant_id,
        subdivision_id = ac.subdivision_id,
        division_id = ac.division_id,
        install_date=ac.install_date,
        manufacturing_date=ac.manufacturing_date,
        model=ac.model,
        station=ac.station 
    )
    db.add(db_ac)
    db.commit()
    db.refresh(db_ac)
    return db_ac
# -----------------------------------------------------------
# UTILITY FUNCTIONS
# -----------------------------------------------------------
@router.get("/overdue", response_model= MaintenanceDatesResponse)
def get_overdue_maintenance(db: Session = Depends(get_db)) -> list[MaintenanceRecord]:
    """Get all overdue maintenance records"""
    return db.query(MaintenanceRecord).filter(
        MaintenanceRecord.next_due_date < date.today(),
        MaintenanceRecord.status.in_([MaintenanceStatus.Scheduled, MaintenanceStatus.Overdue]),
        MaintenanceRecord.is_active == True
    ).all()

@router.get("/all-acs", response_model= AirConditionerResponse)
def get_active_air_conditioners(division_id: Optional[int] = None, db: Session = Depends(get_db)) -> list[AirConditioner]:
    """Get all active air conditioners, optionally filtered by division"""
    query = db.query(AirConditioner)
    
    if division_id:
        query = query.filter(AirConditioner.division_id == division_id)
    
    return query.all()

@router.get("/{ac_id}/maintenance-summary", response_model=AirConditionerMaintenanceSummarySchema)
def get_ac_maintenance_summary(ac_id: int, db: Session = Depends(get_db)):
    ac = db.query(AirConditioner).options(
    joinedload(AirConditioner.maintenance_records)
    ).filter(AirConditioner.id == ac_id).first()


    if not ac:
        raise HTTPException(status_code=404, detail="AirConditioner not found")


    maintenance_history = sorted(ac.maintenance_records, key=lambda x: x.maintenance_date, reverse=True)
    return {
        "id": ac.id,
        "serial_number": ac.serial_number,
        "maintenance_history": maintenance_history
    }


@router.get("/{ac_id}/maintenance-detailed", response_model=AirConditionerMaintenanceDetailedSchema)
def get_ac_maintenance_detailed(ac_id: int, db: Session = Depends(get_db)):
    ac = db.query(AirConditioner).options(
    joinedload(AirConditioner.maintenance_records)
    .joinedload("checklist_records")
    .joinedload("checklist_item"),
    joinedload(AirConditioner.maintenance_records)
    .joinedload("parts_replaced")
    ).filter(AirConditioner.id == ac_id).first()


    if not ac:
        raise HTTPException(status_code=404, detail="AirConditioner not found")


    # Build nested detailed records
    detailed_records = []
    for record in sorted(ac.maintenance_records, key=lambda x: x.maintenance_date, reverse=True):
        checklist = [
        {
            "id": item.checklist_item.id,
            "description": item.checklist_item.description,
            "done": item.done
        } for item in record.checklist_records
        ]


        parts = [
        {
            "id": part.id,
            "part_name": part.part_name,
            "quantity": part.quantity,
            "remarks": part.remarks
        } for part in record.parts_replaced
        ]


        detailed_records.append({
            "maintenance_date": record.maintenance_date,
            "maintenance_type": record.maintenance_type,
            "status": record.status,
            "remarks": record.remarks,
            "checklist": checklist,
            "parts_replaced": parts
        })


    return {
        "id": ac.id,
        "serial_number": ac.serial_number,
        "maintenance_records": detailed_records
    }


def soft_delete_entity(entity: Base,db: Session = Depends(get_db)) -> None:
    """Soft delete an entity by setting is_active to False"""
    entity.is_active = False
    entity.updated_at = datetime.now()
    db.add(entity)

