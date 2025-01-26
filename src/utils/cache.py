from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path
import logging
from dataclasses import dataclass
import pickle


@dataclass
class CacheEntry:
    key: str
    value: Any
    expiry: Optional[datetime]
    tags: List[str]


class CacheHandler:
    def __init__(self, cache_dir: Path, max_size: int = 1000):
        self.logger = logging.getLogger("nexus.cache")
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()
        self._init_cache_dir()

    def _init_cache_dir(self):
        """Initialize cache directory"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def set(self,
            key: str,
            value: Any,
            ttl: Optional[int] = None,
            tags: List[str] = None) -> bool:
        """Set cache entry with optional TTL (in seconds)"""
        with self.lock:
            try:
                expiry = datetime.now() + timedelta(seconds=ttl) if ttl else None
                entry = CacheEntry(
                    key=key,
                    value=value,
                    expiry=expiry,
                    tags=tags or []
                )

                self.memory_cache[key] = entry
                self._persist_to_disk(key, entry)
                self._enforce_size_limit()
                return True

            except Exception as e:
                self.logger.error(f"Cache set error: {str(e)}")
                return False

    def get(self, key: str) -> Optional[Any]:
        """Get cache entry"""
        with self.lock:
            entry = self.memory_cache.get(key)

            if not entry:
                entry = self._load_from_disk(key)
                if entry:
                    self.memory_cache[key] = entry

            if entry:
                if self._is_expired(entry):
                    self.delete(key)
                    return None
                return entry.value

            return None

    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        with self.lock:
            try:
                if key in self.memory_cache:
                    del self.memory_cache[key]

                cache_file = self.cache_dir / f"{key}.cache"
                if cache_file.exists():
                    cache_file.unlink()
                return True

            except Exception as e:
                self.logger.error(f"Cache delete error: {str(e)}")
                return False

    def clear(self) -> bool:
        """Clear all cache entries"""
        with self.lock:
            try:
                self.memory_cache.clear()
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                return True

            except Exception as e:
                self.logger.error(f"Cache clear error: {str(e)}")
                return False

    def get_by_tag(self, tag: str) -> List[Any]:
        """Get all cache entries with specific tag"""
        with self.lock:
            results = []
            for entry in self.memory_cache.values():
                if tag in entry.tags and not self._is_expired(entry):
                    results.append(entry.value)
            return results

    def delete_by_tag(self, tag: str) -> int:
        """Delete all cache entries with specific tag"""
        with self.lock:
            deleted_count = 0
            keys_to_delete = []

            for key, entry in self.memory_cache.items():
                if tag in entry.tags:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                if self.delete(key):
                    deleted_count += 1

            return deleted_count

    def _persist_to_disk(self, key: str, entry: CacheEntry):
        """Persist cache entry to disk"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            self.logger.error(f"Cache persistence error: {str(e)}")

    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        """Load cache entry from disk"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Cache load error: {str(e)}")
        return None

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return entry.expiry and datetime.now() > entry.expiry

    def _enforce_size_limit(self):
        """Enforce maximum cache size"""
        if len(self.memory_cache) > self.max_size:
            # Remove oldest entries
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].expiry or datetime.max
            )
            entries_to_remove = len(self.memory_cache) - self.max_size

            for key, _ in sorted_entries[:entries_to_remove]:
                self.delete(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_entries': len(self.memory_cache),
            'disk_usage': self._get_disk_usage(),
            'memory_usage': self._get_memory_usage(),
            'hit_ratio': self._get_hit_ratio()
        }

    def _get_disk_usage(self) -> int:
        """Get total disk usage of cache"""
        return sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))

    def _get_memory_usage(self) -> int:
        """Estimate memory usage of cache"""
        import sys
        return sys.getsizeof(self.memory_cache)

    def _get_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        # Implementation specific to hit tracking
        return 0.0
