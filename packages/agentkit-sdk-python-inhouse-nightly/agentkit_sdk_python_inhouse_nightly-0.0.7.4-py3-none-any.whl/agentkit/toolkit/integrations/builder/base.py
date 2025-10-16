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
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Builder(ABC):
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def build(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        pass
    
    @abstractmethod
    def check_artifact_exists(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def remove_artifact(self, config: Dict[str, Any]) -> bool:
        pass
    