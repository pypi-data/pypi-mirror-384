from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_setting(name: str, is_required: bool = False, default_value: Any = None) -> Any:
    """
    Get a setting from the settings module.
    """
    setting = getattr(settings, name, default_value)

    if is_required and not setting:
        raise ImproperlyConfigured(f"Setting {name} is required")

    return setting


# Default
DEFAULT_FEATURES_CACHE_TTL = 60  # 1 minute

# GrowthBook
GROWTHBOOK_CLIENT_KEY = get_setting("GROWTHBOOK_CLIENT_KEY", is_required=True)
GROWTHBOOK_HOST_BASE_URL = get_setting("GROWTHBOOK_HOST_BASE_URL", is_required=True)
GROWTHBOOK_REQUESTS_TIMEOUT = get_setting(
    "GROWTHBOOK_REQUESTS_TIMEOUT", is_required=False, default_value=60
)
GROWTHBOOK_WEBHOOK_SECRET = get_setting("GROWTHBOOK_WEBHOOK_SECRET", is_required=False)


# Caching
CACHE_KEY_PREFIX = get_setting(
    "CACHE_KEY_PREFIX", is_required=False, default_value="weni_feature_flags"
)
FEATURES_CACHE_TTL = get_setting(
    "FEATURES_CACHE_TTL",
    is_required=False,
    default_value=DEFAULT_FEATURES_CACHE_TTL,
)
