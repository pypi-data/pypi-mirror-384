from unittest import TestCase
from unittest.mock import Mock

from rest_framework.exceptions import AuthenticationFailed

from weni_feature_flags.authentication import GrowthbookWebhookSecretAuthentication
from weni_feature_flags.settings import GROWTHBOOK_WEBHOOK_SECRET


class TestAuthentication(TestCase):
    def setUp(self):
        self.authentication = GrowthbookWebhookSecretAuthentication()

    def test_authenticate(self):
        request = Mock(headers={"Secret": GROWTHBOOK_WEBHOOK_SECRET})
        self.assertTrue(self.authentication.authenticate(request))

    def test_authenticate_with_invalid_secret(self):
        request = Mock(headers={"Secret": "invalid-secret"})
        with self.assertRaises(AuthenticationFailed):
            self.authentication.authenticate(request)

    def test_authenticate_header(self):
        request = Mock()
        self.assertEqual(
            self.authentication.authenticate_header(request), "Growthbook-Secret"
        )
