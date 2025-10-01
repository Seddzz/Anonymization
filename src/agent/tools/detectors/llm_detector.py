import json
import re
import ollama
from typing import List, Dict, Optional


class LLMDetector:
    """
    LLM-based entity detector using local Ollama models.
    
    Features:
    - Natural language understanding for complex contexts
    - Automatic fake data generation via FakerReplacer
    - Robust JSON parsing with multiple fallback strategies
    - Better for Arabic and ambiguous cases
    """
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.client = ollama.Client()
        self.faker_replacer = self._load_faker_replacer()
    
    def _load_faker_replacer(self):
        """Load FakerReplacer for generating fake data."""
        try:
            from ..replacers.faker_replacer import FakerReplacer
            return FakerReplacer()
        except ImportError:
            try:
                from src.agent.tools.replacers.faker_replacer import FakerReplacer
                return FakerReplacer()
            except ImportError:
                print("⚠️ FakerReplacer not available, entities will not have fake replacements")
                return None
    
    def detect(self, text: str, entity_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Detect entities in text using LLM.
        
        Args:
            text: Input text to analyze
            entity_types: List of entity types to detect (None = all)
        
        Returns:
            List of dicts: [{'text': '...', 'label': '...', 'fake': '...'}, ...]
        """
        if entity_types is None:
            entity_types = ["PERSON", "EMAIL", "ORGANIZATION", "AGE", "PHONE", "LOCATION"]
        
        prompt = self._build_prompt(text, entity_types)
        entities = self._attempt_detection(prompt, entity_types)
        
        # Generate fake replacements
        if entities and self.faker_replacer:
            self._add_fake_replacements(entities)
        
        return entities
    
    def _build_prompt(self, text: str, entity_types: List[str]) -> str:
        """Build the LLM prompt for entity extraction."""
        entity_types_str = ", ".join(entity_types)
        return (
            f"Extract all entities from the following text. "
            f"Return only a valid JSON array, where each item is an object with exactly two keys: "
            f"'text' (the entity value) and 'label' (one of: {entity_types_str}). "
            f"Do not include any explanations, comments, or extra objects. "
            f"If there are no entities, return an empty array []. "
            f"The output must be valid JSON and nothing else.\n"
            f"Text: {text}\nJSON:"
        )
    
    def _attempt_detection(self, prompt: str, entity_types: List[str], max_attempts: int = 2) -> List[Dict]:
        """
        Attempt LLM detection with retries and robust error handling.
        
        Args:
            prompt: The prompt to send to LLM
            entity_types: Valid entity types for filtering
            max_attempts: Number of retry attempts
        
        Returns:
            List of valid entities
        """
        for attempt in range(max_attempts):
            try:
                print(f"\n===== LLM Detection (Attempt {attempt + 1}/{max_attempts}) =====")
                print(f"Model: {self.model}")
                
                # Call Ollama API
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                output = response['message']['content'].strip()
                
                print(f"Raw output length: {len(output)} chars")
                
                if len(output) < 5:
                    print("⚠️ Output too short, retrying...")
                    continue
                
                # Parse JSON response
                entities = self._parse_json_response(output, entity_types)
                
                if entities:
                    print(f"✅ Successfully parsed {len(entities)} entities")
                    return entities
                else:
                    print("⚠️ No valid entities found, retrying...")
            
            except Exception as e:
                print(f"⚠️ Ollama API error: {e}")
                if attempt < max_attempts - 1:
                    continue
        
        print("❌ All detection attempts failed")
        return []
    
    def _parse_json_response(self, output: str, entity_types: List[str]) -> List[Dict]:
        """
        Parse JSON response with multiple fallback strategies.
        
        Args:
            output: Raw LLM output
            entity_types: Valid entity types for validation
        
        Returns:
            List of valid entities
        """
        # Extract JSON array from output
        json_start = output.find('[')
        json_end = output.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            return []
        
        json_str = output[json_start:json_end]
        
        # Try progressively aggressive parsing strategies
        for fix_level in range(3):
            try:
                if fix_level == 0:
                    # Try as-is
                    entities_data = json.loads(json_str)
                elif fix_level == 1:
                    # Basic fixes
                    fixed = self._fix_json_format(json_str)
                    entities_data = json.loads(fixed)
                else:
                    # Aggressive fixes
                    fixed = self._aggressive_json_fix(json_str)
                    entities_data = json.loads(fixed)
                
                # Filter and validate
                if isinstance(entities_data, list):
                    filtered = [
                        e for e in entities_data 
                        if isinstance(e, dict) and 'text' in e and 'label' in e
                    ]
                    return self._extract_valid_entities(filtered, entity_types)
            
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        # Regex fallback - extract entity objects manually
        pattern = r'\{\s*"text"\s*:\s*"(.*?)"\s*,\s*"label"\s*:\s*"(.*?)"\s*\}'
        matches = re.findall(pattern, json_str)
        
        if matches:
            filtered = [{"text": m[0], "label": m[1]} for m in matches]
            print(f"📝 Regex fallback extracted {len(filtered)} entities")
            return self._extract_valid_entities(filtered, entity_types)
        
        return []
    
    def _fix_json_format(self, json_str: str) -> str:
        """Fix common JSON formatting issues."""
        # Remove comments
        json_str = re.sub(r'//.*', '', json_str)
        
        # Fix escaped quotes
        json_str = json_str.replace('\\"', '"').replace("\\'", "'")
        
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Fix unquoted keys
        for key in ['text', 'label', 'start', 'end']:
            json_str = json_str.replace(f'{key}:', f'"{key}":')
        
        return json_str
    
    def _aggressive_json_fix(self, json_str: str) -> str:
        """More aggressive JSON fixing for messy responses."""
        # Remove markdown code blocks
        fixed = re.sub(r'```json\s*', '', json_str)
        fixed = re.sub(r'```\s*', '', fixed)
        
        # Remove comments
        fixed = re.sub(r'//.*', '', fixed)
        
        # Trim to array boundaries
        fixed = re.sub(r'^[^[]*\[', '[', fixed)
        fixed = re.sub(r'\][^\]]*$', ']', fixed)
        
        # Fix trailing commas
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        # Fix missing commas between objects
        fixed = re.sub(r'}\s*{', '}, {', fixed)
        
        return fixed
    
    def _extract_valid_entities(self, parsed_entities: List[Dict], entity_types: List[str]) -> List[Dict]:
        """
        Extract and validate entities against allowed types.
        
        Args:
            parsed_entities: Raw parsed entities
            entity_types: Valid entity types
        
        Returns:
            List of validated entities
        """
        valid_labels = entity_types + ['ORG']  # ORG is alias for ORGANIZATION
        valid_entities = []
        
        for entity in parsed_entities:
            raw_label = entity.get("label", "").strip()
            text = entity.get("text", "").strip()
            
            # Handle multi-labels (e.g., "PERSON|AGE")
            labels = [lbl for lbl in raw_label.split("|") if lbl in valid_labels]
            
            if not labels:
                print(f"❌ Invalid label: {raw_label}")
                continue
            
            # Create entity for each valid label
            for label in labels:
                valid_entity = {"text": text, "label": label}
                
                # Preserve position info if present
                if "start" in entity:
                    valid_entity["start"] = entity["start"]
                if "end" in entity:
                    valid_entity["end"] = entity["end"]
                
                valid_entities.append(valid_entity)
                print(f"✅ Valid entity: {text} ({label})")
        
        if not valid_entities:
            print("⚠️ No valid entities found in LLM output")
        
        print(f"🎯 Total valid entities: {len(valid_entities)}")
        return valid_entities
    
    def _add_fake_replacements(self, entities: List[Dict]) -> None:
        """Generate fake replacements for detected entities (in-place)."""
        for entity in entities:
            original_text = entity.get('text', '')
            entity_label = entity.get('label', '')
            
            if original_text and entity_label:
                fake_replacement = self.faker_replacer._get_smart_replacement(
                    original_text, 
                    entity_label
                )
                entity['fake'] = fake_replacement
                print(f"🤖 Generated fake for '{original_text}' ({entity_label}): '{fake_replacement}'")