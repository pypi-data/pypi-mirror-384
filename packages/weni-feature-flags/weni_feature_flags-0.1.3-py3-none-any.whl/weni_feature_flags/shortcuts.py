from uuid import UUID

from weni_feature_flags.services import FeatureFlagsService
from weni_feature_flags.validators import is_email_valid


def is_feature_active_for_attributes(
    key: str, attributes: dict, should_convert_uuids_to_strings: bool = True
) -> bool:
    """
    Check if a feature is active by its key and attributes.
    """
    features_service = FeatureFlagsService()

    return features_service.evaluate_feature_flag_by_attributes(
        key=key,
        attributes=attributes,
        should_convert_uuids_to_strings=should_convert_uuids_to_strings,
    )


def is_feature_active(key: str, user_email: str, project_uuid: str) -> bool:
    """
    Check if a feature is active by user email and project uuid.
    """

    if not isinstance(project_uuid, UUID):
        try:
            UUID(project_uuid)
        except ValueError:
            raise ValueError("project_uuid must be a valid UUID")

    if not is_email_valid(user_email):
        raise ValueError("user_email must be a valid email")

    return is_feature_active_for_attributes(
        key,
        {
            "userEmail": user_email,
            "projectUUID": str(project_uuid),
        },
    )
