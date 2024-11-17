from abc import ABC, abstractmethod
from typing import List, Dict
import os
import uuid
from ..utils.file_handler import FileHandler

class BaseProcessor(ABC):
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        self.file_handler = FileHandler()

    @abstractmethod
    async def process(self, file_path: str, actions: List[str]) -> Dict:
        """Process the file with selected modifications."""
        pass

    @abstractmethod
    def get_description(self, action: str) -> str:
        """Return description for processing actions."""
        pass

    def get_processed_path(self, original_path: str, action: str, extension: str) -> str:
        """Generate path for processed file."""
        return os.path.join(
            self.upload_dir, 
            f"processed_{action}_{uuid.uuid4().hex}{extension}"
        )

    def handle_error(self, error: Exception, action: str = None) -> Dict:
        """Handle processing errors."""
        error_msg = f"Error processing {action}: {str(error)}" if action else str(error)
        print(error_msg)
        return {"error": error_msg} 