
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

import typer
import os
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path
from dataclasses import dataclass, field

from agentkit.toolkit.workflows import Workflow
from rich.console import Console
from agentkit.toolkit.config import get_config, CommonConfig
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin

console = Console()

@dataclass
class LocalDockerConfig_v1(AutoSerializableMixin):
    """Local Docker workflow configuration"""
    # User configurable fields
    image_tag: str = field(default="latest", metadata={"description": "Docker image tag", "icon": "🏷️"})

    # System internal fields (not visible to users)
    container_name: str = field(default="", metadata={"system": True, "description": "Container name, uses agent_name if empty"})
    environment: Dict[str, str] = field(default_factory=dict, metadata={"system": True, "description": "Environment variables"})
    ports: List[str] = field(default_factory=lambda: ["8000:8000"], metadata={"system": True, "description": "Port mappings in host:container format, comma-separated"})
    volumes: List[str] = field(default_factory=list, metadata={"system": True, "description": "Volume mappings in host:container format, comma-separated"})
    restart_policy: str = field(default="unless-stopped", metadata={"system": True, "description": "Restart policy"})
    memory_limit: str = field(default="1g", metadata={"system": True, "description": "Memory limit"})
    cpu_limit: str = field(default="1", metadata={"system": True, "description": "CPU limit"})
    container_id: str = field(default=None, metadata={"system": True})
    image_id: str = field(default=None, metadata={"system": True})
    build_timestamp: str = field(default=None, metadata={"system": True})
    deploy_timestamp: str = field(default=None, metadata={"system": True})
    full_image_name: str = field(default=None, metadata={"system": True})

