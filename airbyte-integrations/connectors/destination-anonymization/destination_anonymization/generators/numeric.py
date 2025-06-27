import hashlib
import random
from typing import Any, Union

from .base import BaseGenerator


class NumericShiftGenerator(BaseGenerator):
    """
    Generator for transforming numeric data while preserving statistical properties.
    
    Applies consistent shifts, scaling, or noise to numeric values while
    maintaining the overall distribution characteristics.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        seed_hash = int(hashlib.md5(f"{seed}:numeric".encode()).hexdigest()[:8], 16)
        self.random = random.Random(seed_hash)
    
    def generate(self, value: Any) -> Union[int, float]:
        """
        Generate a transformed numeric value.
        
        Args:
            value: Original numeric value
            
        Returns:
            Transformed numeric value
        """
        if not isinstance(value, (int, float)) or value is None:
            return value
        
        transform_type = self.config.get('transform_type', 'shift')
        preserve_type = self.config.get('preserve_type', True)
        
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        value_random = random.Random(value_seed)
        
        if transform_type == 'shift':
            result = self._apply_shift(value, value_random)
        elif transform_type == 'scale':
            result = self._apply_scale(value, value_random)
        elif transform_type == 'noise':
            result = self._apply_noise(value, value_random)
        elif transform_type == 'range_map':
            result = self._apply_range_mapping(value, value_random)
        else:
            result = self._apply_shift(value, value_random)
        
        if preserve_type and isinstance(value, int):
            return int(round(result))
        else:
            return result
    
    def _apply_shift(self, value: Union[int, float], rng: random.Random) -> float:
        """
        Apply a consistent shift to the value.
        
        Args:
            value: Original value
            rng: Random number generator
            
        Returns:
            Shifted value
        """
        shift_range = self.config.get('shift_range', 100)
        shift_amount = rng.uniform(-shift_range, shift_range)
        return value + shift_amount
    
    def _apply_scale(self, value: Union[int, float], rng: random.Random) -> float:
        """
        Apply a consistent scaling factor to the value.
        
        Args:
            value: Original value
            rng: Random number generator
            
        Returns:
            Scaled value
        """
        scale_min = self.config.get('scale_min', 0.8)
        scale_max = self.config.get('scale_max', 1.2)
        scale_factor = rng.uniform(scale_min, scale_max)
        return value * scale_factor
    
    def _apply_noise(self, value: Union[int, float], rng: random.Random) -> float:
        """
        Apply random noise to the value.
        
        Args:
            value: Original value
            rng: Random number generator
            
        Returns:
            Value with added noise
        """
        noise_percentage = self.config.get('noise_percentage', 0.1)
        noise_amount = abs(value) * noise_percentage
        noise = rng.uniform(-noise_amount, noise_amount)
        return value + noise
    
    def _apply_range_mapping(self, value: Union[int, float], rng: random.Random) -> float:
        """
        Map the value to a different range while preserving relative position.
        
        Args:
            value: Original value
            rng: Random number generator
            
        Returns:
            Mapped value
        """
        original_min = self.config.get('original_min', 0)
        original_max = self.config.get('original_max', 100)
        target_min = self.config.get('target_min', 0)
        target_max = self.config.get('target_max', 100)
        
        if original_max == original_min:
            normalized = 0.5
        else:
            normalized = (value - original_min) / (original_max - original_min)
        
        mapped_value = target_min + normalized * (target_max - target_min)
        
        variation = self.config.get('mapping_variation', 0.05)
        if variation > 0:
            range_size = target_max - target_min
            noise = rng.uniform(-variation * range_size, variation * range_size)
            mapped_value += noise
        
        return mapped_value
    
    def validate_input(self, value: Any) -> bool:
        """
        Validate that the input value is numeric.
        
        Args:
            value: Value to validate
            
        Returns:
            True if numeric, False otherwise
        """
        return isinstance(value, (int, float)) and value is not None
