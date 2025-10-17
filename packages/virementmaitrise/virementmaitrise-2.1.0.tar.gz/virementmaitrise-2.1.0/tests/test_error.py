# -*- coding: utf-8 -*-

from tests.conftest import sdk


class TestFintectureError(object):
    def test_formatting(self):
        err = sdk.error.FintectureError("öre")
        assert str(err) == "öre"

    def test_formatting_with_request_id(self):
        err = sdk.error.FintectureError("öre", headers={"x-request-id": "123"})
        assert str(err) == "Request 123: öre"

    def test_formatting_with_none(self):
        err = sdk.error.FintectureError(None, headers={"x-request-id": "123"})
        assert str(err) == "Request 123: <empty message>"

    def test_formatting_with_message_none_and_request_id_none(self):
        err = sdk.error.FintectureError(None)
        assert str(err) == "<empty message>"

    def test_repr(self):
        err = sdk.error.FintectureError("öre", headers={"x-request-id": "123"})
        assert (
            repr(err)
            == "FintectureError(message='öre', url=None, http_status=None, log_id=None, "
            "x_request_id='123', errors=None)"
        )

    def test_error_object(self):
        err = sdk.error.FintectureError(
            "message",
            json_body={
                "status": "477",
                "code": "invalid_test_code",
                "log_id": "2398-a872-323a-xxxx",
                "errors": [
                    {
                        "code": "some_invalid_code",
                        "title": "Title of test error",
                        "detail": "Details of test error with invalid code",
                    }
                ],
            },
        )
        assert err.error is not None
        assert err.error.code == "invalid_test_code"
        assert err.error.status == "477"
        assert len(err.error.errors) == 1
        assert err.error.errors[0].code == "some_invalid_code"

    def test_error_object_not_dict(self):
        err = sdk.error.FintectureError(
            "message", json_body={"error": "not a dict"}
        )
        assert err.error is None


class TestApiConnectionError(object):
    def test_default_no_retry(self):
        err = sdk.error.APIConnectionError("msg")
        assert err.should_retry is False

        err = sdk.error.APIConnectionError("msg", should_retry=True)
        assert err.should_retry
