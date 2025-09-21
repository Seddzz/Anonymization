"""
Memory management for the anonymization agent
"""

class Memory:
    """Base memory class"""
    
    def __init__(self):
        self.short_term = {}
        self.long_term = {}
    
    def store_short_term(self, key, value):
        """Store information in short-term memory"""
        self.short_term[key] = value
    
    def store_long_term(self, key, value):
        """Store information in long-term memory"""
        self.long_term[key] = value
    
    def retrieve(self, key):
        """Retrieve information from memory"""
        return self.short_term.get(key) or self.long_term.get(key)
