from ..models import models
from ..schemas.schemas import UserCreate, UserResponse
from ..utils.utils import hash_password
from fastapi import responses, status, HTTPException, Depends, APIRouter
from ..database.database import get_db
from sqlalchemy.orm import Session
from ..oauth2 import get_current_user
from pinecone import Pinecone
import os




router = APIRouter(prefix="/users", tags=["Users"])

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "notes-api"  # must be lowercase
index = pc.Index(INDEX_NAME)

# CREATE USER (public)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user.password = hash_password(user.password)

    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# GET USER BY ID
@router.get("/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db),current_user = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} does not exist"
        )

    return user


# GET ALL USERS
@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db),current_user = Depends(get_current_user)):
    users = db.query(models.User).all()
    return users


# --------------------------------------------------
# DELETE USER (admin OR self) + Pinecone cleanup
# --------------------------------------------------

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_query = db.query(models.User).filter(models.User.id == id)
    user = user_query.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    #  Not admin AND trying to delete someone else
    if current_user.role != "Admin" and current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )

    # --------------------------------------------------
    # 1️⃣ Delete Pinecone vectors for this user
    # --------------------------------------------------
    try:
        index.delete(
            filter={
                "user_id": id
            }
        )
    except Exception as e:
        # Optional: log error instead of failing hard
        print(f"Pinecone delete failed for user {id}: {e}")

    # --------------------------------------------------
    # 2️⃣ Delete user from SQL (CASCADE deletes notes)
    # --------------------------------------------------
    user_query.delete(synchronize_session=False)
    db.commit()

    return responses.Response(status_code=status.HTTP_204_NO_CONTENT)
