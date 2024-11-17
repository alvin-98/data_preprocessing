from PIL import Image, ImageOps
from typing import List, Dict
from .base_processor import BaseProcessor

class ImageProcessor(BaseProcessor):
    async def process(self, file_path: str, actions: List[str]) -> Dict:
        """Process image with selected modifications."""
        try:
            processed_results = []
            
            for action in actions:
                try:
                    img = Image.open(file_path)
                    processed_img = self._apply_action(img, action)
                    
                    processed_path = self.get_processed_path(file_path, action, ".png")
                    processed_img.save(processed_path)
                    
                    processed_results.append({
                        "action": action,
                        "file_path": processed_path,
                        "original_path": file_path,
                        "description": self.get_description(action)
                    })
                except Exception as e:
                    return self.handle_error(e, action)

            return {"processed_images": processed_results}
            
        except Exception as e:
            return self.handle_error(e)

    def _apply_action(self, img: Image.Image, action: str) -> Image.Image:
        """Apply specific action to image."""
        if action == "grayscale":
            return ImageOps.grayscale(img)
        elif action == "resize":
            return img.resize((128, 128))
        elif action == "flip":
            return ImageOps.flip(img)
        elif action == "rotate":
            return img.rotate(45)
        return img

    def get_description(self, action: str) -> str:
        """Return description for image processing actions."""
        descriptions = {
            "grayscale": "Converts the image to grayscale by removing color information.",
            "resize": "Resizes the image to 128x128 pixels while maintaining aspect ratio.",
            "flip": "Flips the image vertically, creating a mirror effect.",
            "rotate": "Rotates the image by 45 degrees clockwise."
        }
        return descriptions.get(action, "No description available.") 