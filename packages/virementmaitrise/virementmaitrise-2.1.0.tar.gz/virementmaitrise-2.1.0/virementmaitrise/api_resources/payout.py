# File generated from our OpenAPI spec

from .. import util
from .abstract import CreateableAPIResource
from .abstract import ListableAPIResource
from .abstract import UpdateableAPIResource


class Payout(
    CreateableAPIResource, ListableAPIResource, UpdateableAPIResource
):
    OBJECT_NAME = "payout"

    @classmethod
    def _cls_cancel(
        cls, payout, app_id=None, fintecture_version=None, **params
    ):
        return cls._static_request(
            "post",
            "/v1/payouts/{payout}/cancel".format(
                payout=util.sanitize_id(payout)
            ),
            app_id=app_id,
            fintecture_version=fintecture_version,
            params=params,
        )

    @util.class_method_variant("_cls_cancel")
    def cancel(self, **params):
        return self._request(
            "post",
            "/v1/payouts/{payout}/cancel".format(
                payout=util.sanitize_id(self.get("id"))
            ),
            params=params,
        )

    @classmethod
    def _cls_reverse(
        cls, payout, app_id=None, fintecture_version=None, **params
    ):
        return cls._static_request(
            "post",
            "/v1/payouts/{payout}/reverse".format(
                payout=util.sanitize_id(payout)
            ),
            app_id=app_id,
            fintecture_version=fintecture_version,
            params=params,
        )

    @util.class_method_variant("_cls_reverse")
    def reverse(self, **params):
        return self._request(
            "post",
            "/v1/payouts/{payout}/reverse".format(
                payout=util.sanitize_id(self.get("id"))
            ),
            params=params,
        )
