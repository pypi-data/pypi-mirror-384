from collections.abc import Iterable, Sequence
from typing import Any

from django.urls import URLPattern, URLResolver
from django.urls.resolvers import RoutePattern


class UrlArgsContext:
    def __init__(self, *args: Sequence[tuple[str, dict[str, Any]]]) -> None:
        self._urls: list[str] = [""]
        self._args = args

    def __getitem__(self, key):
        for prefixes, params in self._args:
            for prefix in prefixes:
                if self._urls[-1].startswith(prefix):
                    if key in params:
                        return params[key]
        raise KeyError(f"'{key}' not found in context")

    def __call__(self, url: str):
        self._urls.append(url)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._urls.pop()

    def keys(self):
        keys: set[str] = set()
        for prefixes, params in self._args:
            for prefix in prefixes:
                if self._urls[-1].startswith(prefix):
                    keys.update(params.keys())
        return keys


def _iter_url_patterns(
    url_patterns: Iterable[URLPattern | URLResolver], base=None
) -> Iterable[tuple[URLPattern | RoutePattern, ...]]:
    if base is None:
        base = tuple()
    if not url_patterns:
        return
    for url_pattern in url_patterns:
        if isinstance(url_pattern, URLPattern):
            yield base + (url_pattern,)
        elif isinstance(url_pattern, URLResolver):
            yield from _iter_url_patterns(url_pattern.url_patterns, base + (url_pattern.pattern,))
        else:
            raise RuntimeError(f"Unexpected url_pattern type: {type(url_pattern)}")


def _iter_route_patterns(url_patterns: Iterable[RoutePattern | URLPattern]) -> Iterable[tuple[RoutePattern, ...]]:
    for url_pattern in url_patterns:
        if isinstance(url_pattern, URLPattern):
            yield url_pattern.pattern
        elif isinstance(url_pattern, RoutePattern):
            yield url_pattern
        else:
            raise RuntimeError(f"Unexpected url_pattern type: {type(url_pattern)}")


def _route_pattern_to_regex_pattern(route_pattern: RoutePattern) -> str:
    return route_pattern.regex.pattern.removeprefix("^").replace("/", r"\/")


def _route_patterns_to_regex_pattern(route_patterns: Iterable[RoutePattern]) -> str:
    return "^" + "".join(map(_route_pattern_to_regex_pattern, route_patterns))


def _route_patterns_to_str(route_patterns: Iterable[RoutePattern]) -> str:
    return "".join(map(str, route_patterns))


def iter_regex_patterns(url_patterns: Iterable[URLPattern | URLResolver]) -> Iterable[tuple[str, str]]:
    for url_patterns_ in _iter_url_patterns(url_patterns):
        route_patterns = list(_iter_route_patterns(url_patterns=url_patterns_))
        yield (
            _route_patterns_to_regex_pattern(route_patterns=route_patterns),
            _route_patterns_to_str(route_patterns=route_patterns),
        )
