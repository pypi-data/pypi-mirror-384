# -*- coding: utf-8 -*-
"""
缓存管理 - 全局状态缓存
"""
from typing import Optional, Dict


class DeviceCache:
    """设备推荐结果缓存"""
    
    _last_recommendation: Optional[Dict[str, str]] = None
    
    @classmethod
    def set_recommendation(cls, drone_sn: str, gateway_sn: str) -> None:
        """设置最近一次设备推荐结果"""
        cls._last_recommendation = {
            "drone_sn": drone_sn,
            "gateway_sn": gateway_sn,
        }
    
    @classmethod
    def get_gateway_sn(cls) -> Optional[str]:
        """获取缓存的网关SN"""
        if cls._last_recommendation:
            return cls._last_recommendation["gateway_sn"]
        return None
    
    @classmethod
    def get_drone_sn(cls) -> Optional[str]:
        """获取缓存的无人机SN"""
        if cls._last_recommendation:
            return cls._last_recommendation["drone_sn"]
        return None
    
    @classmethod
    def clear(cls) -> None:
        """清除缓存"""
        cls._last_recommendation = None
    
    @classmethod
    def get_recommendation(cls) -> Optional[Dict[str, str]]:
        """获取完整的推荐结果"""
        return cls._last_recommendation
