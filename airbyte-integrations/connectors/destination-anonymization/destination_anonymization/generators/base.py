from abc import ABC, abstractmethod
from typing import Any


class BaseGenerator(ABC):
    """
    Abstract base class for all anonymization generators.
    
    All generators must implement the generate method to transform
    input values into anonymized outputs.
    """
    
    def __init__(self, seed: str = "default", **config):
        """
        Initialize the generator.
        
        Args:
            seed: Seed value for consistent generation
            **config: Additional configuration parameters
        """
        self.seed = seed
        self.config = config
    
    @abstractmethod
    def generate(self, value: Any) -> Any:
        """
        Generate an anonymized version of the input value.
        
        Args:
            value: Original value to anonymize
            
        Returns:
            Anonymized value
        """
        pass
    
    def validate_input(self, value: Any) -> bool:
        """
        Validate that the input value is appropriate for this generator.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_generator_info(self) -> dict:
        """
        Get information about this generator.
        
        Returns:
            Dictionary with generator metadata
        """
        return {
            "type": self.__class__.__name__,
            "seed": self.seed,
            "config": self.config
        }
