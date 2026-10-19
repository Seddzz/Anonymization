from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
from transformers.utils import logging

from anonymizer.detect import Entity

LABEL_MAP = {
    "PER": "PERSON",
    "ORG": "ORGANIZATION",
    "LOC": "LOCATION",
    "MISC": "MISC",
}

class NerDetector:
    def __init__(self, model_name:str = "dslim/bert-base-NER", confidence_threshold: float = 0.5,):
        logging.set_verbosity_error()
        logging.disable_progress_bar()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.nlp = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            )
        self.confidence_threshold = confidence_threshold

    def detect(self, text: str) -> list[Entity]:
        if not text or not text.strip():
            return []
        results = self.nlp(text)
        entities = []

        for item in results:
            score = float(item["score"])
            if score < self.confidence_threshold:
                continue
            raw_group = item["entity_group"]
            label = LABEL_MAP.get(raw_group, raw_group)
            start = item["start"]
            end = item["end"]
            matched_text = text[start:end]

            entities.append(
                Entity(
                    label=label,
                    start=start,
                    end=end,
                    text=matched_text,
                    score=score,
                    source="ner"
                )
            )

        return entities