from fastapi import APIRouter, Depends, HTTPException
from app.schemas  import UserBase, MaintainerResponse, MaintainerBase, Token
from app.models import User, SubDivision, Maintainer, UserRole
from app.api.auth_utils import get_current_user,get_password_hash,verify_password, create_access_token
from sqlalchemy.orm import Session
from app.db.database import get_db
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(prefix="/user", tags=["user"])
@router.get("/me",response_model=UserBase)
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/maintainers", response_model=MaintainerResponse)
def add_maintainer(m: MaintainerBase, db: Session = Depends(get_db)):
    if not db.query(SubDivision).get(m.subdivision_id):
        raise HTTPException(404, "SubDivision not found")
    mt = Maintainer(**m.dict())
    db.add(mt); db.commit(); db.refresh(mt)
    return mt


@router.post("/register")
def register_user(first_name: str, last_name:str, designation:str, email: str, password: str, role: UserRole, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(password)
    user = User(first_name=first_name, last_name=last_name, designation=designation, email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered successfully"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user" :user}

