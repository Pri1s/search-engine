from datetime import datetime

from sqlalchemy import Text, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    source_file: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text) # `Text` means that a database column can store a large amount of text
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )