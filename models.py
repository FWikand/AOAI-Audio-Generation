from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, JSON, Text
from sqlalchemy.sql import func
from database import Base
import base64

class HistoryEntry(Base):
    __tablename__ = "history_entries"

    id = Column(String, primary_key=True)  # Using string ID to maintain compatibility
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    original_filename = Column(String)
    summary_html = Column(Text)
    audio_data = Column(LargeBinary)  # For storing WAV files
    settings_metadata = Column(JSON)  # For storing processing settings
    extracted_text = Column(Text)

    def to_dict(self):
        """Convert entry to dictionary format"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "original_filename": self.original_filename,
            "summary_html": self.summary_html,
            "audio_data": base64.b64encode(self.audio_data).decode('utf-8') if self.audio_data else None,
            "settings": self.settings_metadata,
            "extracted_text": self.extracted_text
        } 