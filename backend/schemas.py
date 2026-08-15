from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    title: str
    url: str
    content: str

# basic class we use for the creation of a new document
class DocumentCreate(DocumentBase):
    pass

# our response object back to the client per API operation
class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True # tells Pydantic: "when creting this schema, allow me to read values fro object attributes, not just dictionaries"
    )