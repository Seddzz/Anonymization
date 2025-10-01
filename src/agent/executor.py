"""
Anonymizer Pipeline - orchestrates detection and replacement.
Supports multi-language detection (EN/FR/AR) with optional LLM fallback.
"""
from typing import Dict, List, Optional
from .tools.detectors.spacy_detector import SpacyDetector
from .tools.detectors.llm_detector import LLMDetector
from .tools.replacers.faker_replacer import FakerReplacer


class AnonymizerPipeline:
    """
    Main anonymization pipeline coordinating detection and replacement.
    
    Detector Options:
    - "spacy" (default): Fast multi-language detector (EN/FR/AR)
    - "llm": Slower but more flexible LLM-based detection
    - Or pass detector instance directly for reuse across requests
    """
    
    def __init__(self, detector="spacy"):
        # Initialize detector (support instance or string)
        if isinstance(detector, (SpacyDetector, LLMDetector)):
            self.detector = detector
            self.detector_type = type(detector).__name__
        elif detector == "spacy":
            self.detector = SpacyDetector()
            self.detector_type = "SpacyDetector"
        elif detector == "llm":
            self.detector = LLMDetector()
            self.detector_type = "LLMDetector"
        else:
            raise ValueError(f"Unknown detector type: {detector}")
        
        # Initialize replacer for generating fake data
        self.replacer = FakerReplacer()
    
    def anonymize(self, text: str, entity_types: Optional[List[str]] = None) -> Dict:
        """
        Anonymize text by detecting and replacing sensitive entities.
        
        Args:
            text: Input text to anonymize
            entity_types: List of entity types to detect (None = all types)
        
        Returns:
            dict with:
                - anonymized_text: Text with entities replaced
                - replacement_mapping: Dict of original -> fake mappings
                - entity_info: Dict of original -> entity type
                - success: Boolean indicating success/failure
                - error: Error message (if success=False)
        """
        # Clear previous replacements for fresh start
        self.replacer.replacements.clear()
        self.replacer.entity_types.clear()
        
        if isinstance(self.detector, LLMDetector):
            return self._anonymize_with_llm(text, entity_types)
        else:
            return self._anonymize_with_faker(text, entity_types)
    
    def _anonymize_with_llm(self, text: str, entity_types: Optional[List[str]]) -> Dict:
        """
        Anonymize using LLM detector (generates fakes inline).
        
        LLM detector returns entities with fake data already generated:
        [{'text': '...', 'label': '...', 'fake': '...'}, ...]
        """
        try:
            entities = self.detector.detect(text, entity_types)
            
            anonymized_text = text
            replacement_mapping = {}
            entity_info = {}
            
            # Replace entities with fake data
            for entity in entities:
                original = entity.get('text', '')
                fake = entity.get('fake', original)  # Fallback to original
                label = entity.get('label', 'UNKNOWN')
                
                anonymized_text = anonymized_text.replace(original, fake)
                replacement_mapping[original] = fake
                entity_info[original] = label
            
            return {
                'anonymized_text': anonymized_text,
                'replacement_mapping': replacement_mapping,
                'entity_info': entity_info,
                'success': True
            }
        
        except Exception as e:
            return {
                'anonymized_text': text,
                'replacement_mapping': {},
                'entity_info': {},
                'success': False,
                'error': str(e)
            }
    
    def _anonymize_with_faker(self, text: str, entity_types: Optional[List[str]]) -> Dict:
        """
        Anonymize using SpacyDetector + FakerReplacer.
        
        SpacyDetector returns entities with positions:
        [(text, label, start, end), ...]
        """
        try:
            # Detect entities
            entities = self.detector.detect(text, entity_types)
            
            # Replace entities with fake data
            anonymized_text = self.replacer.replace(text, entities)
            
            return {
                'anonymized_text': anonymized_text,
                'replacement_mapping': self.replacer.replacements.copy(),
                'entity_info': self.replacer.entity_types.copy(),
                'success': True
            }
        
        except Exception as e:
            return {
                'anonymized_text': text,
                'replacement_mapping': {},
                'entity_info': {},
                'success': False,
                'error': str(e)
            }