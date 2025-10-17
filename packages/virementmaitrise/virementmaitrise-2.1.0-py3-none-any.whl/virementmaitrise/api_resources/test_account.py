# File generated from our OpenAPI spec

from .abstract import ListableAPIResource
from .abstract import SearchableAPIResource


class TestAccount(
    ListableAPIResource,
    SearchableAPIResource,
):
    OBJECT_NAME = "testaccount"

    @classmethod
    def search(cls, *args, **kwargs):
        return cls._search(search_url="/res/v1/testaccounts", *args, **kwargs)
