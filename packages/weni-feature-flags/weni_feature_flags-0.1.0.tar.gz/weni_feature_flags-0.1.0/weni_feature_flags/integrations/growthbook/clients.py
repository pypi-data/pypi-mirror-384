import requests

from weni_feature_flags.settings import (
    GROWTHBOOK_CLIENT_KEY,
    GROWTHBOOK_HOST_BASE_URL,
    GROWTHBOOK_REQUESTS_TIMEOUT,
)


class GrowthBookClient:
    """
    Client to interact with the GrowthBook API.
    """

    def __init__(self):
        self.client_key = GROWTHBOOK_CLIENT_KEY
        self.host = GROWTHBOOK_HOST_BASE_URL
        self.timeout = GROWTHBOOK_REQUESTS_TIMEOUT

    def get_features(self):
        """
        Get feature flags definitions from GrowthBook API.
        """

        url = f"{self.host}/api/features/{self.client_key}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                "Error getting feature flags definitions from GrowthBook API: %s", e
            )

        response = response.json()
        features = response.get("features", {})

        return features
