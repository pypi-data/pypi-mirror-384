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

import logging
import requests
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

from agentkit.toolkit.config import CommonConfig, AUTO_CREATE_VE
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
from agentkit.utils.misc import generate_random_id
from agentkit.runtime.runtime import AgentkitRuntime, ARTIFACT_TYPE_DOCKER_IMAGE, PROJECT_NAME_DEFAULT, API_KEY_LOCATION, RUNTIME_STATUS_READY, RUNTIME_STATUS_ERROR, GetAgentkitRuntimeRequest
from agentkit.runtime.types import CreateAgentkitRuntimeRequest, CreateAgentkitRuntimeResponse, DeleteAgentkitRuntimeRequest, AuthorizerConfiguration, KeyAuth_

from .base import Runner

logger = logging.getLogger(__name__)

console = Console()

@dataclass
class VeAgentkitRunnerConfig(AutoSerializableMixin):
    """VeAgentkit Runner配置"""
    common_config: Optional[CommonConfig] = field(default=None, metadata={"system": True, "description": "公共配置"})
    
    # Runtime配置
    runtime_id: str = field(default=AUTO_CREATE_VE, metadata={"description": "Runtime ID，Auto表示自动创建"})
    runtime_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "Runtime名称，Auto表示自动生成"})
    runtime_role_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "Runtime角色名称，Auto表示自动创建"})
    runtime_apikey: str = field(default="", metadata={"description": "Runtime API密钥"})
    runtime_apikey_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "Runtime API密钥名称，Auto表示自动生成"})
    runtime_endpoint: str = field(default="", metadata={"description": "Runtime访问端点"})
    runtime_envs: Dict[str, str] = field(default_factory=dict, metadata={"description": "Runtime环境变量"})
    
    # 镜像配置
    image_url: str = field(default="", metadata={"description": "容器镜像完整URL"})


@dataclass
class VeAgentkitDeployResult(AutoSerializableMixin):
    """部署结果"""
    success: bool = field(default=False)
    runtime_id: str = field(default="")
    runtime_name: str = field(default="")
    runtime_endpoint: str = field(default="")
    runtime_apikey: str = field(default="")
    message: str = field(default="")
    error: str = field(default="")


