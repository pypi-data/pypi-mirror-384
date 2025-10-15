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

import os
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from agentkit.toolkit.config import CommonConfig, AUTO_CREATE_VE, DEFAULT_WORKSPACE_NAME
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
from agentkit.utils.misc import generate_random_id
from agentkit.toolkit.integrations.services import CRService, CRServiceConfig, DefaultCRConfigCallback
from .base import Builder



logger = logging.getLogger(__name__)

console = Console()

# 常量定义 - 已移动到 agentkit.toolkit.config.constants

@dataclass
class VeCPCRBuilderConfig(AutoSerializableMixin):
    """VeCPCRBuilder配置类"""
    
    # 公共配置
    common_config: Optional[CommonConfig] = field(default=None, metadata={"system": True, "description": "公共配置"})
    
    # TOS配置
    tos_bucket: str = field(default=AUTO_CREATE_VE, metadata={"description": "TOS存储桶名称"})
    tos_region: str = field(default="cn-beijing", metadata={"description": "TOS区域"})
    tos_prefix: str = field(default="agentkit-builds", metadata={"description": "TOS路径前缀"})
    
    # CR配置
    cr_instance_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "CR实例名称"})
    cr_namespace_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "CR命名空间"})
    cr_repo_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "CR仓库名称"})
    cr_region: str = field(default="cn-beijing", metadata={"description": "CR区域"})
    
    # Code Pipeline配置
    cp_workspace_name: str = field(default=DEFAULT_WORKSPACE_NAME, metadata={"description": "Pipeline工作区名称"})
    cp_pipeline_name: str = field(default=AUTO_CREATE_VE, metadata={"description": "Pipeline名称"})
    cp_pipeline_id: str = field(default="", metadata={"description": "Pipeline ID"})
    
    # 构建配置
    image_tag: str = field(default="latest", metadata={"description": "镜像标签"})
    dockerfile_template: str = field(default="Dockerfile.j2", metadata={"description": "Dockerfile模板"})
    build_timeout: int = field(default=3600, metadata={"description": "构建超时时间(秒)"})
    
    # 系统字段（自动更新）
    image_url: str = field(default=None, metadata={"system": True})
    build_timestamp: str = field(default=None, metadata={"system": True})
    tos_object_key: str = field(default=None, metadata={"system": True})

@dataclass
class VeCPCRBuilderResult(AutoSerializableMixin):
    """VeCPCRBuilder结果类"""
    success: bool = field(default=False, metadata={"description": "构建是否成功"})
    image_url: str = field(default="", metadata={"description": "构建成功的镜像URL"})
    cr_instance_name: str = field(default="", metadata={"description": "CR实例名称"})
    cr_namespace_name: str = field(default="", metadata={"description": "CR命名空间名称"})
    cr_repo_name: str = field(default="", metadata={"description": "CR仓库名称"})
    cp_pipeline_id: str = field(default="", metadata={"description": "Pipeline ID"})
    build_timestamp: str = field(default="", metadata={"description": "构建时间戳"})
    build_logs: List[str] = field(default_factory=list, metadata={"description": "构建日志"})
    error_message: str = field(default="", metadata={"description": "错误信息"})
    resources: Dict[str, Any] = field(default_factory=dict, metadata={"description": "创建的资源信息"})





