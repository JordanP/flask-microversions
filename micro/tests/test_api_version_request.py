import unittest

from micro import api_version_request


class TestAPIVersionRequest(unittest.TestCase):
    def test_matches_versioned_method_with_null_version(self):
        some_obj = object()
        versioned_request = api_version_request.APIVersionRequest("1.0")
        self.assertRaises(
            ValueError, versioned_request.matches_versioned_method, some_obj)

    def test_matches(self):
        null_version = api_version_request.APIVersionRequest()
        self.assertRaises(
            ValueError, null_version.matches, "1.0", "1.2")

        v1dot0 = api_version_request.APIVersionRequest("1.0")
        versioned_request = api_version_request.APIVersionRequest("1.1")

        self.assertEqual(
            True, versioned_request.matches(null_version, null_version))

        self.assertEqual(
            False, versioned_request.matches(null_version, "1.0"))

        self.assertEqual(
            True, versioned_request.matches(v1dot0, null_version))

    def test_get_string_with_null_version(self):
        null_version = api_version_request.APIVersionRequest()
        self.assertRaises(
            ValueError, null_version.get_string)
