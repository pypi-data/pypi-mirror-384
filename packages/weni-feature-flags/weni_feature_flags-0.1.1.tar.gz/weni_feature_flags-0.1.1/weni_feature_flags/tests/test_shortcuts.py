import uuid
from unittest import TestCase
from unittest.mock import Mock, patch

from weni_feature_flags.services import FeatureFlagsService
from weni_feature_flags.shortcuts import (
    is_feature_active,
    is_feature_active_for_attributes,
)

mock_service = Mock(spec=FeatureFlagsService)


@patch("weni_feature_flags.shortcuts.FeatureFlagsService", return_value=mock_service)
class TestShortcuts(TestCase):
    def setUp(self):
        self.mock_service = Mock(spec=FeatureFlagsService)

    def test_is_feature_active_for_attributes_when_the_feature_is_active(
        self, mock_feature_flags_svc
    ):
        mock_service.evaluate_feature_flag_by_attributes.return_value = True

        self.assertTrue(
            is_feature_active_for_attributes(
                "test", {"projectUUID": uuid.uuid4(), "userEmail": "test@test.com"}
            )
        )

    def test_is_feature_active_for_attributes_when_the_feature_is_not_active(
        self, mock_feature_flags_svc
    ):
        mock_service.evaluate_feature_flag_by_attributes.return_value = False

        self.assertFalse(
            is_feature_active_for_attributes(
                "test", {"projectUUID": uuid.uuid4(), "userEmail": "test@test.com"}
            )
        )

    def test_is_feature_active_when_the_feature_is_active(self, mock_feature_flags_svc):
        mock_service.evaluate_feature_flag_by_attributes.return_value = True

        self.assertTrue(is_feature_active("test", "test@test.com", uuid.uuid4()))

    def test_is_feature_active_when_the_feature_is_not_active(
        self, mock_feature_flags_svc
    ):
        mock_service.evaluate_feature_flag_by_attributes.return_value = False

        self.assertFalse(is_feature_active("test", "test@test.com", uuid.uuid4()))
