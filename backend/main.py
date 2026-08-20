from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session # a session is a temporary workspace for interacting with the database
from contextlib import asynccontextmanager # a tool for defining the lifetime of a resource

from database import Base, get_db, engine
from models import Document
from schemas import DocumentCreate, DocumentResponse
from search.tokenizer import tokenize
from index_documents import build_index

@asynccontextmanager
async def lifespan(app: FastAPI):
    # the following line: look at my SQLAlchemy models & make sure the database tables exist
    Base.metadata.create_all(bind=engine) # database tables need to exist prior to us building the index
    app.state.index = build_index()
    # everything prior to the yield is is interpretted as the enter/setup phase: runs once when FastAPI starts
    # the yielded period is the resource-is-active 
    # FastAPI serves requests while we're here
    yield
    # everything after the yield is the exit/cleanup phase: runs when FastAPI shuts down

app = FastAPI(lifespan=lifespan)

# allows the static frontend (served from a different origin, e.g. a local file server) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # requests from any origin are allowed
    allow_methods=["GET"], # only GET methods are permitted
    allow_headers=["*"], # allows any HTTP request headers
)

@app.get("/")
def root():
    return {"message": "Basketball Search Engine API"}

@app.post("/documents", response_model=DocumentResponse)
def create_document(
    doc: DocumentCreate,
    db: Session = Depends(get_db) # calls `get_db` which creates a SessionLocal() & gives session to the function
    ):
    db_doc = Document(
        title=doc.title,
        url=doc.url,
        content=doc.content
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc) # updates PYTHON object w/ values that the database created for our object (i.e default values for NULL fields sent in)
    return db_doc

@app.get("/documents", response_model=list[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/search")
def search_documents(
    q: str,
    request: Request,
    db: Session = Depends(get_db)
):
    tokens = tokenize(q)
    ranked_results = request.app.state.index.search(tokens)
    ranked_doc_ids = [doc_id for doc_id, _ in ranked_results]
    docs = db.query(Document).filter(Document.id.in_(ranked_doc_ids)).all()
    docs_lookup = {doc.id: doc for doc in docs}
    return [
        {
            "document": docs_lookup[doc_id],
            "score": score
        } for doc_id, score in ranked_results if doc_id in docs_lookup
    ]