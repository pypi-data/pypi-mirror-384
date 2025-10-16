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

import json

from typing import Tuple
from agentkit.utils.ve_sign import ve_request, get_volc_ak_sk_region, get_volc_agentkit_host_info
from agentkit.utils.misc import generate_random_id



from agentkit.runtime.types import (
    CreateAgentkitRuntimeRequest,
    CreateAgentkitRuntimeResponse,
    DeleteAgentkitRuntimeRequest,
    DeleteAgentkitRuntimeResponse,
    GetAgentkitRuntimeRequest,
    GetAgentkitRuntimeResponse,
    GetAgentkitRuntimeVersionRequest,
    GetAgentkitRuntimeVersionResponse,
    ListAgentkitRuntimeErrorDetailsRequest,
    ListAgentkitRuntimeErrorDetailsResponse,
    ListAgentkitRuntimesRequest,
    ListAgentkitRuntimesResponse,
    ListAgentkitRuntimeVersionsRequest,
    ListAgentkitRuntimeVersionsResponse,
    ReleaseAgentkitRuntimeRequest,
    ReleaseAgentkitRuntimeResponse,
    UpdateAgentkitRuntimeRequest,
    UpdateAgentkitRuntimeResponse,
)


ARTIFACT_TYPE_DOCKER_IMAGE = "image"
API_KEY_LOCATION = "HEADER"
PROJECT_NAME_DEFAULT = "default"
RUNTIME_STATUS_READY = "Ready"
RUNTIME_STATUS_ERROR = "Error"





class AgentkitRuntime:
    def __init__(
        self,
        access_key: str = "",
        secret_key: str = "",
        region: str = "",
    ) -> None:
        """Agentkit Runtime control panel class."""
        if not any([access_key, secret_key, region]):
            access_key, secret_key, region = get_volc_ak_sk_region('AGENTKIT')
        else:
            if not all([access_key, secret_key, region]):
                raise ValueError("Error create cr instance: missing access key, secret key or region")
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

        self._host, self._api_version, self._service = get_volc_agentkit_host_info()

    def create(
        self, request: CreateAgentkitRuntimeRequest
    ) -> Tuple[CreateAgentkitRuntimeResponse, str]:
        """Create a new AgentKit Runtime on Volcengine."""
        if request.authorizer_configuration is None:
            raise ValueError("authorizer_configuration is required")
        response = ve_request(
            request_body=request.model_dump(by_alias=True),
            action="CreateAgentKitRuntime",
            ak=self.access_key,
            sk=self.secret_key,
            region=self.region,
            service=self._service,
            version=self._api_version,
            host=self._host,
        )
        if "Error" in response["ResponseMetadata"]:
            error_code = response["ResponseMetadata"]["Error"]["Code"]
            error_message = response["ResponseMetadata"]["Error"]["Message"]
            raise ValueError(
                f"Error create agentkit runtime: {error_code} {error_message}"
            )
        return CreateAgentkitRuntimeResponse(Id=response['Result']['Id']), response['ResponseMetadata']['RequestId']

    def get(self, request: GetAgentkitRuntimeRequest) -> GetAgentkitRuntimeResponse:
        """Get details of a specific AgentKit Runtime from Volcengine."""
        response = ve_request(
            request_body=request.model_dump(by_alias=True),
            action="GetAgentKitRuntime",
            ak=self.access_key,
            sk=self.secret_key,
            region=self.region,
            service=self._service,
            version=self._api_version,
            host=self._host,
        )
        
        # 从API响应中提取数据并创建响应对象
        result = response.get('Result', {})
        return GetAgentkitRuntimeResponse(
            RuntimeId=result.get('RuntimeId', ''),
            Name=result.get('Name', ''),
            Description=result.get('Description', ''),
            ArtifactType=result.get('ArtifactType', ''),
            ArtifactUrl=result.get('ArtifactUrl', ''),
            Command=result.get('Command', ''),
            ProjectName=result.get('ProjectName', ''),
            Status=result.get('Status', ''),
            CreatedAt=result.get('CreatedAt', ''),
            UpdatedAt=result.get('UpdatedAt', ''),
            RoleName=result.get('RoleName', ''),
            AuthorizerConfiguration=result.get('AuthorizerConfiguration'),
            Envs=result.get('Envs', []),
            Tags=result.get('Tags', []),
            Endpoint=result.get('Endpoint', ''),
            ApmplusEnable=result.get('ApmplusEnable', False)
        )

    def update(
        self, request: UpdateAgentkitRuntimeRequest
    ) -> UpdateAgentkitRuntimeResponse:
        """Update an existing AgentKit Runtime on Volcengine."""
        ...

    def delete(
        self, request: DeleteAgentkitRuntimeRequest
    ) -> DeleteAgentkitRuntimeResponse:
        """Delete an AgentKit Runtime on Volcengine."""
        try:
            print(f"Delete agentkit runtime: {request.id}, body: {request.model_dump(by_alias=True)}")
            response = ve_request(
                request_body=request.model_dump(by_alias=True),
                action="DeleteAgentKitRuntime",
                ak=self.access_key,
                sk=self.secret_key,
                region=self.region,
                service=self._service,
                version=self._api_version,
                host=self._host,
            )
        except Exception as e:
            if "NOTFOUND" in str(e).upper(): # 已删除
                return DeleteAgentkitRuntimeResponse(RuntimeId=request.id)
            raise ValueError(f"Error delete agentkit runtime: {e}")
        return DeleteAgentkitRuntimeResponse(RuntimeId=response['Result']['RuntimeId'])

    def list(
        self, request: ListAgentkitRuntimesRequest
    ) -> ListAgentkitRuntimesResponse:
        """List all AgentKit Runtimes from Volcengine."""
        ...

    def release(
        self, request: ReleaseAgentkitRuntimeRequest
    ) -> ReleaseAgentkitRuntimeResponse:
        """Release an AgentKit Runtime on Volcengine."""
        ...

    def list_error_details(
        self, request: ListAgentkitRuntimeErrorDetailsRequest
    ) -> ListAgentkitRuntimeErrorDetailsResponse:
        """List error details for a specific AgentKit Runtime on Volcengine."""
        ...

    def get_version(
        self, request: GetAgentkitRuntimeVersionRequest
    ) -> GetAgentkitRuntimeVersionResponse:
        """Get the version of the AgentKit SDK."""
        ...

    def list_versions(
        self, request: ListAgentkitRuntimeVersionsRequest
    ) -> ListAgentkitRuntimeVersionsResponse:
        """List all available versions of the AgentKit SDK."""
        ...


