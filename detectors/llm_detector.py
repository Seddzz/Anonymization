# detectors/llm_detector.py
import subprocess
import json
import re

class LLMDetector:
    def __init__(self, model="mistral"):
        self.model = model

    def detect(self, text: str):
        """
        Detect sensitive entities using Mistral via Ollama.
        Returns a list of tuples: (entity_text, entity_label, start, end)
        """
        # Construct a more specific prompt for Mistral
        prompt = f"""You are an expert at identifying sensitive personal information. Analyze the following text and identify ONLY real sensitive entities.

ONLY detect these types:
- PERSON: Real person names (first + last name)
- EMAIL: Email addresses
- ORGANIZATION: Company/organization names
- AGE: Age information

Return ONLY a valid JSON array. Each object must have: text, label, start, end

Example format:
[{{"text": "John Smith", "label": "PERSON", "start": 0, "end": 10}}]

Text to analyze:
{text}

JSON response:"""

        try:
            # Run Ollama subprocess with timeout
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=30,
                encoding="utf-8",
                errors="ignore"
            )

            if result.returncode != 0:
                print(f"LLM detector failed, falling back to regex: {result.stderr}")
                return self._fallback_detection(text)

            output = result.stdout.strip()
            print(f"LLM raw output: {output[:200]}...")  # Debug output
            
            # Clean up the output - remove any text before/after JSON
            json_start = output.find('[')
            json_end = output.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                print("No JSON array found in LLM output, using fallback")
                return self._fallback_detection(text)
            
            json_str = output[json_start:json_end]
            
            try:
                entities_data = json.loads(json_str)
                entities = []
                
                for entity in entities_data:
                    if isinstance(entity, dict) and all(key in entity for key in ['text', 'label', 'start', 'end']):
                        # Validate the entity
                        entity_text = str(entity['text']).strip()
                        entity_label = str(entity['label']).strip()
                        
                        # Skip invalid entries
                        if len(entity_text) < 2 or entity_label in ['UNKNOWN', 'text', 'label', 'start', 'end']:
                            continue
                        
                        # Additional validation
                        if self._is_valid_entity(entity_text, entity_label):
                            entities.append((entity_text, entity_label, entity['start'], entity['end']))
                
                if entities:
                    return entities
                else:
                    print("No valid entities found in LLM output, using fallback")
                    return self._fallback_detection(text)
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}, using fallback")
                return self._fallback_detection(text)

        except subprocess.TimeoutExpired:
            print("LLM detector timed out, using fallback")
            return self._fallback_detection(text)
        except Exception as e:
            print(f"LLM detector error: {e}, using fallback")
            return self._fallback_detection(text)

    def _is_valid_entity(self, text: str, label: str) -> bool:
        """Validate if the detected entity makes sense"""
        text = text.strip()
        
        if label == 'PERSON':
            # Must look like a real name
            if len(text.split()) < 2:
                return False
            return bool(re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', text))
        elif label == 'EMAIL':
            return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text))
        elif label == 'ORGANIZATION':
            return len(text) > 2 and not text.lower() in ['the', 'and', 'for', 'with']
        elif label == 'AGE':
            return bool(re.search(r'\d+', text))
        
        return False

    def _fallback_detection(self, text: str):
        """Fallback to regex-based detection when LLM fails"""
        print("Using regex fallback detection")
        entities = []
        
        # Email detection
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append((match.group(), 'EMAIL', match.start(), match.end()))
        
        # Simple name detection (conservative)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        for match in re.finditer(name_pattern, text):
            candidate = match.group()
            # Basic validation
            if not any(word.lower() in candidate.lower() for word in ['the', 'and', 'for', 'with', 'this', 'that']):
                entities.append((candidate, 'PERSON', match.start(), match.end()))
        
        return entities
