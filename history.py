from datetime import datetime
import base64
from database import SessionLocal
from models import HistoryEntry
from sqlalchemy import desc

class HistoryManager:
    def __init__(self):
        """Initialize the HistoryManager with database session"""
        self.db = SessionLocal()

    def save_entry(self, audio_data, summary_html, original_filename, metadata, extracted_text):
        """Save a new history entry to the database"""
        try:
            # Create timestamp-based ID (maintaining compatibility)
            entry_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create new entry
            entry = HistoryEntry(
                id=entry_id,
                original_filename=original_filename,
                summary_html=summary_html,
                audio_data=base64.b64decode(audio_data),  # Store as binary
                settings_metadata=metadata,  # Using new column name
                extracted_text=extracted_text
            )
            
            # Add and commit to database
            self.db.add(entry)
            self.db.commit()
            
            return entry_id
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to save history entry: {str(e)}")

    def get_entries(self, limit=10, offset=0, include_text=False):
        """Get the most recent history entries from the database"""
        try:
            # Query entries with ordering and pagination
            query = self.db.query(HistoryEntry).order_by(desc(HistoryEntry.timestamp))
            entries = query.offset(offset).limit(limit).all()
            
            # Convert entries to dictionary format
            result = []
            for entry in entries:
                entry_dict = entry.to_dict()
                if not include_text:
                    entry_dict.pop('extracted_text', None)
                result.append(entry_dict)
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to get history entries: {str(e)}")

    def get_entry_text(self, entry_id):
        """Get the extracted text for a specific entry"""
        try:
            entry = self.db.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
            return entry.extracted_text if entry else None
        except Exception as e:
            raise Exception(f"Failed to get entry text: {str(e)}")

    def delete_entry(self, entry_id):
        """Delete a history entry"""
        try:
            entry = self.db.query(HistoryEntry).filter(HistoryEntry.id == entry_id).first()
            if entry:
                self.db.delete(entry)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete history entry: {str(e)}")

    def clear_history(self):
        """Clear all history entries"""
        try:
            self.db.query(HistoryEntry).delete()
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to clear history: {str(e)}")

    def __del__(self):
        """Ensure database session is closed"""
        self.db.close() 