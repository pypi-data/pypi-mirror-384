# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import json

from six import string_types

from .base_resource import DDObject


class SolveStatus(DDObject):
    """The class representing solve status.

    Attributes:

        jobDetails: Details of the solve job, containing :

            - executionStatus: status of the job (has it been processed?)

            - solveStatus: status of the solve (did it fail or succeed?)

            - logTail: displays the logs from the solve

        state: State of the job
    """

    def __init__(self, json=None, **kwargs):
        """Creates a Table.

        Args:
            name (:obj:`string`): The name of the asset.
            json (:obj:`dict`): The dict describing the asset.
            **kwargs (optional): kwargs to override container attributes.
                Attributes specified here will override those of ``json``.
        """
        authorized_properties = [
            "jobDetails",
            "executionStatus",
            "solveStatus",
            "logTail",
            "state",
            "endedAt",
            "startedAt",
        ]
        super(SolveStatus, self).__init__(
            json=json, authorized_properties=authorized_properties, **kwargs
        )

    def _repr_html_(self):
        from IPython.display import HTML

        try:
            import pandas

            if self.jobDetails is not None:
                elapsed = self.jobDetails["endedAt"] - self.jobDetails["startedAt"]
                exec_status = self.jobDetails["executionStatus"]
            else:
                elapsed = "-"
                exec_status = "-"
            df = pandas.DataFrame(
                [[self.state, exec_status, elapsed]],
                columns=["State", "Execution status", "Elapsed"],
            )
            return df.to_html(index=False)
        except ImportError:
            return repr(self)


class SolveConfig(DDObject):
    """The class representing solve configuration.

    Attributes:
        containerId: The container name.
        collectEngineLog: The collect engine log flag.
        applicationVersion: The application version.
        solveParameters: A dict with { name: value } for solve parameters
    ```

    Attributes:
        json: The json fragment used to build this Table.
    """

    def __init__(self, json=None, **kwargs):
        """Creates a Table.

        Args:
            name (:obj:`string`): The name of the asset.
            json (:obj:`dict`): The dict describing the asset.
            **kwargs (optional): kwargs to override container attributes.
                Attributes specified here will override those of ``json``.
        """
        super(SolveConfig, self).__init__(json=json, **kwargs)

    def __repr__(self):
        d = {}
        d.update(self.json)
        return json.dumps(d, indent=3)
