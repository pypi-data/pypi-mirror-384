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
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from rich.console import Console
from agentkit.utils.misc import generate_random_id
from agentkit.utils.ve_sign import get_volc_ak_sk_region
import agentkit.toolkit.integrations.ve_cr as ve_cr
import agentkit.toolkit.config as config
from agentkit.toolkit.config import AUTO_CREATE_VE
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
import time

logger = logging.getLogger(__name__)
console = Console()

# 常量定义 - 已移动到 agentkit.toolkit.config.constants

@dataclass
class CRServiceConfig(AutoSerializableMixin):
    """CR服务配置"""
    instance_name: str = AUTO_CREATE_VE
    namespace_name: str = AUTO_CREATE_VE
    repo_name: str = AUTO_CREATE_VE
    region: str = "cn-beijing"
    vpc_id: str = field(default=AUTO_CREATE_VE, metadata={"system": True})
    subnet_id: str = field(default=AUTO_CREATE_VE, metadata={"system": True})
    image_full_url: str = field(default=None, metadata={"system": True})

@dataclass
class CRServiceResult:
    """CR服务操作结果"""
    success: bool = False
    error: Optional[str] = None
    instance_name: Optional[str] = None
    namespace_name: Optional[str] = None
    repo_name: Optional[str] = None
    registry_url: Optional[str] = None
    image_full_url: Optional[str] = None

class CRConfigCallback:
    """CR配置回调接口"""
    def on_config_update(self, cr_config: Dict[str, Any]) -> None:
        """配置更新回调"""
        pass

class DefaultCRConfigCallback(CRConfigCallback):
    """默认CR配置回调实现"""
    def __init__(self, config_updater=None):
        self.config_updater = config_updater
    
    def on_config_update(self, cr_config: Dict[str, Any]) -> None:
        """更新工作流配置"""
        if self.config_updater:
            self.config_updater("cr_service", cr_config)

