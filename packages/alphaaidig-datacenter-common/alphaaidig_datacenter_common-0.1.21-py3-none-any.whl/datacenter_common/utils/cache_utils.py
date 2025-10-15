import os
import time
import json
from typing import Callable
import pandas as pd
import os
import time
import csv  # 添加CSV模块导入
from typing import Callable, Any, Optional, List

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CacheUtils:
    @staticmethod
    def __ensure_dir_exist(cache_dir: str):
        if os.path.exists(cache_dir):
            return        
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"创建缓存目录失败: {str(e)}")
            raise e

    @staticmethod
    def __is_cache_available(file_path: str, cache_duration_seconds: int = 300,force_refresh: bool = False) -> bool:
        if force_refresh or not os.path.exists(file_path):
            return False
        
        file_age = time.time() - os.path.getmtime(file_path)
        if file_age > cache_duration_seconds:
            return False
        
        return True
    
    @staticmethod
    def acquire_cache_path(file_path: str, suffix: str) -> str:
        base_path = os.path.splitext(file_path)[0]
        return f"{base_path}{suffix}"

    @staticmethod
    def acquire_pd_cache_path(file_path: str) -> str:
        return CacheUtils.acquire_cache_path(file_path, '.csv')

    @staticmethod
    def acquire_json_cache_path(file_path: str) -> str:
        return CacheUtils.acquire_cache_path(file_path, '.json')

    @staticmethod
    def get_cached_data_pd(
        cache_path: str,
        fetch_func: Callable[..., pd.DataFrame],
        cache_duration: int = 300,
        force_refresh: bool = False,
        str_fields: Optional[List[str]] = None,
        *args, **kwargs
    ) -> pd.DataFrame:
        cached_data = pd.DataFrame()
        cache_path = CacheUtils.acquire_pd_cache_path(cache_path)
        cache_dir = os.path.dirname(cache_path)
        
        # 确保目录存在
        CacheUtils.__ensure_dir_exist(cache_dir)

        # 如果缓存可用，直接读缓存
        if CacheUtils.__is_cache_available(cache_path, cache_duration, force_refresh):
            try:
                cached_data = pd.read_csv(
                    cache_path,
                    encoding='utf-8',
                    low_memory=False,
                    dtype={field: str for field in str_fields} if str_fields else None
                )
                return cached_data
            except Exception as e:
                logger.error(f"读取缓存失败: {str(e)}")
                os.remove(cache_path)
        
        # 走到这里要么缓存不可用，要么就是异常了文件被干掉了
        try:
            new_data = fetch_func(*args, **kwargs)
            if isinstance(new_data, pd.DataFrame) and not new_data.empty:
                # 转换指定字段为字符串类型
                if str_fields:
                    for field in str_fields:
                        if field in new_data.columns:
                            new_data[field] = new_data[field].astype(str)
                new_data.to_csv(
                    cache_path,
                    index=False,
                    encoding='utf-8'
                )
                logger.info(f"已更新缓存: {cache_path}")
                return new_data
            else:
                logger.warning("fetch_func返回空数据或非DataFrame类型")
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
        
        return cached_data

    @staticmethod
    def get_cached_data_json(
        cache_path: str,
        fetch_func: Callable[..., dict],
        cache_duration: int = 300,
        force_refresh: bool = False,
        str_fields: Optional[List[str]] = None,
        *args, **kwargs
    ) -> pd.DataFrame:
        cached_data = {}
        cache_path = CacheUtils.acquire_json_cache_path(cache_path)
        cache_dir = os.path.dirname(cache_path)
        
        # 确保目录存在
        CacheUtils.__ensure_dir_exist(cache_dir)

        # 如果缓存可用，直接读缓存
        if CacheUtils.__is_cache_available(cache_path, cache_duration, force_refresh):
            try:
                cached_data = json.load(open(cache_path,'r'))
                return cached_data
            except Exception as e:
                logger.error(f"读取缓存失败: {str(e)}")
                os.remove(cache_path)
        
        # 走到这里要么缓存不可用，要么就是异常了文件被干掉了
        try:
            new_data = fetch_func(*args, **kwargs)
            if isinstance(new_data, dict):
                # 转换指定字段为字符串类型
                with open(cache_path, 'w', encoding='utf-8') as f:
                     json.dump(new_data, f, ensure_ascii=False, indent=2)
                return new_data
            else:
                logger.warning("fetch_func返回空数据或非DataFrame类型")
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
        
        return cached_data
