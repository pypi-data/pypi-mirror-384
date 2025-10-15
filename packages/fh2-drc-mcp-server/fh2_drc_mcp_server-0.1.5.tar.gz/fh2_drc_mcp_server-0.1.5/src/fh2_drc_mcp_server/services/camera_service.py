# -*- coding: utf-8 -*-
"""
相机控制服务 - 拍照、瞄准、云台控制
"""
import asyncio
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import post_json
from ..config.settings import USER_TOKEN_FIXED, DEFAULT_PAYLOAD_INDEX
from ..utils.helpers import auto_fill_device_sn, auto_fill_uuid
from .device_service import cloud_controls_create

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance

## 自动获取负载控制权
async def _acquire_payload_control(
    proj_uuid: str,
    payload_index: str,
    drone_sn: Optional[str],
    token: str,
    auto_acquire: bool = True
) -> Optional[str]:
    """
    自动获取负载控制权（包括飞行控制权和负载控制权）
    
    Args:
        proj_uuid: 项目UUID
        payload_index: 负载索引
        drone_sn: 无人机SN（用于申请控制权）
        token: 认证token
        auto_acquire: 是否自动获取控制权
        
    Returns:
        如果失败返回错误信息，成功返回None
    """
    if not auto_acquire:
        return None
    
    # 构造控制权列表：flight + payload
    control_keys = ["flight", f"payload_{payload_index}"]
    
    print(f"🔐 正在获取控制权: {control_keys}")
    result = await cloud_controls_create(
        proj_uuid=proj_uuid,
        control_keys=control_keys,
        drone_sn=drone_sn,  # 传递drone_sn用于申请控制权
        token=token
    )
    
    # 检查是否成功
    if isinstance(result, str):
        return f"❌ 获取控制权失败: {result}"
    
    if isinstance(result, dict):
        if result.get("code") == 0:
            print("✅ 控制权获取成功")
            return None
        else:
            return f"❌ 获取控制权失败: {result.get('message', '未知错误')}"
    
    return "❌ 获取控制权失败: 响应格式错误"

