from faker import Faker
import random

class FakerReplacer:
    def __init__(self):
        self.faker = Faker(['en_US', 'fr_FR'])  # Support both English and French
        self.replacements = {}
        self.entity_types = {}  # Track entity types for each replacement
        
        # Predefined lists for more realistic replacements
        self.tech_companies = [
            "TechFlow Solutions", "DataSync Corp", "CloudVision Systems", "InnovateLab",
            "DigitalBridge Technologies", "NextGen Analytics", "SmartCode Industries",
            "FutureLogic Group", "CyberEdge Solutions", "ByteForge Systems",
            "Silicon Dynamics", "CodeCraft Technologies", "DataStream Solutions",
            "TechNova Industries", "IntelliCore Systems"
        ]
        
        self.consulting_firms = [
            "Strategic Insights Consulting", "Business Excellence Partners", "Growth Dynamics Group",
            "Innovation Consulting Solutions", "Strategic Development Associates", "Excellence Partners",
            "Business Transformation Group", "Strategic Vision Consulting", "Performance Solutions",
            "Enterprise Excellence Group"
        ]

    def _get_smart_replacement(self, text: str, entity_type: str) -> str:
        """Generate contextually appropriate replacements"""
        if entity_type == "PERSON":
            return self.faker.name()
        elif entity_type == "GPE":
            return self.faker.city()
        elif entity_type in ["ORG", "ORGANIZATION"]:
            # Smart organization replacement based on context
            text_lower = text.lower()
            if any(word in text_lower for word in ['tech', 'digital', 'software', 'data', 'ai', 'intelligence', 'holokia']):
                return random.choice(self.tech_companies)
            elif any(word in text_lower for word in ['consulting', 'conseil', 'advisory', 'partners']):
                return random.choice(self.consulting_firms)
            else:
                return self.faker.company()
        elif entity_type == "EMAIL":
            return self.faker.email()
        elif entity_type == "PHONE":
            return self.faker.phone_number()
        elif entity_type == "AGE":
            # Extract the number and generate a similar age
            import re
            age_match = re.search(r'\d+', text)
            if age_match:
                original_age = int(age_match.group())
                # Generate age within +/- 5 years, keeping it realistic
                new_age = max(18, min(65, original_age + random.randint(-5, 5)))
                
                # Try to preserve the format
                if 'ans' in text.lower():
                    return f"{new_age} ans"
                elif 'years old' in text.lower():
                    return f"{new_age} years old"
                else:
                    return str(new_age)
            return "25 ans"  # fallback
        else:
            return f"[REDACTED_{entity_type}]"

    def replace(self, text: str, entities: list):
        """Replace detected entities in text with fake values."""
        new_text = text
        for ent_text, ent_label, start, end in entities:
            if ent_text not in self.replacements:
                self.replacements[ent_text] = self._get_smart_replacement(ent_text, ent_label)
                # Store the entity type
                self.entity_types[ent_text] = ent_label

            new_text = new_text.replace(ent_text, self.replacements[ent_text])
        return new_text
    
    def get_replacements_with_types(self):
        """Get replacements with their entity types."""
        return [(original, replacement, self.entity_types.get(original, 'UNKNOWN')) 
                for original, replacement in self.replacements.items()]
