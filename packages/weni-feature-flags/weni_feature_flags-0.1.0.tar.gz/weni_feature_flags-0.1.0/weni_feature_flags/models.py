from django.db import models
from django.utils.translation import gettext_lazy as _


class FeatureFlagSnapshot(models.Model):
    """
    Model used to store a snapshot of the feature flags.
    """

    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Feature Flags Snapshot")
        verbose_name_plural = _("Feature Flags Snapshot")

    def __str__(self):
        return "Feature Flags Snapshot"
