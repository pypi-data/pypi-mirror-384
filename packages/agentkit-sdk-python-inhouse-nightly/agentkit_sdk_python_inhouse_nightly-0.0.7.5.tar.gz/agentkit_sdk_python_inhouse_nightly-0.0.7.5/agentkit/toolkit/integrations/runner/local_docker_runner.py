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
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin
from rich.console import Console
from agentkit.toolkit.config import CommonConfig
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin

from .base import Runner
from ..container import DockerManager



logger = logging.getLogger(__name__)
console = Console()

@dataclass
class LocalDockerRunnerConfig(AutoSerializableMixin):
    common_config: Optional[CommonConfig] = field(default=None, metadata={"system": True, "description": "Common configuration"})
    full_image_name: str = field(default=None, metadata={"system": True, "description": "Full image name"})
    image_id: str = field(default="", metadata={"description": "Image ID"})
    image_name: str = field(default="", metadata={"description": "Image name"})
    image_tag: str = field(default="latest", metadata={"description": "Image tag"})
    container_name: str = field(default="", metadata={"system": True, "description": "Container name, uses agent_name if empty"})
    container_id: str = field(default=None, metadata={"system": True, "description": "Container ID"})
    environment: Dict[str, str] = field(default_factory=lambda: {}, metadata={"system": True, "description": "Environment variables"})
    ports: List[str] = field(default_factory=lambda: ["8000:8000"], metadata={"system": True, "description": "Port mappings, format: host-port:container-port, comma-separated, default 8000:8000"})
    volumes: List[str] = field(default_factory=lambda: [], metadata={"system": True, "description": "Volume mappings, format: host-path:container-path, comma-separated"})
    restart_policy: str = field(default="unless-stopped", metadata={"system": True, "description": "Restart policy"})
    memory_limit: str = field(default="1g", metadata={"system": True, "description": "Memory limit"})
    cpu_limit: str = field(default="1", metadata={"system": True, "description": "CPU limit"})

@dataclass
class LocalDockerDeployResult(AutoSerializableMixin):
    success: bool = field(default=False, metadata={"description": "Deployment success status"})
    container_id: Optional[str] = field(default=None, metadata={"description": "Container ID"})
    container_name: Optional[str] = field(default=None, metadata={"description": "Container name"})
    deploy_timestamp: Optional[datetime] = field(default=None, metadata={"description": "Deployment timestamp"})
    error_message: Optional[str] = field(default=None, metadata={"description": "Error message"})


