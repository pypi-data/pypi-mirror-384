# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------


import json
import os
import threading
import warnings

import requests
from six import string_types

try:
    from urllib import urlencode
except ImportError:
    # py3
    from urllib.parse import urlencode

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import time

from decision_optimization_client.experiment import Experiment, get_experiment_id
from six import iteritems

from .asset import Asset, get_asset_name
from .container import Container, get_container_id
from .proxyUtils import CallWithToken
from .solve import SolveConfig, SolveStatus
from .table import Table, TableType, get_table_name
from .token import Token

content_json = {"Content-Type": "application/json"}
content_octet_stream = {
    "Content-Type": "application/octet-stream",
    "Content-Encoding": "identity",
}
content_csv = {"Content-Type": "text/csv"}
accept_csv = {"Content-Type": "application/json", "Accept": "text/csv"}


def display_headers(session, headers=None):
    h = {}
    h.update(session.headers)
    h.update(headers)
    print(json.dumps(h, indent=3))


class DDException(Exception):
    """The base exception for the Decision Optimization client.

    Attributes:
        errors: A list of errors as [{'code': code, 'message': message}]
        trace: The trace id
        message: a string representation of the errors
    """

    def __init__(self, json_def):
        self.errors = json_def["errors"]
        self.trace = json_def.get("trace")
        super(DDException, self).__init__(self.message)

    @property
    def message(self):
        m = [("%s:%s" % (x["code"], x["message"])) for x in self.errors]
        return "\n".join(m)


class DDClientException(Exception):
    """Generic client exception"""

    pass


class MCSPIAMAuthHandler(object):
    def __init__(self, apikey):
        self.apikey = apikey

    def get_authorization(self, iam_url=None):

        if iam_url is None:
            from ibm_watson_studio_lib.impl.environment import environ

            ys1 = False
            storefront = environ.get("RUNTIME_ENV_STOREFRONT", None)
            if storefront:
                ys1 = storefront in ["aws/staging"]
            iam_url = (
                "https://account-iam.platform.saas.ibm.com/api/2.0/apikeys/token"
                if not ys1
                else "https://account-iam.platform.test.saas.ibm.com/api/2.0/apikeys/token"
            )
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Mcsp-ApiKey": self.apikey,
        }
        r = requests.post(iam_url, headers=headers)
        if r.status_code == 200:
            iam_info = json.loads(
                r.content.decode(r.encoding if r.encoding else "utf-8")
            )
            if not "token" in iam_info:
                raise DDClientException("Could not request token from MCSP IAM server")
            return [iam_info["token"], None, iam_url]
        else:
            r.raise_for_status()


class IAMAuthHandler(object):
    def __init__(self, apikey):
        self.apikey = apikey

    def get_authorization(self, iam_url=None):

        if iam_url is None:
            from ibm_watson_studio_lib.impl.environment import determine_iam_endpoint

            iam_url = determine_iam_endpoint()
        headers = {
            "Authorization": "Basic Yng6Yng=",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "cache-control": "no-cache",
        }
        data = "grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey={apikey}&response_type=cloud_iam".format(
            apikey=self.apikey
        )
        r = requests.post(iam_url, headers=headers, data=data)
        if r.status_code == 200:
            iam_info = json.loads(
                r.content.decode(r.encoding if r.encoding else "utf-8")
            )
            if not "access_token" in iam_info:
                raise DDClientException(
                    "Could not request access_token from IAM server"
                )
            return [iam_info["access_token"], iam_info["refresh_token"], iam_url]
        else:
            r.raise_for_status()


