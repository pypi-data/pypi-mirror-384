"""
Result cache manager that coordinates in-memory and persistent storage.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional

from .memory_cache import LRUCache, SingleFlight
from .sqlite_backend import CacheEntry, PersistentCache

logger = logging.getLogger(__name__)


@dataclass
class CacheRecord:
    value: Any
    expires_at: Optional[float]
    namespace: str
    version: str


class ResultCacheManager:
    """Facade around memory + persistent cache layers."""

    def __init__(
        self,
        *,
        memory_size: int = 256,
        persistent_path: Optional[str] = None,
        enabled: bool = True,
        persistence_enabled: bool = True,
        singleflight: bool = True,
        default_ttl: Optional[int] = None,
    ):
        self.enabled = enabled
        self.default_ttl = default_ttl

        self.memory = LRUCache(max_size=memory_size)
        persistence_path = persistent_path
        if persistence_path is None:
            cache_dir = os.environ.get("TOOLUNIVERSE_CACHE_DIR")
            if cache_dir:
                persistence_path = os.path.join(cache_dir, "tooluniverse_cache.sqlite")
        self.persistent = None
        if persistence_enabled and persistence_path:
            try:
                self.persistent = PersistentCache(persistence_path, enable=True)
            except Exception as exc:
                logger.warning("Failed to initialize persistent cache: %s", exc)
                self.persistent = None

        self.singleflight = SingleFlight() if singleflight else None

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    @staticmethod
    def compose_key(namespace: str, version: str, cache_key: str) -> str:
        return f"{namespace}::{version}::{cache_key}"

    def _now(self) -> float:
        return time.time()

    def _ttl_or_default(self, ttl: Optional[int]) -> Optional[int]:
        return ttl if ttl is not None else self.default_ttl

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, *, namespace: str, version: str, cache_key: str) -> Optional[Any]:
        if not self.enabled:
            return None

        composed = self.compose_key(namespace, version, cache_key)
        record = self.memory.get(composed)
        if record:
            if record.expires_at and record.expires_at <= self._now():
                self.memory.delete(composed)
            else:
                return record.value

        entry = self._get_from_persistent(composed)
        if entry:
            expires_at = entry.created_at + entry.ttl if entry.ttl else None
            self.memory.set(
                composed,
                CacheRecord(
                    value=entry.value,
                    expires_at=expires_at,
                    namespace=namespace,
                    version=version,
                ),
            )
            return entry.value
        return None

    def set(
        self,
        *,
        namespace: str,
        version: str,
        cache_key: str,
        value: Any,
        ttl: Optional[int] = None,
    ):
        if not self.enabled:
            return

        effective_ttl = self._ttl_or_default(ttl)
        expires_at = self._now() + effective_ttl if effective_ttl else None
        composed = self.compose_key(namespace, version, cache_key)

        self.memory.set(
            composed,
            CacheRecord(
                value=value,
                expires_at=expires_at,
                namespace=namespace,
                version=version,
            ),
        )

        if self.persistent:
            try:
                self.persistent.set(
                    composed,
                    value,
                    namespace=namespace,
                    version=version,
                    ttl=effective_ttl,
                )
            except Exception as exc:
                logger.warning("Persistent cache write failed: %s", exc)
                self.persistent = None

    def delete(self, *, namespace: str, version: str, cache_key: str):
        composed = self.compose_key(namespace, version, cache_key)
        self.memory.delete(composed)
        if self.persistent:
            try:
                self.persistent.delete(composed)
            except Exception as exc:
                logger.warning("Persistent cache delete failed: %s", exc)

    def clear(self, namespace: Optional[str] = None):
        if namespace:
            # Clear matching namespace in memory
            keys_to_remove = [
                key
                for key, record in self.memory.items()
                if hasattr(record, "namespace") and record.namespace == namespace
            ]
            for key in keys_to_remove:
                self.memory.delete(key)
        else:
            self.memory.clear()

        if self.persistent:
            try:
                self.persistent.clear(namespace=namespace)
            except Exception as exc:
                logger.warning("Persistent cache clear failed: %s", exc)

    def stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "memory": self.memory.stats(),
            "persistent": (
                self.persistent.stats() if self.persistent else {"enabled": False}
            ),
        }

    def dump(self, namespace: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        if not self.persistent:
            return iter([])
        return (
            {
                "cache_key": entry.key,
                "namespace": entry.namespace,
                "version": entry.version,
                "ttl": entry.ttl,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "hit_count": entry.hit_count,
                "value": entry.value,
            }
            for entry in self._iter_persistent(namespace=namespace)
        )

    def _get_from_persistent(self, composed_key: str) -> Optional[CacheEntry]:
        if not self.persistent:
            return None
        try:
            return self.persistent.get(composed_key)
        except Exception as exc:
            logger.warning("Persistent cache read failed: %s", exc)
            self.persistent = None
            return None

    def _iter_persistent(self, namespace: Optional[str]):
        if not self.persistent:
            return iter([])
        try:
            return self.persistent.iter_entries(namespace=namespace)
        except Exception as exc:
            logger.warning("Persistent cache iterator failed: %s", exc)
            return iter([])

    # ------------------------------------------------------------------
    # Context manager for singleflight
    # ------------------------------------------------------------------
    def singleflight_guard(self, composed_key: str):
        if self.singleflight:
            return self.singleflight.acquire(composed_key)
        return _DummyContext()

    def close(self):
        if self.persistent:
            try:
                self.persistent.close()
            except Exception as exc:
                logger.warning("Persistent cache close failed: %s", exc)


class _DummyContext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
