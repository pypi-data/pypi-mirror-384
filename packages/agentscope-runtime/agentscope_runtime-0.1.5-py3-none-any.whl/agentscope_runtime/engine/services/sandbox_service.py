# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
from typing import List

from ...sandbox.enums import SandboxType
from ...sandbox.manager import SandboxManager
from ...sandbox.registry import SandboxRegistry
from ...sandbox.tools.mcp_tool import MCPTool
from ...sandbox.tools.sandbox_tool import SandboxTool
from ...sandbox.tools.function_tool import FunctionTool
from ...engine.services.base import ServiceWithLifecycleManager


class SandboxService(ServiceWithLifecycleManager):
    def __init__(self, base_url=None, bearer_token=None):
        self.manager_api = SandboxManager(
            base_url=base_url,
            bearer_token=bearer_token,
        )

        self.base_url = base_url
        self.bearer_token = bearer_token
        self.sandbox_type_set = set(item.value for item in SandboxType)

        self.session_mapping = {}

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        # Release all environments
        for _, env_ids in self.session_mapping.items():
            for env_id in env_ids:
                self.manager_api.release(env_id)

        if self.base_url is None:
            # Embedded mode
            self.manager_api.cleanup()

    async def health(self) -> bool:
        return True

    def connect(
        self,
        session_id,
        user_id,
        env_types=None,
        tools=None,
    ) -> List:
        for tool in tools:
            if not isinstance(tool, (SandboxTool, FunctionTool, MCPTool)):
                raise ValueError(
                    "tools must be instances of SandboxTool, FunctionTool, "
                    "or MCPTool",
                )

        # Create a composite key
        composite_key = self._create_composite_key(session_id, user_id)

        # Check if the composite_key already has an environment
        if composite_key in self.session_mapping:
            # Connect to existing environment
            return self._connect_existing_environment(composite_key)
        else:
            # Create a new environment
            return self._create_new_environment(
                composite_key,
                env_types,
                tools,
            )

    def _create_new_environment(
        self,
        composite_key,
        env_types=None,
        tools=None,
    ):
        if env_types is None:
            assert (
                tools is not None
            ), "tools must be specified when env_types is not set"

        server_configs = None
        if tools:
            server_config_list = []
            tool_env_types = set()
            for tool in tools:
                tool_env_types.add(tool.sandbox_type)
                if isinstance(tool, MCPTool):
                    server_config_list.append(tool.server_configs)

            if env_types is None:
                env_types = []

            if server_config_list:
                server_configs = {"mcpServers": {}}
                for server_config in server_config_list:
                    server_configs["mcpServers"].update(
                        server_config["mcpServers"],
                    )

            env_types = set(env_types) | tool_env_types

        wbs = []
        for env_type in env_types:
            if env_type is None:
                continue

            box_type = SandboxType(env_type)

            box_id = self.manager_api.create_from_pool(
                sandbox_type=box_type.value,
            )
            box_cls = SandboxRegistry.get_classes_by_type(box_type)

            box = box_cls(
                sandbox_id=box_id,
                base_url=self.manager_api.base_url,
                bearer_token=self.bearer_token,
            )

            # All the operation must be done after replace this action in
            # embedded mode
            if self.base_url is None:
                # Embedded mode
                box.manager_api = self.manager_api

            if box_type == SandboxType.BASE:
                if server_configs:
                    box.add_mcp_servers(server_configs, overwrite=False)

            # Store mapping from composite_key to env_id
            if composite_key not in self.session_mapping:
                self.session_mapping[composite_key] = []

            self.session_mapping[composite_key].append(box_id)

            wbs.append(box)
        return wbs

    def _connect_existing_environment(self, composite_key):
        env_ids = self.session_mapping.get(composite_key)

        boxes = []
        for env_id in env_ids:
            info = self.manager_api.get_info(env_id)
            version = info.get("version", "")

            env_type = None
            for x in SandboxType:
                if x.value in version:
                    env_type = x.value
                    break

            if env_type is None:
                continue

            wb_type = SandboxType(env_type)

            box_cls = SandboxRegistry.get_classes_by_type(wb_type)

            box = box_cls(
                sandbox_id=env_id,
                base_url=self.manager_api.base_url,
                bearer_token=self.bearer_token,
            )
            if self.base_url is None:
                # Embedded mode
                box.manager_api = self.manager_api

            boxes.append(box)

        return boxes

    def release(self, session_id, user_id):
        composite_key = self._create_composite_key(session_id, user_id)

        # Retrieve and remove env_id using composite_key
        env_ids = self.session_mapping.pop(composite_key, [])

        for env_id in env_ids:
            self.manager_api.release(env_id)

        return True

    def _create_composite_key(self, session_id, user_id):
        # Create a composite key from session_id and user_id
        return f"{session_id}_{user_id}"
