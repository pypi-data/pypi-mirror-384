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

from volcenginesdkcore.rest import ApiException
import volcenginesdkcore
import volcenginesdkagentkit
import volcenginesdkcr
import os
from agentkit.utils.ve_sign import get_volc_ak_sk_region


class AgentkitMemoryCollection:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
    ) -> None:
        """Agentkit Memory class."""
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

        self._host = "open.volcengineapi.com"
        self._api_version = "2020-04-01"
        self._service = "agentkitplatform"
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = self.access_key
        configuration.sk = self.secret_key
        configuration.region = self.region
        configuration.host = self._host
        # set default configuration
        volcenginesdkcore.Configuration.set_default(configuration)
    
    def create(
        self, request: volcenginesdkagentkit.CreateMemoryCollectionRequest
    ) -> volcenginesdkagentkit.CreateMemoryCollectionResponse:
        """Create a new AgentKit Memory on Volcengine."""
        resp :volcenginesdkagentkit.CreateMemoryCollectionResponse = agentkit_api.create_memory_collection(request)
        return resp
    
    def delete(
        self, request: volcenginesdkagentkit.DeleteMemoryRequest
    ) -> volcenginesdkagentkit.DeleteMemoryResponse:
        """Delete an AgentKit Memory on Volcengine."""
        resp :volcenginesdkagentkit.DeleteMemoryResponse = agentkit_api.delete_memory(request)
        return resp
    
    def list(
        self, request: volcenginesdkagentkit.ListMemoryCollectionsRequest
    ) -> volcenginesdkagentkit.ListMemoryCollectionsResponse:
        """List AgentKit Memory Collections on Volcengine."""
        resp :volcenginesdkagentkit.ListMemoryCollectionsResponse = agentkit_api.list_memory_collections(request)
        return resp
    
    def get(
        self, request: volcenginesdkagentkit.GetMemoryCollectionRequest
    ) -> volcenginesdkagentkit.GetMemoryCollectionResponse:
        """Get an AgentKit Memory Collection on Volcengine."""
        resp :volcenginesdkagentkit.GetMemoryCollectionResponse = agentkit_api.get_memory_collection(request)
        resp.long_term_configuration
        return resp
    
    def get_connection_info(
        self, request: volcenginesdkagentkit.GetMemoryConnectionInfoRequest
    ) -> volcenginesdkagentkit.GetMemoryConnectionInfoResponse:
        """Get the connection info of an AgentKit Memory Collection on Volcengine."""
        resp :volcenginesdkagentkit.GetMemoryConnectionInfoResponse = agentkit_api.get_memory_connection_info(request)
        return resp


    def update(
        self, request: volcenginesdkagentkit.UpdateMemoryCollectionRequest
    ) -> volcenginesdkagentkit.UpdateMemoryCollectionResponse:
        """Update an AgentKit Memory Collection on Volcengine."""
        resp :volcenginesdkagentkit.UpdateMemoryCollectionResponse = agentkit_api.update_memory_collection(request)
        return resp
        



if __name__ == '__main__':
    # 注意示例代码安全，代码泄漏会导致AK/SK泄漏，有极大的安全风险。
    ak, sk, region = get_volc_ak_sk_region('AGENTKIT')
    configuration = volcenginesdkcore.Configuration()
    configuration.ak = ak
    configuration.sk = sk
    configuration.region = region
    # set default configuration
    volcenginesdkcore.Configuration.set_default(configuration)
    agentkit_api = volcenginesdkagentkit.AGENTKITApi()

