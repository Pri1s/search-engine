from database import SessionLocal # so we can create a database session
from models import Document # so we can query the docs table

from search.tokenizer import tokenize
from search.index import InvertedIndex

def build_index():
    db = SessionLocal()
    index = InvertedIndex() # this inverted index does not persist in memory for now
    try:
        docs = db.query(Document).all()
        for doc in docs:
            tokens = tokenize(doc.content)
            index.add_document(
                doc.id,
                tokens
            )
        return index
    finally:
        db.close()