from fastapi import Body, FastAPI, responses, status, HTTPException, Depends
from sqlalchemy.orm import Session
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from app.models import models
from app.database.database import engine
from app.routers import notes,ai_route,user,auth,admin

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# PostgreSQL (psycopg2) connection loop
while True:
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="fastAPI",
            user="postgres",
            password="password",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        print("Database connected successfully")
        break
    except Exception as error:
        print("Database connection failed")
        print("Error:", error)
        time.sleep(2)


app.include_router(user.router)
app.include_router(notes.router)
app.include_router(ai_route.router) 
app.include_router(auth.router)
app.include_router(admin.router)

# ROOT ROUTE
@app.get("/")
async def read_root():
    return {"Hello": "World"}
