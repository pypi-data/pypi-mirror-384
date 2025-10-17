import os
from unittest import mock
from unittest.mock import MagicMock, patch
from django.test import TestCase
from datetime import date, timedelta

from esi.openapi_clients import ESIClientProvider
from django.core.cache import cache
from django.utils import timezone
from httpx import RequestError, HTTPStatusError
from esi.exceptions import ESIErrorLimitException, HTTPNotModified
from esi import app_settings
from esi import __title__, __url__, __version__
import httpx

from .. import openapi_clients as oc

SPEC_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_openapi.json"
)


class TestClientFunctions(TestCase):
    def test_time_to_expiry_valid(self):
        expires = (
            timezone.now() + timedelta(seconds=120)
        ).strftime('%a, %d %b %Y %H:%M:%S %Z')
        ttl = oc._time_to_expiry(expires)

        # this shouldnt take more that 10 seconds
        self.assertGreater(ttl, 110)

    def test_time_to_expiry_invalid(self):
        # invalid format returns 0
        self.assertEqual(oc._time_to_expiry("not-a-date"), 0)

    def test_httpx_exceptions_valids(self):
        self.assertTrue(
            oc._httpx_exceptions(
                RequestError("Bad Request")
            )
        )

        response = MagicMock(status_code=502)
        exc = HTTPStatusError("msg", request=None, response=response)

        self.assertTrue(
            oc._httpx_exceptions(exc)
        )

        response.status_code = 400
        exc = HTTPStatusError("msg", request=None, response=response)

        self.assertFalse(
            oc._httpx_exceptions(exc)
        )

        self.assertFalse(
            oc._httpx_exceptions(
                ESIErrorLimitException(reset=10)
            )
        )

    def test_httpx_exceptions_invalid(self):
        self.assertFalse(
            oc._httpx_exceptions(
                "this is not an exception!"
            )
        )


class BuildUserAgentTests(TestCase):
    app_name = "TestApp"
    app_ver = "1.2.3"
    app_url = "https://tests.pass"

    def test_build_user_agent_with_url(self):
        ua = oc._build_user_agent(self.app_name, self.app_ver, self.app_url)

        expected_app_name = "TestApp"
        expected_title = 'DjangoEsi'

        self.assertEqual(
            (
                f"{expected_app_name}/{self.app_ver} "
                f"({app_settings.ESI_USER_CONTACT_EMAIL}{f'; +{self.app_url})'} "
                f"{expected_title}/{__version__} (+{__url__})"
            ),
            ua
        )

    def test_enforce_pascal_case_for_ua_appname_with_space(self):
        """
        Test that the application name is converted to PascalCase in the User-Agent string when it contains spaces.

        :return:
        :rtype:
        """

        ua = oc._build_user_agent("test app", self.app_ver, self.app_url)

        expected_app_name = "TestApp"
        expected_title = 'DjangoEsi'

        self.assertEqual(
            (
                f"{expected_app_name}/{self.app_ver} "
                f"({app_settings.ESI_USER_CONTACT_EMAIL}{f'; +{self.app_url})'} "
                f"{expected_title}/{__version__} (+{__url__})"
            ),
            ua
        )

    def test_enforce_pascal_case_for_ua_appname_with_hyphen(self):
        """
        Test that the application name is converted to PascalCase in the User-Agent string when it contains hyphens.

        :return:
        :rtype:
        """

        ua = oc._build_user_agent("test-app", self.app_ver, self.app_url)

        expected_app_name = "TestApp"
        expected_title = 'DjangoEsi'

        self.assertEqual(
            (
                f"{expected_app_name}/{self.app_ver} "
                f"({app_settings.ESI_USER_CONTACT_EMAIL}{f'; +{self.app_url})'} "
                f"{expected_title}/{__version__} (+{__url__})"
            ),
            ua
        )

    def test_build_user_agent_without_url(self):
        ua = oc._build_user_agent(self.app_name, self.app_ver)

        expected_app_name = "TestApp"
        expected_title = 'DjangoEsi'

        self.assertEqual(
            (
                f"{expected_app_name}/{self.app_ver} "
                f"({app_settings.ESI_USER_CONTACT_EMAIL}) "
                f"{expected_title}/{__version__} (+{__url__})"
            ),
            ua
        )