class LocalDockerRunner(Runner):
    def __init__(self):
        super().__init__()
        self.docker_manager = DockerManager()
    
    def deploy(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        try:
            from agentkit.toolkit.integrations.container import DockerManager
        except ImportError:
            logger.error("Missing Docker dependencies, please install agentkit[docker] extras")
            return False, LocalDockerDeployResult(success=False, error_message="Missing Docker dependencies").to_dict()
        
        try:
            docker_config = LocalDockerRunnerConfig.from_dict(config)
            common_config = None
            if docker_config.common_config is not None:
                common_config = CommonConfig.from_dict(docker_config.common_config)
            
            if common_config is None:
                logger.error("Missing common configuration")
                return False, LocalDockerDeployResult(success=False, error_message="Missing common configuration").to_dict()
            
            image_name = docker_config.full_image_name or f"{docker_config.image_name}:{docker_config.image_tag}"
            
            image_exists, image_info, actual_image_id = self.docker_manager.check_image_exists(
                image_name, docker_config.image_id
            )
            
            if image_exists:
                if docker_config.image_id and actual_image_id != docker_config.image_id:
                    docker_config.image_id = actual_image_id
                    logger.info(f"Updated image ID: {actual_image_id[:12]}")
                elif not docker_config.image_id:
                    docker_config.image_id = actual_image_id
                    logger.info(f"Found image, ID: {actual_image_id[:12]}")
            else:
                logger.error(f"Image {image_name} does not exist")
                return False, LocalDockerDeployResult(success=False, error_message=f"Image {image_name} does not exist").to_dict()

            if not docker_config.container_name:
                docker_config.container_name = f"{common_config.agent_name or 'agentkit-app'}-container"
            
            try:
                existing_container = self.docker_manager.get_container(docker_config.container_name)
                if existing_container:
                    logger.info(f"Container {docker_config.container_name} exists, stopping and removing")
                    self.docker_manager.stop_container(existing_container['id'])
                    self.docker_manager.remove_container(existing_container['id'])
            except Exception as e:
                logger.warning(f"Error stopping or removing existing container: {str(e)}")

            port_dict = {}
            for port in docker_config.ports:
                if ":" in port:
                    host_port, container_port  = port.split(":")
                    port_dict[host_port] = f"{container_port}/tcp"
                elif port.isdigit():
                    port_dict[str(port)] = f"{port}/tcp"
                else:
                    logger.error(f"Invalid port format: {port}")
                    return False, LocalDockerDeployResult(success=False, error_message=f"Invalid port format: {port}").to_dict()
            container_resources = {
                'mem_limit': docker_config.memory_limit,
                'cpu_quota': int(float(docker_config.cpu_limit) * 100000)
            }
            
            success, cid = self.docker_manager.create_container(
                image_name=image_name,
                container_name=docker_config.container_name,
                ports=port_dict,
                environment=docker_config.environment,
                volumes={vol.split(':', 1)[0]: {'bind': vol.split(':', 1)[1], 'mode': 'rw'}
                         for vol in docker_config.volumes if ':' in vol},
                restart_policy={'Name': docker_config.restart_policy},
                **container_resources
            )

            if success:
                logger.info(f"Container deployed successfully: {docker_config.container_name} ({cid[:12]})")
                return True, LocalDockerDeployResult(
                    success=True, 
                    container_id=cid, 
                    container_name=docker_config.container_name, 
                    deploy_timestamp=datetime.now().isoformat()
                ).to_dict()
            else:
                logger.error(f"Container creation failed: {cid}")
                return False, LocalDockerDeployResult(success=False, error_message=str(cid)).to_dict()

        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            return False, LocalDockerDeployResult(success=False, error_message=str(e)).to_dict()
    
    def destroy(self, config: Dict[str, Any]) -> bool:
        try:
            docker_config = LocalDockerRunnerConfig.from_dict(config)
            common_config = None
            if docker_config.common_config is not None:
                common_config = CommonConfig.from_dict(docker_config.common_config)
            
            if common_config is None:
                logger.error("Missing common configuration")
                return False
            
            project_name = docker_config.container_name or f"{common_config.agent_name or 'agentkit-app'}-container"
            image_name = docker_config.full_image_name or f"{docker_config.image_name or common_config.agent_name or 'agentkit-app'}:{docker_config.image_tag or 'latest'}"
            
            logger.info(f"Cleaning up resources: {project_name}")
            
            container_removed = False
            image_removed = False
            
            if docker_config.container_id:
                try:
                    logger.info(f"Removing container: {project_name} ({docker_config.container_id[:12]})")
                    if self.docker_manager.remove_container(docker_config.container_id, force=True):
                        logger.info(f"Container removed successfully: {project_name}")
                        container_removed = True
                    else:
                        logger.error(f"Failed to remove container: {project_name}")
                except Exception as e:
                    logger.error(f"Error removing container by ID: {str(e)}")
                    
                    try:
                        logger.info(f"Attempting to remove container by name: {project_name}")
                        if self.docker_manager.remove_container(project_name, force=True):
                            logger.info(f"Container removed successfully: {project_name}")
                            container_removed = True
                    except Exception as e2:
                        logger.error(f"Error removing container by name: {str(e2)}")
            else:
                try:
                    containers = self.docker_manager.list_containers(all_containers=True)
                    for container in containers:
                        if container['name'] == project_name:
                            logger.info(f"Removing container: {project_name}")
                            if self.docker_manager.remove_container(container['id'], force=True):
                                logger.info(f"Container removed successfully: {project_name}")
                                container_removed = True
                            break
                except Exception as e:
                    logger.error(f"Error finding and removing container: {str(e)}")
            
            if docker_config.image_id:
                try:
                    logger.info(f"Removing image: {image_name} ({docker_config.image_id[:12]})")
                    if self.docker_manager.remove_image(docker_config.image_id, force=True):
                        logger.info(f"Image removed successfully: {image_name}")
                        image_removed = True
                    else:
                        logger.error(f"Failed to remove image: {image_name}")
                except Exception as e:
                    logger.error(f"Error removing image by ID: {str(e)}")
                    
                    if image_name:
                        try:
                            logger.info(f"Attempting to remove image by name: {image_name}")
                            if self.docker_manager.remove_image(image_name, force=True):
                                logger.info(f"Image removed successfully: {image_name}")
                                image_removed = True
                        except Exception as e2:
                            logger.error(f"Error removing image by name: {str(e2)}")
            else:
                if image_name:
                    try:
                        logger.info(f"Removing image: {image_name}")
                        if self.docker_manager.remove_image(image_name, force=True):
                            logger.info(f"Image removed successfully: {image_name}")
                            image_removed = True
                    except Exception as e:
                        logger.error(f"Error removing image: {str(e)}")
            
            logger.info("Local Docker resource cleanup completed")
            return container_removed or image_removed
            
        except Exception as e:
            logger.error(f"Destruction error: {str(e)}")
            return False

    def status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from datetime import datetime
            
            docker_config = LocalDockerRunnerConfig.from_dict(config)
            common_config = None
            if docker_config.common_config is not None:
                common_config = CommonConfig.from_dict(docker_config.common_config)
            
            if common_config is None:
                error_msg = "Missing common configuration"
                logger.error(error_msg)
                return {
                    'error': error_msg,
                    'project_name': None,
                    'image_name': None,
                    'build': {'exists': False, 'message': 'Query failed'},
                    'deploy': {'exists': False, 'message': 'Query failed'},
                    'system': {'docker_available': False, 'timestamp': datetime.now().isoformat()}
                }
            
            project_name = docker_config.container_name or f"{common_config.agent_name or 'agentkit-app'}-container"
            image_name = docker_config.full_image_name or f"{docker_config.image_name or common_config.agent_name or 'agentkit-app'}:{docker_config.image_tag or 'latest'}"
            
            logger.info(f"Checking status: {project_name}")
            
            image_exists = False
            image_info = None
            actual_image_id = None
            images = self.docker_manager.list_images()
            for img in images:
                tags = img.get('tags', [])
                if image_name in tags or any(tag.startswith(image_name) for tag in tags):
                    image_exists = True
                    image_info = img
                    actual_image_id = img.get('id', '').replace('sha256:', '')
                    break
            
            container_exists = False
            container_running = False
            container_info = None
            containers = self.docker_manager.list_containers(all_containers=True)
            for container in containers:
                if container['name'] == project_name:
                    container_exists = True
                    container_running = container['status'] == 'running'
                    container_info = container
                    break
            
            status_result = {
                'error': None,
                'project_name': project_name,
                'image_name': image_name,
                'build': {
                    'exists': image_exists,
                    'message': 'Image built' if image_exists else 'Image not built',
                    'image_id': actual_image_id[:12] if actual_image_id else None,
                    'tags': image_info.get('tags', []) if image_info else [],
                    'created': image_info.get('created', '') if image_info else None,
                    'size': image_info.get('size', 0) if image_info else 0
                },
                'deploy': {
                    'exists': container_exists,
                    'message': 'Container running' if container_running else ('Container created but not running' if container_exists else 'Container not deployed'),
                    'container_id': container_info.get('id', '') if container_info else None,
                    'status': container_info.get('status', '') if container_info else None,
                    'ports': container_info.get('ports', {}) if container_info else {},
                    'created': container_info.get('created', '') if container_info else None
                },
                'system': {
                    'docker_available': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if image_exists:
                logger.info(f"Image status: Built ({actual_image_id[:12] if actual_image_id else 'unknown'})")
            else:
                logger.info("Image status: Not built")
                
            if container_running:
                logger.info("Container status: Running")
            elif container_exists:
                logger.info("Container status: Created but not running")
            else:
                logger.info("Container status: Not deployed")
            
            return status_result
            
        except Exception as e:
            error_msg = f"Failed to get status: {str(e)}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'project_name': None,
                'image_name': None,
                'build': {'exists': False, 'message': 'Query failed'},
                'deploy': {'exists': False, 'message': 'Query failed'},
                'system': {'docker_available': False, 'timestamp': datetime.now().isoformat()}
            }

    def invoke(self, config: Dict[str, Any], payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Any]:
        try:
            docker_config = LocalDockerRunnerConfig.from_dict(config)
            common_config = None
            if docker_config.common_config is not None:
                common_config = CommonConfig.from_dict(docker_config.common_config)
            
            if common_config is None:
                error_msg = "Missing common configuration"
                logger.error(error_msg)
                return False, error_msg
            
            if not docker_config.container_id:
                error_msg = "Container not deployed, please run deploy command first"
                logger.error(error_msg)
                return False, error_msg
            
            if payload is None:
                error_msg = "Please provide payload parameter"
                logger.error(error_msg)
                return False, error_msg
            
            port = common_config.entry_port or 8000
            endpoint = f"http://localhost:{port}/"
            invoke_endpoint = urljoin(endpoint, "invoke")
            
            if headers is None:
                headers = {
                    "Authorization": "Bearer xxx",
                    "user_id": "agentkit_user", 
                    "session_id": "agentkit_sample_session"
                }
            
            logger.info(f"Invoking service: {invoke_endpoint}")
            
            response = requests.post(
                url=invoke_endpoint, 
                json=payload, 
                headers=headers, 
                timeout=60
            )
            
            if response.status_code != 200:
                error_msg = f"Invocation failed: {response.status_code} {response.text}"
                logger.error(error_msg)
                return False, error_msg
            
            try:
                response_data = response.json()
                return True, response_data
            except ValueError as e:
                error_msg = f"Response parsing failed: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Invocation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg