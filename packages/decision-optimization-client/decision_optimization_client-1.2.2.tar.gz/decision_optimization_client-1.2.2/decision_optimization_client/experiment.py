# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import json

from six import string_types

from .base_resource import DDObject
from .container import Container


def get_experiment_id(what):
    if hasattr(what, "id"):
        return what.id
    elif isinstance(what, string_types):
        return what
    else:
        raise ValueError("Don't know how to get Experiment id from %s" % what)


class Experiment(DDObject):
    """
    Attributes:
       name: Name of the experiment
       description: Description of the experiment
    """

    def __init__(self, json=None, **kwargs):
        # Creates a new Experiment.
        #
        # Examples:
        #
        #             To create a list of :class:`~Experiment` from Experiment metadata of a
        #             project, for instance, the response.json() from
        #             :class:`~dd_decisionservice.Client.get_experiments()`:
        #
        #                 >>> experiments = [Experiment(json=s) for s in client.get_experiments()]
        #
        #             To create a Experiment with a given name and projectId:
        #
        #                 >>> experiment = Experiment(name="foo", projectId="aeiou")
        #
        #         Args:
        #            json (:obj:`dict`, optional): The dict describing the container.
        #            client: The client that this Experiment is bound to.
        #            **kwargs (optional): kwargs to override container attributes.
        #                Attributes specified here will override those of ``desc``.
        authorized_properties = ["id", "name", "description"]
        super(Experiment, self).__init__(
            json=json, authorized_properties=authorized_properties, **kwargs
        )

    def create_container(self, category=None, **kwargs):
        """Creates a :class:`~Container` whose parent is this
        Experiment.

        Currently supported categories are:

            * ``'scenario'``

        Example:
            This creates an ``scenario`` :class:`~Container` with the name 'foo'::

                >>> c = experiment.create_container(category='scenario', name='foo')

        Args:
            category: The category of the container.
            **kwargs: kwargs passed to the :class:`~Container`
                constructor. For example, you can pass params such as
                ``name`` etc..
        Returns:
            The created :class:`~Container`
        """
        if category is None:
            raise ValueError("parameter 'category' is mandatory")
        container = Container(parentId=self.id, category=category, **kwargs)
        sc = self.client.create_container(self.id, container)
        return sc

    def get_containers(self, category=None, as_dict=False):
        """Returns containers of the specified category in this :class:`~Experiment`.

        Args:
            category: The category of :class:`~Container`. Can be
                ``'scenario'`` or ``'dashboard'``.
            as_dict: If True, the containers are returned as a dict where its keys
                are the container names and its values are containers.
        Returns:
            A list of :class:`~Container` or a dict mapping
            container names to :class:`~Container`
        """
        containers = self.client.get_containers(parent_id=self.id, category=category)
        return {s.name: s for s in containers} if as_dict else containers

    def lookup_container(self, name, category=None):
        containers = self.client.get_containers(parent_id=self.id, category=category)
        target = [x for x in containers if x.name == name]
        return target[0] if target else None

    def delete_container(self, container):
        """Deletes the specified :class:`~Container`

        Args:
            container: The :class:`~Container` to be deleted.
        """
        self.client.delete_container(container)

    def create_scenario(self, name, **kwargs):
        """Creates a new :class:`~Container` attached as a
        scenario  of this :class:`~Experiment`.

        Args:
            name: The name of the container.
            **kwargs: kwargs passed to the :class:`~Container`
               constructor.
        Returns:
            :class:`~Container`: The scenario as a
            :class:`~Container`

        Raises:
            ~decision_optimization_client.NotBoundException: when the Artifact is not bound to
                a client.
        """
        return self.create_container(category="scenario", name=name, **kwargs)

    def get_scenario(self, name):
        """Returns the scenario for the specified name.

        Args:
            name: The name of the scenario.
        Returns:
            :class:`~Container`: The scenario as a
                :class:`~Container`
        """
        return self.lookup_container(name=name, category="scenario")

    def get_scenarios(self, as_dict=False):
        """Returns scenarios of this :class:`~Experiment`.

        Args:
            as_dict: If True, the containers are returned as a dict which keys
                are container names and which values are containers.
        Returns:
            A list of :class:`~Container` or a dict mapping
            container names to :class:`~Container`
        """
        return self.get_containers(category="scenario", as_dict=as_dict)
