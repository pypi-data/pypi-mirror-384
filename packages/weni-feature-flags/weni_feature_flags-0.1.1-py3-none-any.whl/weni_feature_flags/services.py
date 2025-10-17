import json
from typing import List, Optional

from django.core.cache import cache
from growthbook import GrowthBook

from weni_feature_flags.converters import convert_uuids_to_strings
from weni_feature_flags.integrations.growthbook.clients import GrowthBookClient
from weni_feature_flags.models import FeatureFlagSnapshot
from weni_feature_flags.settings import CACHE_KEY_PREFIX, FEATURES_CACHE_TTL
from weni_feature_flags.tasks import update_feature_flags

CACHE_KEY = f"{CACHE_KEY_PREFIX}:features"


class FeatureFlagsService:
    def __init__(self, growthbook_client: GrowthBookClient = GrowthBookClient()):
        self.growthbook_client = growthbook_client

    def get_features_from_cache(self) -> dict:
        """
        Get feature flags features from cache.
        """

        data = cache.get(CACHE_KEY)

        if not data:
            return

        if not isinstance(data, dict):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return

        return data

    def save_features_to_cache(self, features: dict):
        """
        Save feature flags features to cache.
        """
        cache.set(
            CACHE_KEY,
            json.dumps(features, ensure_ascii=False),
            FEATURES_CACHE_TTL,
        )

    def get_features_db_object(self) -> Optional[FeatureFlagSnapshot]:
        """
        Get feature flags snapshot from the database.
        """
        return FeatureFlagSnapshot.objects.order_by("created_at").last()

    def get_features_from_db(self) -> Optional[dict]:
        """
        Get feature flags snapshot's data from the database.
        """
        obj = self.get_features_db_object()

        return obj.data if obj else None

    def save_features_to_db(self, data: dict) -> Optional[FeatureFlagSnapshot]:
        """
        Save feature flags snapshot's data to the database.
        """
        obj = self.get_features_db_object()

        if obj:
            obj.data = data
            obj.save(update_fields=["data"])
        else:
            obj = FeatureFlagSnapshot.objects.create(data=data)

        return obj

    def get_features(self) -> dict:
        """
        Get feature flags.
        """
        if features_from_cache := self.get_features_from_cache():
            return features_from_cache

        features_from_db = self.get_features_from_db()

        if features_from_db:
            update_feature_flags.delay()

            return features_from_db

        return self.update_features()

    def update_features(self):
        """
        Update feature flags.
        """
        features = self.growthbook_client.get_features()

        self.save_features_to_db(features)
        self.save_features_to_cache(features)

        return features

    def get_active_feature_flags_for_attributes(
        self, attributes: dict, should_convert_uuids_to_strings: bool = True
    ) -> List[str]:
        """
        Get feature flags for attributes.
        """
        features = self.get_features()

        if should_convert_uuids_to_strings:
            attributes = convert_uuids_to_strings(attributes)

        gb = GrowthBook(
            attributes=attributes,
            features=features,
        )

        active_features: list[str] = []

        for feature in features:
            if gb.is_on(feature):
                active_features.append(feature)

        return active_features

    def evaluate_feature_flag_by_attributes(
        self, key: str, attributes: dict, should_convert_uuids_to_strings: bool = True
    ) -> bool:
        """
        Evaluate feature flag by attributes.
        """
        features = self.get_features()

        if should_convert_uuids_to_strings:
            attributes = convert_uuids_to_strings(attributes)

        gb = GrowthBook(
            attributes=attributes,
            features=features,
        )

        return gb.eval_feature(key).on
