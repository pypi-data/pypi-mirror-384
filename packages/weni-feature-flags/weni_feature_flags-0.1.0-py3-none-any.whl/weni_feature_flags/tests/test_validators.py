from unittest import TestCase

from weni_feature_flags.validators import is_email_valid


class TestValidators(TestCase):
    def test_is_email_valid(self):
        self.assertTrue(is_email_valid("test@example.com"))
        self.assertTrue(is_email_valid("1@example.com"))

    def test_is_email_valid_for_invalid_strings(self):
        self.assertFalse(is_email_valid(""))
        self.assertFalse(is_email_valid("test"))
        self.assertFalse(is_email_valid("test@"))
        self.assertFalse(is_email_valid("test@example"))
        self.assertFalse(is_email_valid("test@example.com."))
        self.assertFalse(is_email_valid("test@example.1"))

    def test_is_email_valid_for_invalid_types(self):
        self.assertFalse(is_email_valid(None))
        self.assertFalse(is_email_valid(1))
        self.assertFalse(is_email_valid(1.0))
        self.assertFalse(is_email_valid(True))
        self.assertFalse(is_email_valid(False))
        self.assertFalse(is_email_valid(object()))
        self.assertFalse(is_email_valid(list()))
        self.assertFalse(is_email_valid(dict()))
        self.assertFalse(is_email_valid(tuple()))
        self.assertFalse(is_email_valid(set()))
        self.assertFalse(is_email_valid(range(10)))