class LocalWorkflow_v1(Workflow):
    """Local Docker workflow implementation"""

    def prompt_for_config(self, current_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate interactive configuration based on dataclass"""
        from agentkit.toolkit.config.auto_prompt import generate_config_from_dataclass
        
        if current_config is None:
            current_config = {}

        return generate_config_from_dataclass(LocalDockerConfig_v1, current_config)

    def build(self, config: Dict[str, Any]) -> bool:
        """Build the agent image using LocalDockerBuilder."""
        try:
            from agentkit.toolkit.integrations.builder.local_docker_builder import (
                LocalDockerBuilder, LocalDockerBuilderConfig, LocalDockerBuilderResult
            )
        except ImportError:
            console.print("[red]Error: Docker dependencies missing, install agentkit[docker] extras[/red]")
            return False
            
        try:
            agent_config = get_config()
            common_config = agent_config.get_common_config()
            docker_config = LocalDockerConfig_v1.from_dict(config)
            
            builder_config = LocalDockerBuilderConfig(
                common_config=common_config,
                image_name=common_config.agent_name or "agentkit-app",
                image_tag=docker_config.image_tag
            ).to_dict()

            builder = LocalDockerBuilder()
            success, build_result = builder.build(builder_config)
            
            if success:
                result = LocalDockerBuilderResult.from_dict(build_result)
                docker_config.full_image_name = result.full_image_name
                docker_config.image_id = result.image_id
                docker_config.build_timestamp = result.build_timestamp
                agent_config.update_workflow_config("local", docker_config.to_dict())
                console.print(f"[green]✅ Build completed: {result.full_image_name}[/green]")
                return True
            else:
                result = LocalDockerBuilderResult.from_dict(build_result)
                error_msg = result.build_logs or "Build failed"
                console.print(f"[red]❌ Build failed: {error_msg}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Build error: {str(e)}[/red]")
            return False

    def deploy(self, config: Dict[str, Any]) -> bool:
        """Deploy agent image to local Docker container"""
        try:
            from agentkit.toolkit.integrations.runner.local_docker_runner import (
                LocalDockerRunner, LocalDockerRunnerConfig, LocalDockerDeployResult
            )
        except ImportError:
            console.print("[red]Error: Docker dependencies missing, install agentkit[docker] extras[/red]")
            return False
            
        try:
            docker_config = LocalDockerConfig_v1.from_dict(config)
            agent_config = get_config()
            common_config = agent_config.get_common_config()
            
            runner_config = self._build_runner_config(docker_config, common_config)
            runner = LocalDockerRunner()
            success, deploy_result = runner.deploy(runner_config)
            
            result = LocalDockerDeployResult.from_dict(deploy_result)
            
            if success:
                docker_config.container_id = result.container_id
                docker_config.container_name = result.container_name
                docker_config.deploy_timestamp = result.deploy_timestamp
                agent_config.update_workflow_config("local", docker_config.to_dict())
                console.print(f"[green]✅ Container deployed successfully: {result.container_name}[/green]")
                return True
            else:
                error_msg = result.error_message or "Deployment failed"
                console.print(f"[red]❌ Container deployment failed: {error_msg}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Deployment error: {str(e)}[/red]")
            return False
        
    def invoke(self, config: Dict[str, Any] = None, args: Dict[str, Any] = None) -> bool:
        """Invoke the workflow with given configuration and arguments."""
        try:
            from agentkit.toolkit.integrations.runner.local_docker_runner import LocalDockerRunner, LocalDockerRunnerConfig
        except ImportError:
            console.print("[red]Error: Docker dependencies missing, install agentkit[docker] extras[/red]")
            return False
            
        try:
            agent_config = get_config()
            common_config = agent_config.get_common_config()
            docker_config = LocalDockerConfig_v1.from_dict(config)
            
            payload = args.get("payload") if args else None
            headers = args.get("headers") if args else None
            
            runner_config = self._build_runner_config(docker_config, common_config)
            runner = LocalDockerRunner()
            success, response_data = runner.invoke(runner_config, payload, headers)
            
            if success:
                console.print(f"[green]✅ Invocation successful: {response_data}[/green]")
                return True
            else:
                console.print(f"[red]❌ Invocation failed: {response_data}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Invocation error: {str(e)}[/red]")
            return False

    def status(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get local Docker deployment status"""
        try:
            from agentkit.toolkit.integrations.runner.local_docker_runner import LocalDockerRunner, LocalDockerRunnerConfig
        except ImportError:
            console.print("[red]Error: Docker dependencies missing, install agentkit[docker] extras[/red]")
            return {
                'error': 'Docker dependencies missing',
                'project_name': None,
                'image_name': None,
                'build': {'exists': False, 'message': 'Query failed'},
                'deploy': {'exists': False, 'message': 'Query failed'},
                'system': {'docker_available': False, 'timestamp': datetime.now().isoformat()}
            }
        
        try:
            agent_config = get_config()
            if config is None:
                config = agent_config.get_workflow_config("local")
                
            docker_config = LocalDockerConfig_v1.from_dict(config)
            common_config = agent_config.get_common_config()
            runner_config = self._build_runner_config(docker_config, common_config)
            
            runner = LocalDockerRunner()
            return runner.status(runner_config)
            
        except Exception as e:
            console.print(f"[red]Status query failed: {str(e)}[/red]")
            return {
                'error': str(e),
                'project_name': None,
                'image_name': None,
                'build': {'exists': False, 'message': 'Query failed'},
                'deploy': {'exists': False, 'message': 'Query failed'},
                'system': {'docker_available': False, 'timestamp': datetime.now().isoformat()}
            }

    def _build_runner_config(self, docker_config: LocalDockerConfig_v1, common_config: CommonConfig) -> Dict[str, Any]:
        """Build LocalDockerRunner configuration object"""
        from agentkit.toolkit.integrations.runner.local_docker_runner import LocalDockerRunnerConfig
        
        return LocalDockerRunnerConfig(
            common_config=common_config,
            full_image_name=docker_config.full_image_name,
            image_name=common_config.agent_name or "agentkit-app",
            image_tag=docker_config.image_tag,
            container_name=docker_config.container_name,
            container_id=docker_config.container_id,
            image_id=docker_config.image_id,
            environment=getattr(docker_config, 'environment', None),
            ports=getattr(docker_config, 'ports', None),
            volumes=getattr(docker_config, 'volumes', None),
            restart_policy=getattr(docker_config, 'restart_policy', None),
            memory_limit=getattr(docker_config, 'memory_limit', None),
            cpu_limit=getattr(docker_config, 'cpu_limit', None)
        ).to_dict()

    def stop(self) -> None:
        """Stop the workflow."""
        pass
    
    def destroy(self) -> None:
        """Stop and destroy workflow resources"""
        try:
            from agentkit.toolkit.config import get_config
            try:
                from agentkit.toolkit.integrations.runner.local_docker_runner import LocalDockerRunner, LocalDockerRunnerConfig
            except ImportError:
                console.print("[red]Error: Docker dependencies missing, install agentkit[docker] extras[/red]")
                return
            
            agent_config = get_config()
            config = agent_config.get_workflow_config("local")
            docker_config = LocalDockerConfig_v1.from_dict(config)
            common_config = agent_config.get_common_config()
            
            runner_config = self._build_runner_config(docker_config, common_config)
            runner = LocalDockerRunner()
            runner.destroy(runner_config)
            
            # Clear configuration state
            docker_config.container_id = None
            docker_config.deploy_timestamp = None
            docker_config.image_id = None
            docker_config.build_timestamp = None
            docker_config.full_image_name = None
            
            agent_config.update_workflow_config("local", docker_config.to_dict())
            
            # Clean up Dockerfile
            try:
                dockerfile_path = Path.cwd() / "Dockerfile"
                if dockerfile_path.exists():
                    dockerfile_path.unlink()
            except Exception:
                pass
                
        except Exception as e:
            console.print(f"[red]❌ Destruction error: {str(e)}[/red]")
            raise