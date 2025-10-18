# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import json

from six import string_types

from .base_resource import DDObject


def get_asset_name(what):
    if what is None:
        return None
    elif hasattr(what, "name"):
        return what.name
    elif isinstance(what, string_types):
        return what
    else:
        raise ValueError("Don't know how to get asset name from %s" % what)


class Asset(DDObject):
    """
    Attributes:
       name: Name of the asset
       category: Category of the asset. Currently supported value is ``model``
    """

    def __init__(self, json=None, **kwargs):
        # Creates a asset.
        #
        #         Args:
        #             name (:obj:`string`): The name of the asset.
        #             category: The category of the asset. Currently supported value is
        #                 ``model``
        #             json (:obj:`dict`): The dict describing the asset.
        #             **kwargs (optional): kwargs to override scenario attributes.
        #                 Attributes specified here will override those of ``desc``.
        authorized_properties = ["name", "category"]
        super(Asset, self).__init__(
            json=json, authorized_properties=authorized_properties, **kwargs
        )
