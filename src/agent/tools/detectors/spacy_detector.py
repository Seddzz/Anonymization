import spacy
import re
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpacyDetector:
    """
    Multi-language PII detector supporting English, French, and Arabic.
    
    Features:
    - Automatic language detection
    - SpaCy for French/English (fast, accurate)
    - Arabic deferred to LLM detector (better language understanding)
    - Graceful fallback when models unavailable
    """
    
    def __init__(self):
        self.nlp_models = {}
        self._load_spacy_models()
    
    def _load_spacy_models(self):
        """Load available SpaCy models for French and English."""
        models = [('fr', 'fr_core_news_sm'), ('en', 'en_core_web_sm')]
        
        for lang, model_name in models:
            try:
                self.nlp_models[lang] = spacy.load(model_name)
                logger.info(f"✅ Loaded {lang.upper()} spaCy model")
            except OSError:
                logger.warning(f"⚠️ {lang.upper()} spaCy model not found")
    
    def detect(self, text: str, entity_types=None) -> List[Tuple[str, str, int, int]]:
        """
        Main detection method - automatically detects language and routes to detector.
        
        Args:
            text: Input text to analyze
            entity_types: List of entity types to detect (None = all)
        
        Returns:
            List of tuples: (entity_text, label, start_char, end_char)
        """
        if entity_types is None:
            entity_types = ["PERSON", "EMAIL", "ORGANIZATION", "AGE", "PHONE", "LOCATION"]
        
        lang = self._detect_language(text)
        logger.info(f"Detected language: {lang}")
        
        # Route based on language
        if lang == 'ar':
            return self._detect_arabic(text, entity_types)
        elif lang in self.nlp_models:
            return self._detect_spacy(text, entity_types, lang)
        elif lang == 'mixed':
            return self._detect_mixed(text, entity_types)
        else:
            return self._detect_regex_only(text, entity_types)
    
    def _detect_language(self, text: str) -> str:
        """
        Fast language detection based on character analysis.
        
        Returns: 'ar', 'fr', 'en', or 'mixed'
        """
        # Count character types
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
        latin_chars = len(re.findall(r'[a-zA-ZàâäçéèêëïîôùûüÿñæœÀÂÄÇÉÈÊËÏÎÔÙÛÜŸÑÆŒ]', text))
        
        total = arabic_chars + latin_chars
        if total == 0:
            return 'en'
        
        arabic_ratio = arabic_chars / total
        
        if arabic_ratio > 0.3:
            return 'ar'
        elif arabic_ratio > 0.05:
            return 'mixed'
        else:
            # Distinguish French from English
            french_indicators = ['le', 'la', 'les', 'de', 'des', 'un', 'une', 'dans', 'sur', 'pour']
            text_lower = text.lower()
            french_count = sum(1 for word in french_indicators if f' {word} ' in text_lower)
            return 'fr' if french_count >= 2 else 'en'
    
    def _detect_spacy(self, text: str, entity_types: List[str], lang: str) -> List[Tuple]:
        """Use SpaCy for French/English detection."""
        entities = []
        nlp = self.nlp_models[lang]
        doc = nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            entity_text = ent.text.strip()
            
            if ent.label_ in ['PERSON', 'PER'] and 'PERSON' in entity_types:
                if self._is_valid_person_name(entity_text):
                    entities.append((entity_text, 'PERSON', ent.start_char, ent.end_char))
            
            elif ent.label_ == 'ORG' and 'ORGANIZATION' in entity_types:
                entities.append((entity_text, 'ORGANIZATION', ent.start_char, ent.end_char))
            
            elif ent.label_ in ['GPE', 'LOC', 'FAC'] and 'LOCATION' in entity_types:
                if len(entity_text) > 2 and not re.search(r'\d', entity_text):
                    entities.append((entity_text, 'LOCATION', ent.start_char, ent.end_char))
        
        # Add regex patterns for structured data
        entities.extend(self._detect_patterns(text, entity_types))
        
        return self._deduplicate(entities)
    
    def _detect_arabic(self, text: str, entity_types: List[str]) -> List[Tuple]:
        """
        Arabic detection - deferred to LLM detector.
        
        Returns empty list as Arabic processing happens in LLM pipeline
        for better language understanding and cultural naming conventions.
        """
        return []
    
    def _detect_mixed(self, text: str, entity_types: List[str]) -> List[Tuple]:
        """Handle mixed-language documents by processing segments."""
        entities = []
        segments = self._split_by_language(text)
        
        for segment_text, lang, offset in segments:
            if lang == 'ar':
                segment_entities = self._detect_arabic(segment_text, entity_types)
            elif lang in self.nlp_models:
                segment_entities = self._detect_spacy(segment_text, entity_types, lang)
            else:
                segment_entities = self._detect_patterns(segment_text, entity_types)
            
            # Adjust positions by segment offset
            for ent_text, label, start, end in segment_entities:
                entities.append((ent_text, label, start + offset, end + offset))
        
        return self._deduplicate(entities)
    
    def _detect_patterns(self, text: str, entity_types: List[str]) -> List[Tuple]:
        """Detect structured data using regex (emails, phones, ages)."""
        entities = []
        
        # Email addresses
        if 'EMAIL' in entity_types:
            pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(pattern, text):
                entities.append((match.group(), 'EMAIL', match.start(), match.end()))
        
        # Phone numbers (international formats)
        if 'PHONE' in entity_types:
            patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}',
                r'\b0[1-9](?:[ .-]?\d{2}){4}\b',  # French/EU format
                r'[\u0660-\u0669]{10,}',  # Arabic numerals
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    phone = match.group()
                    # Require at least 8 digits
                    if len(re.findall(r'[\d\u0660-\u0669]', phone)) >= 8:
                        entities.append((phone, 'PHONE', match.start(), match.end()))
        
        # Ages (multilingual)
        if 'AGE' in entity_types:
            patterns = [
                r'\b(\d{1,2})\s+(?:ans?|years?|سنة|سنوات|عام)\b',
                r'\b(?:âgé(?:e)?|aged|عمره|عمرها)\s+(\d{1,2})\b',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append((match.group(), 'AGE', match.start(), match.end()))
        
        return entities
    
    def _detect_regex_only(self, text: str, entity_types: List[str]) -> List[Tuple]:
        """Fallback when no SpaCy models available - regex only."""
        entities = []
        
        # Basic name pattern (First Last format)
        if 'PERSON' in entity_types:
            pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            for match in re.finditer(pattern, text):
                name = match.group()
                if self._is_valid_person_name(name):
                    entities.append((name, 'PERSON', match.start(), match.end()))
        
        entities.extend(self._detect_patterns(text, entity_types))
        return self._deduplicate(entities)
    
    def _split_by_language(self, text: str) -> List[Tuple[str, str, int]]:
        """Split mixed-language text into language segments."""
        segments = []
        current_chars = []
        current_lang = None
        start_pos = 0
        
        for i, char in enumerate(text):
            # Detect character language
            if '\u0600' <= char <= '\u06FF':
                char_lang = 'ar'
            elif char.isalpha():
                char_lang = 'en'
            else:
                char_lang = None  # Neutral (space, punctuation)
            
            # Handle language transitions
            if char_lang is None:
                current_chars.append(char)
            elif char_lang == current_lang or current_lang is None:
                current_lang = char_lang
                current_chars.append(char)
            else:
                # Language switch detected
                if current_chars:
                    segments.append((''.join(current_chars), current_lang, start_pos))
                    start_pos = i
                current_chars = [char]
                current_lang = char_lang
        
        # Add final segment
        if current_chars:
            segments.append((''.join(current_chars), current_lang, start_pos))
        
        return segments
    
    def _is_valid_person_name(self, text: str) -> bool:
        """Validate if text looks like a person name."""
        text = text.strip()
        
        # Basic validation
        if len(text) < 2 or len(text) > 50 or re.search(r'\d', text):
            return False
        
        # Filter out organization keywords
        org_patterns = [
            r'\b(company|corp|ltd|inc|sa|sarl|sas|entreprise)\b',
            r'\b(university|université|school|école)\b',
            r'^[A-Z]{3,}$',  # All caps acronyms
        ]
        
        for pattern in org_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    def _deduplicate(self, entities: List[Tuple]) -> List[Tuple]:
        """Remove overlapping entities, keeping the longest/most specific."""
        if not entities:
            return []
        
        # Sort by position, then by length (descending)
        sorted_entities = sorted(entities, key=lambda x: (x[2], -len(x[0])))
        
        result = []
        for entity in sorted_entities:
            text, label, start, end = entity
            
            # Check for overlap with existing entities
            overlap = False
            for existing_text, existing_label, existing_start, existing_end in result:
                if not (end <= existing_start or start >= existing_end):
                    # Overlap detected - keep longer entity
                    if len(text) > len(existing_text):
                        result.remove((existing_text, existing_label, existing_start, existing_end))
                    else:
                        overlap = True
                    break
            
            if not overlap:
                result.append(entity)
        
        return result