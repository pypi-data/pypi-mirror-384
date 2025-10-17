# File generated from our OpenAPI spec

from .abstract import ListableAPIResource
from .abstract import SearchableAPIResource


class Provider(
    ListableAPIResource,
    SearchableAPIResource,
):
    OBJECT_NAME = "provider"

    @classmethod
    def search(cls, *args, **kwargs):
        return cls._search(search_url="/res/v1/providers", *args, **kwargs)

    @classmethod
    def search_auto_paging_iter(cls, *args, **kwargs):
        return cls.search(*args, **kwargs).auto_paging_iter()
