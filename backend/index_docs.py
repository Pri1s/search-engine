from database import SessionLocal # so we can create a database session
from models import Document # so we can query the docs table

from search.tokenizer import tokenize
from search.index import InvertedIndex

db = SessionLocal()
index = InvertedIndex() # this inverted index does not persist in memory for now
documents = db.query(Document).all()

for document in documents:
    tokens = tokenize(document.content)
    index.add_document(
        document.id,
        tokens
    )

print(index.index)

db.close()