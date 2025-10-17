"""
Caching functionality for PyConvexity data operations.

This module handles caching of processed datasets to improve performance.
"""

import pandas as pd
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCache:
    """Manages caching of processed datasets."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to 'data/cache'
        """
        if cache_dir is None:
            cache_dir = "data/cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_key(self, dataset_name: str, filters: Dict[str, Any]) -> str:
        """Generate a unique cache key for a dataset and filters combination."""
        # Create a hash of the filters
        filters_str = json.dumps(filters, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()
        
        return f"{dataset_name}_{filters_hash}"
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.parquet"
    
    def get_cached_data(
        self, 
        dataset_name: str, 
        filters: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve cached data if available and not expired.
        
        Args:
            dataset_name: Name of the dataset
            filters: Filters applied to the dataset
            
        Returns:
            pandas.DataFrame or None: Cached data if available and valid
        """
        cache_key = self._get_cache_key(dataset_name, filters)
        cache_file = self._get_cache_file_path(cache_key)
        
        # Check if cache file exists
        if not cache_file.exists():
            return None
        
        # Check if cache entry exists in metadata
        if cache_key not in self.metadata:
            # Clean up orphaned cache file
            cache_file.unlink(missing_ok=True)
            return None
        
        # Check if cache is expired (default: 7 days)
        cache_info = self.metadata[cache_key]
        created_time = datetime.fromisoformat(cache_info['created'])
        max_age = timedelta(days=cache_info.get('max_age_days', 7))
        
        if datetime.now() - created_time > max_age:
            logger.info(f"Cache expired for '{dataset_name}', removing...")
            self._remove_cache_entry(cache_key)
            return None
        
        # Load cached data
        try:
            cached_data = pd.read_parquet(cache_file)
            logger.info(f"Loaded cached data for '{dataset_name}' ({len(cached_data)} rows)")
            return cached_data
        except Exception as e:
            logger.warning(f"Failed to load cached data for '{dataset_name}': {e}")
            self._remove_cache_entry(cache_key)
            return None
    
    def cache_data(
        self, 
        dataset_name: str, 
        data: pd.DataFrame, 
        filters: Dict[str, Any],
        max_age_days: int = 7
    ):
        """
        Cache processed data.
        
        Args:
            dataset_name: Name of the dataset
            data: Processed pandas DataFrame
            filters: Filters applied to the dataset
            max_age_days: Maximum age of cache in days
        """
        cache_key = self._get_cache_key(dataset_name, filters)
        cache_file = self._get_cache_file_path(cache_key)
        
        # Save data to parquet file
        data.to_parquet(cache_file, index=False)
        
        # Update metadata
        self.metadata[cache_key] = {
            'dataset_name': dataset_name,
            'filters': filters,
            'created': datetime.now().isoformat(),
            'max_age_days': max_age_days,
            'rows': len(data),
            'columns': list(data.columns)
        }
        
        self._save_metadata()
        logger.info(f"Cached data for '{dataset_name}' ({len(data)} rows)")
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove a cache entry and its file."""
        cache_file = self._get_cache_file_path(cache_key)
        cache_file.unlink(missing_ok=True)
        
        if cache_key in self.metadata:
            del self.metadata[cache_key]
            self._save_metadata()
    
    def clear_cache(self, dataset_name: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            dataset_name: If provided, only clear cache for this dataset
        """
        keys_to_remove = []
        
        for cache_key, info in self.metadata.items():
            if dataset_name is None or info['dataset_name'] == dataset_name:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            self._remove_cache_entry(key)
        
        logger.info(f"Cleared {len(keys_to_remove)} cache entries")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache."""
        total_size = 0
        dataset_counts = {}
        
        for cache_key, info in self.metadata.items():
            dataset_name = info['dataset_name']
            dataset_counts[dataset_name] = dataset_counts.get(dataset_name, 0) + 1
            
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                total_size += cache_file.stat().st_size
        
        return {
            'total_entries': len(self.metadata),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'dataset_counts': dataset_counts,
            'cache_dir': str(self.cache_dir)
        }
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        expired_keys = []
        
        for cache_key, info in self.metadata.items():
            created_time = datetime.fromisoformat(info['created'])
            max_age = timedelta(days=info.get('max_age_days', 7))
            
            if datetime.now() - created_time > max_age:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        else:
            logger.info("No expired cache entries found")
