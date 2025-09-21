from detectors.spacy_detector import SpacyDetector
from detectors.llm_detector import LLMDetector
from replacers.faker_replacer import FakerReplacer

class AnonymizerPipeline:
    def __init__(self, detector="spacy", replacer=None):
        if detector == "spacy":
            self.detector = SpacyDetector()
        elif detector == "llm":
            self.detector = LLMDetector()
        else:
            raise ValueError("Unknown detector type")

        self.replacer = replacer or FakerReplacer()

    def anonymize(self, text: str, entity_types=None):
        # Clear previous replacements for fresh start
        self.replacer.replacements.clear()
        self.replacer.entity_types.clear()
        
        # Pass entity_types to both LLM and SpaCy detectors
        if hasattr(self.detector, 'detect') and isinstance(self.detector, LLMDetector):
            entities = self.detector.detect(text, entity_types)
        else:
            # SpaCy detector also supports entity_types now
            entities = self.detector.detect(text, entity_types)
        
        # Get anonymized text
        anonymized_text = self.replacer.replace(text, entities)
        
        # Return dictionary format for consistency
        return {
            'anonymized_text': anonymized_text,
            'replacement_mapping': self.replacer.replacements.copy(),
            'entity_info': self.replacer.entity_types.copy(),
            'success': True
        }
