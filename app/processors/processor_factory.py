from typing import Dict
from .image_processor import ImageProcessor
from .text_processor import TextProcessor
from .audio_processor import AudioProcessor
from .base_processor import BaseProcessor

class ProcessorFactory:
    def __init__(self, upload_dir: str):
        self.processors: Dict[str, BaseProcessor] = {
            "image": ImageProcessor(upload_dir),
            "text": TextProcessor(upload_dir),
            "audio": AudioProcessor(upload_dir)
        }

    def get_processor(self, type_: str) -> BaseProcessor:
        """Get appropriate processor for the file type."""
        processor = self.processors.get(type_)
        if not processor:
            raise ValueError(f"Unsupported file type: {type_}")
        return processor 