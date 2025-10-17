import django
from django.conf import settings

# Configure Django settings for all tests
if not settings.configured:
    settings.configure(
        GROWTHBOOK_CLIENT_KEY="test-client-key",
        GROWTHBOOK_HOST_BASE_URL="https://test.growthbook.com",
        GROWTHBOOK_REQUESTS_TIMEOUT=60,
        GROWTHBOOK_WEBHOOK_SECRET="test-webhook-secret",
        CACHE_KEY_PREFIX="weni_feature_flags",
        FEATURES_CACHE_TTL=60,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "weni_feature_flags",
        ],
    )
    django.setup()
