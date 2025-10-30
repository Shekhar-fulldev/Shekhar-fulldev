from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas  import *
from app.models import *
from app.db.database import get_db
from app.api.auth_utils import get_current_user
router = APIRouter(prefix="/gen", tags=["General"])

@router.post("/divisions", response_model=DivisionResponse)
def add_division(div: DivisionBase, db: Session = Depends(get_db)):
    d = Division(**div.dict())
    db.add(d); db.commit(); db.refresh(d)
    return d

@router.get("/divisions", response_model=List[DivisionResponse])
def get_divisions(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(Division).all()

@router.get("/stations", response_model=List[StationResponse])
def get_stations(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(Station).all()
@router.get("/subdivisions", response_model=List[SubDivisionResponse])
def get_subdivisions(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(SubDivision).all()
    

@router.get("/subdivisions/by_division/{div_id}", response_model=List[SubDivisionResponse])
def get_sub_divisions_by_division_id(div_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(SubDivision).filter(SubDivision.division_id == div_id).all()
    
@router.get("/stations/by_subdivision/{subdiv_id}", response_model=List[StationResponse])
def get_stations_by_subdivision_id(subdiv_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(Station).filter(Station.subdivision_id == subdiv_id).all()


@router.get("/airconditioners/by_station/{stn_id}", response_model=List[AirConditionerResponse])
def get_acs_by_station(stn_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(AirConditioner).filter(AirConditioner.division_id == stn_id).all()

@router.get("/airconditioners/by_subdivision/{subdiv_id}", response_model=List[AirConditionerResponse])
def get_ac_by_subdivisions(subdiv_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return db.query(AirConditioner).filter(AirConditioner.subdivision_id == subdiv_id).all()
@router.post("/subdivisions", response_model=SubDivisionResponse)
def add_subdivision(sub: SubDivisionBase, db: Session = Depends(get_db)):
    if not db.query(Division).get(sub.division_id):
        raise HTTPException(404, "Division not found")
    s = SubDivision(**sub.dict())
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.get("/dashboard/subdivision/{subdivision_id}")
def subdivision_dashboard(
    subdivision_id: int,
    show_overdue: Optional[bool] = Query(False, description="Show only overdue ACs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Maintainer can only access own subdivision
    if current_user.role == UserRole.Maintainer:
        if current_user.maintainer.subdivision_id != subdivision_id:
            raise HTTPException(403, "Access denied to this subdivision")

    subdivision = db.query(SubDivision).get(subdivision_id)
    if not subdivision:
        raise HTTPException(404, "Subdivision not found")

    ac_list = []
    today = date.today()

    for ac in subdivision.acs:
        last_record = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.ac_id == ac.id
        ).order_by(MaintenanceRecord.maintenance_date.desc()).first()

        next_due = last_record.next_due_date if last_record else None
        status = last_record.status if last_record else MaintenanceStatus.Scheduled

        # If show_overdue is True, skip ACs that are not overdue
        if show_overdue and (not next_due or status != MaintenanceStatus.Overdue):
            continue

        ac_list.append({
            "ac_id": ac.id,
            "ac_name": ac.name,
            "station": ac.location,
            "last_maintenance_date": last_record.maintenance_date if last_record else None,
            "next_due_date": next_due,
            "current_status": status.value,
            "maintenance_type": last_record.maintenance_type.value if last_record else None,
            "parts_replaced": last_record.parts_replaced if last_record else None
        })

    return {
        "subdivision": subdivision.name,
        "division": subdivision.division.name,
        "total_acs": len(subdivision.acs),
        "acs": ac_list
    }
@router.get("/dashboard/division/{division_id}")
def division_dashboard(
    division_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admins can access full division dashboard
    if current_user.role != UserRole.Admin:
        raise HTTPException(403, "Access denied: Admins only")

    division = db.query(Division).get(division_id)
    if not division:
        raise HTTPException(404, "Division not found")

    dashboard = {
        "division": division.name,
        "total_acs": 0,
        "subdivisions": []
    }

    today = date.today()

    for sub in division.subdivisions:
        sub_acs = []
        status_counts = {
            "Scheduled": 0,
            "Completed": 0,
            "Overdue": 0,
            "Breakdown": 0
        }

        for ac in sub.acs:
            last_record = db.query(MaintenanceRecord).filter(
                MaintenanceRecord.ac_id == ac.id
            ).order_by(MaintenanceRecord.maintenance_date.desc()).first()

            status = last_record.status if last_record else MaintenanceStatus.Scheduled

            status_counts[status.value] += 1

            sub_acs.append({
                "ac_id": ac.id,
                "ac_name": ac.name,
                "location": ac.location,
                "last_maintenance_date": last_record.maintenance_date if last_record else None,
                "next_due_date": last_record.next_due_date if last_record else None,
                "current_status": status.value,
                "maintenance_type": last_record.maintenance_type.value if last_record else None,
                "parts_replaced": last_record.parts_replaced if last_record else None
            })

        dashboard["subdivisions"].append({
            "subdivision": sub.name,
            "total_acs": len(sub.acs),
            "status_counts": status_counts,
            "acs": sub_acs
        })
        dashboard["total_acs"] += len(sub.acs)

    return dashboard