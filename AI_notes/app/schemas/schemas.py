from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional



class user(BaseModel):
    username:str 
    email:EmailStr
    password:str

class login_user(BaseModel):
    email:EmailStr
    password:str


class NotesCreate(BaseModel):
    title:str
    content:str

class Notes(BaseModel):
    title:str
    content:str
    create_at:datetime

class NotesResponse(Notes):
    id:int
    pass  
    user_id:int  
    

class QuestionRequest(BaseModel):
    question: str

class AI(Notes):
    pass
    create_at:datetime



class UserBase(BaseModel):
    email:EmailStr
    password:str


class UserCreate(UserBase):
    pass            


class UserResponse(BaseModel):
    
    id:int
    email:EmailStr
    create_at: datetime   


    class Config:
        from_attributes = True
   


class UserLogin(BaseModel):
    email:EmailStr
    password:str


class token(BaseModel):
    access_token: str
    token_type:str

class token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int]
    role: Optional[str]
        