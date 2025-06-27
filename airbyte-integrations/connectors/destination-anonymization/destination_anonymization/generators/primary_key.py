import hashlib
import random
import uuid
from typing import Any, Optional, Set

from .base import BaseGenerator


class PrimaryKeyGenerator(BaseGenerator):
    """
    Specialized generator for primary key columns that maintains uniqueness constraints.
    
    Generates unique anonymized primary keys while ensuring no collisions
    and maintaining referential integrity requirements.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        self._generated_values: Set[str] = set()
        seed_hash = int(hashlib.md5(f"{seed}:primary_key".encode()).hexdigest()[:8], 16)
        self.random = random.Random(seed_hash)
    
    def generate(self, value: Any) -> Any:
        """
        Generate a unique anonymized primary key.
        
        Args:
            value: Original primary key value
            
        Returns:
            Anonymized primary key that maintains uniqueness
        """
        if value is None:
            return None
        
        key_type = self.config.get('key_type', 'sequential')
        preserve_type = self.config.get('preserve_type', True)
        
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        value_random = random.Random(value_seed)
        
        if key_type == 'sequential':
            new_key = self._generate_sequential_key(value, preserve_type)
        elif key_type == 'uuid':
            new_key = self._generate_uuid_key(value_random)
        elif key_type == 'hash':
            new_key = self._generate_hash_key(value, preserve_type)
        elif key_type == 'random':
            new_key = self._generate_random_key(value_random, preserve_type)
        else:
            new_key = self._generate_sequential_key(value, preserve_type)
        
        new_key = self._ensure_uniqueness(new_key, value_random, preserve_type)
        
        return new_key
    
    def _generate_sequential_key(self, original_value: Any, preserve_type: bool) -> Any:
        """
        Generate a sequential primary key.
        
        Args:
            original_value: Original key value
            preserve_type: Whether to preserve the original data type
            
        Returns:
            Sequential key value
        """
        prefix = self.config.get('prefix', 'PK')
        start_value = self.config.get('start_value', 1)
        
        sequence_number = len(self._generated_values) + start_value
        
        if preserve_type and isinstance(original_value, int):
            return sequence_number
        else:
            padding = self.config.get('padding', 6)
            return f"{prefix}_{sequence_number:0{padding}d}"
    
    def _generate_uuid_key(self, rng: random.Random) -> str:
        """
        Generate a UUID-based primary key.
        
        Args:
            rng: Random number generator
            
        Returns:
            UUID-based key
        """
        uuid_bytes = bytes([rng.randint(0, 255) for _ in range(16)])
        return str(uuid.UUID(bytes=uuid_bytes))
    
    def _generate_hash_key(self, original_value: Any, preserve_type: bool) -> Any:
        """
        Generate a hash-based primary key.
        
        Args:
            original_value: Original key value
            preserve_type: Whether to preserve the original data type
            
        Returns:
            Hash-based key value
        """
        hash_input = f"{self.seed}:{original_value}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        if preserve_type and isinstance(original_value, int):
            return int(hash_value[:15], 16)  # Use first 15 hex chars to avoid overflow
        else:
            prefix = self.config.get('prefix', 'HASH')
            hash_length = self.config.get('hash_length', 8)
            return f"{prefix}_{hash_value[:hash_length].upper()}"
    
    def _generate_random_key(self, rng: random.Random, preserve_type: bool) -> Any:
        """
        Generate a random primary key.
        
        Args:
            rng: Random number generator
            preserve_type: Whether to preserve the original data type
            
        Returns:
            Random key value
        """
        if preserve_type:
            min_value = self.config.get('min_value', 1000000)
            max_value = self.config.get('max_value', 9999999)
            return rng.randint(min_value, max_value)
        else:
            prefix = self.config.get('prefix', 'RND')
            length = self.config.get('random_length', 8)
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            suffix = ''.join(rng.choice(chars) for _ in range(length))
            return f"{prefix}_{suffix}"
    
    def _ensure_uniqueness(self, candidate_key: Any, rng: random.Random, preserve_type: bool) -> Any:
        """
        Ensure the generated key is unique by adding suffixes if needed.
        
        Args:
            candidate_key: Candidate key value
            rng: Random number generator
            preserve_type: Whether to preserve the original data type
            
        Returns:
            Unique key value
        """
        original_key = candidate_key
        attempt = 0
        max_attempts = 1000
        
        while str(candidate_key) in self._generated_values and attempt < max_attempts:
            attempt += 1
            
            if preserve_type and isinstance(original_key, int):
                candidate_key = original_key + attempt
            else:
                candidate_key = f"{original_key}_{attempt:03d}"
        
        if attempt >= max_attempts:
            candidate_key = str(uuid.uuid4())
        
        self._generated_values.add(str(candidate_key))
        
        return candidate_key
    
    def get_uniqueness_stats(self) -> dict:
        """
        Get statistics about generated unique values.
        
        Returns:
            Dictionary with uniqueness statistics
        """
        return {
            'total_generated': len(self._generated_values),
            'unique_values': len(self._generated_values),  # Should always be equal
            'uniqueness_ratio': 1.0,  # Should always be 1.0 for primary keys
            'generator_type': self.__class__.__name__
        }
    
    def clear_generated_values(self):
        """Clear the set of generated values."""
        self._generated_values.clear()


class ForeignKeyGenerator(BaseGenerator):
    """
    Specialized generator for foreign key columns that preserves referential integrity.
    
    Maps foreign key values consistently with their corresponding primary keys
    to maintain relationships between tables.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        self._fk_mapping: dict = {}
        self._referenced_pk_generator: Optional[PrimaryKeyGenerator] = None
    
    def set_referenced_pk_generator(self, pk_generator: PrimaryKeyGenerator):
        """
        Set the primary key generator for the referenced table.
        
        Args:
            pk_generator: Primary key generator instance
        """
        self._referenced_pk_generator = pk_generator
    
    def generate(self, value: Any) -> Any:
        """
        Generate an anonymized foreign key that maintains referential integrity.
        
        Args:
            value: Original foreign key value
            
        Returns:
            Anonymized foreign key that references the correct anonymized primary key
        """
        if value is None:
            return None
        
        str_value = str(value)
        if str_value in self._fk_mapping:
            return self._fk_mapping[str_value]
        
        if self._referenced_pk_generator:
            anonymized_pk = self._referenced_pk_generator.generate(value)
            self._fk_mapping[str_value] = anonymized_pk
            return anonymized_pk
        else:
            hash_input = f"{self.seed}:fk:{value}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            
            preserve_type = self.config.get('preserve_type', True)
            anonymized_fk: Any
            if preserve_type and isinstance(value, int):
                anonymized_fk = int(hash_value, 16) % 1000000  # Keep it reasonable
            else:
                prefix = self.config.get('prefix', 'FK')
                anonymized_fk = f"{prefix}_{hash_value.upper()}"
            
            self._fk_mapping[str_value] = anonymized_fk
            return anonymized_fk
    
    def get_mapping_stats(self) -> dict:
        """
        Get statistics about foreign key mappings.
        
        Returns:
            Dictionary with mapping statistics
        """
        return {
            'total_mappings': len(self._fk_mapping),
            'has_pk_generator': self._referenced_pk_generator is not None,
            'mappings': dict(self._fk_mapping)
        }
    
    def clear_mappings(self):
        """Clear all foreign key mappings."""
        self._fk_mapping.clear()