class Client(object):
    """The class to access Experiments in Decision Optimization.

    To use the client in Cloud Pak For Data::

        from decision_optimization_client import Client
        client = Client()

    To use the client in Cloud Pak For Data as a Service::

        from decision_optimization_client import Client
        client = Client(wslib=wslib) # with wslib being the ibm-watson-studio-lib context

    or if you want to access another project::

        from decision_optimization_client import Client
        client = Client(project_id="project id string",
                        authorization="bearer authorization token")

    Then use the following method to retrieve one or more experiments:

        * :meth:`~decision_optimization_client.Client.get_experiment`
        * :meth:`~decision_optimization_client.Client.get_experiments`

    Example:
        To return the list of experiments::

            from decision_optimization_client import Client

            client = Client()
            # get list of available experiments
            containers = client.get_experiments()
    """

    def __init__(
        self,
        api_url=None,
        authorization=None,
        refresh_token=None,
        project_id=None,
        max_retries=3,
        proxies=None,
        cognitive_url=None,
        pc=None,
        wslib=None,
        apikey=None,
        verify=None,
        iam_url=None,
    ):
        """Creates a new Decision Optimization scenario client.

        Args:
            authorization (:obj:`str`, optional): The authorization key (to set the value of the bearer token (that you get from your api key when using iam).
            max_retries (:obj:`int`, optional): maximum number of retries.
                Default is 3.
            proxies (:obj:`dict`, optional): Optional dictionary mapping
                protocol to the URL of the proxy. (more info: https://docs.python-requests.org/en/master/user/advanced/#proxies)
            wslib (:obj:`object`, mandatory in Cloud Pak for Data notebooks): ibm-watson-studio-lib context
            apikey (:obj:`str`, optional): IAM api key
            verify (:obj:`boolean`, optional): override http's verify property
        """
        self.api_url = api_url
        if self.api_url is None:
            from ibm_watson_studio_lib.impl.environment import determine_api_url

            self.api_url = "%s/v2" % determine_api_url()

        # legacy support for apikey which is not necessary anymore
        if apikey:
            # apikey is an IAM apikey, request for a token
            auth_handler = (
                MCSPIAMAuthHandler(apikey)
                if "aws" in self.api_url
                else IAMAuthHandler(apikey)
            )
            authorizations = auth_handler.get_authorization(iam_url)
            authorization = authorizations[0]
            refresh_token = authorizations[1]
            iam_url = authorizations[2]
        # at this point, if api_url has not been guessed, use a default
        # value suitable for use with DSX
        self.cognitive_url = (
            cognitive_url
            if cognitive_url is not None
            else "https://internal-nginx-svc:12443/v1/cognitive"
        )
        # Create session
        self.session = requests.Session()
        # mount custom adapters for http and https for this session
        hta = requests.adapters.HTTPAdapter
        self.session.mount("http://", hta(max_retries=max_retries))
        self.session.mount("https://", hta(max_retries=max_retries))
        if verify is not None:
            self.session.verify = verify
        # Relay authorization token
        token = ""
        token_file = None
        self.token_file = None
        if authorization:
            token = authorization
            refresh_token = refresh_token
        elif wslib:
            token = wslib.auth.get_current_token()
            refresh_token = None
        elif pc:
            raise RuntimeError(
                f"project-lib and associated 'pc' parameter are no more supported. You should migrate to ibm-watson-studio-lib and 'wslib' parameter."
            )
        else:
            raise RuntimeError(f"Missing authorization or wslib parameter.")
        self._call = CallWithToken(
            Token(token, refresh_token, iam_url, wslib),
            lambda r: r.status_code == 401,
            session=self.session,
        )
        # bearer = "Bearer"
        # if bearer != token[:len(bearer)]:
        #    token = "%s %s" % (bearer, token)
        # self.session.headers.update({'Authorization': token})
        self.project_id = project_id
        if self.project_id is None and wslib:
            self.project_id = wslib.here.get_ID()
        # proxies
        if proxies is not None:
            self.session.proxies.update(proxies)
        self.lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        # Closes this client and frees up used resources.
        self.session.close()

    def _check_status(self, response, ok_status):
        # Checks that the request is performed correctly. '''
        if not (response.status_code in ok_status):
            # if the error already has a corresponding exception in the HTTP
            # lib, just raise it
            raise_this = None
            try:
                j = response.json()
                if "errors" in j:
                    raise DDException(j)
            except DDException:
                raise
            except ValueError:  # no json
                pass
            response.raise_for_status()
            raise RuntimeError("%s: %s" % (response.status_code, response.reason))

    def get_containers(self, parent_id, category=None):
        # Returns the list of containers.
        #
        # Container type include:
        #
        #     * ``scenario``
        #     * ``inputset``
        #     * ``model``
        #
        # Args:
        #     parent_id: The parent_id
        #     category: The container category.
        # Returns:
        #     a list of :class:`~decision_optimization_client.Container`
        type_sel = "&category=%s" % category if category else ""
        url = "{api_url}/containers?projectId={pid}&parentId={parent}{type_sel}".format(
            api_url=self.api_url,
            pid=self.project_id,
            parent=parent_id,
            type_sel=type_sel,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        containers_as_json = response.json()
        return [
            Container(parent_id=parent_id, json=s, client=self)
            for s in containers_as_json
        ]

    def create_container(self, parent_id, container):
        # Creates a container.
        #
        # Args:
        #     container (:class:`~decision_optimization_client.Container`): The container metadata
        # Returns:
        #     The container.
        if getattr(container, "projectId") == None:
            container.projectId = self.project_id
        url = "{api_url}/containers?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            pid=self.project_id,
            parent=parent_id,
        )
        response = self._call.POST(
            url, headers=content_json, data=container._DDObject__to_json()
        )
        self._check_status(response, [201])
        container_as_json = response.json()
        return Container(parent_id=parent_id, json=container_as_json, client=self)

    def get_container(self, parent_id, id):
        #  Returns the container metadata.
        #
        # Args:
        #     id: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        # Returns:
        #     a list of :class:`~decision_optimization_client.Container`
        sid = get_container_id(id)
        url = "{api_url}/containers/{container_id}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=sid,
            pid=self.project_id,
            parent=parent_id,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        container_as_json = response.json()
        return Container(parent_id=parent_id, json=container_as_json, client=self)

    def update_container(self, container, new_data):
        #  Updates container metadata.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container`. This ``container`` is used to indicate which container
        #        is to be updated. If ``new_data`` is None, the container is
        #        updated with the data from this ``container``.
        #     new_data (:class:`~decision_optimization_client.Container`, optional): A
        #        :class:`~decision_optimization_client.Container` containing metadata to update.
        sid = get_container_id(container)
        url = "{api_url}/containers/{container_id}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=sid,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(
            url,
            headers=content_json,
            data=new_data._DDObject__to_json(),
            allow_redirects=False,
        )
        self._check_status(response, [200, 301])

    def delete_container(self, container):
        # Deletes the container.
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        sid = get_container_id(container)
        url = "{api_url}/containers/{container_id}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=sid,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def delete_containers(self, parent_id):
        #  Deletes all of the parents' containers.
        #
        #  Args:
        #       parent_id: The parent_id
        url = "{api_url}/containers?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url, pid=self.project_id, parent=parent_id
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def copy_container(self, container, metadata=None):
        # Copies a container.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This is the source container.
        #     metadata (:class:`~decision_optimization_client.Container`, optional): new metadata
        #         to override, as a ``Container``.
        # Returns:
        #     The created container
        sid = get_container_id(container)
        url = "{api_url}/containers/{container_id}/copy?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=sid,
            pid=self.project_id,
            parent=container.parent_id,
        )
        container_data = metadata
        if isinstance(container, Container) and metadata is None:
            container_data = container
        response = self._call.POST(
            url,
            headers=content_json,
            data=container_data._DDObject__to_json() if container_data else None,
        )
        self._check_status(response, [201])
        container_as_json = response.json()
        return Container(
            parent_id=container.parent_id, json=container_as_json, client=self
        )

    def get_assets(self, container, name=None):
        # Returns assets for a container.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        # Returns:
        #     A dict where keys are asset name and values are
        #     :class:`~decision_optimization_client.Asset`.
        qparams = {}
        if name is not None:
            qparams["name"] = name
        query_str = "&%s" % urlencode(qparams) if qparams else ""
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/assets?projectId={pid}&parentId={parent}{qstr}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
            qstr=query_str,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        assets_as_json = response.json()
        return {asset_json["name"]: Asset(asset_json) for asset_json in assets_as_json}

    def update_asset(self, container, name, new_data=None):
        #  Updates asset metadata.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This ``container`` is used to indicate which container
        #        is to be updated.
        #     name: An asset name.
        #     new_data (:class:`~decision_optimization_client.Asset`): A
        #        :class:`~decision_optimization_client.Asset` containing metadata to update.
        container_id = get_container_id(container)
        if new_data is None:
            raise ValueError("No asset data provided")
        url = "{api_url}/containers/{container_id}/assets/{asset_id}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_id=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.POST(
            url, headers=content_json, data=json.dumps(new_data), allow_redirects=False
        )
        self._check_status(response, [200, 301])

    def create_asset(self, container, asset_meta=None):
        # Creates a new asset with given meta data.
        container_id = get_container_id(container)
        asset_name = get_asset_name(asset_meta)
        url = "{api_url}/containers/{container_id}/assets/{asset_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_name=asset_name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(
            url, headers=content_json, data=asset_meta._DDObject__to_json()
        )
        self._check_status(response, [201])
        asset_as_json = response.json()
        return Asset(json=asset_as_json, container=container)

    def get_asset(self, container, name):
        # Gets asset metadata.
        #
        # This can get the asset by id or by name.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: An asset name
        # Returns:
        #     A :class:`~decision_optimization_client.Asset` instance.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        if name is None:
            return None
        if not isinstance(name, string_types):
            raise ValueError("name shoudl be a string type")
        url = "{api_url}/containers/{container_id}/assets/{asset_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200, 404])
        if response.status_code == 404:
            return None
        asset_as_json = response.json()
        return Asset(json=asset_as_json, client=self)

    def get_asset_data(self, container, name):
        # Gets asset data.
        #
        #  Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: An asset name.
        # Returns:
        #     The asset data as a byte array.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/assets/{asset_id}/data?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_id=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=content_octet_stream)
        self._check_status(response, [200, 204])
        if response.status_code == 204:
            return None
        return response.content

    def get_asset_name(self, asset=None, name=None):
        # returns the id for an asset or asset name
        asset_name = None
        if name:
            asset_name = name
        if asset_name is None:
            asset_name = get_asset_name(asset)
        return asset_name

    def get_table_name(self, table=None, name=None):
        # returns the id for a table or table name
        table_name = None
        if name:
            table_name = name
        if not table_name:
            table_name = get_table_name(table)
        return table_name

    def import_table(
        self,
        container,
        project_asset_id,
        imported_table_name,
        category="input",
        lineage=None,
    ):
        return self.__import_from_project_asset(
            container,
            project_asset_id,
            imported_table_name,
            "table",
            category=category,
            lineage=lineage,
        )

    def export_table(
        self,
        container,
        container_table_name,
        project_asset_name=None,
        project_asset_id=None,
        write_mode=None,
    ):
        if project_asset_name != None and project_asset_id != None:
            raise ValueError(
                "Either project_asset_name or project_asset_id should be provided, but not both"
            )
        if write_mode != None and write_mode not in ["append", "truncate"]:
            raise ValueError(
                "Only valid values for `write_mode` are `append` and `truncate`."
            )
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables/{table_name}/data/asset?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=container_table_name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        payload = {"description": "Exported from Decision Optimization experiment"}
        if project_asset_id:
            payload["id"] = project_asset_id
        else:
            payload["name"] = project_asset_name or container_table_name
        if write_mode:
            payload["write_mode"] = write_mode
        response = self._call.POST(url, headers=content_json, data=json.dumps(payload))
        self._check_status(response, [200])
        return response.json()["id"]

    def __import_from_project_asset(
        self,
        container,
        project_asset_id,
        imported_name,
        type="table",
        category="input",
        lineage=None,
    ):
        container_id = get_container_id(container)
        if not type in ["table", "asset"]:
            raise ValueError(
                "Incorrect value for 'type' parameter. Supported types 'table', 'asset', but received: '{}'".format(
                    type
                )
            )
        url = "{api_url}/containers/{container_id}/bulk_update?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
        )
        if lineage == None:
            lineage = "Imported from project asset (asset_id: {})".format(
                project_asset_id
            )
        payload = [
            {
                "id": project_asset_id,
                "name": imported_name,
                "type": type,
                "category": category,
                "lineage": lineage,
            }
        ]
        response = self._call.POST(url, headers=content_json, data=json.dumps(payload))
        self._check_status(response, [200])

    def import_asset(
        self,
        container,
        project_asset_id,
        imported_asset_name,
        category="input",
        lineage=None,
    ):
        return self.__import_from_project_asset(
            container,
            project_asset_id,
            imported_asset_name,
            "asset",
            category=category,
            lineage=lineage,
        )

    def export_asset(
        self,
        container,
        container_asset_name,
        project_asset_name=None,
        project_asset_id=None,
    ):
        if project_asset_name != None and project_asset_id != None:
            raise ValueError(
                "Either project_asset_name or project_asset_id should be provided, but not both"
            )
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/assets/{asset_name}/data/asset?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_name=container_asset_name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        payload = {"description": "Exported from Decision Optimization experiment"}
        if project_asset_id:
            payload["id"] = project_asset_id
        else:
            payload["name"] = project_asset_name or container_asset_name
        response = self._call.POST(url, headers=content_json, data=json.dumps(payload))
        self._check_status(response, [200])
        return response.json()["id"]

    def add_asset_data(self, container, name, data=None):
        # Adds or updates asset data.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This ``container`` is used to indicate which container
        #        is to be updated.
        #     name: An asset name.
        #     data: A stream containing the data to upload.
        # Returns:
        #     the asset metadata as :class:`~decision_optimization_client.Asset`
        container_id = get_container_id(container)
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        if data is None:
            raise ValueError("No data provided")
        url = "{api_url}/containers/{sid}/assets/{asset_id}/data?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            sid=container_id,
            asset_id=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(url, headers=content_octet_stream, data=data)
        self._check_status(response, [200])

        return Asset(json=response.json(), client=self)

    def delete_asset(self, container, name):
        #  Deletes the asset.
        #
        # This can delete the asset by id if ``asset`` is specified or by name
        # if ``name`` is specified.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        #     name: An asset name.
        container_id = get_container_id(container)
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        url = "{api_url}/containers/{container_id}/assets/{asset_id}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            asset_id=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def delete_assets(self, container, category=None):
        #  Deletes all the assets of a container
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        #     category: The category of assets. Can be 'input', 'output' or None
        #         if both input and output assets are to be deleted.
        container_id = get_container_id(container)
        qparams = {}
        if category is not None:
            qparams["category"] = category
        query_str = "&%s" % urlencode(qparams) if qparams else ""
        url = "{api_url}/containers/{container_id}/assets?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
            qstr=query_str,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def get_tables(self, container, category=None, name=None):
        # Returns all container table metadata.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: A name to filter tables with.
        #     category: The category of tables. Can be 'input', 'output' or None
        #         if both input and output tables are to be returned.
        # Returns:
        #     A dict where keys are table name and values are
        #     :class:`~decision_optimization_client.Table`.
        qparams = {}
        if category is not None:
            qparams["category"] = category
        if name is not None:
            qparams["name"] = name
        query_str = "&%s" % urlencode(qparams) if qparams else ""
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables?projectId={pid}&parentId={parent}{qstr}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
            qstr=query_str,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        tables_as_json = response.json()
        return {
            table_json["name"]: Table(json=table_json, container=container)
            for table_json in tables_as_json
        }

    def create_table(self, container, table_meta=None):
        # Creates a new table with given meta data.
        container_id = get_container_id(container)
        table_name = get_table_name(table_meta)
        url = "{api_url}/containers/{container_id}/tables/{table_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=table_name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(
            url, headers=content_json, data=table_meta._DDObject__to_json()
        )
        self._check_status(response, [200, 201])
        table_as_json = response.json()
        return Table(json=table_as_json, container=container)

    def add_table(self, container, name, new_data=None, category=None):
        # Adds table metadata.
        #
        # This can add metadata by table id or table name.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This ``container`` is used to indicate which container
        #        is to be updated.
        #     name: A table name.
        #     new_data (:class:`~decision_optimization_client.Table`): A
        #        :class:`~dd_container.Table` containing metadata to update.
        container_id = get_container_id(container)
        table_data = new_data
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        if table_data is None:
            raise ValueError("No table data provided")
        if category is not None:
            table_data.category = category
        url = "{api_url}/containers/{container_id}/tables/{table_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(
            url, headers=content_json, data=table_data._DDObject__to_json()
        )
        self._check_status(response, [200])

    def get_table(self, container, name):
        #  Gets table metadata.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: A table name.
        # Returns:
        #     A :class:`~decision_optimization_client.Table` instance.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables/{table_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200, 404])
        if response.status_code == 404:
            return None
        table_as_json = response.json()
        return Table(json=table_as_json, container=container)

    def delete_table(self, container, name):
        #  Deletes the table.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        #     name: A table name.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables/{table_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def delete_tables(self, container, category=None):
        #  Deletes all the tables of a container.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        #     category: The category of tables. Can be 'input', 'output' or None
        #         if both input and output tables are to be deleted.
        qparams = {}
        if category is not None:
            qparams["category"] = category
        query_str = "&%s" % urlencode(qparams) if qparams else ""
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
            qstr=query_str,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def get_table_type(self, container, name):
        # Gets table type.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: the name of the table
        # Returns:
        #     A :class:`~decision_optimization_client.TableType` instance.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{sid}/tables/{table_name}/type?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            sid=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        type_as_json = response.json()
        return TableType(json=type_as_json, id=name)

    def update_table_type(self, container, name, new_value=None):
        #  Updates table type.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This ``container`` is used to indicate which container
        #        is to be updated.
        #     name: the name of the table.
        #     new_value (:class:`~dd_container.TableType`): A
        #        :class:`~dd_container.TableType` containing metadata to update.
        container_id = get_container_id(container)
        if new_value is None:
            raise ValueError("No container table type provided")
        url = "{api_url}/containers/{sid}/tables/{table_name}/type?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            sid=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.PUT(
            url, headers=content_json, data=json.dumps(new_value._DDObject__to_json())
        )
        self._check_status(response, [200])

    def get_tables_type(self, container):
        # Returns a dictionary of table types for each table.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #     as string.
        # Returns:
        #     A dict which keys are table names and values are
        #     :class:`~decision_optimization_client.TableType`'s.
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/tables/types?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        types_as_json = response.json()
        return {
            name: TableType(json=type_json, name=name)
            for name, type_json in iteritems(types_as_json)
        }

    def get_table_data(self, container, name, raw=False):
        # Gets table data.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string.
        #     name: the name of the table.
        #     raw: If set, data is returned as is from the server, without
        #        conversion into a `pandas.DataFrame`
        # Returns:
        #     A :py:obj:`pandas.DataFrame` containing the data or the raw data.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{sid}/tables/{table_name}/data?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            sid=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.GET(url, headers=accept_csv)
        self._check_status(response, [200, 204])
        if response.status_code == 200:
            if pd and not raw:
                data = BytesIO(response.content)
                return pd.read_csv(data, index_col=None)
            else:
                return response.content
        else:
            return None

    def add_table_data(self, container, name, category=None, data=None):
        #  Adds table metadata.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string. This ``container`` is used to indicate which container
        #        is to be updated.
        #     name: the name of the table.
        #     category (optional): The category of the table ('input' or 'output')
        #     data (:obj:`pandas.DataFrame` or bytes): The data to upload. If
        #         the data is a `pandas.DataFrame`, it is converted to csv first.
        container_id = get_container_id(container)
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        if data is None:
            raise ValueError("No data provided")
        if pd and isinstance(data, pd.DataFrame):
            if type(data.index) != pd.RangeIndex:
                data = data.reset_index()
            data = data.to_csv(index=False)
        qparams = []
        if category is not None:
            qparams.append("category=%s" % category)
        query_str = "&%s" % "&".join(qparams) if qparams else ""
        url = "{api_url}/containers/{sid}/tables/{table_name}/data?projectId={pid}&parentId={parent}{query_str}".format(
            api_url=self.api_url,
            sid=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
            query_str=query_str,
        )
        response = self._call.PUT(url, headers=content_csv, data=data)
        self._check_status(response, [200])

    def delete_table_data(self, container, name):
        #  Deletes table data.
        #
        # Args:
        #     container: A :class:`~decision_optimization_client.Container` or a container name
        #        as string
        #     name: the name of the table.
        if not isinstance(name, string_types):
            raise ValueError("name should be a string type")
        container_id = get_container_id(container)
        url = "{api_url}/containers/{container_id}/table/{table_name}?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url,
            container_id=container_id,
            table_name=name,
            pid=self.project_id,
            parent=container.parent_id,
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def get_experiments(self, name=None, folder_id=None, folder_path=None):
        """Returns the list of decision Experiments.

        Args:
            name: An optional parameter. If given, only the Experiments for which
                names match ``name`` are returned.
        Returns:
            a list of :class:`~decision_optimization_client.Experiment`
        """
        query_params = "projectId={pid}".format(pid=self.project_id)
        if name is not None:
            query_params += "&name={param}".format(param=name)
        if folder_id is not None:
            query_params += "&folder_id={param}".format(param=folder_id)
        if folder_path is not None:
            query_params += "&folder_path={param}".format(param=folder_path)
        url = "{api_url}/decisions?{params}".format(
            api_url=self.api_url, params=query_params
        )
        response = self._call.GET(url, headers=content_json)
        self._check_status(response, [200])
        experiments_as_json = response.json()
        return [Experiment(json=s, client=self) for s in experiments_as_json]

    def create_experiment(self, experiment=None, folder_id=None, **kwargs):
        """
            Creates a decision experiment.


        If this method is given an ``experiment`` argument, that experiment is
        used to initialize the values for the new experiment. Otherwise, the
        ``**kwargs`` are used to initialize a
        :class:`~decision_optimization_client.Experiment`.

        Example:

            Creates a Experiment using the Experiment name passed as ``kwargs``::

                experiment = client.create_experiment(name='test experiment')

            Creates a Experiment using the experiment passed as a Experiment:

                meta = Experiment(name='test experiment')
                experiment = client.create_experiment(experiment=meta)

        Args:
            experiment (:class:`~decision_optimization_client.Experiment`): The
                Experiment metadata used as initial data.
            **kwargs: kwargs used to initialize the Experiment
        Returns:
            The decision Experiment as a :class:`~decision_optimization_client.Experiment`
        """
        experiment_value = Experiment()
        if experiment:
            experiment_value.json.update(experiment.json)
        if kwargs:
            experiment_value.json.update(kwargs)
        query_params = "projectId={pid}".format(pid=self.project_id)
        if folder_id is not None:
            query_params += "&folder_id={param}".format(param=folder_id)
        url = "{api_url}/decisions?{params}".format(
            api_url=self.api_url, params=query_params
        )
        response = self._call.POST(
            url, headers=content_json, data=experiment_value.to_json()
        )
        self._check_status(response, [201])
        json_resp = response.json()
        return Experiment(json=json_resp, client=self)

    def get_experiment(self, name=None, id=None, folder_id=None):
        """Returns the decision Experiment metadata.

        Args:
            name: The name of the Experiment to look for

        Returns:
            an :class:`~decision_optimization_client.Experiment`
            If the decision doesn't exist, you'll get an error telling you so.
        """
        # search by Experiment name
        if id is not None:
            guid = get_experiment_id(id)
            url = "{api_url}/decisions/{guid}?projectId={pid}".format(
                api_url=self.api_url, guid=guid, pid=self.project_id
            )
            response = self._call.GET(url, headers=content_json)
            self._check_status(response, [200])
            framework_as_json = response.json()
            return Experiment(json=framework_as_json, client=self)
        elif name is not None:
            possible = self.get_experiments(name=name, folder_id=folder_id)
            return possible[0] if possible else None
        else:
            raise ValueError(
                "get_experiment expects an id or name to filter decision models."
            )

    def update_experiment(self, experiment, new_data=None, folder_id=None):
        """Updates decision model metadata.

        Examples:

          Updates a Experiment with new data using name::

            >>> new = Experiment()
            >>> new.description = "new description"
            >>> client.update_experiment(decision_model_name, new)

          Gets a Experiment, then replaces description::

            >>> experiment = client.get_experiment(id=guid)
            >>> experiment.description = "new description"
            >>> client.update_experiment(experiment)

          Gets a Experiment by name, then replaces description::

            >>> experiment = client.get_experiment(name='decision model name')
            >>> experiment.description = "new description"
            >>> client.update_experiment(experiment)

        Args:
           experiment: A :class:`~decision_optimization_client.Experiment` or a name
              as string. This ``experiment`` is used to indicate which
              Experiment is to be updated. If ``new_data`` is None, the
              Experiment is updated with the data from this ``experiment``.
           new_data (:class:`~decision_optimization_client.Experiment`, optional): A
               :class:`~decision_optimization_client.Experiment` containing metadata to
               update.
        """
        guid = get_experiment_id(experiment)
        experiment_data = new_data
        if isinstance(experiment, Experiment) and new_data is None:
            experiment_data = json.loads(experiment.to_json())
        if experiment_data is None:
            raise ValueError("No experiment data provided")
        query_params = "projectId={pid}".format(pid=self.project_id)
        if folder_id is not None:
            query_params += "&folder_id={param}".format(param=folder_id)
        url = "{api_url}/decisions/{guid}?{params}".format(
            api_url=self.api_url, guid=guid, params=query_params
        )
        response = self._call.PUT(
            url, headers=content_json, data=json.dumps(experiment_data)
        )
        self._check_status(response, [200])

    def delete_experiment(self, experiment):
        # Deletes the decision model.
        #
        # Args:
        #     experiment: A :class:`~decision_optimization_client.Experiment` or a name
        #        as string
        guid = get_experiment_id(experiment)
        url = "{api_url}/decisions/{guid}?projectId={pid}".format(
            api_url=self.api_url, guid=guid, pid=self.project_id
        )
        response = self._call.DELETE(url, headers=content_json)
        self._check_status(response, [204])

    def get_experiment_environments(self, container, model_type):
        experiment = self.get_experiment(id=container.parent_id)
        guid = get_experiment_id(experiment)
        url = "{api_url}/decisions/{guid}/environments?projectId={pid}&model_type={model_type}".format(
            api_url=self.api_url, guid=guid, pid=self.project_id, model_type=model_type
        )
        response = self._call.GET(url, headers=content_json)
        if response.status_code == 404:
            return None
        self._check_status(response, [200])
        return response.json()

    def add_environment_to_experiment(self, container, environment):
        experiment = self.get_experiment(id=container.parent_id)
        guid = get_experiment_id(experiment)
        url = "{api_url}/decisions/{guid}/environments?projectId={pid}".format(
            api_url=self.api_url, guid=guid, pid=self.project_id
        )
        response = self._call.POST(url, headers=content_json, data=environment)
        self._check_status(response, [202])

        json_env = json.loads(environment)
        timeout = 0
        while True:
            time.sleep(1)
            timeout += 1
            envs = self.get_experiment_environments(
                container, json_env[0]["model"]["model_type"]
            )
            state = envs["environments"][0]["status"]["state"]
            if state != "preparing":
                env_id = envs["environments"][0]["id"]
                break
            if timeout > 120:
                break

    def add_default_environment_to_experiment(self, container, warn=False):
        with self.lock:
            model_type = self.get_model_type(container)
            environments = self.get_experiment_environments(container, model_type)
            if environments is not None and len(environments.get("environments")) == 0:
                environment = [
                    {
                        "name": "{model_type}-default-2".format(model_type=model_type),
                        "model": {"model_type": model_type},
                        "default_environment": True,
                    }
                ]
                self.add_environment_to_experiment(container, json.dumps(environment))
                if warn:
                    warnings.warn(
                        'Default environment for "{model_type}" has been added.'.format(
                            model_type=model_type
                        )
                    )

    def is_cognitive_scenario(self, container):
        # get container info
        container_id = get_container_id(container)
        qualifiers = None
        try:
            qualifiers = container.qualifiers
        except AttributeError:
            cc = self.get_container(container.parent_id, container_id)
            qualifiers = cc.qualifiers
        # check if this is a cognitive model
        if qualifiers is None:
            return False
        qual_dict = {q["name"]: q["value"] for q in qualifiers}
        return "modelType" in qual_dict and qual_dict.get("modelType") == "cognitive"

    def solve(self, container, **kwargs):
        # Solves the scenario model of the container which id is specified.
        #
        # This method returns as soon as the request is sent. Use
        # Client.wait_for_completion() to wait for solve completion.
        #
        # Args:
        #    container: The Container or container id to solve()
        #    **kwargs: extra arguments passed to the solve using a SolveConfig
        self.add_default_environment_to_experiment(container, True)
        container_id = get_container_id(container)
        endpoint = None
        if self.is_cognitive_scenario(container):
            endpoint = "{api_url}/solve?projectId={pid}&parentId={parent}".format(
                api_url=self.cognitive_url,
                pid=self.project_id,
                parent=container.parent_id,
            )
        else:
            endpoint = (
                "{api_url}/decisions/solve?projectId={pid}&parentId={parent}".format(
                    api_url=self.api_url,
                    pid=self.project_id,
                    parent=container.parent_id,
                )
            )
        # create SolveConfig
        sc = SolveConfig(containerId=container_id, **kwargs)
        # run the solve
        response = self._call.POST(
            endpoint, headers=content_json, data=sc._DDObject__to_json()
        )
        self._check_status(response, [202])

    def stop_solve(self, container):
        """
        Stops the solve for a scenario.
        """
        container_id = get_container_id(container)
        endpoint = None
        if self.is_cognitive_scenario(container):
            endpoint = "{api_url}/solve/status/{guid}?projectId={pid}&parentId={parent}".format(
                api_url=self.cognitive_url,
                guid=container_id,
                pid=self.project_id,
                parent=container.parent_id,
            )
        else:
            endpoint = "{api_url}/decisions/solve/status/{guid}?projectId={pid}&parentId={parent}".format(
                api_url=self.api_url,
                guid=container_id,
                pid=self.project_id,
                parent=container.parent_id,
            )
        response = self._call.DELETE(endpoint, headers=content_json)
        self._check_status(response, [202])

    def wait_for_completion(self, container, timeout=None):
        # Waits for the solve operation specified container to complete.
        #
        # Returns:
        #     The last :class:`~decision_optimization_client.SolveStatus`
        s = self.get_solve_status(container)
        start_time = int(round(time.time() * 1000))
        while s.state not in {"FAILED", "TERMINATED"}:
            time.sleep(1)
            s = self.get_solve_status(container)
            if timeout != None:
                if int(round(time.time() * 1000)) - start_time > timeout:
                    print(
                        "Timeout reached... Returning whatever we have as a status now"
                    )
                    return s
        return s

    def get_solve_status(self, container):
        # Queries and returns the solve status for the specified container.
        #
        # Returns:
        #     A :class:`~decision_optimization_client.SolveStatus`
        container_id = get_container_id(container)
        endpoint = None
        if self.is_cognitive_scenario(container):
            endpoint = "{api_url}/solve/status/{guid}?projectId={pid}&parentId={parent}".format(
                api_url=self.cognitive_url,
                guid=container_id,
                pid=self.project_id,
                parent=container.parent_id,
            )
        else:
            endpoint = "{api_url}/decisions/solve/status/{guid}?projectId={pid}&parentId={parent}".format(
                api_url=self.api_url,
                guid=container_id,
                pid=self.project_id,
                parent=container.parent_id,
            )
        response = self._call.GET(endpoint, headers=content_json)
        return SolveStatus(json=response.json())

    def export_notebook(self, container, name, description=None):
        # Creates a notebook from a container's model.
        #
        # Args:
        #     container: The container or container_id
        #     name: the name of the notebook
        #     descrition (Optional): The notebook description
        # Returns:
        #     A dict with the notebook creation info::
        #
        #     {
        #        'projectNotebookId': 'aeiou',
        #        'notebookId': 'aeiou',
        #        'notebookUrl': 'aeiou'
        #     }
        payload = {"containerId": get_container_id(container), "notebookName": name}
        if description:
            payload["notebookDescription"] = description
        url = "{api_url}/decisions/export/notebook?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url, pid=self.project_id, parent=container.parent_id
        )
        response = self._call.POST(url, headers=content_json, data=json.dumps(payload))
        self._check_status(response, [200])
        return response.json()

    def import_notebook(self, container, notebook_id):
        # Updates container model from notebook.
        #
        # Args:
        #     container: The container or container_id
        #     name: the name of the notebook
        #     descrition (Optional): The notebook description
        payload = {
            "containerId": get_container_id(container),
            "notebookId": notebook_id,
        }
        url = "{api_url}/decisions/import/notebook?projectId={pid}&parentId={parent}".format(
            api_url=self.api_url, pid=self.project_id, parent=container.parent_id
        )
        response = self._call.POST(url, headers=content_json, data=json.dumps(payload))
        self._check_status(response, [200])
        print(response.content)

    def get_model_type(self, container):
        # Returns
        #     docplex, cplex, cpo, opl
        assets = self.get_assets(container)
        if (
            next(("docplex" for a in assets.keys() if str(a).endswith(".py")), None)
            is not None
        ):
            return "docplex"
        if (
            next(("opl" for a in assets.keys() if str(a).endswith(".mod")), None)
            is not None
        ):
            return "opl"
        if (
            next(("cpo" for a in assets.keys() if str(a).endswith(".cpo")), None)
            is not None
        ):
            return "cpo"
        if (
            next(
                (
                    "cplex"
                    for a in assets.keys()
                    if str(a).endswith(".lp")
                    or str(a).endswith(".lp.gz")
                    or str(a).endswith(".lp.bz2")
                    or str(a).endswith(".mps")
                    or str(a).endswith(".mps.gz")
                    or str(a).endswith(".mps.bz2")
                    or str(a).endswith(".sav")
                    or str(a).endswith(".sav.gz")
                    or str(a).endswith(".sav.bz2")
                ),
                None,
            )
            is not None
        ):
            return "cplex"
        return "docplex"
