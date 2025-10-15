# -*- coding: utf-8 -*-
"""
POI兴趣点服务 - POI环绕和退出
"""
import asyncio
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import post_json, delete_json
from ..config.settings import USER_TOKEN_FIXED, DEFAULT_PAYLOAD_INDEX
from ..utils.helpers import auto_fill_device_sn
from .device_service import cloud_controls_create
from .camera_service import camera_look_at

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance


## POI兴趣点环绕
async def poi_enter(
    proj_uuid: str,
    poi_latitude: float,
    poi_longitude: float,
    poi_height: float,
    circle_radius: float,
    gateway_sn: Optional[str] = None,
    drone_sn: Optional[str] = None,
    speed: int = -1,
    payload_index: str = DEFAULT_PAYLOAD_INDEX,
    token: str = USER_TOKEN_FIXED,
    auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    【POI兴趣点环绕】让飞行器围绕指定兴趣点进行环绕飞行 (poi-enter)
    用途: 飞行器围绕目标点进行圆形轨迹飞行，常用于环拍、巡检等任务
    场景: 需要从多个角度观察或拍摄某个目标点时使用
    前提: 飞行器必须已经在空中飞行状态
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权
    📷 自动相机朝向: 自动让相机朝向POI目标点
    
    POI环绕流程:
    1. 获取飞行和负载控制权
    2. 相机朝向POI目标点
    3. 开始POI环绕飞行

    Args:
        proj_uuid: 项目 UUID（路径参数）
        poi_latitude: POI中心点纬度
        poi_longitude: POI中心点经度
        poi_height: POI中心点高度 (米)
        circle_radius: 环绕半径 (米)
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        speed: 环绕速度，-1为自动速度
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权并朝向目标点，默认True

    Returns:
        POI任务执行结果 JSON 或错误信息字符串。
    """
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    # 步骤1: 获取飞行和负载控制权
    if auto_acquire_control:
        print("🔐 步骤1: 获取飞行和负载控制权...")
        control_keys = ["flight", f"payload_{payload_index}"]
        
        control_result = await cloud_controls_create(
            proj_uuid=proj_uuid,
            control_keys=control_keys,
            drone_sn=drone_sn,
            token=token
        )
        
        # 检查是否成功
        if isinstance(control_result, str):
            return f"❌ 获取控制权失败: {control_result}"
        
        if isinstance(control_result, dict):
            if control_result.get("code") != 0:
                return f"❌ 获取控制权失败: {control_result.get('message', '未知错误')}"
        
        print("✅ 控制权获取成功")
        await asyncio.sleep(0.5)
        
        # 步骤2: 相机朝向POI目标点
        print(f"📷 步骤2: 相机朝向POI目标点 ({poi_latitude}, {poi_longitude}, {poi_height}m)...")
        look_at_result = await camera_look_at(
            proj_uuid=proj_uuid,
            target_latitude=poi_latitude,
            target_longitude=poi_longitude,
            target_height=poi_height,
            gateway_sn=filled_gateway_sn,
            drone_sn=None,  # 已经获取过控制权
            payload_index=payload_index,
            locked=True,  # 锁定朝向
            token=token,
            auto_acquire_control=False  # 已经获取过控制权
        )
        
        # 检查是否成功
        if isinstance(look_at_result, str):
            return f"❌ 相机朝向失败: {look_at_result}"
        
        if isinstance(look_at_result, dict):
            if look_at_result.get("code") != 0:
                return f"❌ 相机朝向失败: {look_at_result.get('message', '未知错误')}"
        
        print("✅ 相机已朝向POI目标点")
        await asyncio.sleep(1)  # 等待相机调整完成

    # 步骤3: 开始POI环绕飞行
    print(f"🔄 步骤3: 开始POI环绕飞行（半径{circle_radius}米）...")
    body = {
        "device_sn": filled_gateway_sn,
        "poi_center_point": {
            "latitude": poi_latitude,
            "longitude": poi_longitude,
            "height": poi_height
        },
        "speed": speed,
        "circle_radius": circle_radius,
        "payload_index": payload_index
    }

    result = await post_json(
        f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/poi-enter",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        print("✅ POI环绕任务已启动")
    
    return result


## POI兴趣点退出
async def poi_exit(
    proj_uuid: str,
    gateway_sn: Optional[str] = None,
    drone_sn: Optional[str] = None,
    payload_index: str = DEFAULT_PAYLOAD_INDEX,
    token: str = USER_TOKEN_FIXED,
    auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    【POI兴趣点退出】停止当前的POI环绕飞行任务 (poi-exit)
    用途: 中断正在进行的POI环绕飞行，让飞行器停止环绕并保持当前位置
    场景: 需要提前结束POI环绕任务或紧急停止时使用
    前提: 飞行器正在执行POI环绕任务
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        POI退出执行结果 JSON 或错误信息字符串。
    """
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    # 步骤1: 获取飞行和负载控制权
    if auto_acquire_control:
        print("🔐 获取飞行和负载控制权...")
        control_keys = ["flight", f"payload_{payload_index}"]
        
        control_result = await cloud_controls_create(
            proj_uuid=proj_uuid,
            control_keys=control_keys,
            drone_sn=drone_sn,
            token=token
        )
        
        # 检查是否成功
        if isinstance(control_result, str):
            return f"❌ 获取控制权失败: {control_result}"
        
        if isinstance(control_result, dict):
            if control_result.get("code") != 0:
                return f"❌ 获取控制权失败: {control_result.get('message', '未知错误')}"
        
        print("✅ 控制权获取成功")
        await asyncio.sleep(0.5)

    # 步骤2: 退出POI环绕
    print("⏹️  退出POI环绕飞行...")
    body = {
        "device_sn": filled_gateway_sn
    }

    result = await delete_json(
        f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/poi-exit",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        print("✅ POI环绕任务已退出")
    
    return result
