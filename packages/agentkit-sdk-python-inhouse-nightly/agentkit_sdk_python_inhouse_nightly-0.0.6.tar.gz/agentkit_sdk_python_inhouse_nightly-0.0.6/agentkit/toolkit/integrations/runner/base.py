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
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class Runner(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def deploy(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        pass
    
    @abstractmethod
    def destroy(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def invoke(self, config: Dict[str, Any], payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Any]:
        pass
