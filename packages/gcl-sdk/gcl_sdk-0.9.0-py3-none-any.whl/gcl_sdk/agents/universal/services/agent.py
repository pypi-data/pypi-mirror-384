#    Copyright 2025 Genesis Corporation.
#
#    All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import annotations

import logging
import re
import typing as tp
import uuid as sys_uuid

from gcl_looper.services import basic as looper_basic

from gcl_sdk.agents.universal.drivers import base as driver_base
from gcl_sdk.agents.universal.drivers import meta as driver_meta
from gcl_sdk.agents.universal.drivers import exceptions as driver_exc
from gcl_sdk.agents.universal.dm import models
from gcl_sdk.agents.universal.clients.orch import base as orch_base
from gcl_sdk.agents.universal.clients.orch import exceptions as orch_exc
from gcl_sdk.agents.universal import constants as c
from gcl_sdk.agents.universal import utils


LOG = logging.getLogger(__name__)


class UniversalAgentService(looper_basic.BasicService):

    def __init__(
        self,
        agent_uuid: sys_uuid.UUID,
        orch_client: orch_base.AbstractOrchClient,
        caps_drivers: list[driver_base.AbstractCapabilityDriver],
        facts_drivers: list[driver_base.AbstractFactDriver],
        payload_path: str | None = c.PAYLOAD_PATH,
        iter_min_period: float = 3,
        iter_pause: float = 0.1,
    ):
        super().__init__(iter_min_period, iter_pause)
        self._orch_client = orch_client
        self._payload_path = payload_path
        self._agent_uuid = agent_uuid

        # Make driver maps by capability and facts:
        # For instance, {"config": ConfigDriver, "service": ServiceDriver}
        self._caps_driver_map = {}
        for d in caps_drivers:
            for capability in d.get_capabilities():
                self._caps_driver_map[capability] = d

        self._facts_driver_map = {}
        for d in facts_drivers:
            for fact in d.get_facts():
                self._facts_driver_map[fact] = d

    def _register_agent(self) -> None:
        capabilities = self._caps_driver_map.keys()
        facts = self._facts_driver_map.keys()
        agent = models.UniversalAgent.from_system_uuid(
            capabilities, facts, self._agent_uuid
        )
        try:
            self._orch_client.agents_create(agent)
            LOG.info("Agent registered: %s", agent.uuid)
        except orch_exc.AgentAlreadyExists:
            LOG.warning("Agent already registered: %s", agent.uuid)

            # Update the agent capabilities and facts if they were changed
            self._orch_client.agents_update(agent)

    def _create_resource(
        self,
        driver: driver_base.AbstractCapabilityDriver,
        resource: models.Resource,
    ) -> models.Resource:
        try:
            dp_resource = driver.create(resource)
        except driver_exc.ResourceAlreadyExists:
            LOG.warning("The resource already exists: %s", resource.uuid)
            dp_resource = driver.get(resource)

        return dp_resource

    def _delete_resource(
        self,
        driver: driver_base.AbstractCapabilityDriver,
        resource: models.Resource,
    ) -> None:
        try:
            driver.delete(resource)
        except driver_exc.ResourceNotFound:
            LOG.warning("The resource does not exist: %s", resource.uuid)

    def _update_resource(
        self,
        driver: driver_base.AbstractCapabilityDriver,
        resource: models.Resource,
    ) -> models.Resource:
        dp_resource = driver.update(resource)
        return dp_resource

    def _actualize_resources(
        self,
        driver: driver_base.AbstractCapabilityDriver,
        capability: str,
        resources: list[models.Resource],
    ) -> list[models.Resource]:
        """
        Actualize resources and return a list of resources from data plane.
        """
        try:
            # Perform some preparations for the driver
            driver.start()
            return self._driver_cap_iteration(driver, capability, resources)
        finally:
            # Finalize the driver
            driver.finalize()

    def _driver_cap_iteration(
        self,
        driver: driver_base.AbstractCapabilityDriver,
        capability: str,
        resources: list[models.Resource],
    ) -> list[models.Resource]:
        """
        Actualize resources and return a list of resources from data plane.
        """
        target_resources = {r: r for r in resources}
        actual_resources = {r: r for r in driver.list(capability)}

        # A list of resources to be collected from the data plane
        # for this capability
        collected_resources = []

        # Create all new resources
        for r in target_resources.keys() - actual_resources.keys():
            try:
                resource = self._create_resource(driver, r)
                collected_resources.append(resource)
            except Exception:
                LOG.exception("Error creating resource %s", r.uuid)

        # Delete outdated resources
        for r in actual_resources.keys() - target_resources.keys():
            try:
                self._delete_resource(driver, r)
            except Exception:
                # The resource wasn't deleted so add it back
                collected_resources.append(r)
                LOG.exception("Error deleting resource %s", r.uuid)

        for r in target_resources.keys() & actual_resources.keys():
            # set does not guarantee which instance will be given on
            # intersection therefore get actual and target resources
            # explicitly.
            target_resource = target_resources[r]
            actual_resource = actual_resources[r]

            # Nothing to do if the resources are the same
            if target_resource.hash == actual_resource.hash:
                collected_resources.append(actual_resource)
                continue

            try:
                resource = self._update_resource(driver, target_resource)
                collected_resources.append(resource)
            except Exception:
                LOG.exception("Error updating resource %s", r.uuid)

        return collected_resources

    def _actualize_resource_facts(
        self,
        target_facts: list[dict[str : tp.Any]],
        actual_facts: list[dict[str : tp.Any]],
    ) -> None:
        """Actualize facts in Status API.

        target_facts - The facts collected from the data plane.
        actual_facts - The facts collected from the Status API.
        """
        target_resources = {r["uuid"]: r for r in target_facts}
        actual_resources = {r["uuid"]: r for r in actual_facts}

        for uuid in target_resources.keys() - actual_resources.keys():
            resource = target_resources[uuid]
            resource["node"] = str(utils.node_uuid())
            try:
                resource = models.Resource.restore_from_simple_view(**resource)
                self._orch_client.resources_create(resource)
            except Exception:
                LOG.exception("Error creating resource %s", uuid)

        for uuid in actual_resources.keys() - target_resources.keys():
            resource = actual_resources[uuid]

            try:
                resource = models.Resource.restore_from_simple_view(**resource)
                self._orch_client.resources_delete(resource)
            except Exception:
                LOG.exception("Error deleting resource %s", uuid)

        for uuid in target_resources.keys() & actual_resources.keys():
            target_resource = target_resources[uuid]
            actual_resource = actual_resources[uuid]

            # Nothing to do if the resources are the same
            if target_resource["full_hash"] == actual_resource["full_hash"]:
                continue

            # Remove read-only fields
            resource = target_resource.copy()
            resource.pop("created_at", None)
            resource.pop("updated_at", None)
            resource.pop("res_uuid", None)
            resource.pop("node", None)

            res_uuid = resource.pop("uuid")
            kind = resource.pop("kind")

            try:
                self._orch_client.resources_update(kind, res_uuid, **resource)
            except Exception:
                LOG.exception("Error updating resource %s", uuid)

    def _actualize_facts(self, target_facts: dict, actual_facts: dict) -> None:
        """Actualize facts in Status API.

        target_facts - The facts collected from the data plane.
        actual_facts - The facts collected from the Status API.
        """
        # New fact category
        for fact in target_facts.keys() - actual_facts.keys():
            resources = target_facts[fact]["resources"]
            self._actualize_resource_facts(resources, [])

        # Deleted fact category
        for fact in actual_facts.keys() - target_facts.keys():
            resources = actual_facts[fact]["resources"]
            self._actualize_resource_facts([], resources)

        # Actualize resource facts in the existing fact category
        for fact in target_facts.keys() & actual_facts.keys():
            target_resources = target_facts[fact]["resources"]
            actual_resources = actual_facts[fact]["resources"]
            self._actualize_resource_facts(target_resources, actual_resources)

    def _setup(self):
        # Call registry at start to update capabilities and facts
        self._register_agent()

    def _iteration(self):
        # The payload is collected every iteration from the data plane.
        # At the end of the iteration the payload hash is calculated
        # and it is saved
        collected_payload = models.Payload.empty()

        # Last successfully saved payload. Use it to compare with CP payload.
        if self._payload_path:
            last_payload = models.Payload.load(self._payload_path)
        else:
            last_payload = None

        # Check if the agent is registered
        try:
            payload = self._orch_client.agents_get_payload(
                self._agent_uuid, last_payload
            )
        except orch_exc.AgentNotFound:
            # Auto discovery mechanism
            self._register_agent()
            return

        # TODO(akremenetsky): Implement actions

        # Capabilities
        for capability, driver in self._caps_driver_map.items():
            # Skip capabilities that are not in the payload
            if capability not in payload.capabilities:
                LOG.debug("Skipping capability %s", capability)
                continue

            target_resources = payload.caps_resources(capability)

            try:
                collected_resources = self._actualize_resources(
                    driver, capability, target_resources
                )
                collected_payload.add_caps_resources(collected_resources)

                # All gathered resources for capabilities are considered
                # as facts too
                collected_payload.add_facts_resources(collected_resources)
            except Exception:
                LOG.exception("Error actualizing resources for %s", capability)

        # Facts
        for fact, driver in self._facts_driver_map.items():
            # Skip facts that are not in the payload
            if fact not in payload.facts:
                LOG.debug("Skipping fact %s", fact)
                continue

            try:
                collected_facts = driver.list(fact)
                collected_payload.add_facts_resources(collected_facts)
            except Exception:
                LOG.exception("Error collecting resources for fact: %s", fact)

        # All work done. The target resources are applied and facts collected.
        # Calculate the hash of the collected payload
        collected_payload.calculate_hash()

        # The payloads aren't the same. It means the facts were updated.
        if collected_payload != payload:
            self._actualize_facts(collected_payload.facts, payload.facts)

        # The capabilities were applied but the target and actual payloads
        # are different. So the difference in the facts. Update it.

        # Save the collected payload after actualization
        if self._payload_path:
            collected_payload.save(self._payload_path)
