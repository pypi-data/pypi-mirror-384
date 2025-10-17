from .api_resource import APIResource


class CreateableAPIResource(APIResource):
    @classmethod
    def create(cls, app_id=None, fintecture_version=None, **params):
        return cls._static_request(
            "post",
            cls.class_url(),
            app_id,
            fintecture_version,
            params,
        )