class BaseEsiOperationTests(TestCase):
    def setUp(self):
        self.page_param = MagicMock()
        self.page_param.name = "page"

        self.after_param = MagicMock()
        self.after_param.name = "after"

        self.before_param = MagicMock()
        self.before_param.name = "before"

        self.data_param = MagicMock()
        self.data_param.name = "data"

        self.lang_param = MagicMock()
        self.lang_param.name = "Accept-Language"

        self.body_param = MagicMock()
        self.body_param.name = "body"

        self.fake_op = MagicMock()
        self.fake_op.parameters = [
            self.data_param,
            self.lang_param
        ]
        self.fake_op.tags = ["test"]
        self.fake_op.operationId = "fake_op"
        self.api = MagicMock(app_name="TestApp")
        self.op = oc.BaseEsiOperation(
            ("GET", "/fake_op", self.fake_op, {}),
            self.api
        )

    def test_non_unique_kwargs(self):
        op_1 = self.op(data="bar")
        key_1 = op_1._cache_key()
        op_2 = self.op(data="foo")
        key_2 = op_2._cache_key()
        self.assertNotEqual(key_1, key_2)

    def test_unique_kwargs(self):
        op_1 = self.op(data="foo")
        key_1 = op_1._cache_key()
        op_2 = self.op(data="foo")
        key_2 = op_2._cache_key()
        self.assertEqual(key_1, key_2)

    def test_extract_body(self):
        test_body = "something somethng something..."
        op = self.op(body=test_body)
        body = op._extract_body_param()
        self.assertEqual(test_body, body)

    def test_extract_body_exception(self):
        test_body = "something somethng something..."
        self.fake_op.requestBody = False
        op = self.op(body=test_body)
        with self.assertRaises(ValueError):
            op._extract_body_param()

    def test_extract_token(self):
        test_tkn = {"token": "token model goes here"}
        op = self.op(token=test_tkn)
        token = op._extract_token_param()
        self.assertEqual(test_tkn, token)

    def test_extract_token_exception_no_token_needed(self):
        self.op._kwargs = {"token": "token"}
        self.fake_op.security = None
        with self.assertRaises(ValueError):
            self.op._extract_token_param()

    def test_not_page_or_cursor_param(self):
        self.assertFalse(self.op._has_page_param())
        self.assertFalse(self.op._has_cursor_param())

    def test_has_page_param(self):
        self.fake_op.parameters += [self.page_param]
        op = self.op()
        self.assertTrue(op._has_page_param())

    def test_has_cursor_params(self):
        self.fake_op.parameters = [self.after_param]
        op = self.op()
        self.assertTrue(op._has_cursor_param())

        self.fake_op.parameters = [self.before_param]
        op = self.op()
        self.assertTrue(op._has_cursor_param())


class EsiOperationTests(TestCase):
    def setUp(self):
        self.op_mock = MagicMock()
        self.op_mock.parameters = []
        self.op_mock.tags = ["tag"]
        self.op_mock.operationId = "opid"

        self.api_mock = MagicMock()
        self.api_mock.app_name = "TestApp"

        self.op = oc.EsiOperation(
            (
                "GET",
                "/url",
                self.op_mock,
                {}
            ),
            self.api_mock
        )

    @patch.object(oc.EsiOperation, "_make_request")
    def test_result_and_results(self, mock_make_request):
        data = {"data": "stuff"}
        mock_resp = MagicMock(status_code=200, headers={"Expires": "Wed, 1 July 2099 11:00:00 GMT"})
        mock_make_request.return_value = ({"Expires": "date"}, data, mock_resp)
        data_resp = self.op(foo="bar").result()
        self.assertEqual(data, data_resp)


