from unittest import TestCase
from unittest.mock import Mock, patch

from weni_feature_flags.services import FeatureFlagsService
from weni_feature_flags.tasks import update_feature_flags

mock_service = Mock(spec=FeatureFlagsService)


class TestTasks(TestCase):
    @patch("weni_feature_flags.services.FeatureFlagsService", return_value=mock_service)
    def test_update_feature_flags(self, mock_feature_flags_svc):
        update_feature_flags()
        mock_service.update_features.assert_called_once()
