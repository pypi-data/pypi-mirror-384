# File generated from our OpenAPI spec

from .. import util
from .abstract import APIResourceTestHelpers
from .abstract import CreateableAPIResource
from .abstract import test_helpers


@test_helpers
class Refund(
    CreateableAPIResource,
):
    OBJECT_NAME = "refund"

    @classmethod
    def class_url(cls):
        return "/pis/v2/refund"

    @classmethod
    def list_for_payment(cls, session_id, **params):
        return cls._static_request(
            "get",
            "/pis/v2/payments/{session_id}/refunds".format(
                session_id=util.sanitize_id(session_id)
            ),
            params=params,
        )

    class TestHelpers(APIResourceTestHelpers):
        @classmethod
        def _cls_expire(
            cls, refund, app_id=None, fintecture_version=None, **params
        ):
            return cls._static_request(
                "post",
                "/v1/test_helpers/refunds/{refund}/expire".format(
                    refund=util.sanitize_id(refund)
                ),
                app_id=app_id,
                fintecture_version=fintecture_version,
                params=params,
            )

        @util.class_method_variant("_cls_expire")
        def expire(self, **params):
            return self.resource._request(
                "post",
                "/v1/test_helpers/refunds/{refund}/expire".format(
                    refund=util.sanitize_id(self.resource.get("id"))
                ),
                params=params,
            )
