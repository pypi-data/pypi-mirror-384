# -*- coding: utf-8 -*-
"""
状态服务 - 飞行状态查询和智能解析
"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import get_json
from ..config.settings import USER_TOKEN_FIXED
from ..models.enums import (
    TASK_STATUS_MAP, FLYTO_STATUS_MAP, FLIGHT_TYPE_MAP, COMMAND_STATUS_MAP,
    FlightType, TaskStatus, FlyToTaskStatus, CommandTaskStatus
)
from ..utils.helpers import auto_fill_device_sn

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance


## 查询当前飞行任务状态（智能解析版）
async def get_flight_status(
    proj_uuid: str,
    gateway_sn: Optional[str] = None,
    token: str = USER_TOKEN_FIXED,
    raw_data: bool = False,
) -> Dict[str, Any] | str:
    """
    查询当前飞行任务状态，用于监控飞行进度和任务执行情况。
    
    🔍 默认返回智能解析后的人性化状态描述
    📊 可选返回原始JSON数据（设置 raw_data=True）
    
    背景知识:
    - 如果飞行器关机状态，下发一键起飞，到能够查询到飞行状态需要0-80秒范围内
    - 时间长短不定需要等待，建议持续查询直到2min内没查到数据，判定任务失败
    
    **注意**: 此接口建议限制调用频率为 10秒一次，避免频繁请求。
    
    Args:
        proj_uuid: 项目 UUID（路径参数）
        gateway_sn: **网关SN/机场SN**；默认取最近一次设备推荐里的 gateway_sn
                   示例: 8UUDMAQ00A0197 (注意：不是无人机SN)
        token: x-auth-token
        raw_data: 是否返回原始JSON数据（默认False，返回智能解析的人性化描述）
    
    Returns:
        - 默认 (raw_data=False): 人性化的飞行状态描述和建议
        - raw_data=True: 原始飞行状态 JSON，包含：
            - flight_id: 飞行任务ID
            - flight_task_data: 飞行任务基础数据
                - status: 任务状态 (0=待执行, 1=执行中, 2=完成, 3=失败, 4=超时)
            - flight_type: 飞行类型 (1=航线飞行, 2=手动飞行)
            - fly_to_task: 飞向目标点任务（手动飞行时）
                - status: FlyTo任务状态 (0=待执行, 1=执行中, 2=完成, 3=失败, 4=超时)
                - way_points: 航点列表
                - remaining_distance: 剩余距离(米)
                - remaining_time: 剩余时间(秒)
            - return_home_info: 返航信息
            - is_first_fly_to: 是否首次飞向目标点
    
    状态判断逻辑:
    - 刚下发起飞后可能暂时无数据，需等待几秒
    - 手动飞行中，fly_to_task为null表示已到达目标点
    - flight_task_data.status=2 表示飞行执行中
    - fly_to_task.status=2 表示飞向目标点完成
    """
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    
    if filled_gateway_sn is None:
        return "gateway_sn is required (no previous recommendation found)"

    # 获取原始飞行状态数据
    status_result = await get_json(
        f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/in-flight?sn={filled_gateway_sn}",
        token,
    )
    
    # 如果请求失败或需要原始数据，直接返回
    if isinstance(status_result, str) or raw_data:
        return status_result
    
    # 智能解析飞行状态
    try:
        data = status_result.get("data")
        if not data:
            return "📭 当前无飞行任务数据\n💡 可能原因：\n   1. 任务尚未开始或已结束\n   2. 刚下发起飞指令，数据还在生成中（2秒内正常）\n⏱️  建议：等待3-5秒后再次查询"
        
        flight_task = data.get("flight_task_data", {})
        fly_to_task = data.get("fly_to_task")
        flight_type = data.get("flight_type", 0)
        flight_id = data.get("flight_id", "")
        
        task_status_code = flight_task.get("status", -1)
        
        # 🔧 修复：flight_task_data.status 使用 CommandTaskStatus 枚举
        # 对于手动飞行 (flight_type=2):
        # - status=1 (CommandTaskStatus.EXECUTING) + fly_to_task存在 → 正在飞向目标点
        # - status=1 (CommandTaskStatus.EXECUTING) + fly_to_task=null → 已到达目标点（悬停）
        # - status=2 (CommandTaskStatus.FINISH) → 任务完成
        
        if flight_type == FlightType.MANUAL_FLIGHT and task_status_code == CommandTaskStatus.EXECUTING:
            # status=1 (EXECUTING)：飞行任务执行中
            if fly_to_task is not None:
                flyto_status_code = fly_to_task.get("status", -1)
                if flyto_status_code == FlyToTaskStatus.EXECUTING:
                    main_status = "飞行中（前往目标点）"
                elif flyto_status_code == FlyToTaskStatus.FINISH:
                    main_status = "飞行中（即将到达）"
                else:
                    main_status = "飞行中"
            else:
                # fly_to_task 为 null，说明已到达目标点
                main_status = "已到达（空中悬停）"
        else:
            # 其他状态使用命令状态映射表
            main_status = COMMAND_STATUS_MAP.get(task_status_code, TASK_STATUS_MAP.get(task_status_code, "未知状态"))
        
        flight_type_desc = FLIGHT_TYPE_MAP.get(flight_type, "未知类型")
        
        result = ["=" * 50]
        result.append("📊 飞行状态查询结果")
        result.append("=" * 50)
        result.append(f"🆔 任务ID: {flight_id}")
        result.append(f"📍 飞行类型: {flight_type_desc}")
        result.append(f"🔄 主任务状态: {main_status}")
        result.append("")
        
        # 手动飞行的详细分析
        if flight_type == FlightType.MANUAL_FLIGHT:
            result.append("--- 手动飞行详情 ---")
            if fly_to_task is None:
                # 无飞向目标任务
                if task_status_code == CommandTaskStatus.EXECUTING:
                    result.append("✅ 已到达目标点（空中悬停）")
                    result.append("📷 可以执行拍照、录像、飞向目标点等操作")
                elif task_status_code == CommandTaskStatus.FINISH:
                    result.append("✅ 飞行任务已完成")
                else:
                    result.append("ℹ️  无飞向目标任务")
            else:
                # 有飞向目标任务
                flyto_status = FLYTO_STATUS_MAP.get(fly_to_task.get("status", -1), "未知")
                result.append(f"🎯 飞向目标状态: {flyto_status}")
                
                remaining_distance = fly_to_task.get("remaining_distance")
                remaining_time = fly_to_task.get("remaining_time", 0)
                
                if remaining_distance is not None:
                    result.append(f"📏 剩余距离: {remaining_distance:.1f} 米")
                    result.append(f"⏱️  预计剩余时间: {remaining_time:.0f} 秒")
                
                way_points = fly_to_task.get("way_points", [])
                way_point_index = fly_to_task.get("way_point_index", 0)
                if way_points:
                    result.append(f"🗺️  航点进度: {way_point_index}/{len(way_points)}")
                    
                    # 显示当前目标航点信息
                    if way_point_index > 0 and way_point_index <= len(way_points):
                        current_wp = way_points[way_point_index - 1]
                        if isinstance(current_wp, dict):
                            lat = current_wp.get("latitude", "?")
                            lon = current_wp.get("longitude", "?")
                            height = current_wp.get("height", "?")
                            result.append(f"📍 当前目标点: ({lat}, {lon}, {height}m)")
            result.append("")
        
        # 返航信息
        return_home_info = data.get("return_home_info")
        if return_home_info:
            result.append("--- 返航信息 ---")
            rth_status = return_home_info.get("status")
            if rth_status:
                result.append(f"🏠 返航状态: {FLYTO_STATUS_MAP.get(rth_status, '未知')}")
            result.append("")
        
        # 根据状态给出建议
        result.append("=" * 50)
        result.append("💡 操作建议")
        result.append("=" * 50)
        
        if "已到达" in main_status or "悬停" in main_status:
            # 已到达目标点或空中悬停
            result.append("✅ 无人机已到达目标点，处于空中悬停状态")
            result.append("📸 现在可以执行以下操作：")
            result.append("   • 拍照 (camera_photo_take)")
            result.append("   • 录像 (camera_recording_task)")
            result.append("   • 全景拍摄 (panoramic_shooting)")
            result.append("   • POI环绕 (poi_enter)")
            result.append("   • 飞向新目标点 (fly_to_points)")
            result.append("   • 返航 (drone_return_home)")
        elif "飞行中" in main_status:
            # 正在飞向目标点
            if fly_to_task and remaining_distance is not None:
                result.append("🚁 无人机正在飞向目标点，请耐心等待")
                result.append(f"📏 剩余距离: {remaining_distance:.1f} 米")
                result.append(f"⏱️  预计还需 {remaining_time:.0f} 秒到达")
                result.append("🔄 建议：等待10秒后再次查询状态")
            else:
                result.append("🚁 无人机飞行中")
        elif main_status == "执行中":
            result.append("✅ 飞行任务执行中")
            result.append("📸 可以执行相机操作等任务")
        elif main_status in ["成功", "终止"]:
            result.append("🏁 飞行任务已结束")
            result.append("💡 如需继续飞行，请发起新的飞行任务")
        elif main_status == "待开始":
            result.append("⏳ 任务尚未开始")
            result.append("💡 如果刚下发起飞指令，请等待几秒钟后再查询")
            result.append("⚠️  如果持续无数据超过2分钟，可能任务启动失败")
        elif main_status == "失败":
            result.append("❌ 飞行任务执行失败")
            result.append("💡 建议检查设备状态或重新规划任务")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ 解析飞行状态时出错: {str(e)}\n\n💡 建议：可以设置 raw_data=True 查看原始数据"
