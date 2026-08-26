from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    title: str
    url: str
    content: str

# basic class we use for the creation of a new document
class DocumentCreate(DocumentBase):
    pass

# used for partial updates: every field is optional so the client can send only what's changing
class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None

# our response object back to the client per API operation
class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True # tells Pydantic: "when creting this schema, allow me to read values fro object attributes, not just dictionaries"
    )