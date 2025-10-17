import operator
from abc import ABC, abstractmethod
from functools import reduce

from django.contrib.admin import SimpleListFilter
from django.db.models import Q


class InputFilter(SimpleListFilter):
    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def get_facet_counts(self, pk_attname, filtered_qs):
        return {}

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v) for k, values in changelist.get_filters_params().items() for v in values if k != self.parameter_name
        )
        yield all_choice


class CommaSeparatedInputFilter(InputFilter, ABC):
    @abstractmethod
    def value_to_filter(self, value: str) -> Q:
        pass

    def queryset(self, request, queryset):
        if self.value() is not None:
            filters: list[Q] = []
            for i in self.value().split(","):
                value = i.strip()
                if not value:
                    continue
                filters.append(self.value_to_filter(value=value))
            if filters:
                return queryset.filter(reduce(operator.or_, filters))
        return None


class StrArrayInputFilter(InputFilter):
    query_name: str

    def queryset(self, request, queryset):
        if self.value() is not None:
            items: list[str] = []
            for i in self.value().split(","):
                value = i.strip()
                if not value:
                    continue
                items.append(value)
            if items:
                return queryset.filter(**{f"{self.query_name}__contains": items})
        return None
