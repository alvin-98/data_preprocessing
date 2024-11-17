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
from pydub import AudioSegment
from pydub.effects import normalize
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt

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
    Handle file upload for image, text, and audio files.
    """
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Convert audio to WAV if it's an audio file
    if type == "audio" and not file_path.lower().endswith('.wav'):
        audio = AudioSegment.from_file(file_path)
        wav_path = file_path.rsplit('.', 1)[0] + '.wav'
        audio.export(wav_path, format='wav')
        os.remove(file_path)  # Remove original file
        file_path = wav_path
        
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
    Process either image, text, or audio content based on type.
    """
    if type == "image":
        return await process_image(file_path, actions)
    elif type == "text":
        return await process_text(file_path, actions)
    else:
        return await process_audio(file_path, actions)

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

async def process_audio(file_path: str, actions: List[str]):
    """
    Process audio with selected modifications.
    """
    try:
        processed_results = []
        
        for action in actions:
            try:
                # Load audio file
                audio = AudioSegment.from_wav(file_path)
                
                # Store original properties for comparison
                original_properties = {
                    "duration": len(audio) / 1000,  # in seconds
                    "sample_rate": audio.frame_rate,
                    "channels": audio.channels,
                    "max_amplitude": float(audio.max)
                }
                
                if action == "normalize":
                    processed_audio = normalize(audio)
                    description = "Normalized audio volume to a standard level"
                    
                elif action == "noise_reduction":
                    # Modified noise reduction for short audio files
                    sample_rate, samples = wavfile.read(file_path)
                    
                    # Convert to mono if stereo
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)
                    
                    # Ensure minimum length for filtering
                    min_length = 50  # minimum samples needed
                    if len(samples) < min_length:
                        # Pad the audio if too short
                        pad_length = min_length - len(samples)
                        samples = np.pad(samples, (0, pad_length), 'constant')
                    
                    nyquist = sample_rate // 2
                    cutoff = 2000  # Cutoff frequency for noise reduction
                    order = min(4, len(samples) // 4)  # Adjust filter order based on sample length
                    b, a = butter(order, cutoff / nyquist, btype='low')
                    filtered_samples = filtfilt(b, a, samples)
                    
                    # Trim back to original length if padded
                    if len(samples) > len(filtered_samples):
                        filtered_samples = filtered_samples[:len(samples)]
                    
                    processed_audio = AudioSegment(
                        filtered_samples.astype(np.int16).tobytes(), 
                        frame_rate=sample_rate,
                        sample_width=2,  # 16-bit audio
                        channels=1
                    )
                    description = "Reduced background noise using a low-pass filter"
                    
                elif action == "change_speed":
                    processed_audio = audio.speedup(playback_speed=1.5)
                    description = "Increased playback speed by 1.5x"
                    
                elif action == "low_pass_filter":
                    sample_rate, samples = wavfile.read(file_path)
                    
                    # Convert to mono if stereo
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)
                    
                    # Ensure minimum length for filtering
                    min_length = 50
                    if len(samples) < min_length:
                        pad_length = min_length - len(samples)
                        samples = np.pad(samples, (0, pad_length), 'constant')
                    
                    nyquist = sample_rate // 2
                    cutoff = 1000  # Cutoff frequency
                    order = min(4, len(samples) // 4)
                    b, a = butter(order, cutoff / nyquist, btype='low')
                    filtered_samples = filtfilt(b, a, samples)
                    
                    processed_audio = AudioSegment(
                        filtered_samples.astype(np.int16).tobytes(),
                        frame_rate=sample_rate,
                        sample_width=2,
                        channels=1
                    )
                    description = "Applied low-pass filter to remove high frequencies"
                    
                elif action == "high_pass_filter":
                    sample_rate, samples = wavfile.read(file_path)
                    
                    # Convert to mono if stereo
                    if len(samples.shape) > 1:
                        samples = samples.mean(axis=1)
                    
                    # Ensure minimum length for filtering
                    min_length = 50
                    if len(samples) < min_length:
                        pad_length = min_length - len(samples)
                        samples = np.pad(samples, (0, pad_length), 'constant')
                    
                    nyquist = sample_rate // 2
                    cutoff = 500  # Cutoff frequency
                    order = min(4, len(samples) // 4)
                    b, a = butter(order, cutoff / nyquist, btype='high')
                    filtered_samples = filtfilt(b, a, samples)
                    
                    processed_audio = AudioSegment(
                        filtered_samples.astype(np.int16).tobytes(),
                        frame_rate=sample_rate,
                        sample_width=2,
                        channels=1
                    )
                    description = "Applied high-pass filter to remove low frequencies"
                    
                elif action == "trim_silence":
                    processed_audio = audio.strip_silence(
                        silence_len=100,  # Reduced from 1000ms to 100ms for short audio
                        silence_thresh=-50  # -50 dBFS
                    )
                    description = "Removed silent segments from the audio"

                # Save processed audio
                processed_path = os.path.join(UPLOAD_DIR, f"processed_{action}_{uuid.uuid4().hex}.wav")
                processed_audio.export(processed_path, format='wav')
                
                # Get processed properties
                processed_properties = {
                    "duration": len(processed_audio) / 1000,  # in seconds
                    "sample_rate": processed_audio.frame_rate,
                    "channels": processed_audio.channels,
                    "max_amplitude": float(processed_audio.max)
                }
                
                # Calculate changes
                changes = {
                    "duration_change": processed_properties["duration"] - original_properties["duration"],
                    "amplitude_change": processed_properties["max_amplitude"] - original_properties["max_amplitude"]
                }

                processed_results.append({
                    "action": action,
                    "file_path": processed_path,
                    "description": description,
                    "changes": changes,
                    "properties": processed_properties
                })

            except Exception as e:
                print(f"Error processing action {action}: {str(e)}")
                continue

        if not processed_results:
            return {"error": "No successful processing results"}
            
        return {"processed_images": processed_results}
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return {"error": f"Error processing audio: {str(e)}"}

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

def get_audio_description(action: str) -> str:
    """
    Return description for audio processing actions.
    """
    descriptions = {
        "normalize": "Adjusts the volume to a standard level across the audio.",
        "noise_reduction": "Reduces background noise while preserving the main audio.",
        "change_speed": "Changes the playback speed without affecting the pitch.",
        "low_pass_filter": "Removes high frequencies while keeping low frequencies.",
        "high_pass_filter": "Removes low frequencies while keeping high frequencies.",
        "trim_silence": "Removes silent segments from the audio."
    }
    return descriptions.get(action, "No description available.")
