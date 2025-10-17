from ... import util
from .api_resource import APIResource
from urllib.parse import quote_plus


class DeletableAPIResource(APIResource):
    @classmethod
    def _cls_delete(cls, sid, **params):
        url = "%s/%s" % (cls.class_url(), quote_plus(util.utf8(sid)))
        return cls._static_request("delete", url, params=params)

    @util.class_method_variant("_cls_delete")
    def delete(self, **params):
        return self._request_and_refresh(
            "delete", self.instance_url(), params=params
        )
