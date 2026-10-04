import hashlib
from django.core.cache import cache
from django.conf import settings

_CACHE_TIMEOUT = getattr(settings, 'CACHES', {}).get('default', {}).get('TIMEOUT', 300)


def _version_key(model_label: str) -> str:
    return f"__ver__{model_label}"


def get_model_version(model_label: str) -> int:
    key = _version_key(model_label)
    version = cache.get(key)
    if version is None:
        cache.add(key, 1, timeout=None)
        version = 1
    return version


def bump_model_version(model_label: str) -> None:
    key = _version_key(model_label)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=None)


def make_list_cache_key(view_name: str, request, model_labels: list[str]) -> str:
    params = sorted(request.GET.items())
    versions = [f"{lbl}:{get_model_version(lbl)}" for lbl in model_labels]
    raw = f"{view_name}|{request.path}|{params}|{versions}"
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"view_cache:{digest}"


class CachedListMixin:
    """
    Mixin for APIView GET handlers. Caches the response payload per path + query string and
    invalidates it whenever a model in `cache_models` is saved or deleted (see signals.py).
    Subclasses declare:
        cache_models = [ModelClass, ...]
    The cached value is {'data': ..., 'pagination': ... or None}.
    """
    cache_models: list = []

    def _cache_key(self, request):
        labels = [m._meta.label for m in self.cache_models]
        return make_list_cache_key(type(self).__name__, request, labels)

    def get_cached(self, request):
        return cache.get(self._cache_key(request))

    def set_cached(self, request, data, pagination=None):
        cache.set(self._cache_key(request), {'data': data, 'pagination': pagination}, timeout=_CACHE_TIMEOUT)

    def cached_response(self, request):
        """The enveloped response for a cache hit, or None."""
        hit = self.get_cached(request)
        if hit is None:
            return None
        return self.success(hit['data'], pagination=hit['pagination'])

    def respond_and_cache(self, request, data, pagination=None):
        self.set_cached(request, data, pagination)
        return self.success(data, pagination=pagination)
