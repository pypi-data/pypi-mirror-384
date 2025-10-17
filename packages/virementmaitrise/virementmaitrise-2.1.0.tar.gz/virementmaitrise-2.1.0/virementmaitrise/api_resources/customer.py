# File generated from our OpenAPI spec

from .abstract import CreateableAPIResource
from .abstract import DeletableAPIResource
from .abstract import ListableAPIResource
from .abstract import SearchableAPIResource
from .abstract import UpdateableAPIResource
from .account import Account
from .account_holder import AccountHolder


class Customer(
    CreateableAPIResource,
    DeletableAPIResource,
    ListableAPIResource,
    SearchableAPIResource,
    UpdateableAPIResource,
):
    OBJECT_NAME = "customer"

    @classmethod
    def get_accounts(cls, customer_id, **params):
        return Account.search_by_customer(customer_id)

    @classmethod
    def get_account_holders(cls, customer_id, **params):
        return AccountHolder.search_by_customer(customer_id)

    @classmethod
    def get_account_transactions(cls, customer_id, account_id, **params):
        return Account.search_transactions_by_customer_account(
            customer_id, account_id
        )

    @classmethod
    def delete(cls, customer_id, **params):
        return Account.delete(customer_id, params)

    @classmethod
    def class_url(cls):
        return "/ais/v1/customer"
