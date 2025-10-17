# File generated from our OpenAPI spec

from .abstract import CreateableAPIResource
from .abstract import DeletableAPIResource
from .abstract import ListableAPIResource
from .abstract import UpdateableAPIResource


class AccountHolder(
    CreateableAPIResource,
    DeletableAPIResource,
    ListableAPIResource,
    UpdateableAPIResource,
):
    OBJECT_NAME = "accountholder"

    @classmethod
    def search_by_customer(cls, customer_id, **params):
        return cls._static_request(
            "get",
            "/ais/v1/customer/{}/accountholders".format(customer_id),
            params=params,
        )
