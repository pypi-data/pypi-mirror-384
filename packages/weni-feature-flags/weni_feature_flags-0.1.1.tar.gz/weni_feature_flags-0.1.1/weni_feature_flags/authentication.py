from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class GrowthbookWebhookSecretAuthentication(BaseAuthentication):
    """
    Authentication for the Growthbook webhook using the secret provided in the request headers.
    """

    def authenticate(self, request):
        """
        Authenticate the Growthbook webhook using the secret provided in the request headers.
        """
        secret = request.headers.get("Secret")

        if not secret or (secret != settings.GROWTHBOOK_WEBHOOK_SECRET):
            raise AuthenticationFailed("Invalid secret")

        return (None, None)

    def authenticate_header(self, request):
        """
        Return a string to be used as the WWW-Authenticate header in a
        401 Unauthorized response, or None if the authentication scheme
        should return 403 Forbidden responses.
        """
        return "Growthbook-Secret"
