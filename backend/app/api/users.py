from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app import crud, schemas, models
from app.core.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=schemas.UserOut)
async def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Create user - only executive can create field officers and field_officers can create drivers
@router.post("/create", response_model=schemas.UserOut)
async def create_user(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db),
                    current_user: models.User = Depends(require_roles("executive", "field_officer"))):
    # enforce role hierarchy: only executive can create field_officer/executive; field_officer can create drivers
    if current_user.role == "field_officer" and user_in.role != "driver":
        raise HTTPException(status_code=403, detail="Field officers can only create drivers")
    if current_user.role == "executive" and user_in.role == "executive":
        raise HTTPException(status_code=403, detail="Cannot create another executive")
    return await crud.create_user(db, user_in)

@router.post("/init", response_model=schemas.UserOut)
async def create_first_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if any users exist
    result = await db.execute(select(models.User).limit(1))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=403, detail="First user already exists")
    
    # Create user
    password = user.password
    given_hashed_password = hash_password(password)
    new_user = models.User(email=user.email, first_name=user.first_name, last_name=user.last_name,hashed_password=given_hashed_password, role=user.role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
