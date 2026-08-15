from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session # a session is a temporary workspace for interacting with the database

from database import get_db
from models import Document
from schemas import DocumentCreate, DocumentResponse

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Basketball Search Engine API"}

@app.post("/documents", response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db) # calls `get_db` which creates a SessionLocal() & gives session to the function
    ):
    db_document = Document(
        title=document.title,
        url=document.url,
        content=document.content
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@app.get("/documents/{document_id}", response_model=list[DocumentResponse])
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return document
