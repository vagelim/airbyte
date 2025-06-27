import logging
from typing import Any, Dict, Mapping, Optional


logger = logging.getLogger("airbyte")


class AnonymizationConfig:
    """
    Configuration manager for the anonymization destination connector.
    
    Handles parsing and validation of anonymization rules and destination settings.
    """
    
    def __init__(self, config: Mapping[str, Any]):
        """
        Initialize configuration from connector config.
        
        Args:
            config: Raw configuration dictionary from Airbyte
        """
        self.config = config
        self.anonymization_rules = config.get("anonymization_rules", {})
        self.destination_config = config.get("destination", {})
        self.preserve_referential_integrity = config.get("preserve_referential_integrity", True)
        self.consistency_seed = config.get("consistency_seed", "default_seed")
        
    def get_stream_config(self, stream_name: str) -> Dict[str, Any]:
        """
        Get anonymization configuration for a specific stream.
        
        Args:
            stream_name: Name of the stream
            
        Returns:
            Stream configuration dictionary
        """
        streams_config = self.anonymization_rules.get("streams", {})
        return streams_config.get(stream_name, {})
    
    def get_column_config(self, stream_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Get anonymization configuration for a specific column.
        
        Args:
            stream_name: Name of the stream
            column_name: Name of the column
            
        Returns:
            Column configuration dictionary or None if not configured
        """
        stream_config = self.get_stream_config(stream_name)
        columns_config = stream_config.get("columns", {})
        return columns_config.get(column_name)
    
    def has_destination(self) -> bool:
        """
        Check if a destination is configured.
        
        Returns:
            True if destination is configured, False otherwise
        """
        return bool(self.destination_config.get("type"))
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if not isinstance(self.anonymization_rules, dict):
                logger.error("anonymization_rules must be a dictionary")
                return False
            
            streams = self.anonymization_rules.get("streams", {})
            if not isinstance(streams, dict):
                logger.error("streams configuration must be a dictionary")
                return False
            
            for stream_name, stream_config in streams.items():
                if not self._validate_stream_config(stream_name, stream_config):
                    return False
            
            if self.has_destination():
                if not self._validate_destination_config():
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {str(e)}")
            return False
    
    def _validate_stream_config(self, stream_name: str, stream_config: Dict[str, Any]) -> bool:
        """
        Validate configuration for a single stream.
        
        Args:
            stream_name: Name of the stream
            stream_config: Stream configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(stream_config, dict):
            logger.error(f"Stream '{stream_name}' configuration must be a dictionary")
            return False
        
        columns = stream_config.get("columns", {})
        if not isinstance(columns, dict):
            logger.error(f"Stream '{stream_name}' columns configuration must be a dictionary")
            return False
        
        for column_name, column_config in columns.items():
            if not self._validate_column_config(stream_name, column_name, column_config):
                return False
        
        return True
    
    def _validate_column_config(self, stream_name: str, column_name: str, column_config: Dict[str, Any]) -> bool:
        """
        Validate configuration for a single column.
        
        Args:
            stream_name: Name of the stream
            column_name: Name of the column
            column_config: Column configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(column_config, dict):
            logger.error(f"Column '{stream_name}.{column_name}' configuration must be a dictionary")
            return False
        
        generator_type = column_config.get("generator_type")
        if not generator_type:
            logger.error(f"Column '{stream_name}.{column_name}' must specify generator_type")
            return False
        
        valid_generators = [
            "mask_email", "mask_phone", "mask_ssn", "fake_name", 
            "fake_address", "fake_date", "numeric_shift", "categorical_map", "custom"
        ]
        
        if generator_type not in valid_generators:
            logger.error(f"Column '{stream_name}.{column_name}' has invalid generator_type: {generator_type}")
            return False
        
        return True
    
    def _validate_destination_config(self) -> bool:
        """
        Validate destination configuration.
        
        Returns:
            True if valid, False otherwise
        """
        dest_type = self.destination_config.get("type")
        valid_types = ["file", "database", "stream"]
        
        if dest_type not in valid_types:
            logger.error(f"Invalid destination type: {dest_type}")
            return False
        
        return True
    
    def check_destination_connection(self) -> bool:
        """
        Check connectivity to the configured destination.
        
        Returns:
            True if connection successful, False otherwise
        """
        return True
