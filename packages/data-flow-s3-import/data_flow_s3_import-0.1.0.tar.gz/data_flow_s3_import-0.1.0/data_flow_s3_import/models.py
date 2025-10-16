from django.db import models


class IngestedModelQuerySet(models.QuerySet):
    def only_in_last_import(self):
        return self.filter(exists_in_last_import=True)


class IngestedModel(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    exists_in_last_import = models.BooleanField(default=True)

    objects = models.Manager.from_queryset(IngestedModelQuerySet)()