class VeCPCRBuilder(Builder):
    """火山引擎Code Pipeline + CR 云构建器"""
    
    def __init__(self):
        """初始化VeCPCRBuilder"""
        super().__init__()
        self.console = Console()
        self._tos_service = None
        self._cr_service = None
        self._pipeline_service = None
    

    
    def build(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """执行云构建流程
        
        Args:
            config: 构建配置
            
        Returns:
            (是否成功, 构建结果)
        """
        builder_config = VeCPCRBuilderConfig.from_dict(config)
        resources = {}  # 简单字典记录资源信息
        
        try:
            # 验证配置
            if not self._validate_config(builder_config):
                return False, VeCPCRBuilderResult(
                    success=False,
                    error_message="配置验证失败"
                ).to_dict()
            
            self.console.print("[green]开始云构建流程...[/green]")
            
            # 1. 渲染Dockerfile
            self.console.print("[cyan]1/6 渲染Dockerfile...[/cyan]")
            resources['dockerfile_path'] = self._render_dockerfile(builder_config)
            
            # 2. 创建项目压缩包
            self.console.print("[cyan]2/6 创建项目压缩包...[/cyan]")
            resources['archive_path'] = self._create_project_archive(builder_config)
            
            # 3. 上传到TOS
            self.console.print("[cyan]3/6 上传到TOS...[/cyan]")
            resources['tos_url'] = self._upload_to_tos(resources['archive_path'], builder_config)
            resources['tos_object_key'] = builder_config.tos_object_key
            resources['tos_bucket'] = builder_config.tos_bucket
            self.console.print(f"[cyan]已上传到TOS: {resources['tos_url']}, bucket: {resources['tos_bucket']}[/cyan]")
            
            # 4. 准备CR资源
            self.console.print("[cyan]4/6 准备CR资源...[/cyan]")
            resources['cr_config'] = self._prepare_cr_resources(builder_config)
            
            # 5. 准备Pipeline资源
            self.console.print("[cyan]5/6 准备Pipeline资源...[/cyan]")
            resources['pipeline_id'] = self._prepare_pipeline_resources(
                builder_config, resources['tos_url'], resources['cr_config']
            )
            
            # 如果创建了新的Pipeline，将信息添加到资源中
            if hasattr(self, '_build_resources'):
                if 'pipeline_name' in self._build_resources:
                    resources['pipeline_name'] = self._build_resources['pipeline_name']
                if 'pipeline_id' in self._build_resources:
                    resources['pipeline_id'] = self._build_resources['pipeline_id']
            
            # 6. 执行构建
            self.console.print("[cyan]6/6 执行构建...[/cyan]")
            resources['image_url'] = self._execute_build(resources['pipeline_id'], builder_config)
            self.console.print(f"[green]✅ 构建完成: {resources['image_url']}[/green]")
            
            # 构建成功，回写关键信息到config
            builder_config.image_url = resources['image_url']
            builder_config.cp_pipeline_id = resources['pipeline_id']
            builder_config.build_timestamp = datetime.now().isoformat()
            builder_config.tos_object_key = resources['tos_object_key']
            
            return True, VeCPCRBuilderResult(
                success=True,
                image_url=resources['image_url'],
                cp_pipeline_id=resources['pipeline_id'],
                cr_instance_name=builder_config.cr_instance_name,
                cr_namespace_name=builder_config.cr_namespace_name,
                cr_repo_name=builder_config.cr_repo_name,
                build_timestamp=builder_config.build_timestamp,
                resources=resources
            ).to_dict()
            
        except Exception as e:
            logger.error(f"构建失败: {str(e)}")
            
            # 构建失败，仍然回写已创建的资源信息
            if resources:
                builder_config.build_timestamp = datetime.now().isoformat()
                if 'tos_object_key' in resources:
                    builder_config.tos_object_key = resources['tos_object_key']
                if 'pipeline_id' in resources:
                    builder_config.cp_pipeline_id = resources['pipeline_id']
            
            return False, VeCPCRBuilderResult(
                success=False,
                error_message=str(e),
                resources=resources
            ).to_dict()
    
    def check_artifact_exists(self, config: Dict[str, Any]) -> bool:
        """检查镜像是否存在
        
        Args:
            config: 构建配置
            
        Returns:
            镜像是否存在
        """
        try:
            builder_config = VeCPCRBuilderConfig.from_dict(config)
            if not builder_config.image_url:
                return False
            
            # 使用CR服务检查镜像是否存在
            try:
                from agentkit.toolkit.integrations.services import CRService, CRServiceConfig
                
                # 创建CR服务配置
                cr_config = CRServiceConfig(
                    instance_name=builder_config.cr_instance_name,
                    namespace_name=builder_config.cr_namespace_name,
                    repo_name=builder_config.cr_repo_name,
                    region=builder_config.cr_region,
                    image_full_url=builder_config.image_url
                )
                
                # 创建CR服务
                cr_service = CRService()
                
                # 检查镜像是否存在
                # 这里可以通过CR API检查镜像是否存在
                # 目前先简化处理，假设如果配置中有image_url就认为存在
                self.console.print(f"[cyan]检查镜像存在性: {builder_config.image_url}[/cyan]")
                
                # TODO: 实现具体的镜像存在性检查逻辑
                # 可以通过调用CR API来检查镜像是否存在
                return True
                
            except Exception as e:
                logger.warning(f"检查镜像存在性失败: {str(e)}")
                return False
            
        except Exception:
            return False
    
    def remove_artifact(self, config: Dict[str, Any]) -> bool:
        """删除构建产物
        
        Args:
            config: 构建配置
            
        Returns:
            是否删除成功
        """
        try:
            builder_config = VeCPCRBuilderConfig.from_dict(config)
            
            # 删除TOS上的压缩包
            if builder_config.tos_object_key:
                try:
                    from agentkit.toolkit.integrations.services.tos_service import TOSService, TOSServiceConfig
                    
                    tos_config = TOSServiceConfig(
                        bucket=builder_config.tos_bucket,
                        region=builder_config.tos_region,
                        prefix=builder_config.tos_prefix
                    )
                    
                    tos_service = TOSService(tos_config)
                    tos_service.delete_file(builder_config.tos_object_key)
                    logger.info(f"已删除TOS压缩包: {builder_config.tos_object_key}")
                    
                except Exception as e:
                    logger.warning(f"删除TOS压缩包失败: {str(e)}")
            
            # 删除CR上的镜像（可选）
            if builder_config.image_url:
                try:
                    self.console.print(f"[yellow]注意: 删除CR镜像功能暂未实现，镜像保留: {builder_config.image_url}[/yellow]")
                    # TODO: 实现CR镜像删除逻辑
                    # 需要调用CR API删除指定tag的镜像
                    # 考虑到镜像可能被其他服务使用，这里暂时不自动删除
                    
                except Exception as e:
                    logger.warning(f"删除CR镜像失败: {str(e)}")
            
            # 清理Pipeline资源（可选）
            if builder_config.cp_pipeline_id:
                try:
                    self.console.print(f"[yellow]注意: 清理Pipeline资源功能暂未实现，Pipeline ID: {builder_config.cp_pipeline_id}[/yellow]")
                    # TODO: 实现Pipeline资源清理逻辑
                    # 可以删除历史构建记录等
                    
                except Exception as e:
                    logger.warning(f"清理Pipeline资源失败: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除失败: {str(e)}")
            return False
    
    def _validate_config(self, config: VeCPCRBuilderConfig) -> bool:
        """验证配置"""
        if not config.tos_bucket:
            self.console.print("[red]错误: 未配置TOS存储桶[/red]")
            return False
        if not config.cr_region:
            self.console.print("[red]错误: 未配置CR地域[/red]")
            return False
        if not config.tos_region:
            self.console.print("[red]错误: 未配置TOS地域[/red]")
            return False
        return True
    
    def _render_dockerfile(self, config: VeCPCRBuilderConfig) -> str:
        """渲染Dockerfile"""
        try:
            from agentkit.toolkit.integrations.container import DockerfileRenderer
            
            template_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "resources", "templates"
            )
            renderer = DockerfileRenderer(template_dir)
            
            common_config = CommonConfig.from_dict(config.common_config)
            context = {
                "agent_module_path": os.path.splitext(common_config.entry_point)[0],
                "python_version": common_config.python_version,
            }
            
            if common_config.dependencies_file:
                context["dependencies_file"] = common_config.dependencies_file
                if not os.path.exists(common_config.dependencies_file):
                    with open(common_config.dependencies_file, "w") as f:
                        f.write("")
            
            dockerfile_path = Path.cwd() / "Dockerfile"
            renderer.render_dockerfile(
                context=context,
                template_name=config.dockerfile_template,
                output_path=str(dockerfile_path)
            )
            
            return str(dockerfile_path)
            
        except ImportError:
            raise Exception("缺少Docker相关依赖")
    
    def _create_project_archive(self, config: VeCPCRBuilderConfig) -> str:
        """创建项目压缩包"""
        try:
            from agentkit.toolkit.integrations.utils.project_archiver import create_project_archive
            common_config = CommonConfig.from_dict(config.common_config)
            # 生成唯一文件名
            agent_name = common_config.agent_name or "agentkit-app"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{agent_name}_{timestamp}_{uuid.uuid4().hex[:8]}"
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            # 使用项目打包工具创建压缩包
            archive_path = create_project_archive(
                source_dir=str(Path.cwd()),
                output_dir=temp_dir,
                archive_name=archive_name
            )
            
            logger.info(f"项目压缩包已创建: {archive_path}")
            return archive_path
            
        except Exception as e:
            raise Exception(f"创建压缩包失败: {str(e)}")
    
    def _generate_bucket_name(self, prefix: str = "agentkit") -> str:
        """生成唯一的存储桶名称
        
        Args:
            prefix: 桶名称前缀
            
        Returns:
            生成的桶名称
        """
        import uuid
        import re
        from datetime import datetime
        
        # 生成唯一标识符
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 构建桶名称 (TOS桶名称规则：小写字母、数字、连字符，3-63字符)
        bucket_name = f"{prefix}-{timestamp}-{unique_id}".lower()
        
        # 确保只包含合法字符
        bucket_name = re.sub(r'[^a-z0-9-]', '-', bucket_name)
        
        # 确保长度在有效范围内
        if len(bucket_name) > 63:
            bucket_name = bucket_name[:63]
        elif len(bucket_name) < 3:
            bucket_name = f"{prefix}-bucket-{unique_id}".lower()
            
        return bucket_name
    
    def _upload_to_tos(self, archive_path: str, config: VeCPCRBuilderConfig) -> str:
        """上传到TOS"""
        try:            # 初始化TOS服务
            from agentkit.toolkit.integrations.services.tos_service import TOSService, TOSServiceConfig
            
            # 处理存储桶配置
            bucket_name = config.tos_bucket
            auto_created_bucket = False
            
            # 情况1: 如果用户配置的桶是空的或者是AUTO_CREATE_VE，需要自动生成桶名称
            if not bucket_name or bucket_name == AUTO_CREATE_VE:
                bucket_name = self._generate_bucket_name("agentkit")
                self.console.print(f"[cyan]未配置TOS存储桶名称，自动生成...[/cyan]")
                self.console.print(f"[cyan]自动生成TOS存储桶名称: {bucket_name}[/cyan]")
                auto_created_bucket = True
            
            tos_config = TOSServiceConfig(
                bucket=bucket_name,
                region=config.tos_region,
                prefix=config.tos_prefix
            )
            
            tos_service = TOSService(tos_config)
            
            # 检查存储桶是否存在
            self.console.print(f"[cyan]检查TOS存储桶是否存在: {bucket_name}[/cyan]")
            if not tos_service.bucket_exists():
                # 情况2: 桶不存在，需要创建桶
                self.console.print(f"[yellow]⚠️ TOS存储桶不存在，正在创建: {bucket_name}[/yellow]")
                
                if not tos_service.create_bucket():
                    error_msg = f"创建TOS存储桶失败: {bucket_name}"
                    self.console.print(f"[red]❌ {error_msg}[/red]")
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                self.console.print(f"[green]✅ TOS存储桶创建成功: {bucket_name}[/green]")
                
                # 循环检查桶是否存在，直到成功或超时
                self.console.print(f"[cyan]正在验证TOS存储桶创建结果: {bucket_name}[/cyan]")
                import time
                start_time = time.time()
                timeout = 10  # 10秒超时
                check_interval = 1  # 每1秒检查一次
                
                while time.time() - start_time < timeout:
                    if tos_service.bucket_exists():
                        self.console.print(f"[green]✅ TOS存储桶验证成功: {bucket_name}[/green]")
                        break
                    else:
                        self.console.print(f"[yellow]⏳ 等待TOS存储桶就绪... ({time.time() - start_time:.1f}s)[/yellow]")
                        time.sleep(check_interval)
                else:
                    # 超时
                    error_msg = f"TOS存储桶创建验证超时 ({timeout}秒): {bucket_name}"
                    self.console.print(f"[red]❌ {error_msg}[/red]")
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # 如果是用户配置了桶名称但桶不存在，给出提示
                if config.tos_bucket and config.tos_bucket != AUTO_CREATE_VE:
                    self.console.print(f"[yellow]💡 提示: 您配置的存储桶 '{config.tos_bucket}' 不存在，已为您自动创建新桶 '{bucket_name}'[/yellow]")
            else:
                self.console.print(f"[green]✅ TOS存储桶存在: {bucket_name}[/green]")
            
            # 如果自动生成了桶名称，需要回写到配置中
            if auto_created_bucket:
                config.tos_bucket = bucket_name
                        
            # 生成对象键
            archive_name = os.path.basename(archive_path)
            object_key = f"{config.tos_prefix}/{archive_name}"
            
            # 上传文件
            tos_url = tos_service.upload_file(archive_path, object_key)
            
            # 保存对象键到配置
            config.tos_object_key = object_key
            
            logger.info(f"文件已上传到TOS: {tos_url}")
            return tos_url
            
        except Exception as e:
            raise Exception(f"上传到TOS失败: {str(e)}")
    
    def _prepare_cr_resources(self, config: VeCPCRBuilderConfig) -> CRServiceConfig:
        """准备CR资源"""
        try:
            # 创建CR服务配置
            cr_config = CRServiceConfig(
                instance_name=config.cr_instance_name,
                namespace_name=config.cr_namespace_name,
                repo_name=config.cr_repo_name,
                region=config.cr_region
            )
            
            # 创建配置更新回调
            def config_updater(workflow_name: str, cr_config_dict: Dict[str, Any]) -> None:
                """配置更新回调"""
                # 将CR配置同步到builder配置
                if "instance_name" in cr_config_dict:
                    config.cr_instance_name = cr_config_dict["instance_name"]
                if "namespace_name" in cr_config_dict:
                    config.cr_namespace_name = cr_config_dict["namespace_name"]
                if "repo_name" in cr_config_dict:
                    config.cr_repo_name = cr_config_dict["repo_name"]
                if "image_full_url" in cr_config_dict:
                    config.image_url = cr_config_dict["image_full_url"]
            
            # 创建CR服务
            from agentkit.toolkit.integrations.services import CRService, DefaultCRConfigCallback
            cr_service = CRService(config_callback=DefaultCRConfigCallback(config_updater=config_updater))
            
            # 获取公共配置
            common_config = CommonConfig.from_dict(config.common_config)
            
            # 确保CR资源存在
            self.console.print(f"[cyan]正在确保CR资源存在...[/cyan]")
            cr_result = cr_service.ensure_cr_resources(cr_config, common_config)
            
            if not cr_result.success:
                error_msg = f"CR资源准备失败: {cr_result.error}"
                self.console.print(f"[red]❌ {error_msg}[/red]")
                raise Exception(error_msg)
            
            # 确保公网访问
            self.console.print(f"[cyan]正在确保CR公网访问...[/cyan]")
            public_result = cr_service.ensure_public_endpoint(cr_config)
            
            if not public_result.success:
                error_msg = f"公网访问配置失败: {public_result.error}"
                self.console.print(f"[red]❌ {error_msg}[/red]")
                raise Exception(error_msg)
            
            self.console.print(f"[green]✅ CR资源准备完成[/green]")
            self.console.print(f"[green]   实例: {cr_result.instance_name}[/green]")
            self.console.print(f"[green]   命名空间: {cr_result.namespace_name}[/green]")
            self.console.print(f"[green]   仓库: {cr_result.repo_name}[/green]")
            
            return cr_config
            
        except Exception as e:
            raise Exception(f"准备CR资源失败: {str(e)}")
    
    def _prepare_pipeline_resources(self, config: VeCPCRBuilderConfig, tos_url: str, cr_config: CRServiceConfig) -> str:
        """准备Pipeline资源"""
        try:
            # 初始化Code Pipeline服务
            from agentkit.toolkit.integrations.ve_code_pipeline import VeCodePipeline
            
            # 获取认证信息
            from agentkit.utils.ve_sign import get_volc_ak_sk_region
            ak, sk, region = get_volc_ak_sk_region('CP')
            if region != 'cn-beijing':
                self.console.print("[red]错误: 仅支持在cn-beijing地域创建Code Pipeline[/red]")
                return False
            
            # 创建VeCodePipeline实例
            cp_client = VeCodePipeline(
                access_key=ak,
                secret_key=sk,
                region=region
            )
            
            # 获取默认工作区
            workspace_id = cp_client._get_default_workspace()
            logger.info(f"使用默认工作区: {workspace_id}")
            
            # 获取公共配置
            common_config = CommonConfig.from_dict(config.common_config)
            agent_name = common_config.agent_name or "agentkit-app"
            
            # 检查是否已存在Pipeline
            # 情况1: 如果配置了Pipeline ID，优先使用ID进行精确查找
            if config.cp_pipeline_id and config.cp_pipeline_id != AUTO_CREATE_VE:
                try:
                    # 通过ID获取Pipeline详情
                    result = cp_client.list_pipelines(
                        workspace_id=workspace_id,
                        pipeline_ids=[config.cp_pipeline_id]
                    )
                    
                    if result.get("Items") and len(result["Items"]) > 0:
                        pipeline_info = result["Items"][0]
                        found_pipeline_name = pipeline_info.get("Name", "")
                        
                        # 如果同时配置了名称，需要验证名称和ID是否匹配
                        if config.cp_pipeline_name and config.cp_pipeline_name != AUTO_CREATE_VE:
                            if found_pipeline_name != config.cp_pipeline_name:
                                error_msg = f"配置的Pipeline名称 '{config.cp_pipeline_name}' 与ID '{config.cp_pipeline_id}' 对应的名称 '{found_pipeline_name}' 不匹配"
                                logger.error(error_msg)
                                self.console.print(f"[red]❌ {error_msg}[/red]")
                                raise Exception(error_msg)
                        
                        # 验证通过，使用找到的Pipeline
                        logger.info(f"通过ID复用Pipeline: {found_pipeline_name} (ID: {config.cp_pipeline_id})")
                        self.console.print(f"[green]✅ 通过ID复用Pipeline: {found_pipeline_name}[/green]")
                        
                        # 更新配置中的Pipeline名称
                        config.cp_pipeline_name = found_pipeline_name
                        
                        # 保存Pipeline客户端到实例变量
                        self._cp_client = cp_client
                        self._workspace_id = workspace_id
                        
                        # 记录资源信息
                        if not hasattr(self, '_build_resources'):
                            self._build_resources = {}
                        self._build_resources['pipeline_name'] = found_pipeline_name
                        self._build_resources['pipeline_id'] = config.cp_pipeline_id
                        
                        return config.cp_pipeline_id
                    else:
                        logger.warning(f"配置的Pipeline ID '{config.cp_pipeline_id}' 不存在，将创建新的Pipeline")
                        self.console.print(f"[yellow]⚠️ 配置的Pipeline ID不存在，将创建新的Pipeline[/yellow]")
                        
                except Exception as e:
                    if "不匹配" in str(e):
                        raise  # 名称和ID不匹配，直接抛出异常
                    logger.warning(f"通过ID查找Pipeline失败: {str(e)}，将创建新的Pipeline")
            
            # 情况2: 如果只配置了Pipeline名称（且不是AUTO_CREATE_VE），通过名称查找
            elif config.cp_pipeline_name and config.cp_pipeline_name != AUTO_CREATE_VE:
                try:
                    existing_pipelines = cp_client.list_pipelines(
                        workspace_id=workspace_id,
                        name_filter=config.cp_pipeline_name
                    )
                    
                    if existing_pipelines.get("Items") and len(existing_pipelines["Items"]) > 0:
                        # 找到已存在的Pipeline
                        pipeline_info = existing_pipelines["Items"][0]
                        pipeline_id = pipeline_info["Id"]
                        found_name = pipeline_info.get("Name", "")
                        
                        logger.info(f"通过名称复用Pipeline: {found_name} (ID: {pipeline_id})")
                        self.console.print(f"[green]✅ 通过名称复用Pipeline: {found_name}[/green]")
                        
                        # 更新配置中的Pipeline ID
                        config.cp_pipeline_id = pipeline_id
                        
                        # 保存Pipeline客户端到实例变量
                        self._cp_client = cp_client
                        self._workspace_id = workspace_id
                        
                        # 记录资源信息
                        if not hasattr(self, '_build_resources'):
                            self._build_resources = {}
                        self._build_resources['pipeline_name'] = found_name
                        self._build_resources['pipeline_id'] = pipeline_id
                        
                        return pipeline_id
                    else:
                        logger.warning(f"配置的Pipeline名称 '{config.cp_pipeline_name}' 不存在，将创建新的Pipeline")
                        self.console.print(f"[yellow]⚠️ 配置的Pipeline名称不存在，将创建新的Pipeline[/yellow]")
                except Exception as e:
                    logger.warning(f"通过名称查找Pipeline失败: {str(e)}，将创建新的Pipeline")
            
            # 如果config中没有配置或检查失败，则创建新的Pipeline
            pipeline_name = config.cp_pipeline_name if config.cp_pipeline_name and config.cp_pipeline_name != AUTO_CREATE_VE else f"agentkit-cli-{agent_name}-{generate_random_id(4)}"
            self.console.print(f"[cyan]创建新的Pipeline: {pipeline_name}[/cyan]")
            
            # 读取Pipeline模板
            import jinja2
            
            # 获取当前文件所在的目录，然后向上找到项目根目录
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            # 从当前文件目录向上导航到项目根目录: agentkit/toolkit/integrations/builder -> agentkit/toolkit/integrations -> agentkit/toolkit -> agentkit -> project_root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir))))
            template_path = os.path.join(project_root, "agentkit", "toolkit", "resources", "templates", "code-pipeline-tos-cr-step.j2")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 使用Jinja2渲染模板
            template = jinja2.Template(template_content)
            spec_template = template.render(
                bucket_name=config.tos_bucket,
                bucket_region=config.tos_region or 'cn-beijing'
            )
            
            # 创建Pipeline
            logger.info(f"创建Pipeline: {pipeline_name}")
            pipeline_id = cp_client._create_pipeline(
                workspace_id=workspace_id,
                pipeline_name=pipeline_name,
                spec=spec_template,
                parameters= [
                        {"Key": "DOCKERFILE_PATH", "Value": "/workspace/agentkit-app/Dockerfile", "Dynamic": True, "Env": True},
                        {"Key": "DOWNLOAD_PATH", "Value": "/workspace", "Dynamic": True, "Env": True},
                        {"Key": "PROJECT_ROOT_DIR", "Value": "/workspace/agentkit-app", "Dynamic": True, "Env": True},
                        {"Key": "TOS_BUCKET_NAME", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "TOS_PROJECT_FILE_NAME", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "TOS_PROJECT_FILE_PATH", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "TOS_REGION", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_NAMESPACE", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_INSTANCE", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_DOMAIN", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_OCI", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_TAG", "Value": "", "Dynamic": True, "Env": True},
                        {"Key": "CR_REGION", "Value": "", "Dynamic": True, "Env": True},
                    ],
            )
            
            logger.info(f"Pipeline创建成功: {pipeline_id}")
            self.console.print(f"[green]✅ 创建Pipeline成功: {pipeline_name} (ID: {pipeline_id})[/green]")
            
            # 更新config中的Pipeline信息
            config.cp_pipeline_name = pipeline_name
            config.cp_pipeline_id = pipeline_id
            
            # 保存Pipeline客户端到实例变量，供后续使用
            self._cp_client = cp_client
            self._workspace_id = workspace_id
            
            # 将Pipeline信息添加到构建结果中，供上层工作流使用
            if not hasattr(self, '_build_resources'):
                self._build_resources = {}
            self._build_resources['pipeline_name'] = pipeline_name
            self._build_resources['pipeline_id'] = pipeline_id
            
            return pipeline_id
            
        except Exception as e:
            raise Exception(f"准备Pipeline资源失败: {str(e)}")
    
    def _execute_build(self, pipeline_id: str, config: VeCPCRBuilderConfig) -> str:
        """执行构建"""
        try:
            # 获取已保存的Code Pipeline客户端和工作区ID
            if not hasattr(self, '_cp_client') or not hasattr(self, '_workspace_id'):
                raise Exception("Pipeline客户端未初始化，请先调用_prepare_pipeline_resources")
            
            cp_client = self._cp_client
            workspace_id = self._workspace_id
            
            # 获取公共配置
            common_config = CommonConfig.from_dict(config.common_config)
            agent_name = common_config.agent_name or "agentkit-app"
            
            # 准备构建参数
            build_parameters = [
                {"Key": "TOS_BUCKET_NAME", "Value": config.tos_bucket},
                {"Key": "TOS_PROJECT_FILE_NAME", "Value": os.path.basename(config.tos_object_key)},
                {"Key": "TOS_PROJECT_FILE_PATH", "Value": config.tos_object_key},
                {"Key": "TOS_REGION", "Value": config.tos_region},
                {"Key": "PROJECT_ROOT_DIR", "Value": f"/workspace/{agent_name}"},
                {"Key": "DOWNLOAD_PATH", "Value": "/workspace"},
                {"Key": "DOCKERFILE_PATH", "Value": f"/workspace/{agent_name}/Dockerfile"},
                {"Key": "CR_INSTANCE", "Value": config.cr_instance_name},
                {"Key": "CR_DOMAIN", "Value": f"{config.cr_instance_name}-{config.cr_region}.cr.volces.com"},
                {"Key": "CR_NAMESPACE", "Value": config.cr_namespace_name},
                {"Key": "CR_OCI", "Value": config.cr_repo_name},
                {"Key": "CR_TAG", "Value": config.image_tag},
                {"Key": "CR_REGION", "Value": config.cr_region},
            ]
            
            # 运行Pipeline
            run_id = cp_client.run_pipeline(
                workspace_id=workspace_id,
                pipeline_id=pipeline_id,
                description=f"构建Agent: {agent_name}",
                parameters=build_parameters
            )
            
            self.console.print(f"[green]✅ Pipeline触发成功，运行ID: {run_id}[/green]")
            self.console.print(f"[yellow]等待构建完成...[/yellow]")
            
            # 等待构建完成，使用进度条显示
            max_wait_time = 120  # 默认1小时
            check_interval = 3  # 30秒检查一次
            import time
            start_time = time.time()
            
            # 创建进度条
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                "<", TimeRemainingColumn(),
                console=self.console
            ) as progress:
                
                # 创建进度任务，总时长为最大等待时间
                task = progress.add_task("等待构建完成...", total=max_wait_time)
                last_status = None
                
                while True:
                    try:
                        # 获取运行状态
                        status = cp_client.get_pipeline_run_status(
                            workspace_id=workspace_id,
                            pipeline_id=pipeline_id,
                            run_id=run_id
                        )
                        
                        # 更新进度条的描述信息
                        if status != last_status:
                            progress.update(task, description=f"构建状态: {status}")
                            last_status = status
                        
                        # 检查是否完成
                        if status == "Succeeded":
                            # 完成进度条
                            progress.update(task, completed=max_wait_time)
                            self.console.print(f"[green]✅ Pipeline运行完成![/green]")
                            break
                        elif status in ["Failed", "Cancelled", "Timeout"]:
                            # 标记为失败
                            progress.update(task, description=f"[red]构建失败: {status}[/red]")
                            error_msg = f"Pipeline运行失败，状态: {status}"
                            self.console.print(f"[red]❌ {error_msg}[/red]")
                            raise Exception(error_msg)
                        elif status in ["InProgress", "Enqueued", "Dequeued", "Initializing"]:
                            # 继续等待，更新进度
                            elapsed_time = time.time() - start_time
                            if elapsed_time >= max_wait_time:
                                progress.update(task, description=f"[red]等待超时[/red]")
                                error_msg = f"等待超时 ({max_wait_time}秒)，当前状态: {status}"
                                self.console.print(f"[red]⏰ {error_msg}[/red]")
                                raise Exception(error_msg)
                            
                            # 更新进度（基于时间）
                            progress.update(task, completed=min(elapsed_time, max_wait_time))
                            time.sleep(check_interval)
                        else:
                            # 未知状态
                            elapsed_time = time.time() - start_time
                            if elapsed_time >= max_wait_time:
                                progress.update(task, description=f"[red]等待超时[/red]")
                                error_msg = f"等待超时 ({max_wait_time}秒)，最终状态: {status}"
                                self.console.print(f"[red]⏰ {error_msg}[/red]")
                                raise Exception(error_msg)
                            # 更新进度
                            progress.update(task, completed=min(elapsed_time, max_wait_time))
                            time.sleep(check_interval)
                            
                    except Exception as e:
                        progress.update(task, description=f"[red]获取状态异常[/red]")
                        self.console.print(f"[red]获取运行状态时发生异常: {e}[/red]")
                        raise
            
            # 构建镜像URL [实例名称]-[地域].cr.volces.com
            image_url = f"{config.cr_instance_name}-{config.cr_region}.cr.volces.com/{config.cr_namespace_name}/{config.cr_repo_name}:{config.image_tag}"
            config.image_url = image_url
            
            return image_url
            
        except Exception as e:
            raise Exception(f"执行构建失败: {str(e)}")