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

    def anonymize(self, text: str):
        entities = self.detector.detect(text)
        return self.replacer.replace(text, entities)
