# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import json

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

from contextlib import suppress


class NotBoundException(Exception):
    """The exception raised when a method that needs the object to be bound
    to a :class:`~Client` is called, but the object is not bound.

    An object is bound to a :class:`~Client` when it has been
    created with its ``client`` property set.
    """

    pass


class DDObject(object):
    """Base object for Decision service."""

    def __init__(self, json=None, client=None, authorized_properties=None, **kwargs):
        """
        Constructor
        """
        d = dict()
        d_user = dict()  # dictionnary with allowed properties only
        # set values from ``json`` then apply kwargs
        if json:
            d.update(json)
            if authorized_properties:
                self.get_dictionnary_without_unwanted_keys(
                    d, d_user, authorized_properties
                )
            else:
                d_user.update(json)
        d.update(**kwargs)
        d_user.update(**kwargs)
        super(DDObject, self).__setattr__("_json_internal", d)
        super(DDObject, self).__setattr__("json", d_user)
        super(DDObject, self).__setattr__(
            "_authorized_properties", authorized_properties
        )
        super(DDObject, self).__setattr__("_client", client)

    @property
    def client(self):
        if self._client:
            return self._client
        else:
            raise NotBoundException(
                "%s not bound to a DecisionOptimizationClient.Client. Please make an instance of %s from appropriate client API."
                % (type(self), type(self))
            )

    def get_dictionnary_without_unwanted_keys(
        self, dictionary, changed_dictionnary, keys
    ):
        for key in dictionary:
            if key in keys:
                if isinstance(dictionary[key], MutableMapping):
                    changed_dictionnary[key] = dict()
                    self.get_dictionnary_without_unwanted_keys(
                        dictionary[key], changed_dictionnary[key], keys
                    )
                else:
                    changed_dictionnary[key] = dictionary[key]

    def __setattr__(self, name, value):
        self.json[name] = value
        self._json_internal[name] = value

    def __repr__(self):
        return json.dumps(self.json, indent=3)

    def __getattr__(self, name):
        try:
            return self.json[name]
        except KeyError:
            return None

    def __getitem__(self, name):
        if isinstance(name, int):
            return getattr(json, name)
        else:
            return getattr(self, name)

    def __to_json(self, **kwargs):
        """Returns a string with the json for this object, using fields
        and value types that the API service understands.

        This is used to serialize the ``Scenario`` before a query to the REST
        API.
        """
        return json.dumps(self._json_internal, **kwargs)

    def to_json(self, **kwargs):
        """Returns a string with the json for this object, using fields
        and value types that the API service understands.

        This is used to serialize the ``Scenario`` before a query to the REST
        API.
        """
        return json.dumps(self.json, **kwargs)
