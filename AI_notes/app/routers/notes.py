from ..models import models
from ..schemas.schemas import Notes,NotesResponse,NotesCreate
from fastapi import Body, FastAPI, responses, status, HTTPException, Depends,APIRouter
from ..database.database import engine, get_db,pinecone_index
from sqlalchemy.orm import Session
from ..oauth2 import get_current_user
from pinecone import Pinecone
import os
from dotenv import load_dotenv 
from openai import OpenAI
from datetime import timezone


load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY")

client = OpenAI()
router = APIRouter(prefix="/notes", tags=["Notes"])



@router.get("/", response_model=list[NotesResponse])
async def read_notes(db: Session = Depends(get_db),current_user=Depends(get_current_user)):
    
    if current_user.role == "Admin":
        notes = db.query(models.Notes).all()
    else:
        notes = (db.query(models.Notes).filter(models.Notes.user_id == current_user.id).all())

    return notes




@router.post("/", status_code=status.HTTP_201_CREATED, response_model=NotesResponse)
def write_note(
    notes: NotesCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1️⃣ Save note in SQL
    new_note = models.Notes(
        **notes.dict(),
        user_id=current_user.id
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    # 2️⃣ Create embedding from content (and title if you want)
    text_to_embed = f"{new_note.title}\n{new_note.content}"

    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text_to_embed
    )

    embedding_vector = embedding_response.data[0].embedding

    # 3️⃣ Send to Pinecone
    pinecone_index.upsert(
        vectors=[
            {
                "id": f"note-{new_note.id}",
                "values": embedding_vector,
                "metadata": {
                    "user_id": new_note.user_id,
                    "created_at": new_note.create_at.replace(tzinfo=timezone.utc).isoformat(),
                     "text": text_to_embed  # ✅ THIS WAS MISSING
                }
            }
        ]
    )

    return new_note



@router.get("/{id}", response_model=NotesResponse)
async def get_notes(id: int,db: Session = Depends(get_db),current_user=Depends(get_current_user)
):
    note = db.query(models.Notes).filter(models.Notes.id == id,models.Notes.user_id == current_user.id).first()

    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with id {id} not found"
        )

    return note




@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notes(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    note_query = db.query(models.Notes).filter(models.Notes.id == id)
    note = note_query.first()

    if not note:
        raise HTTPException(status_code=404, detail="Post not found")

    # Non-admin users can only delete their own notes
    if current_user.role != "Admin" and note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 1️⃣ Delete from Pinecone
    try:
        pinecone_index.delete(ids=[f"note-{note.id}"])
    except Exception as e:
        # Log but don't block deletion
        print(f"Pinecone delete failed for note {note.id}: {e}")

    # 2️⃣ Delete from SQL
    note_query.delete(synchronize_session=False)
    db.commit()

    return responses.Response(status_code=204)




@router.put("/{id}", response_model=NotesResponse)
async def update_notes(
    id: int,
    notes: NotesCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    note_query = db.query(models.Notes).filter(models.Notes.id == id)
    note = note_query.first()

    if not note:
        raise HTTPException(status_code=404, detail="Post not found")

    # Non-admin users can only update their own notes
    if current_user.role != "Admin" and note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 1️⃣ Update SQL
    note_query.update(notes.dict(), synchronize_session=False)
    db.commit()
    db.refresh(note)

    # 2️⃣ Recreate embedding
    text_to_embed = f"{note.title}\n{note.content}"

    embedding_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text_to_embed
    )
    embedding_vector = embedding_response.data[0].embedding

    # 3️⃣ Update Pinecone (same vector ID)
    pinecone_index.upsert(
        vectors=[
            {
                "id": f"note-{note.id}",
                "values": embedding_vector,
                "metadata": {
                    "user_id": note.user_id,
                    "created_at": note.create_at.replace(tzinfo=timezone.utc).isoformat(),
                    "text": text_to_embed
                }
            }
        ]
    )

    return note
