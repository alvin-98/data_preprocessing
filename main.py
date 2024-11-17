from fastapi import FastAPI, Form, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageOps
import os
import uuid
from typing import List

app = FastAPI()

# Directories for uploads and templates
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

TEMPLATES_DIR = "templates"
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Upload and preprocess files
uploaded_file_path = None
processed_file_path = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page with upload and processing options.
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, 
         "uploaded_file": uploaded_file_path, 
         "processed_file": processed_file_path}
    )

@app.post("/upload_image/")
async def upload_image(file: UploadFile):
    """
    Handle image upload and save the file.
    """
    global uploaded_file_path
    uploaded_file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(uploaded_file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "Image uploaded successfully", "file_path": uploaded_file_path}

@app.post("/process_image/")
async def process_image(actions: List[str] = Form(...)):
    """
    Apply multiple preprocessing or augmentation actions to the uploaded image.
    """
    global uploaded_file_path, processed_file_path
    
    if not uploaded_file_path:
        return {"error": "No image uploaded"}

    processed_images = []
    
    for action in actions:
        img = Image.open(uploaded_file_path)
        
        # Preprocessing/Augmentation
        if action == "grayscale":
            img = ImageOps.grayscale(img)
        elif action == "resize":
            img = img.resize((128, 128))
        elif action == "flip":
            img = ImageOps.flip(img)
        elif action == "rotate":
            img = img.rotate(45)

        # Save processed image
        processed_file_path = os.path.join(UPLOAD_DIR, f"processed_{action}_{uuid.uuid4().hex}.png")
        img.save(processed_file_path)
        processed_images.append({
            "action": action,
            "file_path": processed_file_path,
            "description": get_action_description(action)
        })

    return {"status": "Images processed successfully", "processed_images": processed_images}

def get_action_description(action: str) -> str:
    """
    Return description for each image processing action.
    """
    descriptions = {
        "grayscale": "Converts the image to grayscale by removing color information, resulting in a black and white image.",
        "resize": "Resizes the image to 128x128 pixels while maintaining aspect ratio, useful for standardizing image sizes.",
        "flip": "Flips the image vertically, creating a mirror effect along the horizontal axis.",
        "rotate": "Rotates the image by 45 degrees clockwise, useful for orientation adjustment."
    }
    return descriptions.get(action, "No description available.")

@app.get("/view_image/")
async def view_image(image_path: str):
    """
    Serve the uploaded or processed image.
    """
    return FileResponse(image_path)
