from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpRequest, HttpResponse

from biased.django.aws_waf.aws_waf_regex_pattern import AwsWafRegexPatternSet


class AwsWafWhitelistMiddleware(ABC, Callable[[HttpRequest], HttpResponse]):
    async_capable = True
    sync_capable = False
    aws_waf_regex_pattern_sets: Sequence[AwsWafRegexPatternSet] = tuple()

    @abstractmethod
    def build_forbidden_http_response(self, request: HttpRequest) -> HttpResponse:
        pass

    def __init__(self, get_response):
        if not settings.ENABLE_AWS_WAF_WHITELIST_MIDDLEWARE:
            raise MiddlewareNotUsed()
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def _filter_request(self, request: HttpRequest) -> HttpResponse | None:
        path = request.path
        for regex_pattern_set in self.aws_waf_regex_pattern_sets:
            for regex_pattern in regex_pattern_set:
                if regex_pattern.match(path):
                    return None

        return self.build_forbidden_http_response(request=request)

    async def __call__(self, request):
        response = self._filter_request(request)
        if response is None:
            response = await self.get_response(request)
        return response
