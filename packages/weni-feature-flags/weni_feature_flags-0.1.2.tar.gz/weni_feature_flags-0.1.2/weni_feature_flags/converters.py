from uuid import UUID


def convert_uuids_to_strings(attributes: dict) -> dict:
    return {k: str(v) if isinstance(v, UUID) else v for k, v in attributes.items()}
