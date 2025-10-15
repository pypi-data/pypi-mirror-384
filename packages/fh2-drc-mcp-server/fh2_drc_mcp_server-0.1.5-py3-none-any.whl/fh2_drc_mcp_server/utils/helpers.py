# -*- coding: utf-8 -*-
"""
工具函数 - 通用辅助函数
"""
from typing import Optional, Dict, Any
from ..core.cache import DeviceCache


def create_position(lat: Optional[float], lng: Optional[float], h: Optional[float]) -> Optional[Dict[str, float]]:
    """创建位置坐标字典，如果任一参数为None则返回None"""
    return None if None in (lat, lng, h) else {
        "latitude": lat, 
        "longitude": lng, 
        "height": h
    }


def auto_fill_device_sn(device_sn: Optional[str], use_gateway: bool = True) -> Optional[str]:
    """自动填充设备SN
    
    Args:
        device_sn: 传入的设备SN，如果为None则从缓存获取
        use_gateway: True使用gateway_sn，False使用drone_sn
    
    Returns:
        填充后的设备SN或None
    """
    if device_sn is not None:
        return device_sn
    
    if use_gateway:
        return DeviceCache.get_gateway_sn()
    else:
        return DeviceCache.get_drone_sn()


def validate_device_sn(device_sn: Optional[str], use_gateway: bool = True) -> str:
    """验证并获取设备SN，如果无效则抛出错误信息
    
    Args:
        device_sn: 设备SN
        use_gateway: True使用gateway_sn，False使用drone_sn
    
    Returns:
        有效的设备SN
        
    Raises:
        返回错误信息字符串如果无效
    """
    filled_sn = auto_fill_device_sn(device_sn, use_gateway)
    if filled_sn is None:
        sn_type = "gateway_sn" if use_gateway else "drone_sn"
        return f"device_sn is required (no previous recommendation found for {sn_type})"
    return filled_sn


def auto_fill_uuid(uuid: Optional[str], proj_uuid: str) -> str:
    """自动填充UUID，如果为None则使用proj_uuid"""
    return uuid if uuid is not None else proj_uuid


def check_error_response(result: Any, operation_name: str) -> Optional[str]:
    """检查操作结果是否包含错误
    
    Args:
        result: 操作结果
        operation_name: 操作名称，用于错误信息
    
    Returns:
        错误信息字符串，如果无错误则返回None
    """
    if isinstance(result, str) and "error" in result.lower():
        return f"{operation_name}失败: {result}"
    return None
