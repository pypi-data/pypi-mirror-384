import json
from typing import Any, Dict
from unittest import TestCase
from unittest.mock import patch

import click
import requests

import montecarlodata.settings as settings
from montecarlodata.common.data import MonolithResponse
from montecarlodata.config import Config
from montecarlodata.utils import GqlWrapper

_SAMPLE_ID = "1234"
_SAMPLE_TOKEN = "5678"
_SAMPLE_ENDPOINT = "graphql"
_SAMPLE_QUERY = "foo"
_SAMPLE_SERVICE = "test"
_SAMPLE_VARIABLES = {"bar": "qux"}
_SAMPLE_RESPONSE = {"data": "foo"}
_SAMPLE_ERRORS = {"errors": "error"}
_SAMPLE_CONFIG = Config(
    mcd_id=_SAMPLE_ID, mcd_token=_SAMPLE_TOKEN, mcd_api_endpoint=_SAMPLE_ENDPOINT
)

_SAMPLE_GQL_RAW_VARS = {"bar_qux": "foo"}
_SAMPLE_GQL_TRANSFORMED_VARS = {"barQux": "foo"}
_SAMPLE_GQL_OP_NAME = "operation"
_SAMPLE_GQL_DATA = {"foo": "bar"}
_SAMPLE_GOOD_GQL_RESPONSE = {"data": {_SAMPLE_GQL_OP_NAME: _SAMPLE_GQL_DATA}}
_SAMPLE_BAD_GQL_RESPONSE = {"errors": [{"message": "API is broken"}]}


class MockGoodRequest:
    text = json.dumps(_SAMPLE_RESPONSE)

    @staticmethod
    def raise_for_status():
        return False


class MockBadRequest:
    text = json.dumps(_SAMPLE_RESPONSE)

    @staticmethod
    def raise_for_status():
        raise requests.exceptions.HTTPError


class MockServerErrorRequest:
    status_code = 500
    text = json.dumps(_SAMPLE_RESPONSE)

    @staticmethod
    def raise_for_status():
        raise requests.exceptions.HTTPError("500 Server Error")


class MockBadGatewayRequest:
    status_code = 502
    text = json.dumps(_SAMPLE_RESPONSE)

    @staticmethod
    def raise_for_status():
        raise requests.exceptions.HTTPError("502 Bad Gateway")


class MockGatewayTimeoutRequest:
    status_code = 504
    text = json.dumps(_SAMPLE_RESPONSE)

    @staticmethod
    def raise_for_status():
        raise requests.exceptions.HTTPError("504 Gateway Timeout")


class MockGqlErrors(MockGoodRequest):
    text = json.dumps({**_SAMPLE_RESPONSE, **_SAMPLE_ERRORS})


