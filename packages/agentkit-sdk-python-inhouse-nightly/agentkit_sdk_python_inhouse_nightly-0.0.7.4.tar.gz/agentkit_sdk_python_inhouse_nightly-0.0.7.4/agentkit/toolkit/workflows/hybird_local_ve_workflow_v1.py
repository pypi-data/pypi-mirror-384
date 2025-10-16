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

from agentkit.toolkit.workflows import Workflow
from typing import Dict, Any
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from rich.console import Console
console = Console()
from agentkit.toolkit.config import AUTO_CREATE_VE
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
import os
from pathlib import Path
import agentkit.toolkit.config as config
import agentkit.toolkit.integrations.ve_cr as ve_cr
import agentkit.runtime.types as runtime_types
from datetime import datetime
from agentkit.toolkit.config.auto_prompt import auto_prompt
from agentkit.runtime.runtime import AgentkitRuntime, ARTIFACT_TYPE_DOCKER_IMAGE,PROJECT_NAME_DEFAULT,API_KEY_LOCATION,RUNTIME_STATUS_READY,GetAgentkitRuntimeRequest,RUNTIME_STATUS_ERROR
from agentkit.runtime.types import AuthorizerConfiguration, KeyAuth_
from agentkit.utils.misc import generate_random_id
from agentkit.utils.ve_sign import get_volc_ak_sk_region
from agentkit.toolkit.config import get_config
from agentkit.toolkit.integrations.services import CRService, CRServiceConfig, DefaultCRConfigCallback
from agentkit.toolkit.integrations.runner import VeAgentkitRuntimeRunner
import time
import json
from urllib.parse import urljoin
import requests


@dataclass
class HybridVeAgentkitConfig_v1(AutoSerializableMixin):
    """本地Docker工作流配置"""
    # 用户可配置字段
    image_tag: str = field(default="latest", metadata={"description": "Docker镜像标签", "icon": "🏷️"})
    # 系统内部字段（用户不可见）
    image_id: str = field(default=None, metadata={"system": True})
    build_timestamp: str = field(default=None, metadata={"system": True})
    full_image_name: str = field(default=None, metadata={"system": True})

    ve_region: str = field(default="cn-beijing", metadata={"description": "火山引擎区域", "icon": "🌏"})
    
    # CR相关配置
    ve_cr_instance_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "容器镜像服务实例名称", "icon": "📦"})
    ve_cr_namespace_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "容器镜像命名空间", "icon": "📁"})
    ve_cr_repo_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "容器镜像仓库名称", "icon": "📋"})
    ve_cr_image_full_url: str = field(default=None, metadata={"system": True})

    # runtime相关配置
    ve_runtime_role_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "VE运行时角色名称", "icon": "🔐"})
    ve_runtime_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "VE运行时名称", "icon": "⚙️"})
    ve_runtime_id: str = field(default=None, metadata={"system": True})
    ve_runtime_apikey: str = field(default="", metadata={"system": True})
    ve_runtime_apikey_name: str = field(default=AUTO_CREATE_VE, metadata={"system": True})
    ve_runtime_endpoint: str = field(default="", metadata={"system": True, "description": "运行时访问入口，自动获取"})
    ve_runtime_envs: Dict[str, str] = field(
        default_factory=dict, 
        metadata={
            "description": "运行时环境变量 (输入 KEY=VALUE，空行结束，del KEY 删除，list 查看)",
            "examples": "MODEL_AGENT_API_KEY=your_key_here, DEBUG=true",
            "icon": "🔧"
        }
    )
    _config_metadata = {
        'name': '混合部署运行模式',
        'welcome_message': 'ℹ️ 欢迎使用 AgentKit 混合部署运行模式 配置向导',
        'next_step_hint': '本向导将帮助您完成混合模式下应用部署运行相关配置，请根据提示输入相关信息，或直接按Enter键使用默认值。',
        'completion_message': '太棒了！部署运行配置已完成！',
        'next_action_hint': '下面将开始针对您选择的部署模式进行配置。'
    }