class CRService:
    """CR服务类 - 提供统一的CR资源管理功能"""
    
    def __init__(self, config_callback: Optional[CRConfigCallback] = None):
        """初始化CR服务
        
        Args:
            config_callback: 配置更新回调
        """
        self.config_callback = config_callback or DefaultCRConfigCallback()
        self._vecr_client = None
        self._init_client()
    
    def _init_client(self) -> None:
        """初始化CR客户端"""
        try:
            ak, sk, region = get_volc_ak_sk_region('CR')
            self._vecr_client = ve_cr.VeCR(access_key=ak, secret_key=sk, region=region)
        except Exception as e:
            logger.error(f"初始化CR客户端失败: {str(e)}")
            raise
    
    def ensure_cr_resources(self, cr_config: CRServiceConfig, 
                           common_config: Optional[config.CommonConfig] = None) -> CRServiceResult:
        """确保CR资源存在
        
        Args:
            cr_config: CR服务配置
            common_config: 公共配置（用于获取agent_name等）
            
        Returns:
            CRServiceResult: 操作结果
        """
        try:
            result = CRServiceResult()
            
            # 确保实例存在
            if not self._ensure_cr_instance(cr_config, result):
                return result
            
            # 确保命名空间存在
            if not self._ensure_cr_namespace(cr_config, result):
                return result
            
            # 确保仓库存在
            if not self._ensure_cr_repo(cr_config, result, common_config):
                return result
            
            # 获取注册表URL
            registry_url = self._vecr_client._get_default_domain(instance_name=cr_config.instance_name)
            result.registry_url = registry_url
            
            result.success = True
            return result
            
        except Exception as e:
            result.error = f"CR资源确保失败: {str(e)}"
            logger.error(result.error)
            return result
    
    def _ensure_cr_instance(self, cr_config: CRServiceConfig, result: CRServiceResult) -> bool:
        """确保CR实例存在"""
        instance_name = cr_config.instance_name
        if not instance_name or instance_name == AUTO_CREATE_VE:
            instance_name = f"agentkit-toolkit-cli-{generate_random_id(4)}"
            console.print(f"[blue]🔧 未配置CR实例名，将创建新实例: {instance_name}[/blue]")
            try:
                created_instance = self._vecr_client._create_instance(instance_name)
                cr_config.instance_name = created_instance
                result.instance_name = created_instance
                self._notify_config_update(cr_config)
                console.print(f"[green]✅ CR实例创建成功: {created_instance}[/green]")
            except Exception as e:
                result.error = f"CR实例创建失败: {str(e)}"
                console.print(f"[red]❌ {result.error}[/red]")
                return False
        else:
            status = ""
            try:
                status = self._vecr_client._check_instance(instance_name)
                if status == "NONEXIST":
                    console.print(f"[yellow]⚠️ CR实例不存在，将创建: {instance_name}[/yellow]")
                    self._vecr_client._create_instance(instance_name)
                    console.print(f"[green]✅ CR实例创建成功: {instance_name}[/green]")
                elif status == "Running":
                    console.print(f"[green]✅ CR实例已存在且运行中: {instance_name}[/green]")
                else:
                    console.print(f"[yellow]⚠️ CR实例状态: {status}，等待其就绪...[/yellow]")
            except Exception as e:
                result.error = f"检查CR实例失败: {str(e)}"
                console.print(f"[red]❌ {result.error}[/red]")
                if status == "NONEXIST" and "AlreadyExists" in str(e):
                    console.print(f"[red]实例名称已被使用，请检查配置: {instance_name}[/red]")
                return False
        result.instance_name = cr_config.instance_name
        return True
    
    def _ensure_cr_namespace(self, cr_config: CRServiceConfig, result: CRServiceResult) -> bool:
        """确保CR命名空间存在"""
        namespace_name = cr_config.namespace_name
        if not namespace_name or namespace_name == AUTO_CREATE_VE:
            namespace_name = f"agentkit-{generate_random_id(4)}"
            console.print(f"[blue]🔧 未配置CR命名空间名，将创建新命名空间: {namespace_name}[/blue]")
            try:
                created_namespace = self._vecr_client._create_namespace(cr_config.instance_name, namespace_name)
                cr_config.namespace_name = created_namespace
                result.namespace_name = created_namespace
                self._notify_config_update(cr_config)
                console.print(f"[green]✅ CR命名空间创建成功: {created_namespace}[/green]")
            except Exception as e:
                result.error = f"CR命名空间创建失败: {str(e)}"
                console.print(f"[red]❌ {result.error}[/red]")
                return False
        else:
            try:
                self._vecr_client._create_namespace(cr_config.instance_name, namespace_name)
                console.print(f"[green]✅ CR命名空间已存在或创建成功: {namespace_name}[/green]")
            except Exception as e:
                if "AlreadyExists" in str(e):
                    console.print(f"[green]✅ CR命名空间已存在: {namespace_name}[/green]")
                else:
                    result.error = f"CR命名空间操作失败: {str(e)}"
                    console.print(f"[red]❌ {result.error}[/red]")
                    return False
        
        result.namespace_name = cr_config.namespace_name
        return True
    
    def _ensure_cr_repo(self, cr_config: CRServiceConfig, result: CRServiceResult, 
                       common_config: Optional[config.CommonConfig] = None) -> bool:
        """确保CR仓库存在"""
        repo_name = cr_config.repo_name
        if not repo_name or repo_name == AUTO_CREATE_VE:
            agent_name = common_config.agent_name if common_config else "agentkit"
            repo_name = f"{agent_name}-{generate_random_id(4)}"
            console.print(f"[blue]🔧 未配置CR仓库名，将创建新仓库: {repo_name}[/blue]")
            try:
                created_repo = self._vecr_client._create_repo(cr_config.instance_name, cr_config.namespace_name, repo_name)
                cr_config.repo_name = created_repo
                result.repo_name = created_repo
                self._notify_config_update(cr_config)
                console.print(f"[green]✅ CR仓库创建成功: {created_repo}[/green]")
            except Exception as e:
                result.error = f"CR仓库创建失败: {str(e)}"
                console.print(f"[red]❌ {result.error}[/red]")
                return False
        else:
            try:
                self._vecr_client._create_repo(cr_config.instance_name, cr_config.namespace_name, repo_name)
                console.print(f"[green]✅ CR仓库已存在或创建成功: {repo_name}[/green]")
            except Exception as e:
                if "AlreadyExists" in str(e):
                    console.print(f"[green]✅ CR仓库已存在: {repo_name}[/green]")
                else:
                    result.error = f"CR仓库操作失败: {str(e)}"
                    console.print(f"[red]❌ {result.error}[/red]")
                    return False
        
        result.repo_name = cr_config.repo_name
        return True
    
    def ensure_public_endpoint(self, cr_config: CRServiceConfig) -> CRServiceResult:
        """确保公网访问已启用"""
        result = CRServiceResult()
        try:
            public_endpoint = self._vecr_client._get_public_endpoint(instance_name=cr_config.instance_name)
            if public_endpoint["Enabled"] == False:
                console.print(f"[yellow]⚠️ CR公网访问未启用，正在启用公网访问[/yellow]")
                self._vecr_client._update_public_endpoint(instance_name=cr_config.instance_name, enabled=True)
                self._vecr_client._create_endpoint_acl_policies(instance_name=cr_config.instance_name, acl_policies=["0.0.0.0/0"])
                
                timeout = 120
                while timeout > 0:
                    public_endpoint = self._vecr_client._get_public_endpoint(instance_name=cr_config.instance_name)
                    if public_endpoint["Status"] == "Enabled":
                        break
                    timeout -= 1
                    time.sleep(1)
                if timeout <= 0:
                    result.error = "CR公网访问启用超时"
                    console.print(f"[red]❌ {result.error}[/red]")
                    return result
                console.print(f"✅ CR公网访问启用成功")
            
            result.success = True
            return result
            
        except Exception as e:
            result.error = f"公网访问配置失败: {str(e)}"
            console.print(f"[red]❌ {result.error}[/red]")
            return result
    
    def login_and_push_image(self, cr_config: CRServiceConfig, image_id: str, 
                            image_tag: str, namespace: str) -> Tuple[bool, str]:
        """登录CR并推送镜像
        
        Args:
            cr_config: CR服务配置
            image_id: 本地镜像ID
            image_tag: 镜像标签
            namespace: 命名空间
            
        Returns:
            (是否成功, 远程镜像完整URL或错误信息)
        """
        try:
            from agentkit.toolkit.integrations.container import DockerManager
        except ImportError:
            error_msg = "缺少Docker相关依赖"
            console.print(f"[red]错误: {error_msg}[/red]")
            return False, error_msg
            
        docker_manager = DockerManager()
        
        # 获取登录信息
        registry_url = self._vecr_client._get_default_domain(instance_name=cr_config.instance_name)   
        username, token, expires = self._vecr_client._get_authorization_token(instance_name=cr_config.instance_name)
        console.print(f"✅ 获取CR登录信息成功: username={username}, expires={expires}")
        
        # 登录
        success, message = docker_manager.login_to_registry(
            registry_url=registry_url,
            username=username,
            password=token
        )
        
        if not success:
            error_msg = f"登录CR失败: {message}"
            console.print(f"[red]❌ {error_msg}[/red]")
            return False, error_msg
        
        console.print(f"✅ 登录成功")
        
        # 推送镜像
        console.print(f"[yellow]正在推送镜像 {image_id[:12]} 到 {registry_url}[/yellow]")
        success, remote_image_full_url = docker_manager.push_image(
            local_image=image_id,
            registry_url=registry_url,
            namespace=namespace,
            remote_image_name=cr_config.repo_name,
            remote_tag=image_tag
        )
        
        if success:
            console.print(f"✅ 推送成功: {remote_image_full_url}")
            cr_config.image_full_url = remote_image_full_url
            self._notify_config_update(cr_config)
            return True, remote_image_full_url
        else:
            error_msg = f"推送失败: {remote_image_full_url}"
            console.print(f"[red]❌ {error_msg}[/red]")
            return False, error_msg
    
    def _notify_config_update(self, cr_config: CRServiceConfig) -> None:
        """通知配置更新"""
        try:
            config_dict = cr_config.to_dict()
            self.config_callback.on_config_update(config_dict)
        except Exception as e:
            logger.warning(f"配置更新通知失败: {str(e)}")
    
    def get_cr_config(self) -> Dict[str, Any]:
        """获取CR配置，用于pipeline模板渲染"""
        if not self._vecr_client:
            return {}
        
        try:
            # 这里可以根据需要返回更多CR相关配置
            return {
                "cr_domain": self._vecr_client._get_default_domain(instance_name=""),  # 需要根据实际实例获取
                "cr_region": self._vecr_client.region,
            }
        except Exception as e:
            logger.warning(f"获取CR配置失败: {str(e)}")
            return {}