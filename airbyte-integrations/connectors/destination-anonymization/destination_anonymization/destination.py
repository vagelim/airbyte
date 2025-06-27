import json
import logging
from typing import Any, Dict, Iterable, Mapping

from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, ConfiguredAirbyteCatalog, Status, Type

from .anonymization_engine import AnonymizationEngine
from .config import AnonymizationConfig


logger = logging.getLogger("airbyte")


class DestinationAnonymization(Destination):
    """
    Airbyte destination connector for data anonymization.
    
    This connector receives data from any Airbyte source, applies configured
    anonymization transforms, and outputs anonymized data to a specified destination.
    """

    def write(
        self,
        config: Mapping[str, Any],
        configured_catalog: ConfiguredAirbyteCatalog,
        input_messages: Iterable[AirbyteMessage],
    ) -> Iterable[AirbyteMessage]:
        """
        Process input messages and apply anonymization transforms.
        
        Args:
            config: Connector configuration
            configured_catalog: Configured catalog with stream information
            input_messages: Stream of input messages to process
            
        Yields:
            Anonymized AirbyteMessage objects
        """
        try:
            anonymization_config = AnonymizationConfig(config)
            
            engine = AnonymizationEngine(anonymization_config)
            
            for message in input_messages:
                if message.type == Type.RECORD:
                    anonymized_message = engine.anonymize_record(message, configured_catalog)
                    yield anonymized_message
                elif message.type == Type.STATE:
                    yield message
                else:
                    yield message
                    
        except Exception as e:
            logger.error(f"Error during anonymization: {str(e)}")
            raise

    def check(self, logger: logging.Logger, config: Mapping[str, Any]) -> AirbyteConnectionStatus:
        """
        Check the connection and configuration validity.
        
        Args:
            logger: Logger instance
            config: Connector configuration
            
        Returns:
            Connection status indicating success or failure
        """
        try:
            anonymization_config = AnonymizationConfig(config)
            
            if not anonymization_config.validate():
                return AirbyteConnectionStatus(
                    status=Status.FAILED,
                    message="Invalid anonymization configuration. Please check your anonymization rules."
                )
            
            if anonymization_config.has_destination():
                destination_status = anonymization_config.check_destination_connection()
                if not destination_status:
                    return AirbyteConnectionStatus(
                        status=Status.FAILED,
                        message="Cannot connect to configured destination. Please verify destination settings."
                    )
            
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
            
        except Exception as e:
            return AirbyteConnectionStatus(
                status=Status.FAILED,
                message=f"Connection check failed: {str(e)}"
            )

    def spec(self, logger: logging.Logger) -> Dict[str, Any]:
        """
        Return the connector specification.
        
        Args:
            logger: Logger instance
            
        Returns:
            Connector specification dictionary
        """
        return {
            "documentationUrl": "https://docs.airbyte.com/integrations/destinations/anonymization",
            "connectionSpecification": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Anonymization Destination Spec",
                "type": "object",
                "required": ["anonymization_rules"],
                "properties": {
                    "anonymization_rules": {
                        "type": "object",
                        "title": "Anonymization Rules",
                        "description": "Configuration for anonymization transforms by stream and column",
                        "properties": {
                            "streams": {
                                "type": "object",
                                "title": "Stream Configurations",
                                "description": "Anonymization rules for each stream",
                                "patternProperties": {
                                    ".*": {
                                        "type": "object",
                                        "properties": {
                                            "columns": {
                                                "type": "object",
                                                "title": "Column Configurations",
                                                "description": "Anonymization rules for each column",
                                                "patternProperties": {
                                                    ".*": {
                                                        "type": "object",
                                                        "properties": {
                                                            "generator_type": {
                                                                "type": "string",
                                                                "enum": [
                                                                    "mask_email",
                                                                    "mask_phone",
                                                                    "mask_ssn",
                                                                    "fake_name",
                                                                    "fake_address",
                                                                    "fake_date",
                                                                    "numeric_shift",
                                                                    "categorical_map",
                                                                    "custom"
                                                                ],
                                                                "title": "Generator Type",
                                                                "description": "Type of anonymization generator to apply"
                                                            },
                                                            "generator_config": {
                                                                "type": "object",
                                                                "title": "Generator Configuration",
                                                                "description": "Configuration parameters for the generator"
                                                            },
                                                            "consistency_key": {
                                                                "type": "string",
                                                                "title": "Consistency Key",
                                                                "description": "Key for maintaining consistency across related values"
                                                            }
                                                        },
                                                        "required": ["generator_type"]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "destination": {
                        "type": "object",
                        "title": "Output Destination",
                        "description": "Configuration for where to send anonymized data",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["file", "database", "stream"],
                                "title": "Destination Type",
                                "description": "Type of destination for anonymized data"
                            },
                            "config": {
                                "type": "object",
                                "title": "Destination Configuration",
                                "description": "Configuration parameters for the destination"
                            }
                        }
                    },
                    "preserve_referential_integrity": {
                        "type": "boolean",
                        "title": "Preserve Referential Integrity",
                        "description": "Whether to maintain foreign key relationships",
                        "default": True
                    },
                    "consistency_seed": {
                        "type": "string",
                        "title": "Consistency Seed",
                        "description": "Seed value for consistent anonymization across runs"
                    }
                }
            }
        }
