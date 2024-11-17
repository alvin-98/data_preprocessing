from typing import List, Dict, Tuple
import string
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from .base_processor import BaseProcessor

class TextProcessor(BaseProcessor):
    def __init__(self, upload_dir: str):
        super().__init__(upload_dir)
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

    async def process(self, file_path: str, actions: List[str]) -> Dict:
        """Process text with selected modifications."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            processed_results = []
            
            for action in actions:
                try:
                    processed_text, changes = self._apply_action(text, action)
                    processed_path = self.get_processed_path(file_path, action, ".txt")
                    
                    with open(processed_path, 'w', encoding='utf-8') as f:
                        f.write(processed_text)

                    processed_results.append({
                        "action": action,
                        "file_path": processed_path,
                        "original_path": file_path,
                        "content": processed_text,
                        "description": self.get_description(action),
                        "changes": changes,
                        "word_count": {
                            "before": len(text.split()),
                            "after": len(processed_text.split())
                        }
                    })

                except Exception as e:
                    return self.handle_error(e, action)

            return {"processed_images": processed_results}

        except Exception as e:
            return self.handle_error(e)

    def _apply_action(self, text: str, action: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Apply specific action to text and return processed text and changes."""
        if action == "lowercase":
            return self._apply_lowercase(text)
        elif action == "remove_punctuation":
            return self._apply_remove_punctuation(text)
        elif action == "remove_numbers":
            return self._apply_remove_numbers(text)
        elif action == "remove_stopwords":
            return self._apply_remove_stopwords(text)
        elif action == "lemmatize":
            return self._apply_lemmatize(text)
        elif action == "stem":
            return self._apply_stem(text)
        return text, []

    def _apply_lowercase(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        original_words = text.split()
        processed_text = text.lower()
        changed_words = processed_text.split()
        changes = [
            (orig, changed) 
            for orig, changed in zip(original_words, changed_words) 
            if orig != changed
        ][:5]
        return processed_text, changes

    def _apply_remove_punctuation(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        processed_text = text.translate(str.maketrans("", "", string.punctuation))
        changes = [(char, "") for char in set(text) if char in string.punctuation][:5]
        return processed_text, changes

    def _apply_remove_numbers(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        changes = [(num, "") for num in set(re.findall(r'\d+', text))][:5]
        processed_text = re.sub(r'\d+', '', text)
        return processed_text, changes

    def _apply_remove_stopwords(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        words = text.split()
        processed_text = ' '.join([word for word in words if word.lower() not in self.stop_words])
        changes = [(word, "removed") for word in words if word.lower() in self.stop_words][:5]
        return processed_text, changes

    def _apply_lemmatize(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        words = text.split()
        processed_words = [self.lemmatizer.lemmatize(word) for word in words]
        processed_text = ' '.join(processed_words)
        changes = [(orig, lemm) for orig, lemm in zip(words, processed_words) if orig != lemm][:5]
        return processed_text, changes

    def _apply_stem(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        words = text.split()
        processed_words = [self.stemmer.stem(word) for word in words]
        processed_text = ' '.join(processed_words)
        changes = [(orig, stemmed) for orig, stemmed in zip(words, processed_words) if orig != stemmed][:5]
        return processed_text, changes

    def get_description(self, action: str) -> str:
        """Return description for text processing actions."""
        descriptions = {
            "lowercase": "Converts all text to lowercase, standardizing the text case.",
            "remove_punctuation": "Removes all punctuation marks from the text.",
            "remove_numbers": "Removes all numerical digits from the text.",
            "remove_stopwords": "Removes common words (e.g., 'the', 'is', 'at') that often don't carry significant meaning.",
            "lemmatize": "Reduces words to their base or dictionary form (e.g., 'running' → 'run').",
            "stem": "Reduces words to their root form using the Porter Stemming algorithm."
        }
        return descriptions.get(action, "No description available.")