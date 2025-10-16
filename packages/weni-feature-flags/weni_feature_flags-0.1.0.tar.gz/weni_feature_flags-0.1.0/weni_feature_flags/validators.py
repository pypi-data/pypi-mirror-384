import re


def is_email_valid(email: str) -> bool:
    """
    Validate an email address.
    """
    try:
        return (
            re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)
            is not None
        )
    except Exception:
        return False
