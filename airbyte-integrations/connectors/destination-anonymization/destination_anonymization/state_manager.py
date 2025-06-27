import hashlib
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("airbyte")


class StateManager:
    """
    Manages state and consistency for anonymization transformations.
    
    Ensures that the same input values always produce the same anonymized
    outputs across multiple runs and maintains transformation mappings.
    """
    
    def __init__(self, seed: str = "default"):
        """
        Initialize the state manager.
        
        Args:
            seed: Seed value for consistent transformations
        """
        self.seed = seed
        self._consistency_cache: Dict[str, Dict[str, Any]] = {}
        self._transformation_stats: Dict[str, int] = {}
    
    def get_cached_value(self, consistency_key: str, original_value: Any) -> Optional[Any]:
        """
        Get a cached transformed value for consistency.
        
        Args:
            consistency_key: Key for consistency mapping
            original_value: Original value to look up
            
        Returns:
            Cached transformed value or None if not found
        """
        if consistency_key not in self._consistency_cache:
            return None
        
        value_hash = self._hash_value(original_value)
        
        return self._consistency_cache[consistency_key].get(value_hash)
    
    def cache_value(self, consistency_key: str, original_value: Any, transformed_value: Any):
        """
        Cache a transformed value for future consistency.
        
        Args:
            consistency_key: Key for consistency mapping
            original_value: Original value
            transformed_value: Transformed value to cache
        """
        if consistency_key not in self._consistency_cache:
            self._consistency_cache[consistency_key] = {}
        
        value_hash = self._hash_value(original_value)
        
        self._consistency_cache[consistency_key][value_hash] = transformed_value
        
        self._transformation_stats[consistency_key] = (
            self._transformation_stats.get(consistency_key, 0) + 1
        )
        
        logger.debug(f"Cached value for {consistency_key}: {value_hash} -> {transformed_value}")
    
    def _hash_value(self, value: Any) -> str:
        """
        Create a consistent hash of a value for caching.
        
        Args:
            value: Value to hash
            
        Returns:
            Hash string
        """
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, sort_keys=True)
        else:
            value_str = str(value)
        
        hash_input = f"{self.seed}:{value_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def get_consistency_stats(self) -> Dict[str, Any]:
        """
        Get statistics about consistency mappings.
        
        Returns:
            Dictionary with consistency statistics
        """
        stats = {
            'total_consistency_keys': len(self._consistency_cache),
            'total_cached_values': sum(len(cache) for cache in self._consistency_cache.values()),
            'transformation_counts': dict(self._transformation_stats),
            'cache_sizes': {
                key: len(cache) for key, cache in self._consistency_cache.items()
            }
        }
        
        return stats
    
    def clear_cache(self, consistency_key: Optional[str] = None):
        """
        Clear cached values.
        
        Args:
            consistency_key: Specific key to clear, or None to clear all
        """
        if consistency_key:
            if consistency_key in self._consistency_cache:
                del self._consistency_cache[consistency_key]
                self._transformation_stats.pop(consistency_key, None)
                logger.info(f"Cleared cache for consistency key: {consistency_key}")
        else:
            self._consistency_cache.clear()
            self._transformation_stats.clear()
            logger.info("Cleared all consistency caches")
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export the current state for persistence.
        
        Returns:
            Dictionary containing the current state
        """
        return {
            'seed': self.seed,
            'consistency_cache': self._consistency_cache,
            'transformation_stats': self._transformation_stats,
            'version': '1.0'
        }
    
    def import_state(self, state_data: Dict[str, Any]):
        """
        Import state from previously exported data.
        
        Args:
            state_data: State data to import
        """
        try:
            if state_data.get('version') != '1.0':
                logger.warning(f"State version mismatch: {state_data.get('version')}")
            
            if state_data.get('seed') != self.seed:
                logger.warning(
                    f"Seed mismatch: current={self.seed}, imported={state_data.get('seed')}"
                )
            
            imported_cache = state_data.get('consistency_cache', {})
            self._consistency_cache.update(imported_cache)
            
            imported_stats = state_data.get('transformation_stats', {})
            for key, count in imported_stats.items():
                self._transformation_stats[key] = (
                    self._transformation_stats.get(key, 0) + count
                )
            
            logger.info(f"Imported state with {len(imported_cache)} consistency keys")
            
        except Exception as e:
            logger.error(f"Error importing state: {str(e)}")
            raise
    
    def validate_consistency(self, consistency_key: str, sample_size: int = 100) -> Dict[str, Any]:
        """
        Validate that transformations are consistent for a given key.
        
        Args:
            consistency_key: Key to validate
            sample_size: Number of samples to check
            
        Returns:
            Validation results
        """
        if consistency_key not in self._consistency_cache:
            return {
                'valid': True,
                'message': 'No cached values to validate',
                'sample_size': 0
            }
        
        cache = self._consistency_cache[consistency_key]
        
        sample_keys = list(cache.keys())[:sample_size]
        
        validation_results = {
            'valid': True,
            'total_values': len(cache),
            'sampled_values': len(sample_keys),
            'inconsistencies': [],
            'message': 'All sampled values are consistent'
        }
        
        for key in sample_keys:
            if cache[key] is None:
                validation_results['inconsistencies'].append({
                    'key': key,
                    'issue': 'Null transformed value'
                })
                validation_results['valid'] = False
        
        if not validation_results['valid']:
            validation_results['message'] = f"Found {len(validation_results['inconsistencies'])} inconsistencies"
        
        return validation_results