class VeAgentkitRuntimeRunner(Runner):
    """VeAgentkit Runtime Runner
    
    负责管理云上Runtime的生命周期，包括：
    - 创建和管理Runtime实例
    - 部署和更新Runtime配置
    - 调用Runtime服务
    - 监控Runtime状态
    - 清理Runtime资源
    """
    
    def __init__(self):
        self.agentkit_runtime = AgentkitRuntime()
    
    def deploy(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """部署Runtime
        
        Args:
            config: 部署配置，包含Runtime相关配置
            
        Returns:
            (成功标志, 部署结果字典)
        """
        try:
            runner_config = VeAgentkitRunnerConfig.from_dict(config)
            runner_config.common_config = CommonConfig.from_dict(runner_config.common_config)
            
            if not runner_config.image_url:
                return False, {"error": "镜像URL不能为空，请先构建镜像"}
            
            # 准备Runtime配置
            if not self._prepare_runtime_config(runner_config):
                return False, {"error": "Runtime配置准备失败"}
            
            # 部署Runtime
            if runner_config.runtime_id == AUTO_CREATE_VE:
                return self._create_new_runtime(runner_config)
            else:
                return self._update_existing_runtime(runner_config)
                
        except Exception as e:
            logger.error(f"Runtime部署失败: {str(e)}")
            return False, {"error": str(e)}
    
    def destroy(self, config: Dict[str, Any]) -> bool:
        """销毁Runtime
        
        Args:
            config: 销毁配置，包含Runtime ID
            
        Returns:
            是否成功
        """
        try:
            runner_config = VeAgentkitRunnerConfig.from_dict(config)
            
            if not runner_config.runtime_id or runner_config.runtime_id == AUTO_CREATE_VE:
                console.print("未配置Runtime ID，跳过销毁")
                return True
            
            # 删除Runtime
            delete_request = DeleteAgentkitRuntimeRequest(
                RuntimeId=runner_config.runtime_id
            )
            
            self.agentkit_runtime.delete(delete_request)
            console.print(f"✅ Runtime销毁成功: {runner_config.runtime_id}")
            return True
            
        except Exception as e:
            logger.error(f"Runtime销毁失败: {str(e)}")
            return False

    def status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取Runtime状态
        
        Args:
            config: 状态查询配置，包含Runtime ID
            
        Returns:
            Runtime状态信息
        """
        try:
            runner_config = VeAgentkitRunnerConfig.from_dict(config)
            
            if not runner_config.runtime_id or runner_config.runtime_id == AUTO_CREATE_VE:
                return {"status": "not_deployed", "message": "未部署Runtime"}
            
            # 获取Runtime信息
            runtime = self.agentkit_runtime.get(
                GetAgentkitRuntimeRequest(RuntimeId=runner_config.runtime_id)
            )
            
            # 检查Endpoint连通性
            ping_status = None
            if runtime.status == RUNTIME_STATUS_READY and runtime.endpoint:
                try:
                    ping_response = requests.get(
                        urljoin(runtime.endpoint, "ping"), 
                        timeout=10
                    )
                    ping_status = ping_response.status_code == 200
                except:
                    ping_status = False
            
            return {
                "runtime_id": runner_config.runtime_id,
                "runtime_name": runtime.name if hasattr(runtime, 'name') else runner_config.runtime_name,
                "status": runtime.status,
                "endpoint": runtime.endpoint if hasattr(runtime, 'endpoint') else "",
                "image_url": runtime.artifact_url if hasattr(runtime, 'artifact_url') else "",
                "ping_status": ping_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取Runtime状态失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def invoke(self, config: Dict[str, Any], payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Any]:
        """调用Runtime服务
        
        Args:
            config: 调用配置，包含Runtime端点和API密钥
            payload: 请求负载
            headers: 请求头
            
        Returns:
            (成功标志, 响应数据)
        """
        try:
            runner_config = VeAgentkitRunnerConfig.from_dict(config)
            
            # 获取Runtime端点和API密钥
            endpoint = runner_config.runtime_endpoint
            api_key = runner_config.runtime_apikey
            
            if not endpoint or not api_key:
                if not runner_config.runtime_id or runner_config.runtime_id == AUTO_CREATE_VE:
                    return False, {"error": "Runtime未部署"}
                
                # 自动获取Runtime信息
                runtime = self.agentkit_runtime.get(
                    GetAgentkitRuntimeRequest(RuntimeId=runner_config.runtime_id)
                )
                endpoint = runtime.endpoint
                api_key = runtime.authorizer_configuration.KeyAuth.ApiKey
                
                if not endpoint or not api_key:
                    return False, {"error": f"无法获取Runtime端点或API密钥, runtime: {runtime}"}
            
            # 构造调用URL
            invoke_endpoint = urljoin(endpoint, "invoke")
            
            # 准备请求头
            if headers is None:
                headers = {}
            
            if not headers.get("Authorization"):
                headers["Authorization"] = f"Bearer {api_key}"
            
            # 发送请求
            console.print(f"调用Runtime: {invoke_endpoint}")
            response = requests.post(
                url=invoke_endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                return False, {
                    "error": f"调用失败: {response.status_code}",
                    "details": response.text
                }
            
            return True, response.json()
            
        except Exception as e:
            logger.error(f"Runtime调用失败: {str(e)}")
            return False, {"error": str(e)}
    
    def _prepare_runtime_config(self, config: VeAgentkitRunnerConfig) -> bool:
        """准备Runtime配置
        
        Args:
            config: Runner配置
            
        Returns:
            是否成功
        """
        try:
            # 检查并创建Runtime名称
            if config.runtime_name == AUTO_CREATE_VE or not config.runtime_name:
                config.runtime_name = f"{config.common_config.agent_name}-{generate_random_id()}"
                console.print(f"✅ 生成Runtime名称: {config.runtime_name}")
            
            # 检查并创建角色名称
            if config.runtime_role_name == AUTO_CREATE_VE or not config.runtime_role_name:
                config.runtime_role_name = "TestRoleForAgentKit" #f"iam-agentkit-{config.common_config.agent_name}-{generate_random_id()}"
                # console.print(f"✅ 生成角色名称: {config.runtime_role_name}")
            
            # 检查并创建API密钥名称
            if config.runtime_apikey_name == AUTO_CREATE_VE or not config.runtime_apikey_name:
                config.runtime_apikey_name = f"API-KEY-{generate_random_id()}"
                console.print(f"✅ 生成API密钥名称: {config.runtime_apikey_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Runtime配置准备失败: {str(e)}")
            return False
    
    def _create_new_runtime(self, config: VeAgentkitRunnerConfig) -> Tuple[bool, Dict[str, Any]]:
        """创建新Runtime
        
        Args:
            config: Runner配置
            
        Returns:
            (成功标志, 部署结果字典)
        """
        try:
            console.print(f"[blue]正在创建Runtime: {config.runtime_name}[/blue]")
            
            # 构建创建请求
            envs = [{"Key": k, "Value": v} for k, v in config.runtime_envs.items()]
            
            create_request = CreateAgentkitRuntimeRequest(
                Name=config.runtime_name,
                Description=f"Auto created by VeAgentkitRuntimeRunner for agent project {config.common_config.agent_name}",
                ArtifactType=ARTIFACT_TYPE_DOCKER_IMAGE,
                ArtifactUrl=config.image_url,
                RoleName=config.runtime_role_name,
                Envs=envs,
                ProjectName=PROJECT_NAME_DEFAULT,
                AuthorizerConfiguration=AuthorizerConfiguration(
                    KeyAuth=KeyAuth_(
                        ApiKey=config.runtime_apikey,
                        ApiKeyName=config.runtime_apikey_name,
                        ApiKeyLocation=API_KEY_LOCATION
                    ),
                ),
                ClientToken=generate_random_id(16),
                Tags=[{"Key": "environment", "Value": "test"}],
                ApmplusEnable=True,
            )
            
            console.print("创建请求:")
            console.print(json.dumps(create_request.model_dump(by_alias=True), indent=2))
            
            # 创建Runtime
            runtime_resp, request_id = self.agentkit_runtime.create(create_request)
            config.runtime_id = runtime_resp.id
            
            console.print(f"✅ [green]创建Runtime成功: {runtime_resp.id}, request_id: {request_id}[/green]")
            console.print("[blue]等待Runtime状态为Ready...[/blue]")
            console.print("[blue]💡 提示：Runtime初始化通常需要2-3分钟，请耐心等待，不要中断进程[/blue]")
            
            # 等待Runtime就绪，使用进度条显示
            last_status = None
            start_time = time.time()
            estimated_total_time = 130  # 预计总时间（秒）
            
            # 创建进度条
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                "<", TimeRemainingColumn(),
                console=console
            ) as progress:
                
                # 创建进度任务
                task = progress.add_task("等待Runtime就绪...", total=estimated_total_time)
                
                while True:
                    runtime = self.agentkit_runtime.get(
                        GetAgentkitRuntimeRequest(RuntimeId=config.runtime_id)
                    )
                    
                    if runtime.status == RUNTIME_STATUS_READY:
                        # 完成进度条
                        progress.update(task, completed=estimated_total_time)
                        console.print(f"✅ Runtime状态为Ready, Endpoint: {runtime.endpoint}")
                        config.runtime_endpoint = runtime.endpoint
                        config.runtime_apikey = runtime.authorizer_configuration.KeyAuth.ApiKey
                        
                        return True, {
                            "runtime_id": config.runtime_id,
                            "runtime_name": config.runtime_name,
                            "runtime_endpoint": runtime.endpoint,
                            "runtime_apikey": config.runtime_apikey,
                            "message": "Runtime创建成功"
                        }
                    
                    if runtime.status == RUNTIME_STATUS_ERROR:
                        # 标记为失败
                        progress.update(task, description="[red]Runtime创建失败[/red]")
                        return False, {"error": "Runtime状态为Error，创建失败"}
                    
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    # 状态变化时更新进度条描述
                    if runtime.status != last_status:
                        progress.update(task, description=f"Runtime状态: {runtime.status}")
                        last_status = runtime.status
                    
                    # 更新进度（基于时间，因为状态变化不频繁）
                    progress.update(task, completed=min(elapsed_time, estimated_total_time))
                    
                    time.sleep(3)
                
        except Exception as e:
            logger.error(f"创建Runtime失败: {str(e)}")
            return False, {"error": str(e)}
    
    def _update_existing_runtime(self, config: VeAgentkitRunnerConfig) -> Tuple[bool, Dict[str, Any]]:
        """更新现有Runtime
        
        Args:
            config: Runner配置
            
        Returns:
            (成功标志, 更新结果字典)
        """
        try:
            console.print(f"正在更新Runtime: {config.runtime_id}")
            
            # 获取现有Runtime信息
            runtime = self.agentkit_runtime.get(
                GetAgentkitRuntimeRequest(RuntimeId=config.runtime_id)
            )
            
            if not runtime:
                return False, {"error": f"未找到Runtime: {config.runtime_id}"}
            
            if runtime.artifact_type != ARTIFACT_TYPE_DOCKER_IMAGE:
                return False, {"error": f"不支持的Runtime类型: {runtime.artifact_type}"}
            
            # 检查是否需要更新
            if runtime.artifact_url == config.image_url:
                console.print(f"✅ Runtime镜像URL已是最新: {config.image_url}")
                config.runtime_endpoint = runtime.endpoint
                config.runtime_apikey = runtime.authorizer_configuration.KeyAuth.ApiKey
                
                return True, {
                    "runtime_id": config.runtime_id,
                    "runtime_name": runtime.name if hasattr(runtime, 'name') else config.runtime_name,
                    "runtime_endpoint": runtime.endpoint,
                    "runtime_apikey": config.runtime_apikey,
                    "message": "Runtime配置已是最新"
                }
            
            console.print(f"更新Runtime镜像: {runtime.artifact_url} -> {config.image_url}")
            
            # TODO: 实现Runtime更新逻辑
            # 这里需要调用Agentkit Runtime API的更新接口
            console.print("[yellow]⚠️ Runtime更新功能待实现[/yellow]")
            
            config.runtime_endpoint = runtime.endpoint
            config.runtime_apikey = runtime.authorizer_configuration.KeyAuth.ApiKey
            
            return True, {
                "runtime_id": config.runtime_id,
                "runtime_name": runtime.name if hasattr(runtime, 'name') else config.runtime_name,
                "runtime_endpoint": runtime.endpoint,
                "runtime_apikey": config.runtime_apikey,
                "message": "Runtime更新完成"
            }
            
        except Exception as e:
            logger.error(f"更新Runtime失败: {str(e)}")
            return False, {"error": str(e)}