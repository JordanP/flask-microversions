import unittest

from micro import app
from micro import api_version_request


class BaseTestClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.min_ver = api_version_request.min_api_version().get_string()
        cls.max_ver = api_version_request.max_api_version().get_string()

    def get_with_microversion_header(self, url, version: str):
        return self.client.get(
            url, headers={
                api_version_request.HEADER_NAME: version
            }
        )

    def assert_microversion_header(self, response, expected_version: str):
        self.assertEqual(
            expected_version,
            response.headers[api_version_request.HEADER_NAME]
        )


class TestMicro(BaseTestClass):

    def test_echo(self):
        data = {'toto': 'tata'}
        response = self.client.post('/', json=data).json()
        self.assertEqual(response, data)

    def test_echo_without_wrong_content_type(self):
        data = '<?xml version="1.0" ?><metadata></metadata>'
        response = self.client.post(
            '/',
            headers={'Content-Type': 'application/xml'},
            data=data
        )
        self.assertEqual(415, response.status_code)


class TestRouteWithMinimumVersion1dot1(BaseTestClass):
    def test_index(self):
        response = self.get_with_microversion_header('/min_version', '1.1')
        self.assertEqual(200, response.status_code)

    def test_index_with_microversion_too_low(self):
        response = self.client.get('/min_version')
        self.assertEqual(404, response.status_code)

        response = self.get_with_microversion_header('/min_version', '1.0')
        self.assertEqual(404, response.status_code)


class TestRouteWithMaximumVersion1dot1(BaseTestClass):
    def test_index(self):
        response = self.client.get('/max_version')
        self.assertEqual(200, response.status_code)

        response = self.get_with_microversion_header('/max_version', '1.1')
        self.assertEqual(200, response.status_code)

    def test_index_with_microversion_too_high(self):
        expected_error_msg = 'API version %s is not supported on this method.'

        response = self.get_with_microversion_header('/max_version', '1.2')
        self.assertEqual(404, response.status_code)
        self.assertIn(
            expected_error_msg % "1.2",
            response.data.decode()
        )

        response = self.get_with_microversion_header('/max_version', 'latest')
        self.assertEqual(404, response.status_code)
        self.assertIn(
            expected_error_msg % self.max_ver,
            response.data.decode()
        )


class TestRouteWithMinAndMaxVersionTwoDecorators(BaseTestClass):
    def test_index(self):
        response = self.get_with_microversion_header(
            '/double_decorator', self.min_ver)
        self.assertEqual(200, response.status_code)

        response = self.get_with_microversion_header(
            '/double_decorator', self.max_ver)
        self.assertEqual(200, response.status_code)

    def test_index_out_of_bands(self):
        response = self.get_with_microversion_header(
            '/double_decorator', "1.1")
        self.assertEqual(404, response.status_code)


class TestRouteWithVersionedView(BaseTestClass):
    def test_index(self):
        response = self.get_with_microversion_header(
            '/versioned_view', "1.2")
        self.assertEqual(b'1.2', response.data)

        response = self.get_with_microversion_header(
            '/versioned_view', "1.1")
        self.assertEqual(b'1.1', response.data)

        response = self.get_with_microversion_header(
            '/versioned_view', "1.0")
        self.assertEqual(b'1.0', response.data)


class TestMicroVersionHeader(BaseTestClass):

    def test_index_without_microversion(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assert_microversion_header(response, self.min_ver)

    def test_index_with_latest_microversion(self):
        response = self.get_with_microversion_header('/', 'latest')
        self.assertEqual(200, response.status_code)
        self.assert_microversion_header(response, self.max_ver)

    def test_index_with_exact_microversion(self):
        exact_microversion = '1.1'
        response = self.get_with_microversion_header('/', exact_microversion)
        self.assertEqual(200, response.status_code)
        self.assert_microversion_header(response, exact_microversion)

    def test_index_with_microversion_out_of_bounds(self):
        version_too_low = '0.0'
        version_too_high = '999.0'
        expected_err_msg = ('Version %s is not supported by the API. '
                            'Minimum is %s and maximum is %s.')

        response = self.get_with_microversion_header('/', version_too_low)
        self.assertEqual(406, response.status_code)
        self.assertIn(
            expected_err_msg % (version_too_low, self.min_ver, self.max_ver),
            response.data.decode()
        )

        response = self.get_with_microversion_header('/', version_too_high)
        self.assertEqual(406, response.status_code)
        self.assertIn(
            expected_err_msg % (version_too_high, self.min_ver, self.max_ver),
            response.data.decode()
        )

    def test_index_with_microversion_invalid_format(self):
        invalid_version = b'not-parseable'
        expected_error_msg = b'API Version String %s is of invalid format.'

        response = self.get_with_microversion_header('/', invalid_version)
        self.assertEqual(400, response.status_code)
        self.assertIn(expected_error_msg % invalid_version, response.data)
