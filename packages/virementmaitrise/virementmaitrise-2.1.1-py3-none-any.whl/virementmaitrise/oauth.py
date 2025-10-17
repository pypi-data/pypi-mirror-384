import base64

# Get reference to SDK module (works for any package name)
import sys

sdk = sys.modules[__name__.split(".")[0]]
from . import api_requestor, error


class OAuth(object):

    @staticmethod
    def _set_app_params(params):
        if "app_id" in params and "app_secret" in params:
            return

        # Get values from SDK module
        app_id = sdk.app_id
        app_secret = sdk.app_secret

        no_params = False
        if app_id:
            params["app_id"] = app_id
        else:
            no_params = True

        if app_secret:
            params["app_secret"] = app_secret
        else:
            no_params = True

        if no_params:
            raise error.AuthenticationError(
                "No app_id and/or app_secret provided. Set them using: "
                "<package>.app_id = <APP-ID> and <package>.app_secret = <APP-SECRET>"
            )

    @staticmethod
    def ais_token(app_id=None, app_secret=None, **params):
        if app_id:
            params["app_id"] = app_id
        if app_secret:
            params["app_secret"] = app_secret
        OAuth._set_app_params(params)
        return sdk.AIS.oauth(params)

    @staticmethod
    def pis_token(app_id=None, app_secret=None, **params):
        if app_id:
            params["app_id"] = app_id
        if app_secret:
            params["app_secret"] = app_secret
        OAuth._set_app_params(params)
        return sdk.PIS.oauth(app_id, app_secret, **params)

    @staticmethod
    def refresh_token(app_id=None, app_secret=None, **params):
        if not params.get("refresh_token", False):
            raise error.InvalidRequestError(
                message="refresh_token parameter is required for refresh token",
                param="refresh_token",
            )

        if app_id:
            params["app_id"] = app_id
        if app_secret:
            params["app_secret"] = app_secret

        OAuth._set_app_params(params)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(
                base64.b64encode(
                    "{}:{}".format(
                        params["app_id"], params["app_secret"]
                    ).encode("utf-8")
                ).decode("utf-8")
            ),
        }

        params.update(
            {
                "grant_type": "refresh_token",
            }
        )
        requestor = api_requestor.APIRequestor(
            app_id=params["app_id"],
            app_secret=params["app_secret"],
        )

        response, _ = requestor.request(
            "post", "/oauth/refreshtoken", params, headers
        )
        return response.data
