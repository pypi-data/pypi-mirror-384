import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Self

from django.urls import URLPattern, URLResolver
from django.utils.regex_helper import normalize

from biased.django.aws_waf.url_patterns import UrlArgsContext, iter_regex_patterns


class AwsWafRegexPatternSet(tuple[re.Pattern]):
    def __new__(cls, *patterns: str):
        if len(patterns) > 10:
            raise ValueError("AWS WAF Pattern Set can hold max 10 items")
        return super().__new__(cls, map(re.compile, patterns))

    @classmethod
    def load(cls, file_path: Path) -> Self:
        with open(file_path) as f:
            patterns = filter(bool, (pattern.rstrip() for pattern in f))
            return cls(*patterns)


def validate_aws_waf_regex_patterns(
    url_patterns: Iterable[URLPattern | URLResolver],
    aws_waf_pattern_sets: Sequence[AwsWafRegexPatternSet],
    context: UrlArgsContext,
):
    def search_aws_waf_pattern(url_example: str) -> re.Pattern | None:
        for aws_waf_pattern_set in aws_waf_pattern_sets:
            for aws_waf_pattern in aws_waf_pattern_set:
                if aws_waf_pattern.match(url_example):
                    return aws_waf_pattern
        return None

    for regex_pattern, url in iter_regex_patterns(url_patterns):
        for url_template, url_params in normalize(regex_pattern):
            url_params = set(url_params)
            with context(url=url):
                remaining_params = url_params - context.keys()
                if not remaining_params:
                    url_example = "/" + url_template % context
                    if search_aws_waf_pattern(url_example=url_example) is None:
                        raise ValueError(f"No AWS WAF pattern found for {url_template}, {regex_pattern}")
                else:
                    raise ValueError(
                        f"No example value for argument(s) "
                        f"{', '.join(remaining_params)} of URL {url_template}, {regex_pattern}"
                    )