## 拍照
async def camera_photo_take(
        proj_uuid: str,
        gateway_sn: str,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_photo_take` 负载控制指令，控制无人机相机拍照。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create
    📷 自动模式切换: 拍照前自动切换到拍照模式（mode=0）

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
        
    相机模式枚举:
        0 = 拍照模式
        1 = 录像模式
        2 = 智能低光模式
        3 = 全景拍照模式
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    # 步骤1: 先切换到拍照模式
    print("📷 切换到拍照模式...")
    mode_switch_result = await camera_mode_switch(
        proj_uuid=proj_uuid,
        camera_mode=0,  # 0=拍照模式
        gateway_sn=filled_gateway_sn,
        drone_sn=None,  # 已经获取过控制权
        uuid=filled_uuid,
        payload_index=payload_index,
        token=token,
        auto_acquire_control=False  # 已经获取过控制权
    )
    
    # 检查模式切换是否成功
    if isinstance(mode_switch_result, str):
        return f"❌ 切换拍照模式失败: {mode_switch_result}"
    if isinstance(mode_switch_result, dict) and mode_switch_result.get("code") != 0:
        return f"❌ 切换拍照模式失败: {mode_switch_result.get('message', '未知错误')}"
    
    print("✅ 已切换到拍照模式")
    await asyncio.sleep(0.5)  # 等待模式切换完成
    
    # 步骤2: 执行拍照
    print("📸 执行拍照...")
    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_photo_take",
        "device_cmd_data": {
            "payload_index": payload_index
        }
    }

    result = await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        print("✅ 拍照成功")
    
    return result


## 移动相机镜头角度
async def camera_aim(
        proj_uuid: str,
        x: float,
        y: float,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        camera_type: str = "wide",
        locked: bool = False,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_aim` 负载控制指令，移动相机镜头角度到指定位置。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create

    Args:
        proj_uuid: 项目 UUID（路径参数）
        x: 水平方向坐标 (0.0-1.0)
        y: 垂直方向坐标 (0.0-1.0)
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        camera_type: 相机类型，默认 "wide"
        locked: 是否锁定，默认 False
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_aim",
        "device_cmd_data": {
            "payload_index": payload_index,
            "camera_type": camera_type,
            "locked": locked,
            "x": x,
            "y": y
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )

## 让相机朝向指定的地理坐标位置
async def camera_look_at(
        proj_uuid: str,
        target_latitude: float,
        target_longitude: float,
        target_height: float,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        locked: bool = False,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_look_at` 负载控制指令，让相机朝向指定的地理坐标位置。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create

    Args:
        proj_uuid: 项目 UUID（路径参数）
        target_latitude: 目标位置纬度
        target_longitude: 目标位置经度
        target_height: 目标位置高度 (米)
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        locked: 是否锁定朝向，默认 False
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_look_at",
        "device_cmd_data": {
            "payload_index": payload_index,
            "locked": locked,
            "longitude": target_longitude,
            "latitude": target_latitude,
            "height": target_height
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )

## 将云台复位到水平位置
async def gimbal_reset_horizontal(
        proj_uuid: str,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `gimbal_reset` 负载控制指令，将云台复位到水平位置。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "gimbal_reset",
        "device_cmd_data": {
            "payload_index": payload_index,
            "reset_mode": 0  # 0=水平
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )

## 镜头向下（垂直向下90度）
async def gimbal_reset_downward(
        proj_uuid: str,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    【镜头向下】将云台硬件复位到垂直向下位置（90度）。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create
    
    📐 功能说明:
       - 🔧 硬件云台复位，精确90度垂直向下
       - ⚡ 速度快，直接硬件动作
       - 🎯 适合需要精确垂直拍摄的场景（如正射影像、测绘）
    
    💡 与 camera_tilt_down 的区别:
       - `gimbal_reset_downward`: 镜头向下 = 90度垂直向下（硬件复位）
       - `camera_tilt_down`: 俯视 = 45度俯视（模拟点击屏幕）

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "gimbal_reset",
        "device_cmd_data": {
            "payload_index": payload_index,
            "reset_mode": 1  # 1=向下
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )

## 镜头俯视45度（模拟点击屏幕）
async def camera_tilt_down(
        proj_uuid: str,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    【俯视】让镜头俯视45度，通过模拟点击屏幕实现。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create
    
    📐 实现流程:
       1️⃣ 获取控制权
       2️⃣ 水平复位（确保从一致起始位置）
       3️⃣ 通过 camera_aim(x=0.5, y=1) 调整到45度俯视
    
    📐 固定角度: 45度俯视（适合大多数航拍和巡检场景）
    
    💡 与 gimbal_reset_downward 的区别:
       - `camera_tilt_down`: 俯视 = 45度俯视（模拟点击屏幕）
       - `gimbal_reset_downward`: 镜头向下 = 90度垂直向下（硬件复位）

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
        
    使用场景:
        - 🏗️ 航拍建筑物顶部
        - 🔍 地面目标巡检
        - 📸 需要45度俯视角度的拍摄
    """
    # 步骤1: 获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    # 步骤2: 先水平复位（确保从一致的起始位置开始）
    print("🔄 步骤1/2: 云台水平复位...")
    reset_result = await gimbal_reset_horizontal(
        proj_uuid=proj_uuid,
        gateway_sn=filled_gateway_sn,
        drone_sn=None,  # 已经获取过控制权了
        uuid=filled_uuid,
        payload_index=payload_index,
        token=token,
        auto_acquire_control=False  # 不需要重复获取控制权
    )
    
    # 检查复位是否成功
    if isinstance(reset_result, str) or (isinstance(reset_result, dict) and reset_result.get("code") != 0):
        return f"❌ 云台水平复位失败: {reset_result}"
    
    # 等待云台复位完成
    await asyncio.sleep(0.5)
    
    # 步骤3: 使用 camera_aim 实现45度俯视
    print(f"📐 步骤2/2: 设置镜头45度俯视 (x=0.5, y=1)")
    
    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_aim",
        "device_cmd_data": {
            "payload_index": payload_index,
            "camera_type": "wide",
            "locked": False,
            "x": 0.5,  # 水平居中
            "y": 1  # 固定45度俯视
        }
    }

    result = await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        print(f"✅ 镜头已调整为45度俯视")
    
    return result

## 切换相机模式
async def camera_mode_switch(
        proj_uuid: str,
        camera_mode: int,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_mode_switch` 负载控制指令，切换相机模式。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create

    Args:
        proj_uuid: 项目 UUID（路径参数）
        camera_mode: 相机模式，枚举值：
                    0 = 拍照模式
                    1 = 录像模式
                    2 = 智能低光模式
                    3 = 全景拍照模式
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_mode_switch",
        "device_cmd_data": {
            "payload_index": payload_index,
            "camera_mode": camera_mode
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )

## 开始录像
async def camera_recording_start(
        proj_uuid: str,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
        auto_switch_mode: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_recording_start` 负载控制指令，开始录像。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create
    🎥 自动模式切换: 录像前自动切换到录像模式（mode=1）

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True
        auto_switch_mode: 是否自动切换到录像模式，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
        
    相机模式枚举:
        0 = 拍照模式
        1 = 录像模式
        2 = 智能低光模式
        3 = 全景拍照模式
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    # 步骤1: 先切换到录像模式（如果需要）
    if auto_switch_mode:
        print("🎥 切换到录像模式...")
        mode_switch_result = await camera_mode_switch(
            proj_uuid=proj_uuid,
            camera_mode=1,  # 1=录像模式
            gateway_sn=filled_gateway_sn,
            drone_sn=None,  # 已经获取过控制权
            uuid=filled_uuid,
            payload_index=payload_index,
            token=token,
            auto_acquire_control=False  # 已经获取过控制权
        )
        
        # 检查模式切换是否成功
        if isinstance(mode_switch_result, str):
            return f"❌ 切换录像模式失败: {mode_switch_result}"
        if isinstance(mode_switch_result, dict) and mode_switch_result.get("code") != 0:
            return f"❌ 切换录像模式失败: {mode_switch_result.get('message', '未知错误')}"
        
        print("✅ 已切换到录像模式")
        await asyncio.sleep(0.5)  # 等待模式切换完成
    
    # 步骤2: 开始录像
    print("🔴 开始录像...")
    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_recording_start",
        "device_cmd_data": {
            "payload_index": payload_index
        }
    }

    result = await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        print("✅ 录像已开始")
    
    return result


async def camera_recording_stop(
        proj_uuid: str,
        gateway_sn: str = None,
        drone_sn: str = None,
        uuid: Optional[str] = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    发送 `camera_recording_stop` 负载控制指令，停止录像。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
    """
    # 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)

    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)

    body = {
        "uuid": filled_uuid,
        "device_sn": filled_gateway_sn,
        "device_cmd_method": "camera_recording_stop",
        "device_cmd_data": {
            "payload_index": payload_index
        }
    }

    return await post_json(
        f"/manage/api/v1/projects/{proj_uuid}/payload-commands",
        token,
        body,
    )


## 切换镜头类型（红外/广角/变焦）
async def camera_lens_switch(
        proj_uuid: str,
        video_type: str,
        drone_sn: str,
        gateway_sn: str = None,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        video: str = "normal-0",
        token: str = USER_TOKEN_FIXED,
        auto_acquire_control: bool = True,
) -> Dict[str, Any] | str:
    """
    【切换镜头】切换相机镜头类型（红外/广角/变焦）。
    
    ✨ 自动控制权管理: 默认会自动获取飞行和负载控制权，无需手动调用cloud_controls_create
    
    📷 支持的镜头类型:
       - "ir": 红外镜头（热成像）
       - "wide": 广角镜头（标准视角）
       - "zoom": 变焦镜头（可放大）
    
    Args:
        proj_uuid: 项目 UUID（路径参数）
        video_type: 镜头类型 ("ir"=红外, "wide"=广角, "zoom"=变焦)
        drone_sn: **无人机SN**（必需参数，用于API请求body）
                 示例: 1581F8HGD24BN0010223
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        payload_index: 负载索引，默认 "99-0-0"
        video: 视频流ID，默认 "normal-0"
        token: x-auth-token
        auto_acquire_control: 是否自动获取控制权，默认True

    Returns:
        后端响应 JSON 或错误信息字符串。
        
    使用场景:
        - 🌡️ 红外模式：热成像检测、夜间作业
        - 📐 广角模式：标准航拍、全景拍摄
        - 🔍 变焦模式：细节检查、远距离观察
    """
    # 步骤1: 自动获取控制权
    error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, auto_acquire_control)
    if error:
        return error
    
    # 步骤2: 验证drone_sn（必需参数）
    if not drone_sn:
        return "❌ drone_sn 是必需参数（此API需要无人机SN）"
    
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    # 步骤3: 切换镜头
    print(f"🎥 切换镜头类型: {video_type}")
    
    body = {
        "camera": payload_index,
        "sn": drone_sn,  # 注意：这里使用无人机SN
        "video": video,
        "video_type": video_type
    }

    result = await post_json(
        f"/drc/api/v2/projects/{proj_uuid}/live-channels/stream/change-lens",
        token,
        body,
    )
    
    if isinstance(result, dict) and result.get("code") == 0:
        lens_type_map = {
            "ir": "红外镜头",
            "wide": "广角镜头",
            "zoom": "变焦镜头"
        }
        print(f"✅ 已切换到 {lens_type_map.get(video_type, video_type)}")
    
    return result
