# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

from types import NoneType

import pydantic

from beeai_sdk.a2a.extensions.base import BaseExtensionClient, BaseExtensionServer, BaseExtensionSpec


class AgentDetailTool(pydantic.BaseModel):
    name: str
    description: str


class AgentDetailContributor(pydantic.BaseModel):
    name: str
    email: str | None = None
    url: str | None = None


class EnvVar(pydantic.BaseModel):
    name: str
    description: str | None = None
    required: bool = False


class AgentDetail(pydantic.BaseModel, extra="allow"):
    interaction_mode: str | None = pydantic.Field("multi-turn", examples=["multi-turn", "single-turn"])
    user_greeting: str | None = None
    input_placeholder: str | None = None
    tools: list[AgentDetailTool] | None = None
    framework: str | None = None
    license: str | None = None
    programming_language: str | None = "Python"
    homepage_url: str | None = None
    source_code_url: str | None = None
    container_image_url: str | None = None
    author: AgentDetailContributor | None = None
    contributors: list[AgentDetailContributor] | None = None
    variables: list[EnvVar] | None = None


class AgentDetailExtensionSpec(BaseExtensionSpec[AgentDetail]):
    URI: str = "https://a2a-extensions.beeai.dev/ui/agent-detail/v1"


class AgentDetailExtensionServer(BaseExtensionServer[AgentDetailExtensionSpec, NoneType]): ...


class AgentDetailExtensionClient(BaseExtensionClient[AgentDetailExtensionSpec, AgentDetail]): ...
