from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import require_roles
from app import crud

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/vehicle/{vehicle_id}/total_minutes")
async def vehicle_total(vehicle_id: int, days: int = 30, db: AsyncSession = Depends(get_db),
                        current_user = Depends(require_roles("field_officer","executive"))):
    mins = await crud.get_vehicle_total_run_minutes(db, vehicle_id, days)
    hours = mins // 60
    minutes = mins % 60
    return {"vehicle_id": vehicle_id, "total_minutes": mins, "hours": hours, "minutes": minutes, "period_days": days}

@router.get("/comparative")
async def comparative(days: int = 30, limit: int = 50, db: AsyncSession = Depends(get_db),
                      current_user = Depends(require_roles("executive","field_officer"))):
    rows = await crud.comparative_vehicle_report(db, days=days, limit=limit)
    # convert minutes to hours:minutes for convenience
    for r in rows:
        mins = r["total_minutes"]
        r["hours"] = mins // 60
        r["minutes"] = mins % 60
    return {"period_days": days, "vehicles": rows}
