import uuid
from unittest import TestCase

from weni_feature_flags.converters import convert_uuids_to_strings


class TestConverters(TestCase):
    def test_convert_uuids_to_strings(self):
        project_uuid = uuid.uuid4()

        self.assertEqual(
            convert_uuids_to_strings(
                {"projectUUID": project_uuid, "userEmail": "test@test.com"}
            ),
            {"projectUUID": str(project_uuid), "userEmail": "test@test.com"},
        )
