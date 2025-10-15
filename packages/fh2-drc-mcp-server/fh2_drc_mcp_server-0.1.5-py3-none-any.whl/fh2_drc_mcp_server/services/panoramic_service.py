# -*- coding: utf-8 -*-
"""
环拍服务 - 全景拍摄功能
"""
import asyncio
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..config.settings import USER_TOKEN_FIXED, DEFAULT_PAYLOAD_INDEX
from ..utils.helpers import auto_fill_device_sn, auto_fill_uuid, check_error_response
from .camera_service import (
    camera_photo_take, 
    camera_aim, 
    gimbal_reset_horizontal, 
    gimbal_reset_downward
)

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance



async def panoramic_shooting(
    proj_uuid: str,
    gateway_sn: Optional[str] = None,
    drone_sn: Optional[str] = None,
    uuid: Optional[str] = None,
    payload_index: str = DEFAULT_PAYLOAD_INDEX,
    token: str = USER_TOKEN_FIXED,
) -> str:
    """
    执行完整的环拍功能：到达目标点后进行360度环拍。
    
    拍摄流程:
    1. 镜头水平复位
    2. 向下瞄准 (x=0.5, y=1) 执行3次
    3. 开始环拍: 10个位置 (x=0, y=0.5) 每个位置拍照
    4. 镜头向下复位
    5. 拍照一张
    6. 镜头水平复位
    
    每次操作间隔0.5秒
    
    错误处理:
        如果遇到{"result":{"code":228431,"message":"Bad Request","data":null}}错误码，
        需要先调用cloud_controls_create抢夺飞行和负载控制权["flight","payload_99-0-0"]，然后重试操作。

    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token

    Returns:
        环拍执行结果报告字符串。
    """
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)
    results = []
    
    try:
        # 一次性获取所有需要的控制权
        from .camera_service import _acquire_payload_control
        results.append("🔐 获取控制权...")
        error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, True)
        if error:
            return error
        
        # 步骤1: 镜头水平复位
        results.append("🔄 步骤1: 镜头水平复位")
        result = await gimbal_reset_horizontal(proj_uuid, filled_gateway_sn, None, filled_uuid, payload_index, token, auto_acquire_control=False)
        error = check_error_response(result, "水平复位")
        if error:
            return error
        await asyncio.sleep(0.6)
        
        # 步骤2: 向下瞄准 (x=0.5, y=1) 执行3次
        results.append("🎯 步骤2: 向下瞄准准备 (执行3次)")
        for i in range(3):
            result = await camera_aim(proj_uuid, 0.5, 1.0, filled_gateway_sn, None, filled_uuid, payload_index, "wide", False, token, auto_acquire_control=False)
            error = check_error_response(result, f"向下瞄准第{i+1}次")
            if error:
                return error
            results.append(f"  ✅ 向下瞄准第{i+1}次完成")
            await asyncio.sleep(0.6)
        
        # 步骤3: 开始环拍 - 10个位置拍照
        results.append("📸 步骤3: 开始环拍 (10个位置)")
        for i in range(10):
            # 瞄准位置
            result = await camera_aim(proj_uuid, 0, 0.61, filled_gateway_sn, None, filled_uuid, payload_index, "wide", False, token, auto_acquire_control=False)
            error = check_error_response(result, f"环拍瞄准位置{i+1}")
            if error:
                return error
            await asyncio.sleep(0.6)
            
            # 拍照
            result = await camera_photo_take(proj_uuid, filled_gateway_sn, None, filled_uuid, payload_index, token, auto_acquire_control=False)
            error = check_error_response(result, f"环拍拍照位置{i+1}")
            if error:
                return error
            
            results.append(f"  📷 位置{i+1}: x=0, y=0.5 拍照完成")
            await asyncio.sleep(0.6)
        
        # 步骤4: 镜头向下复位
        results.append("🔽 步骤4: 镜头向下复位")
        result = await gimbal_reset_downward(proj_uuid, filled_gateway_sn, None, filled_uuid, payload_index, token, auto_acquire_control=False)
        error = check_error_response(result, "向下复位")
        if error:
            return error
        await asyncio.sleep(0.6)
        
        # 步骤5: 拍照一张
        results.append("📸 步骤5: 向下拍照")
        result = await camera_photo_take(proj_uuid, filled_gateway_sn, None, filled_uuid, payload_index, token, auto_acquire_control=False)
        error = check_error_response(result, "向下拍照")
        if error:
            return error
        await asyncio.sleep(0.6)
        
        # 步骤6: 镜头水平复位
        results.append("🔄 步骤6: 最终水平复位")
        result = await gimbal_reset_horizontal(proj_uuid, filled_gateway_sn, None, filled_uuid, payload_index, token, auto_acquire_control=False)
        error = check_error_response(result, "最终水平复位")
        if error:
            return error
        
        results.append("✅ 环拍完成！")
        results.append("📊 拍摄统计:")
        results.append("  - 环拍照片: 10张")
        results.append("  - 向下照片: 1张")
        results.append("  - 总计照片: 11张")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"环拍执行过程中出错: {str(e)}\n已完成步骤:\n" + "\n".join(results)
