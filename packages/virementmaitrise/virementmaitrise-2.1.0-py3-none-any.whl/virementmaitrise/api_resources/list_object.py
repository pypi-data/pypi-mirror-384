from .. import util
from ..fintecture_object import FintectureObject
from urllib.parse import quote_plus


class ListObject(FintectureObject):
    OBJECT_NAME = "list"

    def list(self, app_id=None, fintecture_version=None, **params):
        return self._request(
            "get",
            self.get("url"),
            app_id=app_id,
            fintecture_version=fintecture_version,
            params=params,
        )

    def create(self, app_id=None, fintecture_version=None, **params):
        return self._request(
            "post",
            self.get("url"),
            app_id=app_id,
            fintecture_version=fintecture_version,
            params=params,
        )

    def retrieve(self, id, app_id=None, fintecture_version=None, **params):
        url = "%s/%s" % (self.get("url"), quote_plus(util.utf8(id)))
        return self._request(
            "get",
            url,
            app_id=app_id,
            fintecture_version=fintecture_version,
            params=params,
        )

    def __getitem__(self, k):
        if isinstance(k, str):
            return super(ListObject, self).__getitem__(k)
        else:
            raise KeyError(
                "You tried to access the %s index, but ListObject types only "
                "support string keys. (HINT: List calls return an object with "
                "a 'data' (which is the data array). You likely want to call "
                ".data[%s])" % (repr(k), repr(k))
            )

    def __iter__(self):
        return getattr(self, "data", []).__iter__()

    def __len__(self):
        return getattr(self, "data", []).__len__()

    def __reversed__(self):
        return getattr(self, "data", []).__reversed__()

    def auto_paging_iter(self):
        page = self

        while True:
            if (
                "ending_before" in self._retrieve_params
                and "starting_after" not in self._retrieve_params
            ):
                for item in reversed(page):
                    yield item
                page = page.previous_page()
            else:
                for item in page:
                    yield item
                page = page.next_page()

            if page.is_empty:
                break

    @classmethod
    def empty_list(cls, app_id=None, fintecture_version=None):
        return cls.construct_from(
            {"data": []},
            app_id=app_id,
            fintecture_version=fintecture_version,
            last_response=None,
        )

    @property
    def is_empty(self):
        return not self.data

    def next_page(self, app_id=None, fintecture_version=None, **params):
        if not self.has_more:
            return self.empty_list(
                app_id=app_id,
                fintecture_version=fintecture_version,
            )

        last_id = self.data[-1].id

        params_with_filters = self._retrieve_params.copy()
        params_with_filters.update({"starting_after": last_id})
        params_with_filters.update(params)

        return self.list(
            app_id=app_id,
            fintecture_version=fintecture_version,
            **params_with_filters,
        )

    def previous_page(self, app_id=None, fintecture_version=None, **params):
        if not self.has_more:
            return self.empty_list(
                app_id=app_id,
                fintecture_version=fintecture_version,
            )

        first_id = self.data[0].id

        params_with_filters = self._retrieve_params.copy()
        params_with_filters.update({"ending_before": first_id})
        params_with_filters.update(params)

        return self.list(
            app_id=app_id,
            fintecture_version=fintecture_version,
            **params_with_filters,
        )