class GqlUtilTest(TestCase):
    def setUp(self) -> None:
        self._service = GqlWrapper(_SAMPLE_CONFIG, command_name="test")

    def tearDown(self) -> None:
        self._service._abort_on_error = True
        settings.MCD_USER_ID_HEADER = None

    @patch.object(GqlWrapper, "_post", return_value=MockGoodRequest)
    def test_make_request(self, request_mock):
        self.assertEqual(
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            ),
            _SAMPLE_RESPONSE["data"],
        )
        request_mock.assert_called_once_with(**self._build_request())

    @patch.object(GqlWrapper, "_post", return_value=MockBadRequest)
    def test_request_with_status(self, request_mock):
        self._test_error_flow(request_mock)

    @patch.object(GqlWrapper, "_post", side_effect=requests.exceptions.ConnectionError)
    def test_request_with_connection_error(self, request_mock):
        self._test_error_flow(request_mock)

    @patch.object(GqlWrapper, "_post", side_effect=requests.exceptions.Timeout)
    def test_request_with_timeout(self, request_mock):
        self._test_error_flow(request_mock)

    @patch.object(GqlWrapper, "_post", return_value=MockGqlErrors)
    def test_request_with_gql_errors(self, request_mock):
        self._test_error_flow(request_mock)

    @patch("requests.post")
    def test_request_with_500_error_retries(self, post_mock):
        post_mock.side_effect = [
            MockServerErrorRequest(),
            MockServerErrorRequest(),
            MockServerErrorRequest(),
        ]
        with self.assertRaises(click.exceptions.Abort):
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            )
        # Verify it was called 3 times (initial + 2 retries)
        self.assertEqual(post_mock.call_count, 3)

    @patch("requests.post")
    def test_request_with_502_error_retries(self, post_mock):
        post_mock.side_effect = [
            MockBadGatewayRequest(),
            MockBadGatewayRequest(),
            MockBadGatewayRequest(),
        ]
        with self.assertRaises(click.exceptions.Abort):
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            )
        # Verify it was called 3 times (initial + 2 retries)
        self.assertEqual(post_mock.call_count, 3)

    @patch("requests.post")
    def test_request_with_504_error_retries(self, post_mock):
        post_mock.side_effect = [
            MockGatewayTimeoutRequest(),
            MockGatewayTimeoutRequest(),
            MockGatewayTimeoutRequest(),
        ]
        with self.assertRaises(click.exceptions.Abort):
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            )
        # Verify it was called 3 times (initial + 2 retries)
        self.assertEqual(post_mock.call_count, 3)

    @patch.object(GqlWrapper, "_post", return_value=MockGoodRequest)
    def test_make_request_with_user_id(self, request_mock):
        user_id = "thor"
        settings.MCD_USER_ID_HEADER = user_id
        self.assertEqual(
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            ),
            _SAMPLE_RESPONSE["data"],
        )
        request_mock.assert_called_once_with(
            headers={"user-id": user_id},
            payload={
                "query": _SAMPLE_QUERY,
                "variables": _SAMPLE_VARIABLES,
            },
        )

    @patch.object(GqlWrapper, "_make_request", return_value=_SAMPLE_GOOD_GQL_RESPONSE)
    def test_make_request_v2(self, request_mock):
        self.assertEqual(
            self._service.make_request_v2(
                query=_SAMPLE_QUERY,
                operation=_SAMPLE_GQL_OP_NAME,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_GQL_RAW_VARS,
            ),
            MonolithResponse(data=_SAMPLE_GQL_DATA, errors=None),
        )
        request_mock.assert_called_once_with(
            query=_SAMPLE_QUERY,
            service=_SAMPLE_SERVICE,
            variables=_SAMPLE_GQL_TRANSFORMED_VARS,
        )

    @patch.object(GqlWrapper, "_make_request", return_value=_SAMPLE_BAD_GQL_RESPONSE)
    def test_make_request_v2_with_errors(self, request_mock):
        with self.assertRaises(click.exceptions.Abort):
            self._service.make_request_v2(
                query=_SAMPLE_QUERY,
                operation=_SAMPLE_GQL_OP_NAME,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_GQL_RAW_VARS,
            )
            request_mock.assert_called_once_with(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_GQL_TRANSFORMED_VARS,
            )

    @patch.object(GqlWrapper, "_make_request", return_value=_SAMPLE_BAD_GQL_RESPONSE)
    def test_make_request_v2_with_skipped_errors(self, request_mock):
        self._service._abort_on_error = False
        self.assertEqual(
            self._service.make_request_v2(
                query=_SAMPLE_QUERY,
                operation=_SAMPLE_GQL_OP_NAME,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_GQL_RAW_VARS,
            ),
            MonolithResponse(data=None, errors=_SAMPLE_BAD_GQL_RESPONSE["errors"]),
        )
        request_mock.assert_called_once_with(
            query=_SAMPLE_QUERY,
            service=_SAMPLE_SERVICE,
            variables=_SAMPLE_GQL_TRANSFORMED_VARS,
        )

    def _test_error_flow(self, request_mock: Any):
        with self.assertRaises(click.exceptions.Abort):
            self._service.make_request(
                query=_SAMPLE_QUERY,
                service=_SAMPLE_SERVICE,
                variables=_SAMPLE_VARIABLES,
            )
        request_mock.assert_called_once_with(**self._build_request())

    def test_convert_snakes_to_camels(self):
        snakes = {
            "foo_bar": "test1",
            "qux": "test2",
            "baz_quux_quuz": "test3",
            "baz": {"quux_quuz": "test4"},
        }
        expected_camel = {
            "bazQuuxQuuz": "test3",
            "fooBar": "test1",
            "qux": "test2",
            "baz": {"quuxQuuz": "test4"},
        }
        self.assertDictEqual(self._service.convert_snakes_to_camels(snakes), expected_camel)

    @staticmethod
    def _build_request(
        *,
        query: str = _SAMPLE_QUERY,
        service: str = _SAMPLE_SERVICE,
        variables: Dict = _SAMPLE_VARIABLES,
    ):
        return {
            "headers": {
                "x-mcd-id": _SAMPLE_ID,
                "x-mcd-token": _SAMPLE_TOKEN,
                "x-mcd-telemetry-reason": "cli",
                "x-mcd-telemetry-service": service,
                "x-mcd-telemetry-command": "test",
                "Content-Type": "application/json",
            },
            "payload": {
                "query": query,
                "variables": variables,
            },
        }
