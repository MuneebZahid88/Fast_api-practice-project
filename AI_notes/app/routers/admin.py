from ..models import models
from ..schemas.schemas import UserCreate,UserResponse
from fastapi import Body, FastAPI, responses, status, HTTPException, Depends,APIRouter
from ..database.database import engine, get_db
from sqlalchemy.orm import Session
from ..oauth2 import get_current_user
from app.utils.utils import hash_password


router = APIRouter(prefix="/admin", tags=["Admin"])



@router.post("/", response_model=UserResponse)
async def create_user_by_admin(user: UserCreate,db: Session = Depends(get_db),current_user = Depends(get_current_user)):
    

    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only"
        )

    hashed_password = hash_password(user.password)

    new_user = models.User(email=user.email,password=hashed_password,role="Admin")

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

