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
Agentkit Configuration Module

"""

import os
import yaml
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field

from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin
from prompt_toolkit import prompt

WORKFLOW_NAME_IN_YAML = "launch_types"

@dataclass
class CommonConfig(AutoSerializableMixin):
    """Common configuration - automatic prompt generation support"""
    agent_name: str = field(default="", metadata={"description": "Agent application name", "icon": "🤖"})
    entry_point: str = field(default="", metadata={"description": "Agent application entry file", "icon": "📝"})
    description: str = field(default="", metadata={"description": "Application description", "icon": "📄"})
    python_version: str = field(default="3.12", metadata={"description": "Agent application Python version, defaults to 3.12", "icon": "🐍"})
    dependencies_file: str = field(default="requirements.txt", metadata={"description": "Agent application dependencies file, defaults to requirements.txt", "icon": "📦"})
    entry_port: int = field(default=8000, metadata={"description": "Agent application entry port, defaults to 8000", "system": True, "icon": "🌐"})
    current_workflow: str = field(
        default="local",
        metadata={
            "description": "Deployment and runtime mode, defaults to local (local build and deploy), optional hybrid (local build, cloud deploy)",
            "icon": "🚀",
            "choices": [
                {"value": "local", "description": "Local build and deploy"},
                {"value": "hybrid", "description": "Local build, cloud deploy"},
                {"value": "cloud", "description": "Cloud build and deploy base on Volcano Engine Agentkit Platform"}
            ]
        }
    )
    
    _config_metadata = {
        'name': 'CommonConfig',
        'welcome_message': '欢迎使用 AgentKit 配置向导',
        'next_step_hint': '本向导将帮助您完成Agent应用配置，请根据提示输入相关信息，或直接按Enter键使用默认值。',
        'completion_message': '太棒了！通用配置已完成！',
        'next_action_hint': '下面将开始针对您选择的部署模式进行配置。'
    }
    
    @classmethod
    def interactive_create(cls, existing_config: Optional[Dict[str, Any]] = None) -> "CommonConfig":
        """Generate interactive configuration based on dataclass"""
        from .auto_prompt import auto_prompt
        existing = cls.from_dict(existing_config or {})
        config_dict = auto_prompt.generate_config(cls, existing.to_dict())
        return cls.from_dict(config_dict)


class ConfigUpdateResult:
    """Configuration update result for "return and rewrite" mode"""
    
    def __init__(self):
        self.updates: Dict[str, Any] = {}
    
    def add_update(self, key_path: str, value: Any):
        """Add configuration update, supports arbitrary level key paths"""
        self.updates[key_path] = value
    
    def add_common_update(self, key: str, value: Any):
        """Add common configuration update"""
        self.add_update(f"common.{key}", value)
    
    def add_workflow_update(self, workflow_name: str, key: str, value: Any):
        """Add workflow configuration update"""
        self.add_update(f"workflows.{workflow_name}.{key}", value)
    
    def has_updates(self) -> bool:
        """Check if there are updates needed"""
        return bool(self.updates)
    
    def get_updates(self) -> Dict[str, Any]:
        """Get all updates"""
        return self.updates


class AgentkitConfig:
    """Agentkit configuration manager - fully dynamic, no predefined workflow structure"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        if config_path is None:
            config_path = Path.cwd() / "agentkit.yaml"
        self.config_path = Path(config_path)
        self._data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration file"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = self._get_default_config()
            self._save_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration - contains only common config and empty workflow container"""
        return {
            "common": CommonConfig().to_dict(),
            WORKFLOW_NAME_IN_YAML: {}  # Fully dynamic, no predefined workflows
        }
    
    def _save_config(self):
        """Save configuration file"""
        os.makedirs(self.config_path.parent, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)
    
    def get_common_config(self) -> CommonConfig:
        """Get common configuration"""
        return CommonConfig.from_dict(self._data.get("common", {}))
    
    def update_common_config(self, config: CommonConfig):
        """Update common configuration"""
        self._data["common"] = config.to_dict()
        self._save_config()
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get specified workflow configuration (fully dynamic, no structure validation)"""
        return self._data.get(WORKFLOW_NAME_IN_YAML, {}).get(workflow_name, {})
    
    def update_workflow_config(self, workflow_name: str, config: Dict[str, Any]):
        """Update workflow configuration (fully dynamic, no structure validation)"""
        if WORKFLOW_NAME_IN_YAML not in self._data:
            self._data[WORKFLOW_NAME_IN_YAML] = {}
        
        self._data[WORKFLOW_NAME_IN_YAML][workflow_name] = config
        self._save_config()
    
    def list_workflows(self) -> list[str]:
        """List all configured workflow names"""
        return list(self._data.get(WORKFLOW_NAME_IN_YAML, {}).keys())
    
    def workflow_exists(self, workflow_name: str) -> bool:
        """Check if workflow exists"""
        return workflow_name in self._data.get(WORKFLOW_NAME_IN_YAML, {})
    
    def apply_updates(self, update_result: ConfigUpdateResult):
        """Apply update results for "return and rewrite" mode"""
        if not update_result.has_updates():
            return
        
        updates = update_result.get_updates()
        
        for key_path, value in updates.items():
            keys = key_path.split('.')
            current = self._data
            
            # Navigate to parent level
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set final value
            current[keys[-1]] = value
        
        self._save_config()
    
    def get_config_path(self) -> Path:
        """Get configuration file path"""
        return self.config_path
    
    def reload(self):
        """Reload configuration"""
        self._load_config()
    
    def reset_to_default(self):
        """Reset to default configuration"""
        self._data = self._get_default_config()
        self._save_config()
    
    def get_raw_data(self) -> Dict[str, Any]:
        """Get raw configuration data (for debugging or advanced operations)"""
        return self._data.copy()
    
    def set_raw_value(self, key_path: str, value: Any):
        """Directly set value at any path (advanced use case)"""
        keys = key_path.split('.')
        current = self._data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        self._save_config()
    
    def get_raw_value(self, key_path: str, default: Any = None) -> Any:
        """Get value at any path (advanced use case)"""
        keys = key_path.split('.')
        current = self._data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

def get_config(config_path: Optional[Union[str, Path]] = None) -> AgentkitConfig:
    """Get global configuration instance"""
    return AgentkitConfig(config_path)


def create_config_update_result() -> ConfigUpdateResult:
    """Create configuration update result instance"""
    return ConfigUpdateResult()