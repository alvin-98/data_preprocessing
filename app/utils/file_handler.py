import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from pydub import AudioSegment

class FileHandler:
    @staticmethod
    async def save_upload(file: UploadFile, upload_dir: Path) -> str:
        """Save uploaded file and return the file path."""
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return str(file_path)

    @staticmethod
    def convert_audio_to_wav(file_path: str) -> str:
        """Convert audio file to WAV format if needed."""
        if not file_path.lower().endswith('.wav'):
            audio = AudioSegment.from_file(file_path)
            wav_path = file_path.rsplit('.', 1)[0] + '.wav'
            audio.export(wav_path, format='wav')
            os.remove(file_path)
            return wav_path
        return file_path

    @staticmethod
    def get_processed_path(original_path: str, action: str, extension: str) -> str:
        """Generate path for processed file."""
        directory = os.path.dirname(original_path)
        return os.path.join(directory, f"processed_{action}_{uuid.uuid4().hex}{extension}") 