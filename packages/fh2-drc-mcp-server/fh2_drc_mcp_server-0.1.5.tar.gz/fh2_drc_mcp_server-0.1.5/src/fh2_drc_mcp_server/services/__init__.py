# -*- coding: utf-8 -*-
"""
服务模块 - 统一导入所有服务
"""
from mcp.server.fastmcp import FastMCP

# 导入所有服务模块
from . import device_service
from . import flight_service
from . import camera_service
from . import poi_service
from . import status_service
from . import panoramic_service
from . import ai_alert_service


def initialize_services(mcp_instance: FastMCP) -> None:
    """
    初始化所有服务，设置MCP实例
    
    Args:
        mcp_instance: FastMCP实例
    """
    device_service.set_mcp_instance(mcp_instance)
    flight_service.set_mcp_instance(mcp_instance)
    camera_service.set_mcp_instance(mcp_instance)
    poi_service.set_mcp_instance(mcp_instance)
    status_service.set_mcp_instance(mcp_instance)
    panoramic_service.set_mcp_instance(mcp_instance)
    ai_alert_service.set_mcp_instance(mcp_instance)


# 导出所有服务函数
from .device_service import device_recommendation, cloud_controls_create
from .flight_service import drone_takeoff, fly_to_points, drone_return_home
from .camera_service import (
    camera_photo_take, 
    camera_aim, 
    camera_look_at, 
    gimbal_reset_horizontal, 
    gimbal_reset_downward,
    camera_tilt_down,
    camera_mode_switch,
    camera_lens_switch
)
from .poi_service import poi_enter, poi_exit
from .status_service import get_flight_status
from .panoramic_service import panoramic_shooting
from .ai_alert_service import get_alert_config, update_alert_config, enable_llm_alert, disable_alert

__all__ = [
    "initialize_services",
    # 设备服务
    "device_recommendation",
    "cloud_controls_create",
    # 飞行服务
    "drone_takeoff", 
    "fly_to_points", 
    "drone_return_home",
    # 相机服务
    "camera_photo_take", 
    "camera_aim", 
    "camera_look_at",
    "gimbal_reset_horizontal",
    "gimbal_reset_downward",
    "camera_tilt_down",
    "camera_mode_switch",
    "camera_lens_switch",
    # POI服务
    "poi_enter", 
    "poi_exit",
    # 状态服务
    "get_flight_status",
    # 环拍服务
    "panoramic_shooting",
    # AI告警服务
    "get_alert_config",
    "update_alert_config",
    "enable_llm_alert",
    "disable_alert",
]
