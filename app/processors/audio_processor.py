from typing import Dict, List
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from scipy.io import wavfile
from scipy.signal import butter, filtfilt
from .base_processor import BaseProcessor

class AudioProcessor(BaseProcessor):
    async def process(self, file_path: str, actions: List[str]) -> Dict:
        """Process audio with selected modifications."""
        try:
            processed_results = []
            
            for action in actions:
                try:
                    # Load audio file
                    audio = AudioSegment.from_wav(file_path)
                    original_properties = self._get_properties(audio)
                    
                    processed_audio = self._apply_action(audio, file_path, action)
                    processed_path = self.get_processed_path(file_path, action, ".wav")
                    processed_audio.export(processed_path, format='wav')
                    
                    processed_properties = self._get_properties(processed_audio)
                    changes = self._calculate_changes(original_properties, processed_properties)
                    
                    processed_results.append({
                        "action": action,
                        "file_path": processed_path,
                        "original_path": file_path,
                        "description": self.get_description(action),
                        "changes": changes,
                        "properties": processed_properties
                    })

                except Exception as e:
                    return self.handle_error(e, action)

            return {"processed_images": processed_results}
            
        except Exception as e:
            return self.handle_error(e)

    def _apply_action(self, audio: AudioSegment, file_path: str, action: str) -> AudioSegment:
        """Apply specific action to audio."""
        if action == "normalize":
            return normalize(audio)
        elif action == "noise_reduction":
            return self._apply_noise_reduction(file_path)
        elif action == "change_speed":
            return audio.speedup(playback_speed=1.5)
        elif action == "low_pass_filter":
            return self._apply_filter(file_path, 'low')
        elif action == "high_pass_filter":
            return self._apply_filter(file_path, 'high')
        elif action == "trim_silence":
            return audio.strip_silence(
                silence_len=100,
                silence_thresh=-50
            )
        return audio

    def _apply_noise_reduction(self, file_path: str) -> AudioSegment:
        """Apply noise reduction using low-pass filter."""
        sample_rate, samples = self._load_and_prepare_samples(file_path)
        filtered_samples = self._apply_butter_filter(samples, sample_rate, 2000, 'low')
        return self._create_audio_segment(filtered_samples, sample_rate)

    def _apply_filter(self, file_path: str, filter_type: str) -> AudioSegment:
        """Apply low/high pass filter."""
        sample_rate, samples = self._load_and_prepare_samples(file_path)
        cutoff = 1000 if filter_type == 'low' else 500
        filtered_samples = self._apply_butter_filter(samples, sample_rate, cutoff, filter_type)
        return self._create_audio_segment(filtered_samples, sample_rate)

    def _load_and_prepare_samples(self, file_path: str):
        """Load and prepare audio samples."""
        sample_rate, samples = wavfile.read(file_path)
        if len(samples.shape) > 1:
            samples = samples.mean(axis=1)
        
        # Ensure minimum length for filtering
        min_length = 50
        if len(samples) < min_length:
            samples = np.pad(samples, (0, min_length - len(samples)), 'constant')
            
        return sample_rate, samples

    def _apply_butter_filter(self, samples: np.ndarray, sample_rate: int, 
                           cutoff: int, filter_type: str) -> np.ndarray:
        """Apply Butterworth filter to samples."""
        nyquist = sample_rate // 2
        order = min(4, len(samples) // 4)
        b, a = butter(order, cutoff / nyquist, btype=filter_type)
        return filtfilt(b, a, samples)

    def _create_audio_segment(self, samples: np.ndarray, sample_rate: int) -> AudioSegment:
        """Create AudioSegment from samples."""
        return AudioSegment(
            samples.astype(np.int16).tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )

    def _get_properties(self, audio: AudioSegment) -> Dict:
        """Get audio properties."""
        return {
            "duration": len(audio) / 1000,
            "sample_rate": audio.frame_rate,
            "channels": audio.channels,
            "max_amplitude": float(audio.max)
        }

    def _calculate_changes(self, original: Dict, processed: Dict) -> Dict:
        """Calculate changes between original and processed audio."""
        return {
            "duration_change": processed["duration"] - original["duration"],
            "amplitude_change": processed["max_amplitude"] - original["max_amplitude"]
        }

    def get_description(self, action: str) -> str:
        """Return description for audio processing actions."""
        descriptions = {
            "normalize": "Adjusts the volume to a standard level across the audio.",
            "noise_reduction": "Reduces background noise while preserving the main audio.",
            "change_speed": "Changes the playback speed without affecting the pitch.",
            "low_pass_filter": "Removes high frequencies while keeping low frequencies.",
            "high_pass_filter": "Removes low frequencies while keeping high frequencies.",
            "trim_silence": "Removes silent segments from the audio."
        }
        return descriptions.get(action, "No description available.") 