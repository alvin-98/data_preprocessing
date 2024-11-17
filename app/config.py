import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Upload directory
UPLOAD_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Templates directory
TEMPLATES_DIR = BASE_DIR / "templates"
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# NLTK resources
NLTK_RESOURCES = [
    'punkt',
    'stopwords',
    'wordnet',
    'omw-1.4',
    'averaged_perceptron_tagger'
] 