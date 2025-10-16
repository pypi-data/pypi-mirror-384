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

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol
from pathlib import Path



class Workflow(ABC):
    """Abstract base class for workflows."""
    
    def __init__(self):
        pass

    @abstractmethod
    def prompt_for_config(self, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt for the configuration of the workflow. 
        Args:
            current_config (Dict[str, Any]): The current configuration of the workflow.
        Returns:
            Dict[str, Any]: The updated configuration of the workflow.
        """
        pass
    
    @abstractmethod
    def build(self, config: Dict[str, Any]) -> bool:
        """Build the agent image.
        Args:
            config (Dict[str, Any]): The configuration of the workflow.
        Returns:
            bool: True if the build was successful, False otherwise.
        """
        pass

    @abstractmethod
    def deploy(self, config: Dict[str, Any]) -> bool:
        """Run the workflow.
        Args:
            config (Dict[str, Any]): The configuration of the workflow.
        Returns:
            bool: True if the deployment was successful, False otherwise.
        """
        pass

    @abstractmethod
    def invoke(self, config: Dict[str, Any], args: Dict[str, Any]) -> bool:
        """Invoke the workflow.
        Args:
            config (Dict[str, Any]): The configuration of the workflow.
        Returns:
            bool: True if the invocation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of the workflow.
        
        Args:
            config: The configuration of the workflow.
            
        Returns:
            Dict containing status information. Structure is workflow-specific.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the workflow."""
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Stop and destroy the workflow resources."""
        pass