class TestOpenapiClientProvider(TestCase):

    def test_compatibilitydate_date_to_string(self):
        testdate_1 = date(2024, 1, 1)
        testdate_2 = date(2025, 8, 26)

        self.assertEqual("2024-01-01", ESIClientProvider._date_to_string(testdate_1))
        self.assertEqual("2025-08-26", ESIClientProvider._date_to_string(testdate_2))

    @patch.object(httpx.Client, "send")
    def test_ua(self, send: MagicMock):
        app_name = "TestsApp"
        app_ver = "1.2.3"
        app_url = "https://tests.pass"
        esi = ESIClientProvider(
            ua_appname=app_name,
            ua_url=app_url,
            ua_version=app_ver,
            compatibility_date="2020-01-01",
            tags=["Status"],
            spec_file=SPEC_PATH
        )
        cache.clear()

        send.return_value = httpx.Response(
            200,
            json={
                "players": 1234,
                "server_version": "1234",
                "start_time": "2029-09-19T11:02:08Z"
            },
            request=httpx.Request("GET", "test"),
        )

        status = esi.client.Status.GetStatus().result()
        call_args, call_kwargs = send.call_args

        expected_app_name = "TestsApp"
        expected_title = 'DjangoEsi'

        self.assertEqual(
            call_args[0].headers["user-agent"],
            (
                f"{expected_app_name}/{app_ver} "
                f"({app_settings.ESI_USER_CONTACT_EMAIL}{f'; +{app_url})'} "
                f"{expected_title}/{__version__} (+{__url__})"
            )
        )
        self.assertEqual(status.players, 1234)

    @patch.object(httpx.Client, "send")
    def test_etag_hit_cached(self, send: MagicMock):
        app_name = "TestsApp"
        app_ver = "1.2.3"
        app_url = "https://tests.pass"
        etag = "'123456789abcdef123456789abcdef'"
        esi = ESIClientProvider(
            ua_appname=app_name,
            ua_url=app_url,
            ua_version=app_ver,
            compatibility_date="2020-01-01",
            tags=["Status"],
            spec_file=SPEC_PATH
        )
        cache.clear()

        expires = (
            timezone.now() + timedelta(minutes=5)
        ).strftime('%a, %d %b %Y %H:%M:%S %Z')

        send.return_value = httpx.Response(
            200,
            json={
                "players": 1234,
                "server_version": "1234",
                "start_time": "2029-09-19T11:02:08Z"
            },
            headers={
                "etag": etag,
                "expires": expires
            },
            request=httpx.Request(
                "GET",
                "test",
            ),
        )

        esi.client.Status.GetStatus().result()

        with self.assertRaises(HTTPNotModified):
            esi.client.Status.GetStatus().result()

    @patch.object(httpx.Client, "send")
    def test_etag_hit_external(self, send: MagicMock):
        app_name = "TestsApp"
        app_ver = "1.2.3"
        app_url = "https://tests.pass"
        etag = "'123456789abcdef123456789abcdef'"
        esi = ESIClientProvider(
            ua_appname=app_name,
            ua_url=app_url,
            ua_version=app_ver,
            compatibility_date="2020-01-01",
            tags=["Status"],
            spec_file=SPEC_PATH
        )
        cache.clear()
        expires = (
            timezone.now() + timedelta(minutes=5)
        ).strftime('%a, %d %b %Y %H:%M:%S %Z')

        send.return_value = httpx.Response(
            200,
            json={
                "players": 1234,
                "server_version": "1234",
                "start_time": "2029-09-19T11:02:08Z"
            },
            headers={
                "etag": etag,
                "expires": expires
            },
            request=httpx.Request(
                "GET",
                "test",
            ),
        )
        esi.client.Status.GetStatus().result()

        cache.delete(esi.client.Status.GetStatus()._cache_key())

        send.return_value = httpx.Response(
            304,
            headers={
                "etag": etag,
                "expires": expires
            },
            request=httpx.Request(
                "GET",
                "test",
            ),
        )
        with self.assertRaises(HTTPNotModified):
            esi.client.Status.GetStatus().result()
