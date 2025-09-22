
from faker import Faker
import random
import re

class FakerReplacer:
    def __init__(self):
        self.default_locales = ['en_US', 'fr_FR']
        self.faker = Faker(self.default_locales)
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

    def _is_arabic(self, text: str) -> bool:
        # Detect if the text contains a significant amount of Arabic characters
        # Arabic Unicode range: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF, \uFB50-\uFDFF, \uFE70-\uFEFF
        arabic_chars = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text)
        return len(arabic_chars) > 10 or (len(arabic_chars) > 0 and len(arabic_chars) / max(1, len(text)) > 0.2)

    def _get_faker_for_text(self, text: str):
        if self._is_arabic(text):
            return Faker('ar')
        return Faker(self.default_locales)

    def _get_smart_replacement(self, text: str, entity_type: str) -> str:
        """Generate contextually appropriate replacements"""
        faker = self._get_faker_for_text(text)
        if entity_type == "PERSON":
            return faker.name()
        elif entity_type in ["GPE", "LOCATION"]:
            # Smart location replacement
            text_lower = text.lower()
            # Address/Street
            if any(word in text_lower for word in ['street', 'st.', 'avenue', 'road', 'boulevard', 'lane', 'drive', 'rue', 'avenue', 'blvd', 'rd', 'dr', 'str', 'شارع', 'طريق', 'avenue', 'avenue']):
                return faker.street_address()
            # Country
            elif any(word in text_lower for word in ['country', 'nation', 'دولة', 'بلد', 'republic', 'kingdom', 'emirate', 'state', 'province', 'country:', 'country -']):
                return faker.country()
            # City
            elif any(word in text_lower for word in ['city', 'ville', 'مدينة', 'town', 'capital', 'metropolis', 'urban', 'city:', 'city -']):
                return faker.city()
            # If the text looks like a postal code
            elif re.match(r'\b\d{5}(?:-\d{4})?\b', text):
                return faker.postcode()
            # Fallback: try city, then country
            else:
                # Try to avoid person names by checking if city looks like a person
                city = faker.city()
                # If city is a single word and looks like a name, use country instead
                if len(city.split()) == 1 and city[0].isupper() and city.isalpha():
                    return faker.country()
                return city
        elif entity_type in ["ORG", "ORGANIZATION"]:
            # Smart organization replacement based on context
            text_lower = text.lower()
            if any(word in text_lower for word in ['tech', 'digital', 'software', 'data', 'ai', 'intelligence', 'holokia']):
                return random.choice(self.tech_companies)
            elif any(word in text_lower for word in ['consulting', 'conseil', 'advisory', 'partners']):
                return random.choice(self.consulting_firms)
            else:
                return faker.company()
        elif entity_type == "EMAIL":
            return faker.email()
        elif entity_type == "PHONE":
            return faker.phone_number()
        elif entity_type == "AGE":
            # Extract the number and generate a similar age
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
