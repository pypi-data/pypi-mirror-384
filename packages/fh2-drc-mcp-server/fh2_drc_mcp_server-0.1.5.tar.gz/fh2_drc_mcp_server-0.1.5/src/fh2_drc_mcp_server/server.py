# -*- coding: utf-8 -*-
"""
DRC MCP服务 - 重构后的主入口文件
pip install "mcp-server>=0.9.0" "httpx>=0.27"
python main_refactored.py
"""
from mcp.server.fastmcp import FastMCP

# 导入所有服务函数（不使用装饰器版本）
from .services.device_service import (
    # device_recommendation,
    cloud_controls_create)
from .services.flight_service import drone_takeoff, fly_to_points, drone_return_home
from .services.camera_service import (
    camera_photo_take,
    camera_aim,
    camera_look_at,
    gimbal_reset_horizontal,
    gimbal_reset_downward,
    camera_tilt_down,
    camera_mode_switch,
    camera_lens_switch
    # camera_recording_start,  # 基础函数，不暴露给用户，由camera_recording_task调用
    # camera_recording_stop,   # 基础函数，不暴露给用户，由camera_recording_task调用
)
from .services.poi_service import poi_enter, poi_exit
from .services.status_service import get_flight_status
from .services.panoramic_service import panoramic_shooting
from .services.recording_service import camera_recording_task
from .services.map_service import get_pin_points, create_pin_point, get_default_group_id
from .services.ai_alert_service import (
    get_alert_config,
    # update_alert_config,
    enable_llm_alert,
    disable_alert
)

# 创建MCP服务实例
mcp = FastMCP("drc_mcp_service")

# 注册所有工具
# mcp.tool()(device_recommendation)
mcp.tool()(cloud_controls_create)
mcp.tool()(drone_takeoff)
mcp.tool()(fly_to_points)
mcp.tool()(drone_return_home)
mcp.tool()(camera_photo_take)
mcp.tool()(camera_aim)
mcp.tool()(camera_look_at)
mcp.tool()(gimbal_reset_horizontal)
mcp.tool()(gimbal_reset_downward)
mcp.tool()(camera_tilt_down)
mcp.tool()(camera_mode_switch)
mcp.tool()(camera_lens_switch)
# 以下函数作为内部函数，不直接暴露给用户
# mcp.tool()(camera_recording_start)  # 使用 camera_recording_task 代替
# mcp.tool()(camera_recording_stop)   # 使用 camera_recording_task 代替
mcp.tool()(poi_enter)
mcp.tool()(poi_exit)
mcp.tool()(get_flight_status)
mcp.tool()(panoramic_shooting)
mcp.tool()(camera_recording_task)
mcp.tool()(get_pin_points)
mcp.tool()(create_pin_point)
mcp.tool()(get_default_group_id)
mcp.tool()(get_alert_config)
# mcp.tool()(update_alert_config)
mcp.tool()(enable_llm_alert)
mcp.tool()(disable_alert)


def run():
    mcp.run()


if __name__ == '__main__':
    run()
