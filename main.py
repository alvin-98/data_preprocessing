from fastapi import FastAPI, Form, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageOps
import os
import uuid
from typing import List
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
import string
import re

# Download all required NLTK data at once
nltk_resources = ['punkt', 'stopwords', 'wordnet', 'omw-1.4', 'averaged_perceptron_tagger']
for resource in nltk_resources:
    try:
        nltk.download(resource, quiet=True)
    except Exception as e:
        print(f"Error downloading {resource}: {str(e)}")

app = FastAPI()

# Directories for uploads and templates
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

TEMPLATES_DIR = "templates"
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile, type: str = Form(...)):
    """
    Handle file upload for both image and text files.
    """
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "File uploaded successfully", "file_path": file_path}

@app.get("/view_content/")
async def view_content(path: str):
    """
    Serve the uploaded content (text or image).
    """
    if path.lower().endswith(('.txt', '.doc', '.docx')):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return JSONResponse(content={"content": content})
    return FileResponse(path)

@app.post("/process/")
async def process_content(file_path: str = Form(...), actions: List[str] = Form(...), type: str = Form(...)):
    """
    Process either image or text content based on type.
    """
    if type == "image":
        return await process_image(file_path, actions)
    else:
        return await process_text(file_path, actions)

async def process_image(file_path: str, actions: List[str]):
    """
    Process image with selected modifications.
    """
    processed_images = []
    
    for action in actions:
        img = Image.open(file_path)
        
        if action == "grayscale":
            img = ImageOps.grayscale(img)
        elif action == "resize":
            img = img.resize((128, 128))
        elif action == "flip":
            img = ImageOps.flip(img)
        elif action == "rotate":
            img = img.rotate(45)

        processed_path = os.path.join(UPLOAD_DIR, f"processed_{action}_{uuid.uuid4().hex}.png")
        img.save(processed_path)
        
        processed_images.append({
            "action": action,
            "file_path": processed_path,
            "description": get_image_description(action)
        })

    return {"processed_images": processed_images}

async def process_text(file_path: str, actions: List[str]):
    """
    Process text with selected modifications.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        processed_results = []
        
        for action in actions:
            try:
                processed_text = text
                changes_made = []  # Track changes for each method
                
                if action == "lowercase":
                    original_words = text.split()
                    processed_text = processed_text.lower()
                    changed_words = processed_text.split()
                    changes_made = [
                        (orig, changed) 
                        for orig, changed in zip(original_words, changed_words) 
                        if orig != changed
                    ][:5]
                
                elif action == "remove_punctuation":
                    original_text = processed_text
                    processed_text = processed_text.translate(str.maketrans("", "", string.punctuation))
                    changes_made = [
                        (char, "") 
                        for char in set(original_text) 
                        if char in string.punctuation
                    ][:5]
                
                elif action == "remove_numbers":
                    original_text = processed_text
                    processed_text = re.sub(r'\d+', '', processed_text)
                    changes_made = [
                        (num, "") 
                        for num in set(re.findall(r'\d+', original_text))
                    ][:5]
                
                elif action == "remove_stopwords":
                    # Simple word splitting instead of word_tokenize
                    words = processed_text.split()
                    original_words = words.copy()
                    processed_text = ' '.join([word for word in words if word.lower() not in stop_words])
                    changes_made = [
                        (word, "removed") 
                        for word in original_words 
                        if word.lower() in stop_words
                    ][:5]
                
                elif action == "lemmatize":
                    # Simple word splitting instead of word_tokenize
                    words = processed_text.split()
                    original_words = words.copy()
                    processed_words = [lemmatizer.lemmatize(word) for word in words]
                    processed_text = ' '.join(processed_words)
                    changes_made = [
                        (orig, lemm) 
                        for orig, lemm in zip(original_words, processed_words) 
                        if orig != lemm
                    ][:5]
                
                elif action == "stem":
                    # Simple word splitting instead of word_tokenize
                    words = processed_text.split()
                    original_words = words.copy()
                    processed_words = [stemmer.stem(word) for word in words]
                    processed_text = ' '.join(processed_words)
                    changes_made = [
                        (orig, stemmed) 
                        for orig, stemmed in zip(original_words, processed_words) 
                        if orig != stemmed
                    ][:5]

                # Save processed text
                processed_path = os.path.join(UPLOAD_DIR, f"processed_{action}_{uuid.uuid4().hex}.txt")
                with open(processed_path, 'w', encoding='utf-8') as f:
                    f.write(processed_text)

                processed_results.append({
                    "action": action,
                    "file_path": processed_path,
                    "content": processed_text,
                    "description": get_text_description(action),
                    "changes": changes_made,
                    "word_count": {
                        "before": len(text.split()),
                        "after": len(processed_text.split())
                    }
                })

            except Exception as e:
                print(f"Error processing action {action}: {str(e)}")
                # Continue with next action instead of failing completely
                continue

        if not processed_results:
            return {"error": "No successful processing results"}
            
        return {"processed_images": processed_results}

    except Exception as e:
        print(f"Error processing text: {str(e)}")
        return {"error": f"Error processing text: {str(e)}"}

def get_image_description(action: str) -> str:
    """
    Return description for image processing actions.
    """
    descriptions = {
        "grayscale": "Converts the image to grayscale by removing color information.",
        "resize": "Resizes the image to 128x128 pixels while maintaining aspect ratio.",
        "flip": "Flips the image vertically, creating a mirror effect.",
        "rotate": "Rotates the image by 45 degrees clockwise."
    }
    return descriptions.get(action, "No description available.")

def get_text_description(action: str) -> str:
    """
    Return description for text processing actions.
    """
    descriptions = {
        "lowercase": "Converts all text to lowercase, standardizing the text case.",
        "remove_punctuation": "Removes all punctuation marks from the text.",
        "remove_numbers": "Removes all numerical digits from the text.",
        "remove_stopwords": "Removes common words (e.g., 'the', 'is', 'at') that often don't carry significant meaning.",
        "lemmatize": "Reduces words to their base or dictionary form (e.g., 'running' → 'run').",
        "stem": "Reduces words to their root form using the Porter Stemming algorithm."
    }
    return descriptions.get(action, "No description available.")
