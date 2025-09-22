import subprocess
import json
import re
import ollama

class LLMDetector:
    def __init__(self, model="mistral"):
        self.model = model
        self.client = ollama.Client()  # persistent connection

    def detect(self, text, entity_types=None):
        if entity_types is None:
            entity_types = ["PERSON", "EMAIL", "ORGANIZATION", "AGE", "PHONE", "LOCATION"]

        entity_types_str = "|".join(entity_types)
        prompt = f"""Extract personal info from text. Return JSON array only.
Types: {entity_types_str}
Format: [{{"text":"found_text","label":"PERSON","start":0,"end":5}}]
Text: {text}
JSON:"""

        response = self.client.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
        output = response['message']['content'].strip()

        return self._parse_json_response(output, entity_types)


        try:
            # Strategy 1: Multiple attempts with shorter timeout
            entities = self._attempt_detection(prompt, text, entity_types)
            
            # Strategy 2: If empty results, try with fallback
            if not entities and self.fallback_enabled:
                print("🔄 LLM returned empty, trying SpaCy fallback...")
                return self._spacy_fallback(text)
            
            return entities

        except subprocess.TimeoutExpired:
            print("⚠️ Mistral timed out")
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                print(f"🔄 Retrying ({self.retry_count}/{self.max_retries})...")
                return self.detect(text, entity_types)
            elif self.fallback_enabled:
                print("🔄 All retries failed, using SpaCy fallback...")
                return self._spacy_fallback(text)
            return []
        except Exception as e:
            print(f"❌ Mistral error: {e}")
            if self.fallback_enabled:
                print("🔄 Error occurred, using SpaCy fallback...")
                return self._spacy_fallback(text)
            return []

    def _attempt_detection(self, prompt, text, entity_types):
        """Single detection attempt with improved error handling"""
        # Optimized timeout - balance between speed and reliability
    # Timeout removed: allow unlimited execution time

        for attempt in range(2):
            try:
                print(f"\n===== LLM DEBUG START (Attempt {attempt + 1}/2) =====")
                print(f"Prompt sent to Ollama (model: {self.model}):\n{prompt}\n---END PROMPT---")
                print(f"Command: ollama run {self.model}")
                print(f"Timeout: unlimited (no timeout)")
                result = subprocess.run(
                    ["ollama", "run", self.model],
                    input=prompt,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    errors="ignore"  # Ignore encoding errors
                )

                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")

                output = result.stdout.strip()
                print(f"Raw LLM output (full):\n{output}\n---END OUTPUT---")
                print(f"Raw LLM output length: {len(output)}")

                if len(output) < 5:
                    print("⚠️ Output too short, trying again...")
                    continue

                entities = self._parse_json_response(output, entity_types)
                if entities:
                    print(f"✅ Successfully parsed {len(entities)} entities - stopping attempts")
                    print("===== LLM DEBUG END =====\n")
                    return entities
                else:
                    print("⚠️ No entities found in response, trying again...")
                    print("===== LLM DEBUG END =====\n")
            except subprocess.TimeoutExpired as e:
                print(f"⚠️ Subprocess timeout (should not occur, timeout removed)")
                break
            except UnicodeDecodeError as e:
                print(f"⚠️ Unicode decode error: {e}, trying again...")
                break
            except Exception as e:
                print(f"⚠️ Subprocess error: {e}, trying again...")
                break
        return []

    def _spacy_fallback(self, text):
        """Fallback to SpaCy when LLM fails completely"""
        try:
            # Fixed import path for new agent-intelligent structure
            from .spacy_detector import SpacyDetector
            spacy_detector = SpacyDetector()
            print("✅ Using SpaCy as backup detector")
            return spacy_detector.detect(text)
        except ImportError as e:
            print(f"❌ SpaCy detector import failed: {e}")
            print("🔄 Attempting alternative import...")
            try:
                # Alternative import path
                from src.agent.tools.detectors.spacy_detector import SpacyDetector
                spacy_detector = SpacyDetector()
                print("✅ Using SpaCy as backup detector (alternative path)")
                return spacy_detector.detect(text)
            except Exception as e2:
                print(f"❌ All SpaCy import attempts failed: {e2}")
                return []
        except Exception as e:
            print(f"❌ SpaCy fallback execution failed: {e}")
            return []

    def _parse_json_response(self, output: str, entity_types):
        """Parse JSON response from Mistral with aggressive fixing"""
        # Find JSON array in output
        json_start = output.find('[')
        json_end = output.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            return []
        
        json_str = output[json_start:json_end]
        
        # Multiple fix attempts
        for fix_level in range(3):
            try:
                if fix_level == 0:
                    # Try as-is first
                    entities_data = json.loads(json_str)
                elif fix_level == 1:
                    # Try with basic fixes
                    fixed = self._fix_json_format(json_str)
                    entities_data = json.loads(fixed)
                else:
                    # Try with aggressive fixes
                    fixed = self._aggressive_json_fix(json_str)
                    entities_data = json.loads(fixed)
                
                # Success! Process entities
                entities = []
                print(f"🔍 Parsed JSON data: {entities_data}")
                
                for entity in entities_data:
                    print(f"🔍 Processing entity: {entity}")
                    if self._is_valid_entity_format(entity, entity_types):
                        # Handle missing start/end positions
                        start_pos = entity.get('start', 0)
                        end_pos = entity.get('end', len(entity['text']))
                        
                        # If positions are missing, try to find them in the original text
                        if start_pos == 0 and end_pos == len(entity['text']):
                            text_to_find = str(entity['text']).strip()
                            found_pos = output.find(text_to_find)
                            if found_pos != -1:
                                start_pos = found_pos
                                end_pos = found_pos + len(text_to_find)
                        
                        entities.append((
                            str(entity['text']).strip(), 
                            str(entity['label']).strip(), 
                            int(start_pos), 
                            int(end_pos)
                        ))
                        print(f"✅ Added entity: {entity['text']} ({entity['label']})")
                    else:
                        print(f"❌ Invalid entity format: {entity}")
                
                print(f"🎯 Total valid entities: {len(entities)}")
                return entities
                
            except (json.JSONDecodeError, ValueError, KeyError):
                continue  # Try next fix level
                
        return []  # All parsing attempts failed

    def _fix_json_format(self, json_str: str) -> str:
        """Fix common JSON formatting issues from LLM output"""
        # Fix double-escaped quotes first
        json_str = json_str.replace('\\\\"', '"')
        json_str = json_str.replace("\\\\'", "'")
        
        # Fix escaped quotes (common issue)
        json_str = json_str.replace('\\"', '"')
        json_str = json_str.replace("\\'", "'")
        
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Basic cleanup of common patterns
        json_str = json_str.replace('text:', '"text":')
        json_str = json_str.replace('label:', '"label":')
        json_str = json_str.replace('start:', '"start":')
        json_str = json_str.replace('end:', '"end":')
        
        return json_str
    
    def _aggressive_json_fix(self, json_str: str) -> str:
        """More aggressive JSON fixing for very messy responses"""
        # Remove markdown code blocks
        fixed = re.sub(r'```json\s*', '', json_str)
        fixed = re.sub(r'```\s*', '', fixed)
        
        # Remove extra text before/after
        fixed = re.sub(r'^[^[]*\[', '[', fixed)
        fixed = re.sub(r'\][^\]]*$', ']', fixed)
        
        # Fix broken quotes and escaping
        fixed = re.sub(r'(?<!\\)"([^"]*)"(?=\s*:)', r'"\1"', fixed)  # Fix keys
        fixed = re.sub(r':\s*"([^"]*)"(?=\s*[,}])', r': "\1"', fixed)  # Fix values
        
        # Fix trailing commas
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        # Fix missing commas
        fixed = re.sub(r'}\s*{', '}, {', fixed)
        
        return fixed

    def _is_valid_entity_format(self, entity, entity_types):
        """Check if entity has required format (lenient for missing positions)"""
        if not isinstance(entity, dict):
            print(f"❌ Not a dict: {type(entity)}")
            return False
        
        # Only require text and label (start/end are optional)
        required_fields = ['text', 'label']
        missing_fields = [field for field in required_fields if field not in entity]
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        # Check if label is valid (use provided entity_types)
        valid_labels = entity_types + ['ORG']  # Add ORG as alias for ORGANIZATION
        if entity['label'] not in valid_labels:
            print(f"❌ Invalid label: {entity['label']} (valid: {valid_labels})")
            return False
        
        # Check if text is not empty
        if not entity['text'] or len(entity['text'].strip()) < 1:
            print(f"❌ Empty text: {entity['text']}")
            return False
        
        print(f"✅ Valid entity: {entity['text']} ({entity['label']})")
        return True
