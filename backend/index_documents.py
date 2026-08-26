from pathlib import Path

from database import SessionLocal # so we can create a database session
from models import Document # so we can query the docs table

from search.tokenizer import tokenize
from search.index import InvertedIndex

BASE_DIR = Path(__file__).resolve().parent.parent # root directory
INDEX_PATH = BASE_DIR / "data" / "index.pkl"

def build_index():
    db = SessionLocal()
    index = InvertedIndex() # this inverted index does not persist in memory for now
    try:
        docs = db.query(Document).all()
        for doc in docs:
            title_tokens = tokenize(doc.title)
            body_tokens = tokenize(doc.content)
            index.add_document(
                doc.id,
                title_tokens,
                body_tokens
            )
        return index
    finally:
        db.close()

if __name__ == "__main__":
    index = build_index()
    index.save(INDEX_PATH)