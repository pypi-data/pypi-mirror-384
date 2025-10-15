# -*- coding: utf-8 -*-
"""
录像服务 - 完整的录像流程控制
"""
import asyncio
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..config.settings import USER_TOKEN_FIXED, DEFAULT_PAYLOAD_INDEX
from ..utils.helpers import auto_fill_device_sn, auto_fill_uuid, check_error_response
from .camera_service import (
    camera_mode_switch,
    camera_recording_start,
    camera_recording_stop,
    _acquire_payload_control
)

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance

## 完整的录像任务流程：开始录像 → 等待指定时间 → 停止录像 → 切换回拍照模式
async def camera_recording_task(
    proj_uuid: str,
    recording_duration: int,
    gateway_sn: Optional[str] = None,
    drone_sn: Optional[str] = None,
    uuid: Optional[str] = None,
    payload_index: str = DEFAULT_PAYLOAD_INDEX,
    token: str = USER_TOKEN_FIXED,
) -> str:
    """
    执行完整的录像任务流程：开始录像 → 等待指定时间 → 停止录像 → 切换回拍照模式
    
    ⏱️ 执行时间: 约 recording_duration + 5-8秒（包含模式切换和指令发送时间）
    
    录像流程:
    1. 获取控制权
    2. 开始录像（自动切换到录像模式 camera_mode=1）
    3. 录像指定时长（显示进度）
    4. 停止录像
    5. 切换回拍照模式（camera_mode=0）
    
    Args:
        proj_uuid: 项目 UUID（路径参数）
        recording_duration: 录像时长（秒），建议范围：5-300秒
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        drone_sn: **无人机SN**（用于申请控制权）；默认取最近一次设备推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：不是网关SN)
        uuid: 项目UUID
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token
    
    Returns:
        录像任务执行结果报告字符串。
    """
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    filled_uuid = auto_fill_uuid(uuid, proj_uuid)
    results = []
    
    try:
        # 步骤1: 一次性获取所有需要的控制权
        results.append("🔐 步骤1: 获取控制权...")
        error = await _acquire_payload_control(proj_uuid, payload_index, drone_sn, token, True)
        if error:
            return error
        await asyncio.sleep(0.5)
        
        # 步骤2: 开始录像（自动切换到录像模式）
        results.append("🔴 步骤2: 开始录像（自动切换到录像模式）")
        result = await camera_recording_start(
            proj_uuid,
            gateway_sn=filled_gateway_sn,
            drone_sn=None,
            uuid=filled_uuid,
            payload_index=payload_index,
            token=token,
            auto_acquire_control=False,  # 已经获取过控制权
            auto_switch_mode=True  # 自动切换到录像模式
        )
        error = check_error_response(result, "开始录像")
        if error:
            return error
        results.append(f"  ✅ 录像已开始，将录制 {recording_duration} 秒")
        
        # 步骤3: 录像过程 - 显示进度
        results.append(f"⏳ 步骤3: 录像中（{recording_duration}秒）...")
        
        # 每10秒显示一次进度
        elapsed = 0
        while elapsed < recording_duration:
            wait_time = min(10, recording_duration - elapsed)
            await asyncio.sleep(wait_time)
            elapsed += wait_time
            
            if elapsed < recording_duration:
                progress = (elapsed / recording_duration) * 100
                results.append(f"  📹 录像进度: {elapsed}/{recording_duration}秒 ({progress:.1f}%)")
            else:
                results.append(f"  📹 录像完成: {recording_duration}/{recording_duration}秒 (100%)")
        
        # 步骤4: 停止录像
        results.append("⏹️  步骤4: 停止录像")
        result = await camera_recording_stop(
            proj_uuid,
            gateway_sn=filled_gateway_sn,
            drone_sn=None,
            uuid=filled_uuid,
            payload_index=payload_index,
            token=token,
            auto_acquire_control=False
        )
        error = check_error_response(result, "停止录像")
        if error:
            return error
        results.append("  ✅ 录像已停止")
        await asyncio.sleep(1)
        
        # 步骤5: 切换回拍照模式
        results.append("📷 步骤5: 切换回拍照模式")
        result = await camera_mode_switch(
            proj_uuid,
            camera_mode=0,  # 0=拍照模式
            gateway_sn=filled_gateway_sn,
            drone_sn=None,
            uuid=filled_uuid,
            payload_index=payload_index,
            token=token,
            auto_acquire_control=False
        )
        error = check_error_response(result, "切换拍照模式")
        if error:
            # 如果切换回拍照模式失败，不影响整体任务成功，只记录警告
            results.append(f"  ⚠️  切换回拍照模式失败: {error}")
        else:
            results.append("  ✅ 已切换回拍照模式")
        
        # 任务完成总结
        results.append("")
        results.append("✅ 录像任务完成！")
        results.append("📊 录像统计:")
        results.append(f"  - 录像时长: {recording_duration}秒")
        results.append(f"  - 开始时间: 任务启动后 ~2秒")
        results.append(f"  - 结束时间: 任务启动后 ~{recording_duration + 3}秒")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ 录像任务执行过程中出错: {str(e)}\n\n已完成步骤:\n" + "\n".join(results)

