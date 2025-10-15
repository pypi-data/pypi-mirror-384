# -*- coding: utf-8 -*-
"""
设备服务 - 设备推荐和云控权限管理
"""
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import post_json
from ..core.cache import DeviceCache
from ..config.settings import USER_TOKEN_FIXED
from ..utils.helpers import create_position, auto_fill_device_sn

# 获取全局MCP实例（将在main.py中设置）
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance


def register_tools(mcp_instance: FastMCP) -> None:
    """注册工具到MCP实例"""
    mcp_instance.tool()(device_recommendation)
    mcp_instance.tool()(cloud_controls_create)

## 根据任务策略获取最适合执行的 **无人机 + 网关** 列表，并把首条结果缓存
async def device_recommendation(
    proj_uuid: str,
    strategy_id: int,
    fly_latitude: float,
    fly_longitude: float,
    fly_height: float,
    token: str = USER_TOKEN_FIXED,
    wayline_uuid: Optional[str] = None,
) -> Dict[str, Any] | str:
    """
    根据任务策略获取最适合执行的 **无人机 + 网关** 列表，并把首条结果缓存
    在服务器内存，gateway_sn / drone_sn 供后续 cloud_controls_create 与 drone_takeoff 默认使用。

    Args:
        proj_uuid: **项目 UUID**（路径参数）
        token: **x-auth-token**（HTTP Header）
        strategy_id: **推荐策略 ID**
          1 = 指点飞行 ‖ 2 = 普通航线起飞 ‖ 3 = 蛙跳航线降落
          4 = 双机轮转 ‖ 5 = 蛙跳航线起飞
        fly_latitude: 飞行目标点纬度
        fly_longitude: 飞行目标点经度
        fly_height: 飞行目标点高度
        wayline_uuid: 已保存航线的 UUID（可选）

    Returns:
        OpenAPI resp.GetDeviceRecommendationResp JSON 或错误信息字符串。

    Side-effect:
        把第 1 条推荐保存到模块全局缓存
    """
    body: Dict[str, Any] = {
        "strategy_id": strategy_id,
        "fly_to_position": create_position(fly_latitude, fly_longitude, fly_height),
        "wayline_uuid": wayline_uuid,
    }
    # 清除None值
    body = {k: v for k, v in body.items() if v is not None}

    result = await post_json(
        f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/device-recommendation",
        token,
        body,
    )

    # 缓存第一条设备推荐结果
    try:
        if isinstance(result, dict) and "data" in result:
            devices = result["data"].get("devices", [])
            if devices:
                dev0 = devices[0]
                DeviceCache.set_recommendation(
                    drone_sn=dev0["drone_sn"],
                    gateway_sn=dev0["gateway_sn"]
                )
    except Exception:
        DeviceCache.clear()

    return result


async def cloud_controls_create(
    proj_uuid: str,
    control_keys: List[str],
    drone_sn: str = None,
    token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    申请无人机 / 负载的云控权限，可以直接指定drone_sn，也可以从device_recommendation接口获取到推荐的设备

    参数依赖:
        若 drone_sn 省略 → 自动取 **最近一次 device_recommendation 的 drone_sn**。

    Args:
        proj_uuid: 项目 UUID（路径参数）
        token: x-auth-token
        control_keys: 权限 key 列表，例如指点飞行为 ["flight","payload_99-0-0"]
        drone_sn: **无人机SN**（用于标识具体的飞机）；默认取上一条推荐里的 drone_sn
                 示例: 1581F8HGD24BN0010223 (注意：是无人机SN，不是网关SN)
                 
    重要说明:
        - drone_sn (无人机SN): 用于申请权限和配置告警，标识具体哪架飞机
        - device_sn (网关SN): 用于发送飞行控制指令，标识通过哪个网关发送

    Returns:
        OpenAPI dto.DroneControls 响应 JSON 或错误信息字符串。
    """
    filled_drone_sn = auto_fill_device_sn(drone_sn, use_gateway=False)
    
    if filled_drone_sn is None:
        return "drone_sn is required (no previous recommendation found)"

    body = {
        "drone_sn": filled_drone_sn,
        "control_keys": control_keys,
    }
    
    return await post_json(
        f"/drc/api/v1/projects/{proj_uuid}/cloud_controls",
        token,
        {k: v for k, v in body.items() if v is not None},
    )
