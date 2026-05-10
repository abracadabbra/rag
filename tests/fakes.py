"""
测试替身对象
"""

import time


class FakeRedis:
    """支持 TTL 的最小 Redis 替身。"""

    def __init__(self):
        self.store = {}
        self.expiry = {}

    def _is_expired(self, key):
        expires_at = self.expiry.get(key)
        if expires_at is None:
            return False
        if time.time() >= expires_at:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return True
        return False

    def get(self, key):
        if self._is_expired(key):
            return None
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value
        self.expiry[key] = time.time() + ttl

    def expire(self, key, ttl):
        if self._is_expired(key) or key not in self.store:
            return False
        self.expiry[key] = time.time() + ttl
        return True

    def keys(self, pattern):
        keys = [key for key in list(self.store) if not self._is_expired(key)]

        if pattern == "rag:query:*":
            return [key for key in keys if key.startswith("rag:query:")]

        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key for key in keys if key.startswith(prefix)]

        return [key for key in keys if key == pattern]

    def delete(self, *keys):
        deleted = 0
        for key in keys:
            self._is_expired(key)
            if key in self.store:
                deleted += 1
                self.store.pop(key, None)
                self.expiry.pop(key, None)
        return deleted

    def info(self, section):
        assert section == "memory"
        active_keys = len([key for key in list(self.store) if not self._is_expired(key)])
        return {
            "used_memory": active_keys * 100,
            "used_memory_human": f"{active_keys * 100}B",
        }
