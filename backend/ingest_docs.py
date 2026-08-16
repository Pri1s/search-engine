import json
from pathlib import Path # help work with paths

from database import SessionLocal
from models import Document

BASE_DIR = Path(__file__).resolve().parent.parent # root directory
DOCS_DIR = BASE_DIR / "data" / "documents"

db = SessionLocal() # start the database session?

for file_path in DOCS_DIR.glob("*.json"): # find every file in this directory ending with `.json`
    with open(file_path, "r") as file:
        data = json.load(file)
    document = Document(
        title=data["title"],
        url=data["url"],
        content=data["content"]
    )
    db.add(document)

db.commit()
db.close()