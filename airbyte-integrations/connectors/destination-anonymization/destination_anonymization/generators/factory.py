import logging
from typing import Any, Dict

from .base import BaseGenerator
from .masking import EmailMaskingGenerator, PhoneMaskingGenerator, SSNMaskingGenerator
from .synthetic import FakeNameGenerator, FakeAddressGenerator, FakeDateGenerator
from .numeric import NumericShiftGenerator
from .categorical import CategoricalMapGenerator
from .primary_key import PrimaryKeyGenerator, ForeignKeyGenerator
from .composite import CompositeGenerator, LinkedGenerator

logger = logging.getLogger("airbyte")


class GeneratorFactory:
    """
    Factory class for creating and managing anonymization generators.
    
    Provides a centralized way to create generators based on configuration
    and maintains generator instances for reuse.
    """
    
    def __init__(self, seed: str = "default"):
        """
        Initialize the generator factory.
        
        Args:
            seed: Default seed for generator consistency
        """
        self.seed = seed
        self._generators = {}
        
        self._generator_types = {
            "mask_email": EmailMaskingGenerator,
            "mask_phone": PhoneMaskingGenerator,
            "mask_ssn": SSNMaskingGenerator,
            "fake_name": FakeNameGenerator,
            "fake_address": FakeAddressGenerator,
            "fake_date": FakeDateGenerator,
            "numeric_shift": NumericShiftGenerator,
            "categorical_map": CategoricalMapGenerator,
            "primary_key": PrimaryKeyGenerator,
            "foreign_key": ForeignKeyGenerator,
            "composite": CompositeGenerator,
            "linked": LinkedGenerator,
        }
    
    def get_generator(
        self, 
        stream_name: str, 
        column_name: str, 
        column_config: Dict[str, Any]
    ) -> BaseGenerator:
        """
        Get or create a generator for the specified column.
        
        Args:
            stream_name: Name of the stream
            column_name: Name of the column
            column_config: Column configuration
            
        Returns:
            Generator instance
            
        Raises:
            ValueError: If generator type is not supported
        """
        generator_type = column_config.get("generator_type")
        generator_config = column_config.get("generator_config", {})
        
        generator_key = f"{stream_name}.{column_name}.{generator_type}"
        
        if generator_key in self._generators:
            return self._generators[generator_key]
        
        if generator_type not in self._generator_types:
            raise ValueError(f"Unsupported generator type: {generator_type}")
        
        generator_class = self._generator_types[generator_type]
        generator = generator_class(seed=self.seed, **generator_config)
        
        self._generators[generator_key] = generator
        
        logger.debug(f"Created generator {generator_type} for {stream_name}.{column_name}")
        
        return generator
    
    def register_generator_type(self, name: str, generator_class: type):
        """
        Register a new generator type.
        
        Args:
            name: Name of the generator type
            generator_class: Generator class to register
        """
        if not issubclass(generator_class, BaseGenerator):
            raise ValueError("Generator class must inherit from BaseGenerator")
        
        self._generator_types[name] = generator_class
        logger.info(f"Registered generator type: {name}")
    
    def get_available_types(self) -> list:
        """
        Get list of available generator types.
        
        Returns:
            List of generator type names
        """
        return list(self._generator_types.keys())
    
    def clear_cache(self):
        """Clear the generator cache."""
        self._generators.clear()
        logger.debug("Generator cache cleared")
