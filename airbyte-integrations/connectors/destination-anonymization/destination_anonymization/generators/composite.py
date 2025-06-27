import logging
from typing import Any, Dict, List

from .base import BaseGenerator
from .factory import GeneratorFactory

logger = logging.getLogger("airbyte")


class CompositeGenerator(BaseGenerator):
    """
    Composite generator that applies multiple transformations to a single data element.
    
    Allows chaining multiple generators together to create complex anonymization
    patterns, such as generating a fake name and then applying masking to it.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        self.generator_factory = GeneratorFactory(seed)
        self._sub_generators: List[BaseGenerator] = []
        self._initialize_sub_generators()
    
    def _initialize_sub_generators(self):
        """Initialize the sub-generators based on configuration."""
        transformations = self.config.get('transformations', [])
        
        for i, transform_config in enumerate(transformations):
            try:
                generator_type = transform_config.get('generator_type')
                generator_config = transform_config.get('generator_config', {})
                
                if not generator_type:
                    logger.warning(f"Transformation {i} missing generator_type")
                    continue
                
                column_config = {
                    'generator_type': generator_type,
                    'generator_config': generator_config
                }
                
                generator = self.generator_factory.get_generator(
                    f"composite_{i}",
                    f"transform_{i}",
                    column_config
                )
                
                self._sub_generators.append(generator)
                
            except Exception as e:
                logger.error(f"Error initializing sub-generator {i}: {str(e)}")
    
    def generate(self, value: Any) -> Any:
        """
        Apply all configured transformations in sequence.
        
        Args:
            value: Original value to transform
            
        Returns:
            Value after all transformations have been applied
        """
        if not self._sub_generators:
            logger.warning("No sub-generators configured for composite generator")
            return value
        
        current_value = value
        
        for i, generator in enumerate(self._sub_generators):
            try:
                current_value = generator.generate(current_value)
                
                logger.debug(f"Composite step {i}: {value} -> {current_value}")
                
            except Exception as e:
                logger.error(f"Error in composite transformation step {i}: {str(e)}")
                continue
        
        return current_value
    
    def add_transformation(self, generator_type: str, generator_config: Dict[str, Any] = None):
        """
        Add a new transformation to the composite generator.
        
        Args:
            generator_type: Type of generator to add
            generator_config: Configuration for the generator
        """
        if generator_config is None:
            generator_config = {}
        
        try:
            column_config = {
                'generator_type': generator_type,
                'generator_config': generator_config
            }
            
            generator = self.generator_factory.get_generator(
                f"composite_{len(self._sub_generators)}",
                f"transform_{len(self._sub_generators)}",
                column_config
            )
            
            self._sub_generators.append(generator)
            logger.info(f"Added transformation: {generator_type}")
            
        except Exception as e:
            logger.error(f"Error adding transformation {generator_type}: {str(e)}")
            raise
    
    def remove_transformation(self, index: int):
        """
        Remove a transformation by index.
        
        Args:
            index: Index of the transformation to remove
        """
        if 0 <= index < len(self._sub_generators):
            removed = self._sub_generators.pop(index)
            logger.info(f"Removed transformation at index {index}: {removed.__class__.__name__}")
        else:
            raise IndexError(f"Invalid transformation index: {index}")
    
    def get_transformation_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all configured transformations.
        
        Returns:
            List of transformation information dictionaries
        """
        return [
            {
                'index': i,
                'type': generator.__class__.__name__,
                'config': generator.config if hasattr(generator, 'config') else {}
            }
            for i, generator in enumerate(self._sub_generators)
        ]
    
    def validate_input(self, value: Any) -> bool:
        """
        Validate input against all sub-generators.
        
        Args:
            value: Value to validate
            
        Returns:
            True if all sub-generators can handle the input
        """
        if not self._sub_generators:
            return True
        
        return self._sub_generators[0].validate_input(value)


