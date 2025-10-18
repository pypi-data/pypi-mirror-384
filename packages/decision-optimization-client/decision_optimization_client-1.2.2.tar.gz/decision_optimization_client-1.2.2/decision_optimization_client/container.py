# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import json

try:
    from StringIO import StringIO as BytesIO
except ImportError:  # py3
    from io import BytesIO

import sys
from collections import deque

from six import iteritems, string_types

from .asset import Asset
from .base_resource import DDObject
from .table import Table


def get_container_id(what):
    if hasattr(what, "id"):
        return what.id
    elif isinstance(what, string_types):
        return what
    else:
        raise ValueError("Don't know how to get container id from %s" % what)


class Container(DDObject):
    """
    Attributes:
       name: Name of the container
       description: Description of the container
       category: Category of the container, can be ``scenario`` or ``dashboard``
       lineage: If the container has been copied, name of the container that it was copied from
       projectId: ID of the project the container is a part of
    """

    def __init__(self, parent_id=None, json=None, pc=None, **kwargs):
        # Creates a new container.
        #
        #         Examples:
        #
        #             Creates a list of :class:`~Container` from containers metadata of a
        #             project, for instance, the response.json() from
        #             :class:`~Client.get_containers()`:
        #
        #                 >>> containers = [Container(json=s) for s in client.get_containers()]
        #
        #             Creates a container with a given name and projectId:
        #
        #                 >>> container = Container(name="foo", projectId="aeiou")
        #
        #             Creates a container with a given name and using the project context:
        #
        #                 >>> container = Container(name="foo", pc=pc)
        #
        #         Args:
        #            pc (:obj:`projectContext`, optional): The project context
        #            **kwargs (optional): kwargs to override container attributes.
        #                Attributes specified here will override those of ``desc``.
        authorized_properties = [
            "id",
            "name",
            "description",
            "category",
            "lineage",
            "projectId",
        ]
        super(Container, self).__init__(
            json=json, authorized_properties=authorized_properties, **kwargs
        )
        # update project id with pc if pc is passed
        if pc and hasattr(pc, "projectId"):
            self.json.update({"projectId": pc.projectId})
        self.parent_id = parent_id

    def add_table_data(self, what, data=None, category=None):
        """Adds the table data to the container.

        Data must be ``pandas.DataFrame``.

        Examples:

            Adds the data for the table with the specified name::

                >>> container.add_table_data("table1", data=table1_data)

            Adds the data for the tables in the dict:

                >>> tables = { "table1": table1_df, "table2": table2_df }
                >>> scenario.add_table_data(tables)

        Args:
            what: what to add. Can be either a table name or a dict of
                ``{table_name: table_data}``
            data: The data if ``what`` is a table name.
        """
        if isinstance(what, string_types) or isinstance(what, Table):
            # check table existance
            if isinstance(what, string_types):
                tables = self.client.get_tables(self)
                table = tables.get(what, None)
                if not table:
                    table_meta = Table(
                        name=what, category=category, lineage="python client"
                    )
                    table = self.client.create_table(self, table_meta)
                what = table
            self.client.add_table_data(self, what.name, data=data, category=category)
        else:
            for name, value in iteritems(what):
                self.add_table_data(name, data=value, category=category)

    def get_table_data(self, table):
        """Gets table data.

        Args:
            table: :class:`~Table` from which you want the data
        Returns:
            A :py:obj:`pandas.DataFrame` containing the data.
        """
        try:
            table_name = table.name
        except AttributeError:
            table_name = table
        return self.client.get_table_data(self, name=table_name)

    def delete_table_data(self, table):
        """Deletes table data.

        Args:
             table: :class:`~Table` from which you want the data to be deleted
        """
        return self.client.delete_table_data(self, table)

    def get_table_type(self, name):
        """Returns a :class:`~TableType` descriptor for the
        :class:`~Table` which name is specified.

        Args:
            name: A table name as a string.
        Returns:
            A :class:`~TableType` instance.
        """
        return self.client.get_table_type(self, name=name)

    def update_table_type(self, table_type):
        """Updates the table type for the specified :class:`~TableType`.

        Args:
            table_type: A :class:`~TableType` for the update.


        """
        return self.client.update_table_type(self, table_type.id, new_value=table_type)

    def get_tables_data(self, category=None):
        """
        Args:
            category: The category of tables. Can be ``input``, ``output`` or ``None``
                if both input and output tables are to be returned.
        Returns:
            A dict of all tables. Keys are table names, values are DataFrames with table data.
        """
        t = self.client.get_tables(self, category=category)
        return {n: self.client.get_table_data(self, v.name) for n, v in iteritems(t)}

    def get_tables(self, category=None):
        """Returns all container table metadata.

        Args:
            category: The category of tables. Can be ``input``, ``output`` or ``None``
                if both input and output tables are to be returned.
        Returns:
            A dict where its keys are asset names and its values are
            :class:`~Table`.
        """
        return self.client.get_tables(self, category=category)

    def import_table(
        self, project_asset_id, imported_table_name, category="input", lineage=None
    ):
        """Imports table from a project data asset.

        Args:
            project_asset_id: The ID of the project data asset to be imported
            imported_table_name: The name of the new table in the scenario
            category: The category for the table. Default: ``input``
            lineage: Optional comment about the table lineage
        """
        return self.client.import_table(
            self,
            imported_table_name=imported_table_name,
            project_asset_id=project_asset_id,
            category=category,
            lineage=lineage,
        )

    def export_table(
        self,
        table_name,
        project_asset_name=None,
        project_asset_id=None,
        write_mode=None,
    ):
        """Exports a scenario table into a project data asset.

        Args:
            table_name: The name of the table in the scenario
            project_asset_name: The name of a new data asset to be created in the project
            project_asset_id: The ID of an existing data asset in the project to be overwritten
            write_mode: The write mode: ``append`` or ``truncate``. Useful for connected data. Ignored for project assets that do not support it

        Only one of ``project_asset_name`` or ``project_asset_id`` parameters can be used. If none is provided a new asset is created using the source table name with .csv extension.

        Returns:
            An ID of the resulting project asset
        """
        return self.client.export_table(
            self,
            container_table_name=table_name,
            project_asset_name=project_asset_name,
            project_asset_id=project_asset_id,
            write_mode=write_mode,
        )

    def import_asset(
        self, project_asset_id, imported_asset_name, category="input", lineage=None
    ):
        """Imports asset from the project.

        Args:
            project_asset_id: The ID of the project data asset to be imported
            imported_asset_name: The name of the new asset in the scenario
            category: The category for the asset. Default: ``input``
            lineage: Optional comment about the asset lineage
        """
        return self.client.import_asset(
            self,
            imported_asset_name=imported_asset_name,
            project_asset_id=project_asset_id,
            category=category,
            lineage=lineage,
        )

    def export_asset(self, asset_name, project_asset_name=None, project_asset_id=None):
        """Exports scenario asset into a project data asset.

        Args:
            asset_name: The name of the asset in the scenario.
            project_asset_name: The name of a new data asset to be created in the project
            project_asset_id: The ID of an existing data asset in the project to be overwritten

        Only one of ``project_asset_name`` or ``project_asset_id`` parameters can be used. If none is provided a new asset is created using the source asset name.

        Returns:
            An ID of the resulting project asset
        """
        return self.client.export_asset(
            self,
            container_asset_name=asset_name,
            project_asset_name=project_asset_name,
            project_asset_id=project_asset_id,
        )

    def add_asset_data(self, name, data=None, category="model"):
        """Adds or updates asset data.

        Args:
            name: The name of the asset
            data: A stream containing the data to upload.
            category: The category (defaults to ``model``)
        Returns:
            the asset metadata as :class:`~Asset`
        """
        asset = self.client.get_asset(self, name=name)
        if not asset:
            asset_meta = Asset(name=name, category=category)
            asset = self.client.create_asset(self, asset_meta)
        return self.client.add_asset_data(self, name=name, data=data)

    def get_asset_data(self, name):
        """Gets asset data.

        Args:
            name: The name of the asset.
        Returns:
            The asset data as a byte array.
        """
        return self.client.get_asset_data(self, name=name)

    def get_asset(self, name):
        """Gets asset metadata using name.

        Args:
            name: An asset name.
        Returns:
            A :class:`~Asset` instance.
        """
        return self.client.get_asset(self, name=name)

    def delete_asset(self, name):
        """Deletes the asset.

        Args:
            name: The name of the asset as a string.
        """
        return self.client.delete_asset(self, name)

    def create_asset(self, name, data=None, category="model"):
        """Creates an asset.

        Returns:
            A :class:`~Asset` instance.
        """
        asset_meta = Asset(name=name, category=category)
        asset = self.client.create_asset(self, asset_meta)
        if data:
            asset = self.client.add_asset_data(self, name=name, data=data)
        return asset

    def get_assets(self):
        """Returns asset metadata for all of this container's assets.

        Returns:
            A dict where its keys are asset names and its values are
            :class:`~Asset`'s metadata.
        """
        return self.client.get_assets(self)

    def solve(
        self,
        display_log=None,
        log_lines=25,
        log_output=None,
        asynchronous=False,
        timeout=None,
        environment_id=None,
        **kwargs
    ):
        """Solves this scenario.

        If an error occurs and ``display_log`` is None or not set, this prints
        the last ``log_lines`` lines of log (default: 25)

        If ``display_log`` is set to False, nothing is displayed.

        If ``display_log`` display_log is set to True, the log are always displayed.

        Args:
            **kwargs: extra arguments passed as SolveConfig attributes
            display_log: If True, log is downloaded after solve and displayed.
                Default is False
            log_lines: number of lines of log to print. Default is 25. If None,
                all log lines are displayed.
            log_output: the file like object to write logs to. If not specified
                or None, defaults to sys.stdout.
            asynchronous: If true, the solve will be done asynchronously (it won't wait for it to finish),
                allowing you to do multiple solves in parallel
            environment_id: Environment to use to solve this scenario. Useful to override the default environment selected at Decision Optimization Experiment level

        Returns:
            A JSON describing the status of the job that has been launched for this container.
        """
        args = {}
        if kwargs:
            args.update(kwargs)
        # True unless we specifically do not want logs
        if display_log != False:
            args["collectEngineLog"] = True
        if environment_id is not None:
            args["environmentId"] = environment_id
        self.client.solve(self, **args)
        if asynchronous == True:
            return self.get_status()
        status = self.client.wait_for_completion(self, timeout)
        # job state
        state = status["state"]
        # get job details
        execution_status = None
        job_details = status["jobDetails"]
        if job_details is not None:
            # execution status:
            execution_status = job_details.get("executionStatus")
            if execution_status is None:
                print("Could not find jobDetails/executionStatus in status")
                print("Status = %s" % json.dumps(status.json, indent=3))
                raise KeyError("Could not find executionStatus in status")
        # is this failed ?
        is_failed = execution_status == "FAILED" or state == "FAILED"
        # if display_log == False => do exactly nothing
        if display_log or (display_log is None and is_failed):
            if log_output is None:
                log_output = sys.stdout
            assets = self.get_assets()
            if "log.txt" in assets:
                logs = self.get_asset_data("log.txt")
                strio = BytesIO(logs)
                last_n_lines = deque(strio.readlines(), maxlen=log_lines)
                for l in last_n_lines:
                    log_output.write(l.decode("utf-8"))
        return status

    def get_status(self):
        """Get the solve status for this scenario

        Returns:
            A JSON describing the solve status  for that scenario

        """
        return self.client.get_solve_status(self)

    def copy(self, name):
        """Copies this container.

        Arg:
            name (Mandatory): The name of the copy.

        Returns:
            The :class:`~Container` for the copy.
        """
        metadata = Container(name=name)
        return self.client.copy_container(self, metadata=metadata)
