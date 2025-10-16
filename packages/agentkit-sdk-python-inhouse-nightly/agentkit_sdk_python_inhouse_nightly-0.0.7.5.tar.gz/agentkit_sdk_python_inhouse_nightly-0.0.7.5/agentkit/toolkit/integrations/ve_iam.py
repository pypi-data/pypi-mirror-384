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
import volcenginesdkecs
import volcenginesdkcr
import volcenginesdkiam
import os
from agentkit.utils.ve_sign import get_volc_ak_sk_region


if __name__ == '__main__':
    ak, sk, region = get_volc_ak_sk_region('IAM')
    configuration = volcenginesdkcore.Configuration()
    configuration.ak = ak
    configuration.sk = sk
    configuration.region = region
    # set default configuration
    volcenginesdkcore.Configuration.set_default(configuration)


    # IAM test
    iam_api = volcenginesdkiam.IAMApi()
    body = volcenginesdkiam.ListUsersRequest()
    resp :volcenginesdkiam.ListUsersResponse = iam_api.list_users(body)
    print(resp)

    body = volcenginesdkiam.ListRolesRequest()
    resp :volcenginesdkiam.ListRolesResponse = iam_api.list_roles(body)
    print(resp)
