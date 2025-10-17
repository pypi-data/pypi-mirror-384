from typing import Self

from django.db import models


class DeletedAtQuerySet(models.QuerySet):
    def not_deleted(self) -> Self:
        return self.filter(deleted_at__isnull=True)


class DeletedAtManager(models.Manager.from_queryset(DeletedAtQuerySet)):
    pass


class DeletedAtMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = DeletedAtManager()

    class Meta:
        abstract = True
