from fastapi import FastAPI, Form, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import nltk

from .config import UPLOAD_DIR, TEMPLATES_DIR, NLTK_RESOURCES
from .processors.processor_factory import ProcessorFactory
from .utils.file_handler import FileHandler

# Download NLTK resources
for resource in NLTK_RESOURCES:
    try:
        nltk.download(resource, quiet=True)
    except Exception as e:
        print(f"Error downloading {resource}: {str(e)}")

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize processors and file handler
processor_factory = ProcessorFactory(UPLOAD_DIR)
file_handler = FileHandler()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile, type: str = Form(...)):
    """Handle file upload for all types."""
    try:
        file_path = await file_handler.save_upload(file, UPLOAD_DIR)
        
        if type == "audio":
            file_path = file_handler.convert_audio_to_wav(file_path)
            
        return {"status": "File uploaded successfully", "file_path": file_path}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Upload failed: {str(e)}"}
        )

@app.get("/view_content/")
async def view_content(path: str):
    """Serve the uploaded content."""
    if path.lower().endswith(('.txt', '.doc', '.docx')):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return JSONResponse(content={"content": content})
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Error reading file: {str(e)}"}
            )
    return FileResponse(path)

@app.post("/process/")
async def process_content(
    file_path: str = Form(...),
    actions: List[str] = Form(...),
    type: str = Form(...)
):
    """Process content based on type using appropriate processor."""
    try:
        processor = processor_factory.get_processor(type)
        result = await processor.process(file_path, actions)
        
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content=result
            )
            
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"}
        ) 