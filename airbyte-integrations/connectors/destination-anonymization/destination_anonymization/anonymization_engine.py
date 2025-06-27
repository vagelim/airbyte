import logging
from typing import Any, Dict, Optional

from airbyte_cdk.models import AirbyteMessage, AirbyteRecordMessage, ConfiguredAirbyteCatalog

from .config import AnonymizationConfig
from .generators import GeneratorFactory
from .state_manager import StateManager

logger = logging.getLogger("airbyte")


class AnonymizationEngine:
    """
    Core anonymization engine that processes Airbyte records and applies
    configured anonymization transforms while maintaining consistency.
    """
    
    def __init__(self, config: AnonymizationConfig):
        """
        Initialize the anonymization engine.
        
        Args:
            config: Anonymization configuration
        """
        self.config = config
        self.generator_factory = GeneratorFactory(config.consistency_seed)
        self.state_manager = StateManager(config.consistency_seed)
        
    def anonymize_record(
        self, 
        message: AirbyteMessage, 
        configured_catalog: ConfiguredAirbyteCatalog
    ) -> AirbyteMessage:
        """
        Anonymize a single record message.
        
        Args:
            message: Input Airbyte message
            configured_catalog: Configured catalog with stream information
            
        Returns:
            Anonymized Airbyte message
        """
        if not message.record:
            return message
            
        stream_name = message.record.stream
        record_data = message.record.data
        
        stream_config = self.config.get_stream_config(stream_name)
        if not stream_config or not stream_config.get("columns"):
            return message
        
        anonymized_data = self._anonymize_record_data(
            record_data, 
            stream_name, 
            stream_config
        )
        
        anonymized_record = AirbyteRecordMessage(
            stream=stream_name,
            data=anonymized_data,
            emitted_at=message.record.emitted_at,
            namespace=message.record.namespace
        )
        
        return AirbyteMessage(
            type=message.type,
            record=anonymized_record
        )
    
    def _anonymize_record_data(
        self, 
        data: Dict[str, Any], 
        stream_name: str, 
        stream_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Anonymize the data fields in a record.
        
        Args:
            data: Original record data
            stream_name: Name of the stream
            stream_config: Stream configuration
            
        Returns:
            Anonymized record data
        """
        anonymized_data = data.copy()
        columns_config = stream_config.get("columns", {})
        
        for column_name, column_config in columns_config.items():
            if column_name in data:
                original_value = data[column_name]
                
                if original_value is None:
                    continue
                
                try:
                    generator = self.generator_factory.get_generator(
                        stream_name,
                        column_name,
                        column_config
                    )
                    
                    anonymized_value = self._apply_consistent_transform(
                        original_value,
                        generator,
                        column_config.get("consistency_key")
                    )
                    
                    anonymized_data[column_name] = anonymized_value
                    
                except Exception as e:
                    logger.error(
                        f"Error anonymizing column {stream_name}.{column_name}: {str(e)}"
                    )
                    anonymized_data[column_name] = original_value
        
        return anonymized_data
    
    def _apply_consistent_transform(
        self, 
        original_value: Any, 
        generator: Any, 
        consistency_key: Optional[str]
    ) -> Any:
        """
        Apply transformation with consistency management.
        
        Args:
            original_value: Original value to transform
            generator: Generator instance to use
            consistency_key: Key for consistency mapping
            
        Returns:
            Transformed value
        """
        if consistency_key:
            cached_value = self.state_manager.get_cached_value(
                consistency_key, 
                original_value
            )
            
            if cached_value is not None:
                return cached_value
            
            transformed_value = generator.generate(original_value)
            self.state_manager.cache_value(
                consistency_key, 
                original_value, 
                transformed_value
            )
            
            return transformed_value
        else:
            return generator.generate(original_value)
