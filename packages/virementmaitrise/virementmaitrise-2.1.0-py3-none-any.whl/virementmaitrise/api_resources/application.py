from .abstract import SingletonAPIResource


class Application(SingletonAPIResource):
    OBJECT_NAME = "application"

    @classmethod
    def class_url(cls):
        return "/res/v1/applications"
