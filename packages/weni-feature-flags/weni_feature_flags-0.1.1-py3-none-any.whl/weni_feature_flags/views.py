from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from weni_feature_flags.authentication import GrowthbookWebhookSecretAuthentication
from weni_feature_flags.tasks import update_feature_flags


class FeatureFlagsWebhookView(APIView):
    authentication_classes = [GrowthbookWebhookSecretAuthentication]

    def post(self, request: Request) -> Response:
        update_feature_flags.delay()

        return Response(status=status.HTTP_204_NO_CONTENT)
