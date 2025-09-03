import spacy
import re

class SpacyDetector:
    def __init__(self):
        try:
            # Try French model first, then English
            try:
                self.nlp = spacy.load("fr_core_news_sm")
                print("✅ Loaded French spaCy model")
            except OSError:
                self.nlp = spacy.load("en_core_web_sm")
                print("✅ Loaded English spaCy model")
            self.use_spacy = True
        except OSError:
            print("⚠️ No spaCy models found. Using regex fallback.")
            self.use_spacy = False
    
    def _is_valid_person_name(self, text: str) -> bool:
        """Enhanced validation for person names"""
        text = text.strip()
        
        # Skip if too short or too long
        if len(text) < 2 or len(text) > 50:
            return False
        
        # Skip if contains numbers
        if re.search(r'\d', text):
            return False
        
        # Skip common non-name patterns (French and English)
        non_name_patterns = [
            # Business/organization terms
            r'\b(entreprise|company|corp|ltd|inc|sa|sarl|sas)\b',
            r'\b(pour|for|et|and|ou|or|le|la|les|the|de|du|des|of)\b',
            r'\b(intelligence|artificielle|artificial|technology|tech)\b',
            r'\b(chef|manager|director|president|ceo|cto|cfo)\b',
            r'\b(site|web|website|internet|email|mail)\b',
            r'\b(technopark|parc|park|centre|center|bureau|office)\b',
            r'\b(casablanca|rabat|morocco|maroc|france|paris)\b',
            r'\b(adresse|address|rue|street|avenue|boulevard)\b',
            r'\b(université|university|école|school|institut)\b',
            r'\b(stage|internship|convention|contrat|contract)\b',
            r'\b(projet|project|développement|development)\b',
            
            # All caps (likely acronyms or organizations)
            r'^[A-Z]{3,}$',
        ]
        
        text_lower = text.lower()
        for pattern in non_name_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-ZàâäçéèêëïîôùûüÿñæœÀÂÄÇÉÈÊËÏÎÔÙÛÜŸÑÆŒ]', text):
            return False
        
        # For person names, expect typical name patterns
        words = text.split()
        if len(words) == 1:
            # Single word - must be at least 3 chars and look like a name
            return len(words[0]) >= 3 and words[0][0].isupper()
        elif len(words) == 2:
            # Two words - both should start with uppercase (typical first+last name)
            return all(word[0].isupper() and len(word) >= 2 for word in words)
        elif len(words) >= 3:
            # Three or more words - be more selective
            return all(word[0].isupper() and len(word) >= 2 for word in words[:3])
        
        return True

    def detect(self, text: str):
        """Return list of detected entities (text, label, start, end)."""
        if self.use_spacy:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entity_text = ent.text.strip()
                
                # Filter person entities more carefully
                if ent.label_ in ['PERSON', 'PER']:
                    if self._is_valid_person_name(entity_text):
                        entities.append((entity_text, 'PERSON', ent.start_char, ent.end_char))
                elif ent.label_ in ['EMAIL']:
                    entities.append((entity_text, 'EMAIL', ent.start_char, ent.end_char))
                elif ent.label_ in ['ORG']:
                    # Organization names
                    entities.append((entity_text, 'ORGANIZATION', ent.start_char, ent.end_char))
            
            # Detect ages with regex
            age_pattern = r'\b(?:âgé(?:e)?\s+de\s+)?(\d{1,2})\s+ans?\b|\b(\d{1,2})\s+years?\s+old\b'
            for match in re.finditer(age_pattern, text, re.IGNORECASE):
                age_num = match.group(1) or match.group(2)
                if age_num and 16 <= int(age_num) <= 99:  # Reasonable age range
                    entities.append((match.group(), 'AGE', match.start(), match.end()))
            
            # Also detect standalone reasonable ages in context
            age_context_pattern = r'\b(1[6-9]|[2-6][0-9]|7[0-9]|8[0-9]|9[0-9])\s+(?:ans?|years?)\b'
            for match in re.finditer(age_context_pattern, text, re.IGNORECASE):
                # Check if already detected
                overlap = any(start <= match.start() < end or start < match.end() <= end 
                            for _, _, start, end in entities)
                if not overlap:
                    entities.append((match.group(), 'AGE', match.start(), match.end()))
            
            # Also detect emails with regex (spaCy often misses them)
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(email_pattern, text):
                # Check if already detected
                overlap = any(start <= match.start() < end or start < match.end() <= end 
                            for _, _, start, end in entities)
                if not overlap:
                    entities.append((match.group(), 'EMAIL', match.start(), match.end()))
            
            # Enhanced name detection - catch single names that spaCy might miss
            single_name_pattern = r'\b[A-Z][a-z]{2,}\b'
            common_names = {
                'albert', 'marie', 'jean', 'pierre', 'paul', 'michel', 'robert', 'bernard', 'jacques', 'louis',
                'john', 'mary', 'james', 'patricia', 'michael', 'linda', 'william', 'elizabeth', 'david', 'barbara',
                'richard', 'susan', 'joseph', 'jessica', 'thomas', 'sarah', 'charles', 'karen', 'christopher', 'nancy',
                'daniel', 'lisa', 'matthew', 'betty', 'anthony', 'helen', 'mark', 'sandra', 'donald', 'donna',
                'steven', 'carol', 'paul', 'ruth', 'andrew', 'sharon', 'joshua', 'michelle', 'kenneth', 'laura',
                'kevin', 'sarah', 'brian', 'kimberly', 'george', 'deborah', 'edward', 'dorothy', 'ronald', 'lisa',
                'tim', 'nancy', 'jason', 'karen', 'jeffrey', 'betty', 'ryan', 'helen', 'jacob', 'sandra'
            }
            
            for match in re.finditer(single_name_pattern, text):
                candidate = match.group()
                # Check if already detected
                overlap = any(start <= match.start() < end or start < match.end() <= end 
                            for _, _, start, end in entities)
                if not overlap and candidate.lower() in common_names and self._is_valid_person_name(candidate):
                    entities.append((candidate, 'PERSON', match.start(), match.end()))
            
            return entities
        else:
            # Regex fallback - more conservative
            entities = []
            
            # Look for email addresses first
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            for match in re.finditer(email_pattern, text):
                entities.append((match.group(), 'EMAIL', match.start(), match.end()))
            
            # Conservative name detection - only clear first+last name patterns
            name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            for match in re.finditer(name_pattern, text):
                candidate = match.group()
                if self._is_valid_person_name(candidate):
                    entities.append((candidate, 'PERSON', match.start(), match.end()))
            
            # Age detection
            age_pattern = r'\b(?:âgé(?:e)?\s+de\s+)?(\d{1,2})\s+ans?\b|\b(\d{1,2})\s+years?\s+old\b'
            for match in re.finditer(age_pattern, text, re.IGNORECASE):
                age_num = match.group(1) or match.group(2)
                if age_num and 16 <= int(age_num) <= 99:
                    entities.append((match.group(), 'AGE', match.start(), match.end()))
            
            return entities
