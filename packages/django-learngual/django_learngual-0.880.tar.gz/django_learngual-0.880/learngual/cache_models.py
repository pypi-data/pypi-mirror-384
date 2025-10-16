from typing import Any

from django.core.cache import cache


class CacheTranslation:

    key = "CacheTranslation"

    def get_key(self, *keys):
        return "-".join([self.key] + list(keys))

    @property
    def translation(self) -> dict[str, Any]:
        res = cache.get(self.get_key("translation")) or {}
        return res

    @translation.setter
    def translation(self, value: dict[str, Any]):
        cache.set(self.get_key("translation"), value or {})

    @property
    def queue(self) -> list[str]:
        res = cache.get(self.get_key("queue")) or []
        return res

    @queue.setter
    def queue(self, value: list[str]):
        cache.set(self.get_key("queue"), value or [])

    @property
    def headers(self) -> list[str]:
        res = cache.get(self.get_key("headers")) or []
        return res

    @headers.setter
    def headers(self, value: list[str]):
        cache.set(self.get_key("headers"), value or [])

    def add_to_queue(self, *texts: str):
        self.queue = list(set(self.queue + list(texts)))

    def update_translations(self, translations: dict, headers: list = []):
        self.translation = translations

        if headers:
            self.headers = headers

    def update_headers(self, headers: list):
        self.headers = headers

    @classmethod
    def get_default_cache_model(cls):
        return cls()