class LinkedGenerator(BaseGenerator):
    """
    Generator that links transformations between related columns.
    
    Ensures consistency between related fields like first_name and last_name,
    or address components that should belong to the same person/entity.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        self.generator_factory = GeneratorFactory(seed)
        self._linked_generators: Dict[str, BaseGenerator] = {}
        self._link_mappings: Dict[str, Dict[str, Any]] = {}
        self._initialize_linked_generators()
    
    def _initialize_linked_generators(self):
        """Initialize generators for each linked field."""
        linked_fields = self.config.get('linked_fields', {})
        
        for field_name, field_config in linked_fields.items():
            try:
                generator_type = field_config.get('generator_type')
                generator_config = field_config.get('generator_config', {})
                
                if not generator_type:
                    logger.warning(f"Linked field '{field_name}' missing generator_type")
                    continue
                
                column_config = {
                    'generator_type': generator_type,
                    'generator_config': generator_config
                }
                
                generator = self.generator_factory.get_generator(
                    f"linked_{field_name}",
                    field_name,
                    column_config
                )
                
                self._linked_generators[field_name] = generator
                self._link_mappings[field_name] = {}
                
            except Exception as e:
                logger.error(f"Error initializing linked generator for '{field_name}': {str(e)}")
    
    def generate(self, value: Any) -> Dict[str, Any]:
        """
        Generate linked values for all configured fields.
        
        Args:
            value: Original value (used as consistency key)
            
        Returns:
            Dictionary with generated values for all linked fields
        """
        if not self._linked_generators:
            logger.warning("No linked generators configured")
            return {}
        
        consistency_key = str(value)
        
        if consistency_key in self._link_mappings.get(list(self._linked_generators.keys())[0], {}):
            result = {}
            for field_name in self._linked_generators.keys():
                result[field_name] = self._link_mappings[field_name].get(consistency_key)
            return result
        
        result = {}
        
        base_seed = f"{self.seed}:{consistency_key}"
        
        for field_name, generator in self._linked_generators.items():
            try:
                field_input = f"{base_seed}:{field_name}"
                
                generated_value = generator.generate(field_input)
                
                self._link_mappings[field_name][consistency_key] = generated_value
                result[field_name] = generated_value
                
            except Exception as e:
                logger.error(f"Error generating linked value for '{field_name}': {str(e)}")
                result[field_name] = None
        
        return result
    
    def generate_single_field(self, value: Any, field_name: str) -> Any:
        """
        Generate a value for a single linked field.
        
        Args:
            value: Original value (used as consistency key)
            field_name: Name of the field to generate
            
        Returns:
            Generated value for the specified field
        """
        if field_name not in self._linked_generators:
            raise ValueError(f"Unknown linked field: {field_name}")
        
        consistency_key = str(value)
        
        if consistency_key in self._link_mappings[field_name]:
            return self._link_mappings[field_name][consistency_key]
        
        generator = self._linked_generators[field_name]
        field_input = f"{self.seed}:{consistency_key}:{field_name}"
        
        generated_value = generator.generate(field_input)
        
        self._link_mappings[field_name][consistency_key] = generated_value
        
        return generated_value
    
    def get_linked_fields(self) -> List[str]:
        """
        Get list of configured linked fields.
        
        Returns:
            List of linked field names
        """
        return list(self._linked_generators.keys())
    
    def get_link_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about linked value generation.
        
        Returns:
            Dictionary with link statistics
        """
        stats = {
            'linked_fields': list(self._linked_generators.keys()),
            'total_links': 0,
            'field_stats': {}
        }
        
        for field_name, mappings in self._link_mappings.items():
            field_count = len(mappings)
            stats['field_stats'][field_name] = field_count
            stats['total_links'] += field_count
        
        return stats
    
    def clear_link_cache(self, field_name: str = None):
        """
        Clear cached linked values.
        
        Args:
            field_name: Specific field to clear, or None to clear all
        """
        if field_name:
            if field_name in self._link_mappings:
                self._link_mappings[field_name].clear()
                logger.info(f"Cleared link cache for field: {field_name}")
        else:
            for mappings in self._link_mappings.values():
                mappings.clear()
            logger.info("Cleared all link caches")
