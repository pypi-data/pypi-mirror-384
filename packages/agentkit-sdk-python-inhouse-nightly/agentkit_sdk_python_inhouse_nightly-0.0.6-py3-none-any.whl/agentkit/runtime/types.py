# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional

from pydantic import BaseModel, Field

# ==================
# Atomic configs
# ==================

class KeyAuth_(BaseModel):
    ApiKey: str = Field(alias="ApiKey")
    ApiKeyName: str = Field(alias="ApiKeyName")
    ApiKeyLocation: str = Field(alias="ApiKeyLocation")

class AuthorizerConfiguration(BaseModel):
    KeyAuth: Optional[KeyAuth_] = Field(default=None, alias="KeyAuth")
    
    model_config = {
        "arbitrary_types_allowed": True
    }


# ==================
# API configs
# ==================


class CreateAgentkitRuntimeRequest(BaseModel):
    name: str = Field(alias="Name")
    description: Optional[str] = Field(alias="Description")
    artifact_type: str = Field(alias="ArtifactType")
    artifact_url: str = Field(alias="ArtifactUrl")
    # command: str = Field(alias="Command")
    project_name: str = Field(alias="ProjectName")
    client_token: str = Field(alias="ClientToken")
    role_name: str = Field(alias="RoleName")
    authorizer_configuration: AuthorizerConfiguration = Field(alias="AuthorizerConfiguration")
    envs: Optional[list[dict]] = Field(alias="Envs")
    tags: Optional[list[dict]] = Field(alias="Tags")
    enable_apmplus: Optional[bool] = Field(False, alias="ApmplusEnable")


class CreateAgentkitRuntimeResponse(BaseModel):
    id: str = Field(alias="Id")


class GetAgentkitRuntimeRequest(BaseModel):
    runtime_id: str = Field(alias="RuntimeId")


# todo
class GetAgentkitRuntimeResponse(BaseModel):
    runtime_id: str = Field(alias="RuntimeId")
    name: str = Field(alias="Name")
    description: Optional[str] = Field(alias="Description")
    artifact_type: str = Field(alias="ArtifactType")
    artifact_url: str = Field(alias="ArtifactUrl")
    command: str = Field(alias="Command")
    project_name: str = Field(alias="ProjectName")
    status: str = Field(alias="Status")
    created_at: str = Field(alias="CreatedAt")
    updated_at: str = Field(alias="UpdatedAt")
    role_name: str = Field(alias="RoleName")
    endpoint: str = Field(alias="Endpoint")
    authorizer_configuration: Optional[AuthorizerConfiguration] = Field(default=None, alias="AuthorizerConfiguration")
    envs: Optional[list[dict]] = Field(alias="Envs")
    tags: Optional[list[dict]] = Field(alias="Tags")
    enable_apmplus: Optional[bool] = Field(alias="ApmplusEnable")


class UpdateAgentkitRuntimeRequest(BaseModel):
    description: Optional[str]
    artifact_url: Optional[str]
    role_name: Optional[str]
    to_release: bool = False
    client_token: str


class UpdateAgentkitRuntimeResponse(BaseModel):
    id: str


class DeleteAgentkitRuntimeRequest(BaseModel):
    id: str = Field(alias="RuntimeId")
    client_token: Optional[str] = Field(default="",alias="ClientToken")


class DeleteAgentkitRuntimeResponse(BaseModel):
    id: str = Field(alias="RuntimeId")


class ListAgentkitRuntimesRequest(BaseModel):
    name_contains: Optional[str]
    status: Optional[str]
    creation_time_before: Optional[str]
    creation_time_after: Optional[str]
    last_update_time_before: Optional[str]
    last_update_time_after: Optional[str]
    next_token: Optional[str]
    max_results: Optional[int]


class ListAgentkitRuntimesResponse(BaseModel):
    next_token: str


class ReleaseAgentkitRuntimeRequest(BaseModel):
    id: str
    version_number: int


class ReleaseAgentkitRuntimeResponse(BaseModel):
    id: str


class ListAgentkitRuntimeErrorDetailsRequest(BaseModel):
    id: str
    version_number: int
    next_token: str
    max_results: int


class ListAgentkitRuntimeErrorDetailsResponse(BaseModel):
    next_token: str


class GetAgentkitRuntimeVersionRequest(BaseModel):
    id: str
    version_number: int


class GetAgentkitRuntimeVersionResponse(BaseModel):
    id: str
    name: str
    description: str
    version_number: int


class ListAgentkitRuntimeVersionsRequest(BaseModel):
    version: str


class ListAgentkitRuntimeVersionsResponse(BaseModel):
    version: str