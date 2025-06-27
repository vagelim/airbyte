import hashlib
import random
from typing import Any, Dict, List

from .base import BaseGenerator


class CategoricalMapGenerator(BaseGenerator):
    """
    Generator for replacing categorical values with consistent alternatives.
    
    Maps original categorical values to new values while maintaining
    consistency and optionally preserving distribution patterns.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        seed_hash = int(hashlib.md5(f"{seed}:categorical".encode()).hexdigest()[:8], 16)
        self.random = random.Random(seed_hash)
        
        self._value_mapping: Dict[str, str] = {}
        
        predefined_mapping = self.config.get('mapping', {})
        if predefined_mapping:
            self._value_mapping.update(predefined_mapping)
    
    def generate(self, value: Any) -> Any:
        """
        Generate a mapped categorical value.
        
        Args:
            value: Original categorical value
            
        Returns:
            Mapped categorical value
        """
        if value is None:
            return None
        
        str_value = str(value)
        
        if str_value in self._value_mapping:
            return self._value_mapping[str_value]
        
        mapping_type = self.config.get('mapping_type', 'random')
        
        if mapping_type == 'random':
            mapped_value = self._generate_random_mapping(str_value)
        elif mapping_type == 'sequential':
            mapped_value = self._generate_sequential_mapping(str_value)
        elif mapping_type == 'pattern':
            mapped_value = self._generate_pattern_mapping(str_value)
        elif mapping_type == 'dictionary':
            mapped_value = self._generate_dictionary_mapping(str_value)
        else:
            mapped_value = self._generate_random_mapping(str_value)
        
        self._value_mapping[str_value] = mapped_value
        
        return mapped_value
    
    def _generate_random_mapping(self, value: str) -> str:
        """
        Generate a random mapping for the value.
        
        Args:
            value: Original value
            
        Returns:
            Randomly generated mapped value
        """
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        value_random = random.Random(value_seed)
        
        available_values = self.config.get('available_values', [])
        
        if available_values:
            return value_random.choice(available_values)
        else:
            prefix = self.config.get('prefix', 'CAT')
            suffix_length = self.config.get('suffix_length', 4)
            
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            suffix = ''.join(value_random.choice(chars) for _ in range(suffix_length))
            
            return f"{prefix}_{suffix}"
    
    def _generate_sequential_mapping(self, value: str) -> str:
        """
        Generate a sequential mapping for the value.
        
        Args:
            value: Original value
            
        Returns:
            Sequentially generated mapped value
        """
        prefix = self.config.get('prefix', 'ITEM')
        
        sequence_number = len(self._value_mapping) + 1
        padding = self.config.get('padding', 3)
        
        return f"{prefix}_{sequence_number:0{padding}d}"
    
    def _generate_pattern_mapping(self, value: str) -> str:
        """
        Generate a mapping that follows a specific pattern.
        
        Args:
            value: Original value
            
        Returns:
            Pattern-based mapped value
        """
        pattern = self.config.get('pattern', 'TYPE_{hash}')
        
        value_hash = hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:6].upper()
        
        mapped_value = pattern.replace('{hash}', value_hash)
        mapped_value = mapped_value.replace('{original}', value)
        mapped_value = mapped_value.replace('{length}', str(len(value)))
        
        return mapped_value
    
    def _generate_dictionary_mapping(self, value: str) -> str:
        """
        Generate mapping using a predefined dictionary approach.
        
        Args:
            value: Original value
            
        Returns:
            Dictionary-based mapped value
        """
        categories = self.config.get('categories', {})
        default_category = self.config.get('default_category', 'OTHER')
        
        category = default_category
        for cat_name, cat_values in categories.items():
            if value.lower() in [v.lower() for v in cat_values]:
                category = cat_name
                break
        
        if category in categories and categories[category]:
            value_seed = int(hashlib.md5(f"{self.seed}:{category}:{value}".encode()).hexdigest()[:8], 16)
            value_random = random.Random(value_seed)
            return value_random.choice(categories[category])
        else:
            return f"{category}_{len(self._value_mapping) + 1:03d}"
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current mappings.
        
        Returns:
            Dictionary with mapping statistics
        """
        return {
            'total_mappings': len(self._value_mapping),
            'unique_values': len(set(self._value_mapping.values())),
            'mapping_ratio': len(set(self._value_mapping.values())) / len(self._value_mapping) if self._value_mapping else 0,
            'mappings': dict(self._value_mapping)
        }
    
    def clear_mappings(self):
        """Clear all cached mappings."""
        self._value_mapping.clear()
    
    def validate_input(self, value: Any) -> bool:
        """
        Validate that the input value is appropriate for categorical mapping.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        return value is not None