class HybridVeAgentkitWorkflow_v1(Workflow):
    def prompt_for_config(self, current_config: Dict[str, Any] = None) -> Dict[str, Any]:
        from agentkit.toolkit.config.auto_prompt import auto_prompt
        ve_config = auto_prompt.generate_config(HybridVeAgentkitConfig_v1, current_config)
        return ve_config

    def build(self, config: Dict[str, Any]) -> bool:
        """Build the agent image using LocalDockerBuilder."""
        try:
            from agentkit.toolkit.integrations.builder.local_docker_builder import LocalDockerBuilder, LocalDockerBuilderConfig, LocalDockerBuilderResult
        except ImportError as e:
            console.print(f"ImportError: {e}")
            console.print("[red]错误: 缺少Docker相关依赖，请安装agentkit[docker] extras[/red]")
            return False
        try:
            hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
            if hybrid_ve_config.ve_cr_image_full_url:
                console.print(f"[yellow]⚠️ 已配置远程镜像: {hybrid_ve_config.ve_cr_image_full_url}，将跳过本地构建[/yellow]")
                return True
            
            agent_config = get_config()
            common_config = agent_config.get_common_config()

            # 使用LocalDockerBuilderConfig类构建配置，避免硬编码字符串
            builder_config_obj = LocalDockerBuilderConfig(
                common_config=common_config,
                image_name=common_config.agent_name or "agentkit-app",
                image_tag=hybrid_ve_config.image_tag
            )
            builder_config = builder_config_obj.to_dict()

            builder = LocalDockerBuilder()
            success, build_result = builder.build(builder_config)
            result_obj = LocalDockerBuilderResult.from_dict(build_result)            
            if success:
                hybrid_ve_config.full_image_name = result_obj.full_image_name
                hybrid_ve_config.image_id = result_obj.image_id
                hybrid_ve_config.build_timestamp = result_obj.build_timestamp
                
                agent_config.update_workflow_config("hybrid", hybrid_ve_config.to_dict())
                return True
            else:
                build_logs = result_obj.build_logs or []
                console.print(f"[red]❌ 镜像构建失败[/red]")
                if build_logs:
                    console.print(build_logs)
                return False
                
        except Exception as e:
            console.print(f"[red]构建过程中发生错误: {str(e)}[/red]")
            return False

    def deploy(self, config: Dict[str, Any]) -> bool:
        """简化后的主部署函数 - 仅负责流程编排"""
        try:
            hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
            agent_config = get_config()
            common_config = agent_config.get_common_config()
            
            # 1. 镜像准备阶段
            if not self._prepare_and_push_image(hybrid_ve_config, common_config):
                return False
            
            # 2. Runtime 部署阶段  
            return self._deploy_runtime(hybrid_ve_config, common_config)
            
        except Exception as e:
            console.print(f"[red]部署失败: {str(e)}[/red]")
            return False
    
    def _prepare_and_push_image(self, config: HybridVeAgentkitConfig_v1, common_config: config.CommonConfig) -> bool:
        """镜像准备和推送"""
        if config.ve_cr_image_full_url:
            return True
            
        if not self._check_local_image(config, common_config):
            return False
            
        return self._push_image_to_cr(config, common_config)
    
    def _check_local_image(self, config: HybridVeAgentkitConfig_v1, common_config: config.CommonConfig) -> bool:
        """检查本地镜像"""
        try:
            from agentkit.toolkit.integrations.container import DockerManager
        except ImportError:
            console.print("[red]错误: 缺少Docker相关依赖[/red]")
            return False
            
        docker_manager = DockerManager()
        image_exists, image_info, actual_image_id = docker_manager.check_image_exists(
            config.full_image_name or f"{common_config.agent_name or 'agentkit-app'}:{config.image_tag}", 
            config.image_id
        )
        
        if not image_exists:
            console.print(f"[red]❌ 镜像不存在，请先运行 build 命令[/red]")
            return False
            
        # 更新镜像ID
        config.image_id = actual_image_id
        console.print(f"[green]✅ 找到镜像，ID: {actual_image_id[:12]}[/green]")
        return True
    
    def _push_image_to_cr(self, config: HybridVeAgentkitConfig_v1, common_config: config.CommonConfig) -> bool:
        """推送镜像到CR - 使用新的CR服务"""
        # 创建CR配置回调
        def config_updater(workflow_name: str, cr_config_dict: Dict[str, Any]) -> None:
            """配置更新回调"""
            # 将CR配置同步到工作流配置
            if "instance_name" in cr_config_dict:
                config.ve_cr_instance_name = cr_config_dict["instance_name"]
            if "namespace_name" in cr_config_dict:
                config.ve_cr_namespace_name = cr_config_dict["namespace_name"]
            if "repo_name" in cr_config_dict:
                config.ve_cr_repo_name = cr_config_dict["repo_name"]
            if "image_full_url" in cr_config_dict:
                config.ve_cr_image_full_url = cr_config_dict["image_full_url"]
            
            # 更新工作流配置
            get_config().update_workflow_config("hybrid", config.to_dict())
        
        # 创建CR服务配置
        cr_service_config = CRServiceConfig(
            instance_name=config.ve_cr_instance_name,
            namespace_name=config.ve_cr_namespace_name,
            repo_name=config.ve_cr_repo_name,
            image_full_url=config.ve_cr_image_full_url
        )
        
        # 创建CR服务
        cr_service = CRService(config_callback=DefaultCRConfigCallback(config_updater=config_updater))
        
        # 确保CR资源存在
        cr_result = cr_service.ensure_cr_resources(cr_service_config, common_config)
        if not cr_result.success:
            console.print(f"[red]❌ CR资源准备失败: {cr_result.error}[/red]")
            return False
        
        # 确保公网访问
        public_result = cr_service.ensure_public_endpoint(cr_service_config)
        if not public_result.success:
            console.print(f"[red]❌ 公网访问配置失败: {public_result.error}[/red]")
            return False
        
        # 登录并推送镜像
        success, remote_image_full_url = cr_service.login_and_push_image(
            cr_service_config,
            config.image_id,
            config.image_tag,
            cr_result.namespace_name
        )
        
        if success:
            config.ve_cr_image_full_url = remote_image_full_url
            get_config().update_workflow_config("hybrid", config.to_dict())
            return True
        else:
            return False
    
    # 原有的CR相关方法已经移除，逻辑已迁移到CRService中
    
    def _deploy_runtime(self, config: HybridVeAgentkitConfig_v1, common_config) -> bool:
        """部署Runtime - 使用VeAgentkitRuntimeRunner"""
        try:
            # 创建Runner配置
            runner_config = {
                "common_config": common_config.to_dict(),
                "runtime_id": config.ve_runtime_id or AUTO_CREATE_VE,
                "runtime_name": config.ve_runtime_name,
                "runtime_role_name": config.ve_runtime_role_name,
                "runtime_apikey": config.ve_runtime_apikey,
                "runtime_apikey_name": config.ve_runtime_apikey_name,
                "runtime_endpoint": config.ve_runtime_endpoint,
                "runtime_envs": config.ve_runtime_envs,
                "image_url": config.ve_cr_image_full_url
            }
            
            # 使用Runner部署
            runner = VeAgentkitRuntimeRunner()
            success, result = runner.deploy(runner_config)
            
            if success:
                # 更新配置
                config.ve_runtime_id = result["runtime_id"]
                config.ve_runtime_name = result["runtime_name"]
                config.ve_runtime_endpoint = result["runtime_endpoint"]
                config.ve_runtime_apikey = result["runtime_apikey"]
                
                # 保存配置
                agent_config = get_config()
                agent_config.update_workflow_config("hybrid", config.to_dict())
                
                console.print(f"[green]✅ Runtime部署成功: {result['message']}[/green]")
                return True
            else:
                console.print(f"[red]❌ Runtime部署失败: {result.get('error', '未知错误')}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Runtime部署异常: {str(e)}[/red]")
            return False

    def invoke(self, config: Dict[str, Any], args: Dict[str, Any]) -> bool:
        """Invoke the workflow - 使用VeAgentkitRuntimeRunner.
        Args:
            config (Dict[str, Any]): The configuration of the workflow.
        Returns:
            bool: True if the invocation was successful, False otherwise.
        """
        hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
        if not hybrid_ve_config.ve_runtime_id:
            console.print(f"❌ 暂未部署到Agentkit Platform")
            return False
        try:
            # 创建Runner配置
            runner_config = {
                "common_config": {},
                "runtime_id": hybrid_ve_config.ve_runtime_id,
                "runtime_endpoint": hybrid_ve_config.ve_runtime_endpoint,
                "runtime_apikey": hybrid_ve_config.ve_runtime_apikey
            }
            payload = args.get("payload", {"prompt": "北京天气怎么样"})
            if isinstance(payload, str):
                payload = json.loads(payload)
            headers = args.get("headers", {"user_id": "agentkit_user", "session_id": "agentkit_sample_session"})
            if isinstance(headers, str):
                headers = json.loads(headers)
            # 使用Runner调用
            runner = VeAgentkitRuntimeRunner()
            success, result = runner.invoke(runner_config, payload, headers)
            if success:
                console.print(f"[green]✅ Runtime调用成功[/green]")
                console.print(f"📡 响应内容: {result}")
                return True
            else:
                console.print(f"[red]❌ Runtime调用失败: {result}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ 调用Runtime异常: {str(e)}[/red]")
            return False
        

    def status(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get the status of the workflow - 使用VeAgentkitRuntimeRunner."""
        hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
        if not hybrid_ve_config.ve_runtime_id or hybrid_ve_config.ve_runtime_id == AUTO_CREATE_VE:
            console.print(f"❌ 暂未部署到Agentkit Platform")
            return {}
        try:
            # 创建Runner配置
            runner_config = {
                "common_config": {},
                "runtime_id": hybrid_ve_config.ve_runtime_id,
                "runtime_endpoint": hybrid_ve_config.ve_runtime_endpoint
            }
            # 使用Runner获取状态
            runner = VeAgentkitRuntimeRunner()
            status_info = runner.status(runner_config)
            # 控制台输出
            if status_info.get("status") == "Ready":
                console.print(f"[green]✅ Runtime状态为Ready, Endpoint: {status_info.get('endpoint')}[/green]")
            else:
                console.print(f"[yellow]当前Runtime状态: {status_info.get('status')}，状态异常[/yellow]")
            return status_info
        except Exception as e:
            console.print(f"[red]❌ 获取Runtime状态失败: {str(e)}[/red]")
            return {"status": "error", "message": str(e)}
        

    def stop(self) -> None:
        """Stop the workflow - 使用VeAgentkitRuntimeRunner."""
        agent_config = get_config()
        config = agent_config.get_workflow_config("hybrid")
        hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
        if not hybrid_ve_config.ve_runtime_id or hybrid_ve_config.ve_runtime_id == AUTO_CREATE_VE:
            console.print(f"[yellow]⚠️ 未配置Runtime ID，无需停止[/yellow]")
            return
        try:
            # 创建Runner配置
            runner_config = {
                "common_config": {},
                "runtime_id": hybrid_ve_config.ve_runtime_id
            }
            # 使用Runner停止
            runner = VeAgentkitRuntimeRunner()
            success = runner.stop(runner_config)
            if success:
                console.print(f"[green]✅ Runtime停止成功[/green]")
            else:
                console.print(f"[red]❌ Runtime停止失败[/red]")
        except Exception as e:
            console.print(f"[red]❌ 停止Runtime异常: {str(e)}[/red]")

    def destroy(self) -> None:
        """Stop and destroy the workflow resources - 使用VeAgentkitRuntimeRunner."""
        agent_config = get_config()
        config = agent_config.get_workflow_config("hybrid")
        hybrid_ve_config = HybridVeAgentkitConfig_v1.from_dict(config)
        if not hybrid_ve_config.ve_runtime_id or hybrid_ve_config.ve_runtime_id == AUTO_CREATE_VE:
            console.print(f"[yellow]⚠️ 未配置Runtime ID，无需销毁[/yellow]")
            return
        try:
            # 创建Runner配置
            runner_config = {
                "common_config": {},
                "runtime_id": hybrid_ve_config.ve_runtime_id
            }
            # 使用Runner销毁
            runner = VeAgentkitRuntimeRunner()
            success = runner.destroy(runner_config)
            if success:
                # 清除配置中的Runtime信息
                hybrid_ve_config.ve_runtime_id = ""
                hybrid_ve_config.ve_runtime_endpoint = ""
                hybrid_ve_config.ve_runtime_apikey = ""
                agent_config.update_workflow_config("hybrid", hybrid_ve_config.to_dict())
                console.print(f"[green]✅ Runtime销毁成功[/green]")
            else:
                console.print(f"[red]❌ Runtime销毁失败[/red]")
        except Exception as e:
            console.print(f"[red]❌ 销毁Runtime异常: {str(e)}[/red]")