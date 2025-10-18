from unittest.mock import Mock, patch

from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status

from weni_feature_flags.settings import GROWTHBOOK_WEBHOOK_SECRET
from weni_feature_flags.tasks import update_feature_flags
from weni_feature_flags.views import FeatureFlagsWebhookView

mock_update_feature_flags_delay = Mock(spec=update_feature_flags.delay)


@patch(
    "weni_feature_flags.views.update_feature_flags.delay",
    mock_update_feature_flags_delay,
)
class TestFeatureFlagsWebhookView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        mock_update_feature_flags_delay.reset_mock()

    def test_post(self):
        request = self.factory.post("/webhook/", HTTP_SECRET=GROWTHBOOK_WEBHOOK_SECRET)
        response = FeatureFlagsWebhookView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_update_feature_flags_delay.assert_called_once()

    def test_post_with_invalid_secret(self):
        request = self.factory.post("/webhook/", HTTP_SECRET="invalid-secret")
        response = FeatureFlagsWebhookView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_update_feature_flags_delay.assert_not_called()

    def test_post_with_missing_secret(self):
        request = self.factory.post(
            "/webhook/",
        )
        response = FeatureFlagsWebhookView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_update_feature_flags_delay.assert_not_called()
