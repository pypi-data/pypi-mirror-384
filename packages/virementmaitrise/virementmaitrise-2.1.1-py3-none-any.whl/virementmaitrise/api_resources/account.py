# File generated from our OpenAPI spec

from .. import api_requestor, util
from ..fintecture_object import FintectureObject


class Account(FintectureObject):
    OBJECT_NAME = "account"

    @classmethod
    def _static_request(
        cls,
        method_,
        url_,
        app_id=None,
        fintecture_version=None,
        params=None,
    ):
        """Make a static HTTP request to the Fintecture API"""
        params = None if params is None else params.copy()
        fintecture_version = util.read_special_variable(
            params, "fintecture_version", fintecture_version
        )
        fintecture_app_id = util.read_special_variable(
            params, "app_id", app_id
        )
        fintecture_app_secret = util.read_special_variable(
            params, "app_secret", None
        )
        fintecture_private_key = util.read_special_variable(
            params, "private_key", None
        )
        headers = util.read_special_variable(params, "headers", None)

        requestor = api_requestor.APIRequestor(
            app_id=fintecture_app_id,
            app_secret=fintecture_app_secret,
            private_key=fintecture_private_key,
            api_version=fintecture_version,
        )

        response, my_app_id = requestor.request(method_, url_, params, headers)
        return util.convert_to_fintecture_object(
            response, my_app_id, fintecture_version, params
        )

    @classmethod
    def search_by_customer(cls, customer_id, **params):
        return cls._static_request(
            "get",
            "/ais/v1/customer/{}/accounts".format(customer_id),
            params=params,
        )

    @classmethod
    def search_transactions_by_customer_account(
        cls, customer_id, account_id, **params
    ):
        return cls._static_request(
            "get",
            "/ais/v1/customer/{}/accounts/{}/transactions".format(
                customer_id, account_id
            ),
            params=params,
        )

    @classmethod
    def retrieve_by_customer(cls, customer_id, account_id, **params):
        return cls._static_request(
            "get",
            "/ais/v1/customer/{}/accounts/{}".format(customer_id, account_id),
            params=params,
        )

    @classmethod
    def delete(cls, customer_id, **params):
        return cls._static_request(
            "delete",
            "/ais/v1/customer/{}".format(customer_id),
            params=params,
        )
