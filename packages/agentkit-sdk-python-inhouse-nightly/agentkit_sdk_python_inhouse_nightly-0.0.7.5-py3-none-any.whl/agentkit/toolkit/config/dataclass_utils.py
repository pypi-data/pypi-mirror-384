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


from dataclasses import asdict, fields
from typing import Any, Dict, Type, TypeVar, get_type_hints

T = TypeVar('T')

class DataclassSerializer:
    
    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        return asdict(obj)
    
    @staticmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        from dataclasses import MISSING
        
        if not hasattr(cls, '__dataclass_fields__'):
            raise ValueError(f"{cls} must be a dataclass")
        
        field_info = {}
        for field in fields(cls):
            field_info[field.name] = field
        
        kwargs = {}
        for field_name, field in field_info.items():
            if field_name in data:
                kwargs[field_name] = data[field_name]
            else:
                if field.default_factory is not MISSING:
                    kwargs[field_name] = field.default_factory()
                elif field.default is not MISSING:
                    kwargs[field_name] = field.default
                else:
                    kwargs[field_name] = None
        
        return cls(**kwargs)

def auto_to_dict(obj: Any) -> Dict[str, Any]:
    return DataclassSerializer.to_dict(obj)

def auto_from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
    return DataclassSerializer.from_dict(cls, data)

class AutoSerializableMixin:
    
    def to_dict(self) -> Dict[str, Any]:
        return auto_to_dict(self)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return auto_from_dict(cls, data)
