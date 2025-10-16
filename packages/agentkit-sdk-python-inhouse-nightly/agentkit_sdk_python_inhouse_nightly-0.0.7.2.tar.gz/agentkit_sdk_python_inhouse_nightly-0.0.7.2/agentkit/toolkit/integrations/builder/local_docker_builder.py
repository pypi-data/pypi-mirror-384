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

"""
Docker builder implementation
Provides local Docker environment build functionality
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from agentkit.toolkit.config import CommonConfig
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
from .base import Builder
from ..container import DockerManager, DockerfileRenderer

logger = logging.getLogger(__name__)


@dataclass
class LocalDockerBuilderConfig(AutoSerializableMixin):
    """Docker builder configuration"""
    common_config: Optional[CommonConfig] = field(default=None, metadata={"system": True, "description": "Common configuration"})
    image_name: str = field(default="", metadata={"description": "Image name"})
    image_tag: str = field(default="latest", metadata={"description": "Image tag"})
    dockerfile_path: str = field(default=".", metadata={"description": "Dockerfile directory path"})
    dockerfile_name: str = field(default="Dockerfile", metadata={"description": "Dockerfile filename"})
    template_dir: Optional[str] = field(default=None, metadata={"description": "Dockerfile template directory"})
    template_name: str = field(default="Dockerfile.j2", metadata={"description": "Dockerfile template filename"})

@dataclass
class LocalDockerBuilderResult(AutoSerializableMixin):
    """Docker builder result"""
    success: bool = field(default=False, metadata={"description": "Build success status"})
    image_id: Optional[str] = field(default=None, metadata={"description": "Built image ID"})
    build_logs: Optional[List[str]] = field(default=None, metadata={"description": "Build logs"})
    build_timestamp: Optional[str] = field(default=None, metadata={"description": "Build timestamp"})
    full_image_name: Optional[str] = field(default=None, metadata={"description": "Full image name"})

class LocalDockerBuilder(Builder):
    """Docker builder implementation"""
    
    def __init__(self):
        super().__init__()
        self.docker_manager = DockerManager()
        self.dockerfile_renderer = None
    
    
    def build(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Build Docker image"""
        docker_config = LocalDockerBuilderConfig.from_dict(config)
        
        common_config = None
        if docker_config.common_config is not None:
            common_config = CommonConfig.from_dict(docker_config.common_config)
        
        if common_config is None:
            return False, LocalDockerBuilderResult(success=False, build_logs=["Missing common configuration"]).to_dict()
        try:
            template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "templates")
            try:
                from agentkit.toolkit.integrations.container import DockerfileRenderer, DockerManager
            except ImportError:
                return False, LocalDockerBuilderResult(success=False, build_logs=["Missing Docker dependencies"]).to_dict()

            renderer = DockerfileRenderer(template_dir)
            context = {
                "agent_module_path": os.path.splitext(common_config.entry_point)[0],
                "python_version": common_config.python_version,
            }

            if common_config.dependencies_file:
                context["dependencies_file"] = common_config.dependencies_file
                if not os.path.exists(common_config.dependencies_file):
                    with open(common_config.dependencies_file, "w") as f:
                        f.write("")
            
            dockerfile_path = Path.cwd() / docker_config.dockerfile_name
            renderer.render_dockerfile(
                context=context,
                template_name=docker_config.template_name,
                output_path=str(dockerfile_path)
            )
            image_name = f"{docker_config.image_name or 'agentkit-app'}"
            image_tag = f"{docker_config.image_tag or 'latest'}"
            
            success, build_logs, image_id = self.docker_manager.build_image(
                dockerfile_path=str(Path.cwd()),
                image_name=image_name,
                image_tag=image_tag,
                build_args={}
            )
            
            if success:
                return True, LocalDockerBuilderResult(
                    success=True,
                    image_id=image_id,
                    full_image_name=f"{image_name}:{image_tag}",
                    build_timestamp=datetime.now().isoformat(),
                    build_logs=build_logs,
                ).to_dict()
            else:
                return False, LocalDockerBuilderResult(
                    success=False,
                    build_logs=build_logs,
                    build_timestamp=datetime.now().isoformat()
                ).to_dict()
                
        except Exception as e:
            return False, LocalDockerBuilderResult(
                success=False,
                build_logs=[str(e)],
                build_timestamp=datetime.now().isoformat()
            ).to_dict()

    
    def check_artifact_exists(self, config: Dict[str, Any]) -> bool:
        """Check if build artifact exists"""
        try:
            exists, image_info, actual_image_id = self.docker_manager.check_image_exists(
                config['full_image_name'], None
            )
            return exists
        except Exception as e:
            self.logger.error(f"Error checking image existence: {str(e)}")
            return False
    
    def remove_artifact(self, config: Dict[str, Any]) -> bool:
        """Remove Docker image"""
        try:
            return self.docker_manager.remove_image(config['full_image_name'], force=True)
        except Exception as e:
            self.logger.error(f"Error removing image: {str(e)}")
            return False