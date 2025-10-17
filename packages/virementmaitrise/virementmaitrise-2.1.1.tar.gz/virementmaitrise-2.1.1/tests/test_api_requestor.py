import datetime
from collections import OrderedDict

import pytest

from tests.conftest import sdk

VALID_API_METHODS = ("get", "post", "delete")


class GMT1(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "Europe/Prague"


class APIHeaderMatcher(object):
    EXP_KEYS = [
        "app_id",
        "Fintecture-Version",
        "User-Agent",
        "Accept",
    ]
    METHOD_EXTRA_KEYS = {"post": ["Content-Type"]}

    def __init__(
        self,
        app_id=None,
        extra={},
        request_method=None,
        user_agent=None,
        app_info=None,
        fail_platform_call=False,
    ):
        self.request_method = request_method
        self.app_id = app_id or sdk.app_id
        self.extra = extra
        self.user_agent = user_agent
        self.app_info = app_info
        self.fail_platform_call = fail_platform_call

    def __eq__(self, other):
        return (
            self._keys_match(other)
            and self._auth_match(other)
            and self._user_agent_match(other)
            and self._x_fintecture_ua_contains_app_info(other)
            and self._x_fintecture_ua_handles_failed_platform_function(other)
            and self._extra_match(other)
        )

    def __repr__(self):
        return (
            "APIHeaderMatcher(request_method=%s, app_id=%s, extra=%s, user_agent=%s, app_info=%s, fail_platform_call=%s)"
            % (
                repr(self.request_method),
                repr(self.app_id),
                repr(self.extra),
                repr(self.user_agent),
                repr(self.app_info),
                repr(self.fail_platform_call),
            )
        )

    def _keys_match(self, other):
        expected_keys = list(set(self.EXP_KEYS + list(self.extra.keys())))
        if (
            self.request_method is not None
            and self.request_method in self.METHOD_EXTRA_KEYS
        ):
            expected_keys.extend(self.METHOD_EXTRA_KEYS[self.request_method])
        return sorted(other.keys()) == sorted(expected_keys)

    def _auth_match(self, other):
        return other.get("app_id") == self.app_id

    def _user_agent_match(self, other):
        if self.user_agent is not None:
            return other["User-Agent"] == self.user_agent

        return True

    def _x_fintecture_ua_contains_app_info(self, other):
        # Fintecture doesn't use X-Fintecture-Client-User-Agent header
        return True

    def _x_fintecture_ua_handles_failed_platform_function(self, other):
        # Fintecture doesn't use X-Fintecture-Client-User-Agent header
        return True

    def _extra_match(self, other):
        for k, v in self.extra.items():
            if other[k] != v:
                return False

        return True


class QueryMatcher(object):
    def __init__(self, expected):
        self.expected = sorted(expected)

    def __eq__(self, other):
        query = other.split("?")[-1] if "?" in other else other
        parsed = sdk.util.parse_qsl(query)
        return self.expected == sorted(parsed)

    def __repr__(self):
        return "QueryMatcher(expected=%s)" % (repr(self.expected))


class TestAPIRequestor(object):
    valid_path = "/v1/test"

    ENCODE_INPUTS = {
        "dict": {
            "astring": "bar",
            "anint": 5,
            "adatetime": datetime.datetime(2013, 1, 1, tzinfo=GMT1()),
            "atuple": (1, 2),
            "adict": {"foo": "bar", "boz": 5},
            "alist": ["foo", "bar"],
        },
        "list": [1, "foo", "baz"],
        "string": "boo",
        "unicode": "\u1234",
        "datetime": datetime.datetime(2013, 1, 1, second=1, tzinfo=GMT1()),
    }

    ENCODE_EXPECTATIONS = {
        "dict": [
            ("%s[astring]", "bar"),
            ("%s[anint]", "5"),
            ("%s[adatetime]", "1356994800"),
            ("%s[atuple][0]", "1"),
            ("%s[atuple][1]", "2"),
            ("%s[adict][foo]", "bar"),
            ("%s[adict][boz]", "5"),
            ("%s[alist][0]", "foo"),
            ("%s[alist][1]", "bar"),
        ],
        "list": [("%s[0]", "1"), ("%s[1]", "foo"), ("%s[2]", "baz")],
        "string": [("%s", "boo")],
        "unicode": [("%s", "\u1234")],
        "datetime": [("%s", "1356994801")],
    }

    @pytest.fixture
    def requestor(self):
        return sdk.api_requestor.APIRequestor()

    @pytest.fixture
    def http_client(self, mocker):
        mock_client = mocker.Mock(spec=sdk.http_client.HTTPClient)
        mock_client.request_with_retries.return_value = ("{}", 200, {})
        # Patch the default http client
        mocker.patch.object(sdk, "default_http_client", mock_client)
        return mock_client

    @pytest.fixture
    def mock_response(self, http_client):
        def mock_response(res, code=200, headers={}):
            http_client.request_with_retries.return_value = (
                res,
                code,
                headers,
            )

        return mock_response

    @pytest.fixture
    def check_call(self, http_client):
        def check_call(
            method,
            abs_url=None,
            headers=None,
            post_data=None,
        ):
            if not abs_url:
                abs_url = "%s%s" % (sdk.api_base, self.valid_path)
            if not headers:
                headers = APIHeaderMatcher(request_method=method)

            http_client.request_with_retries.assert_called_with(
                method, abs_url, headers, post_data
            )

        return check_call

    def test_dictionary_list_encoding(self):
        params = {"foo": {"0": {"bar": "bat"}}}
        encoded = list(sdk.api_requestor._api_encode(params))
        key, value = encoded[0]

        assert key == "foo[0][bar]"
        assert value == "bat"

    def test_ordereddict_encoding(self):
        params = {
            "ordered": OrderedDict(
                [
                    ("one", 1),
                    ("two", 2),
                    ("three", 3),
                    ("nested", OrderedDict([("a", "a"), ("b", "b")])),
                ]
            )
        }
        encoded = list(sdk.api_requestor._api_encode(params))

        assert encoded[0][0] == "ordered[one]"
        assert encoded[1][0] == "ordered[two]"
        assert encoded[2][0] == "ordered[three]"
        assert encoded[3][0] == "ordered[nested][a]"
        assert encoded[4][0] == "ordered[nested][b]"

    def test_sets_default_http_client(self):
        assert isinstance(
            sdk.default_http_client,
            sdk.http_client.RequestsClient,
        )

    def test_fails_without_app_id(self, requestor):
        sdk.app_id = None

        with pytest.raises(sdk.error.AuthenticationError):
            requestor.request("get", self.valid_path, {})

    def test_invalid_method(self, requestor):
        with pytest.raises(sdk.error.APIConnectionError):
            requestor.request("foo", "bar")
