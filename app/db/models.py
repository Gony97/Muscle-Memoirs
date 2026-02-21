from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.db.database import Base

class DriveAsset(Base):
    __tablename__ = "drive_assets"

    id = Column(Integer, primary_key=True, index=True)

    # UNIQUE pointer key (this is what must be unique)
    logical_key = Column(String(255), unique=True, index=True, nullable=False)

    # Drive file can be referenced by multiple logical keys
    drive_file_id = Column(String(255), nullable=False)

    filename = Column(String(512), nullable=False)
    mime_type = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)