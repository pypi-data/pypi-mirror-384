import datetime
import json
from copy import deepcopy

# Get reference to SDK module (works for any package name)
import sys

sdk = sys.modules[__name__.split(".")[0]]
from . import api_requestor, util


def _compute_diff(current, previous):
    if isinstance(current, dict):
        previous = previous or {}
        diff = current.copy()
        for key in set(previous.keys()) - set(diff.keys()):
            diff[key] = ""
        return diff
    return current if current is not None else ""


def _serialize_list(array, previous):
    array = array or []
    previous = previous or []
    params = {}

    for i, v in enumerate(array):
        previous_item = previous[i] if len(previous) > i else None
        if hasattr(v, "serialize"):
            params[str(i)] = v.serialize(previous_item)
        else:
            params[str(i)] = _compute_diff(v, previous_item)

    return params


class FintectureObject(dict):

    class ReprJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return api_requestor._encode_datetime(obj)
            return super(FintectureObject.ReprJSONEncoder, self).default(obj)

    def __init__(
        self,
        id=None,
        app_id=None,
        fintecture_version=None,
        last_response=None,
        **params,
    ):
        super(FintectureObject, self).__init__()

        self.app_id = app_id

        self._unsaved_values = set()
        self._transient_values = set()
        self._last_response = last_response

        self._retrieve_params = params
        self._previous = None

        object.__setattr__(self, "app_id", app_id)
        object.__setattr__(self, "fintecture_version", fintecture_version)

        if id:
            self["id"] = id

    @property
    def last_response(self):
        return self._last_response

    def update(self, update_dict):
        for k in update_dict:
            self._unsaved_values.add(k)

        return super(FintectureObject, self).update(update_dict)

    def __setattr__(self, k, v):
        if k[0] == "_" or k in self.__dict__:
            return super(FintectureObject, self).__setattr__(k, v)

        self[k] = v
        return None

    def __getattr__(self, k):
        if k[0] == "_":
            raise AttributeError(k)

        try:
            return self[k]
        except KeyError as err:
            raise AttributeError(*err.args)

    def __delattr__(self, k):
        if k[0] == "_" or k in self.__dict__:
            return super(FintectureObject, self).__delattr__(k)
        else:
            del self[k]

    def __setitem__(self, k, v):
        if v == "":
            raise ValueError(
                "You cannot set %s to an empty string on this object. "
                "The empty string is treated specially in our requests. "
                "If you'd like to delete the property using the save() method on this object, you may set %s.%s=None. "
                "Alternatively, you can pass %s='' to delete the property when using a resource method such as modify()."
                % (k, str(self), k, k)
            )

        # Allows for unpickling in Python 3.x
        if not hasattr(self, "_unsaved_values"):
            self._unsaved_values = set()

        self._unsaved_values.add(k)

        super(FintectureObject, self).__setitem__(k, v)

    def __getitem__(self, k):
        try:
            return super(FintectureObject, self).__getitem__(k)
        except KeyError as err:
            if k in self._transient_values:
                raise KeyError(
                    "%r.  HINT: The %r attribute was set in the past."
                    "It was then wiped when refreshing the object with "
                    "the result returned by Fintecture's API, probably as a "
                    "result of a save().  The attributes currently "
                    "available on this object are: %s"
                    % (k, k, ", ".join(list(self.keys())))
                )
            else:
                raise err

    def __delitem__(self, k):
        super(FintectureObject, self).__delitem__(k)

        # Allows for unpickling in Python 3.x
        if hasattr(self, "_unsaved_values") and k in self._unsaved_values:
            self._unsaved_values.remove(k)

    # Custom unpickling method that uses `update` to update the dictionary
    # without calling __setitem__, which would fail if any value is an empty
    # string
    def __setstate__(self, state):
        self.update(state)

    # Custom pickling method to ensure the instance is pickled as a custom
    # class and not as a dict, otherwise __setstate__ would not be called when
    # unpickling.
    def __reduce__(self):
        reduce_value = (
            type(self),  # callable
            (  # args
                self.get("id", None),
                self.app_id,
                self.fintecture_version,
            ),
            dict(self),  # state
        )
        return reduce_value

    @classmethod
    def construct_from(
        cls,
        values,
        app_id,
        fintecture_version=None,
        last_response=None,
    ):
        instance = cls(
            values.get("id"),
            app_id=app_id,
            fintecture_version=fintecture_version,
            last_response=last_response,
        )
        instance.refresh_from(
            values,
            app_id=app_id,
            fintecture_version=fintecture_version,
            last_response=last_response,
        )
        return instance

    def refresh_from(
        self,
        values,
        app_id=None,
        fintecture_version=None,
        last_response=None,
    ):
        self.app_id = app_id or getattr(values, "app_id", None)
        self.fintecture_version = fintecture_version or getattr(
            values, "fintecture_version", None
        )
        self._last_response = last_response or getattr(
            values, "_last_response", None
        )

        removed = set(self.keys()) - set(values)
        self._transient_values = self._transient_values | removed
        self._unsaved_values = set()
        self.clear()

        self._transient_values = self._transient_values - set(values)

        for k, v in values.items():
            super(FintectureObject, self).__setitem__(
                k,
                util.convert_to_fintecture_object(
                    v, app_id, fintecture_version
                ),
            )

        self._previous = values

    @classmethod
    def api_base(cls):
        return None

    def request(self, method, url, params=None, headers=None):
        return FintectureObject._request(
            self, method, url, headers=headers, params=params
        )

    # The `method_` and `url_` arguments are suffixed with an underscore to
    # avoid conflicting with actual request parameters in `params`.
    def _request(
        self,
        method_,
        url_,
        app_id=None,
        fintecture_version=None,
        headers=None,
        params=None,
    ):
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
        headers = util.read_special_variable(params, "headers", headers)

        fintecture_version = fintecture_version or self.fintecture_version

        fintecture_app_id = fintecture_app_id or self.app_id
        params = params or self._retrieve_params

        requestor = api_requestor.APIRequestor(
            app_id=fintecture_app_id,
            app_secret=fintecture_app_secret,
            private_key=fintecture_private_key,
            api_base=self.api_base(),
            api_version=fintecture_version,
        )

        response, my_app_id = requestor.request(method_, url_, params, headers)

        return util.convert_to_fintecture_object(
            response, my_app_id, fintecture_version, params
        )

    def __repr__(self):
        ident_parts = [type(self).__name__]

        if isinstance(self.get("object"), str):
            ident_parts.append(self.get("object"))

        if isinstance(self.get("id"), str):
            ident_parts.append("id=%s" % (self.get("id"),))

        repr_str = "<%s at %s> JSON: %s" % (
            " ".join(ident_parts),
            hex(id(self)),
            str(self),
        )

        return repr_str

    def __str__(self):
        return json.dumps(
            self.to_dict_recursive(),
            sort_keys=True,
            indent=2,
            cls=self.ReprJSONEncoder,
        )

    def to_dict(self):
        return dict(self)

    def to_dict_recursive(self):
        def maybe_to_dict_recursive(value):
            if value is None:
                return None
            elif isinstance(value, FintectureObject):
                return value.to_dict_recursive()
            else:
                return value

        return {
            key: (
                list(map(maybe_to_dict_recursive, value))
                if isinstance(value, list)
                else maybe_to_dict_recursive(value)
            )
            for key, value in dict(self).items()
        }

    @property
    def fintecture_id(self):
        return self.id

    def serialize(self, previous):
        params = {}
        unsaved_keys = self._unsaved_values or set()
        previous = previous or self._previous or {}

        for k, v in self.items():
            if k == "id" or (isinstance(k, str) and k.startswith("_")):
                continue
            elif isinstance(v, sdk.api_resources.abstract.APIResource):
                continue
            elif hasattr(v, "serialize"):
                child = v.serialize(previous.get(k, None))
                if child != {}:
                    params[k] = child
            elif k in unsaved_keys:
                params[k] = _compute_diff(v, previous.get(k, None))
            elif k == "additional_owners" and v is not None:
                params[k] = _serialize_list(v, previous.get(k, None))

        return params

    # This class overrides __setitem__ to throw exceptions on inputs that it
    # doesn't like. This can cause problems when we try to copy an object
    # wholesale because some data that's returned from the API may not be valid
    # if it was set to be set manually. Here we override the class' copy
    # arguments so that we can bypass these possible exceptions on __setitem__.
    def __copy__(self):
        copied = FintectureObject(
            self.get("id"),
            self.app_id,
            fintecture_version=self.fintecture_version,
        )

        copied._retrieve_params = self._retrieve_params

        for k, v in self.items():
            # Call parent's __setitem__ to avoid checks that we've added in the
            # overridden version that can throw exceptions.
            super(FintectureObject, copied).__setitem__(k, v)

        return copied

    # This class overrides __setitem__ to throw exceptions on inputs that it
    # doesn't like. This can cause problems when we try to copy an object
    # wholesale because some data that's returned from the API may not be valid
    # if it was set to be set manually. Here we override the class' copy
    # arguments so that we can bypass these possible exceptions on __setitem__.
    def __deepcopy__(self, memo):
        copied = self.__copy__()
        memo[id(self)] = copied

        for k, v in self.items():
            # Call parent's __setitem__ to avoid checks that we've added in the
            # overridden version that can throw exceptions.
            super(FintectureObject, copied).__setitem__(k, deepcopy(v, memo))

        return copied
