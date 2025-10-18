import uuid
from unittest import TestCase
from unittest.mock import Mock, patch

from weni_feature_flags.integrations.growthbook.clients import GrowthBookClient
from weni_feature_flags.services import FeatureFlagsService

mock_growthbook_client = Mock(spec=GrowthBookClient)
mock_cache_class = Mock()

mock_feature_flag_snapshot = Mock()


@patch("weni_feature_flags.services.cache", mock_cache_class)
@patch("weni_feature_flags.services.FeatureFlagSnapshot", mock_feature_flag_snapshot)
class TestFeatureFlagsService(TestCase):
    def setUp(self):
        self.service = FeatureFlagsService(growthbook_client=mock_growthbook_client)
        mock_growthbook_client.reset_mock()
        mock_cache_class.reset_mock()
        mock_feature_flag_snapshot.reset_mock()
        mock_feature_flag_snapshot.objects.reset_mock()

        mock_cache_class.get.return_value = None

        # Reset the mock and create a fresh queryset for each test

        mock_queryset = Mock()
        mock_queryset.last.return_value = None
        mock_feature_flag_snapshot.objects.order_by.return_value = mock_queryset

    def test_get_features_from_cache_when_the_cache_is_empty(self):
        mock_cache_class.get.return_value = None
        service = self.service
        features = service.get_features_from_cache()

        self.assertIsNone(features)
        mock_cache_class.get.assert_called_once()

    def test_get_features_from_cache_when_the_cache_is_not_empty(self):
        mock_cache_class.get.return_value = {
            "features": {
                "test": {
                    "on": True,
                },
            },
        }
        service = self.service
        features = service.get_features_from_cache()

        self.assertIsNotNone(features)
        mock_cache_class.get.assert_called_once()

    def test_save_features_to_cache(self):
        service = self.service
        service.save_features_to_cache(
            {
                "features": {
                    "test": {
                        "on": True,
                    },
                },
            }
        )
        mock_cache_class.set.assert_called_once()

    def test_get_features_db_object_when_the_db_is_empty(self):
        service = self.service
        features = service.get_features_db_object()

        self.assertIsNone(features)
        mock_feature_flag_snapshot.objects.order_by.assert_called_once_with(
            "created_at"
        )
        mock_feature_flag_snapshot.objects.order_by.return_value.last.assert_called_once()

    def test_get_features_db_object_when_the_db_is_not_empty(self):
        mock_feature_flag_snapshot.objects.order_by.return_value.last.return_value = (
            mock_feature_flag_snapshot
        )
        service = self.service
        features = service.get_features_db_object()

        self.assertIsNotNone(features)
        mock_feature_flag_snapshot.objects.order_by.assert_called_once_with(
            "created_at"
        )
        mock_feature_flag_snapshot.objects.order_by.return_value.last.assert_called_once()

    def test_get_features_from_db_when_the_db_is_empty(self):
        service = self.service
        features = service.get_features_from_db()

        self.assertIsNone(features)
        mock_feature_flag_snapshot.objects.order_by.assert_called_once_with(
            "created_at"
        )
        mock_feature_flag_snapshot.objects.order_by.return_value.last.assert_called_once()

    def test_get_features_from_db_when_the_db_is_not_empty(self):
        mock_feature_flag_snapshot.objects.order_by.return_value.last.return_value = (
            mock_feature_flag_snapshot
        )
        service = self.service
        features = service.get_features_from_db()

        self.assertIsNotNone(features)
        mock_feature_flag_snapshot.objects.order_by.assert_called_once_with(
            "created_at"
        )
        mock_feature_flag_snapshot.objects.order_by.return_value.last.assert_called_once()

    def test_save_features_to_db_when_the_db_is_empty(self):
        service = self.service
        features_snapshot = service.save_features_to_db(
            {
                "features": {
                    "test": {
                        "on": True,
                    },
                },
            }
        )

        mock_feature_flag_snapshot.objects.create.assert_called_once()
        mock_feature_flag_snapshot.objects.save.assert_not_called()
        self.assertIsNotNone(features_snapshot)

    def test_save_features_to_db_when_the_db_is_not_empty(self):
        mock_obj = Mock()
        mock_feature_flag_snapshot.objects.order_by.return_value.last.return_value = (
            mock_obj
        )
        service = self.service
        features_snapshot = service.save_features_to_db(
            {
                "features": {
                    "test": {
                        "on": True,
                    },
                },
            }
        )

        mock_obj.save.assert_called_once()
        mock_obj.save.assert_called_once_with(update_fields=["data"])
        mock_feature_flag_snapshot.objects.create.assert_not_called()
        self.assertIsNotNone(features_snapshot)

    def test_get_features(self):
        mock_growthbook_client.get_features.return_value = {
            "features": {
                "test": {
                    "on": True,
                },
            },
        }
        features = self.service.get_features()

        self.assertIsNotNone(features)
        mock_growthbook_client.get_features.assert_called_once()
        mock_cache_class.get.assert_called_once()
        mock_cache_class.set.assert_called_once()

    def test_get_features_when_the_features_are_from_the_cache(self):
        mock_cache_class.get.return_value = {
            "test": {
                "on": True,
            },
        }
        features = self.service.get_features()

        self.assertIsNotNone(features)
        mock_cache_class.get.assert_called_once()
        mock_cache_class.set.assert_not_called()
        mock_growthbook_client.get_features.assert_not_called()

    def test_update_features(self):
        self.service.update_features()
        mock_growthbook_client.get_features.assert_called_once()
        mock_feature_flag_snapshot.objects.create.assert_called_once()
        mock_cache_class.set.assert_called_once()

    def test_get_active_feature_flags_for_attributes(self):
        project_uuid = str(uuid.uuid4())
        mock_growthbook_client.get_features.return_value = {
            "testUserEmailIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test",
                        "condition": {
                            "userEmail": {
                                "$in": ["test@test.com"],
                            },
                        },
                        "force": True,
                    },
                ],
            },
            "testUserEmailNotIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test",
                        "condition": {
                            "userEmail": {
                                "$in": ["test2@test.com"],  # Email is different
                            },
                        },
                        "force": True,
                    },
                ],
            },
            "testProjectUUIDIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test3",
                        "condition": {
                            "projectUUID": {
                                "$in": [project_uuid],
                            },
                        },
                        "force": True,
                    },
                ],
            },
            "testProjectUUIDNotIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test3",
                        "condition": {
                            "projectUUID": {
                                "$in": [str(uuid.uuid4())],
                            },
                        },
                        "force": True,
                    },
                ],
            },
        }
        features = self.service.get_active_feature_flags_for_attributes(
            {
                "projectUUID": project_uuid,
                "userEmail": "test@test.com",
            }
        )

        self.assertIsInstance(features, list)
        self.assertEqual(len(features), 2)
        self.assertIn("testUserEmailIn", features)
        self.assertNotIn("testUserEmailNotIn", features)
        self.assertIn("testProjectUUIDIn", features)
        self.assertNotIn("testProjectUUIDNotIn", features)

    def test_evaluate_feature_flag_by_attributes(self):
        project_uuid = str(uuid.uuid4())
        mock_growthbook_client.get_features.return_value = {
            "testUserEmailIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test",
                        "condition": {
                            "userEmail": {
                                "$in": ["test@test.com"],
                            },
                        },
                        "force": True,
                    },
                ],
            },
            "testUserEmailNotIn": {
                "defaultValue": False,
                "rules": [
                    {
                        "id": "test",
                        "condition": {
                            "userEmail": {
                                "$in": ["test2@test.com"],  # Email is different
                            },
                        },
                        "force": True,
                    },
                ],
            },
        }
        is_active = self.service.evaluate_feature_flag_by_attributes(
            "testUserEmailIn",
            {
                "projectUUID": project_uuid,
                "userEmail": "test@test.com",
            },
        )

        self.assertTrue(is_active)

        is_active = self.service.evaluate_feature_flag_by_attributes(
            "testUserEmailNotIn",
            {
                "projectUUID": project_uuid,
                "userEmail": "test@test.com",
            },
        )

        self.assertFalse(is_active)
