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
# See the License for the specific governing permissions and
# limitations under the License.

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from agentkit.toolkit.config.dataclass_utils import AutoSerializableMixin

try:
    import tos
    TOS_AVAILABLE = True
except ImportError:
    TOS_AVAILABLE = False
    tos = None

logger = logging.getLogger(__name__)


@dataclass
class TOSServiceConfig(AutoSerializableMixin):
    """TOS服务配置"""
    
    region: str = field(default="cn-beijing", metadata={"description": "区域"})
    endpoint: str = field(default="", metadata={"description": "端点URL"})
    bucket: str = field(default="", metadata={"description": "存储桶名称"})
    prefix: str = field(default="", metadata={"description": "路径前缀"})
    
    def get_endpoint(self) -> str:
        """获取TOS端点"""
        if self.endpoint:
            return self.endpoint
        return f"tos-{self.region}.volces.com"


class TOSService:
    """火山引擎TOS服务封装"""
    
    def __init__(self, config: TOSServiceConfig):
        """初始化TOS服务
        
        Args:
            config: TOS服务配置
        """
        if not TOS_AVAILABLE:
            raise ImportError("TOS SDK未安装，请安装: pip install tos")
            
        self.config = config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化TOS客户端"""
        try:
            # 使用统一的火山引擎AK/SK获取函数
            from agentkit.utils.ve_sign import get_volc_ak_sk_region
            access_key, secret_key, region = get_volc_ak_sk_region("TOS")
            
            # 如果配置中没有指定区域，使用获取到的区域
            if not self.config.region and region:
                self.config.region = region
                logger.info(f"使用区域: {region}")
            
            # 创建TOS客户端
            self.client = tos.TosClientV2(
                access_key,
                secret_key,
                self.config.get_endpoint(),
                self.config.region
            )
            logger.info(f"TOS客户端初始化成功: {self.config.bucket}@{self.config.region}")
            
        except Exception as e:
            logger.error(f"TOS客户端初始化失败: {str(e)}")
            raise
    
    def upload_file(self, local_path: str, object_key: str) -> str:
        """上传文件到TOS
        
        Args:
            local_path: 本地文件路径
            object_key: TOS对象键
            
        Returns:
            TOS文件URL
        """
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
                
            logger.info(f"上传文件: {local_path} -> {object_key}")
            
            # 上传文件到TOS
            self.client.put_object_from_file(
                bucket=self.config.bucket,
                key=object_key,
                file_path=local_path
            )
            
            # 返回可访问的URL
            url = f"https://{self.config.bucket}.{self.config.get_endpoint()}/{object_key}"
            logger.info(f"文件上传成功: {url}")
            return url
            
        except tos.exceptions.TosClientError as e:
            logger.error(f"TOS客户端错误: {e.message}")
            raise
        except tos.exceptions.TosServerError as e:
            logger.error(f"TOS服务端错误: {e.code} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"上传失败: {str(e)}")
            raise
    
    def download_file(self, object_key: str, local_path: str) -> bool:
        """从TOS下载文件
        
        Args:
            object_key: TOS对象键
            local_path: 本地保存路径
            
        Returns:
            是否下载成功
        """
        try:
            logger.info(f"下载文件: {object_key} -> {local_path}")
            
            # TODO: 实现文件下载
            # 1. 检查对象存在
            # 2. 下载文件
            # 3. 保存到本地
            
            return True
            
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            return False
    
    def delete_file(self, object_key: str) -> bool:
        """删除TOS上的文件
        
        Args:
            object_key: TOS对象键
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"删除文件: {object_key}")
            
            # 删除对象
            self.client.delete_object(bucket=self.config.bucket, key=object_key)
            logger.info(f"文件删除成功: {object_key}")
            return True
            
        except tos.exceptions.TosServerError as e:
            if e.status_code == 404:
                logger.warning(f"文件不存在，无需删除: {object_key}")
                return True
            logger.error(f"删除失败: {e.code} - {e.message}")
            return False
        except Exception as e:
            logger.error(f"删除失败: {str(e)}")
            return False
    
    def file_exists(self, object_key: str) -> bool:
        """检查文件是否存在
        
        Args:
            object_key: TOS对象键
            
        Returns:
            文件是否存在
        """
        try:
            self.client.head_object(bucket=self.config.bucket, key=object_key)
            return True
            
        except tos.exceptions.TosServerError as e:
            if e.status_code == 404:
                return False
            logger.error(f"检查文件存在性失败: {e.code} - {e.message}")
            return False
        except Exception as e:
            logger.error(f"检查文件存在性失败: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """列出文件
        
        Args:
            prefix: 路径前缀
            
        Returns:
            文件列表
        """
        try:
            # TODO: 实现文件列表获取
            return []
            
        except Exception as e:
            logger.error(f"获取文件列表失败: {str(e)}")
            return []
    
    def bucket_exists(self) -> bool:
        """检查存储桶是否存在
        
        Returns:
            存储桶是否存在
        """
        try:
            self.client.head_bucket(bucket=self.config.bucket)
            logger.info(f"存储桶存在: {self.config.bucket}")
            return True
            
        except tos.exceptions.TosServerError as e:
            if e.status_code == 404:
                logger.warning(f"存储桶不存在: {self.config.bucket}")
                return False
            logger.error(f"检查存储桶存在性失败: {e.code} - {e.message}")
            return False
        except Exception as e:
            logger.error(f"检查存储桶存在性失败: {str(e)}")
            return False
    
    def create_bucket(self) -> bool:
        """创建存储桶
        
        Returns:
            是否创建成功
        """
        try:
            logger.info(f"创建存储桶: {self.config.bucket}")
            
            # 创建存储桶
            self.client.create_bucket(bucket=self.config.bucket)
            logger.info(f"存储桶创建成功: {self.config.bucket}")
            return True
            
        except tos.exceptions.TosServerError as e:
            if e.status_code == 409:
                logger.warning(f"存储桶已存在: {self.config.bucket}")
                return True  # 桶已存在也算成功
            logger.error(f"创建存储桶失败: {e.code} - {e.message}")
            return False
        except Exception as e:
            logger.error(f"创建存储桶失败: {str(e)}")
            return False