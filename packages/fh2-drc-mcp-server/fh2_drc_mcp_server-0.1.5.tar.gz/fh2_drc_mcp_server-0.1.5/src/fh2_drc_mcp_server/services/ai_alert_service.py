# -*- coding: utf-8 -*-
"""
AI告警服务 - 告警配置的查询和更新
"""
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import get_json, put_json
from ..config.settings import USER_TOKEN_FIXED, DEFAULT_PAYLOAD_INDEX

# 获取全局MCP实例（将在main.py中设置）
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance


## 查询告警配置
async def get_alert_config(
        project_id: str,
        drone_sn: str,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    查询告警配置
    
    用途: 获取指定设备的AI告警配置信息
    场景: 查看当前设备的告警状态、标签、阈值等配置
    
    Args:
        project_id: 项目 UUID
        drone_sn: **无人机SN**（用于标识具体的飞机）
                 示例: 1581F8HGD24BN0010223 (注意：是无人机SN，不是网关SN)
        payload_index: 负载索引，默认 "99-0-0"
        token: x-auth-token 认证令牌
    
    Returns:
        {
            "code": 0,
            "message": "OK",
            "data": {
                "uuid": "配置UUID",
                "project_id": "项目ID",
                "drone_sn": "设备SN",
                "status": {
                    "aircraft_status": 0,      // 机载检测状态：0=关闭, 1=开启
                    "llm_status": 0,            // LLM检测状态：0=关闭, 1=开启
                    "third_aircraft_status": 0, // 第三方机载检测状态
                    "third_llm_status": 0       // 第三方LLM检测状态
                },
                "prompt_uuid": "提示词UUID",
                "labels": {
                    "aircraft_labels": [],       // 机载检测标签
                    "llm_labels": ["标签1", "标签2"],  // LLM检测标签
                    "third_aircraft_labels": [], // 第三方机载检测标签
                    "third_llm_labels": []       // 第三方LLM检测标签
                },
                "thresholds": {
                    "use_min_threshold": false,  // 是否使用最小阈值
                    "use_max_threshold": false,  // 是否使用最大阈值
                    "min_threshold": 0,          // 最小阈值
                    "max_threshold": 0           // 最大阈值
                },
                "interval_seconds": {
                    "aircraft_interval": 0,       // 机载检测间隔（秒）
                    "llm_interval": 5,            // LLM检测间隔（秒）
                    "third_aircraft_interval": 0, // 第三方机载检测间隔
                    "third_llm_interval": 0       // 第三方LLM检测间隔
                },
                "created_by": "创建者ID",
                "updated_by": "更新者ID"
            }
        }
        或错误信息字符串。
    
    示例:
        # 查询设备的告警配置
        result = await get_alert_config(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            payload_index="99-0-0"
        )
        
        if isinstance(result, dict) and result.get("code") == 0:
            data = result["data"]
            print(f"LLM检测状态: {'开启' if data['status']['llm_status'] == 1 else '关闭'}")
            print(f"检测标签: {data['labels']['llm_labels']}")
            print(f"检测间隔: {data['interval_seconds']['llm_interval']}秒")
    """
    return await get_json(
        f"/ai/api/v1/projects/{project_id}/alert-config?drone_sn={drone_sn}&payload_index={payload_index}",
        token
    )


## 更新告警配置
async def update_alert_config(
        project_id: str,
        drone_sn: str,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        alert_config_type: int = 2,
        status: int = 1,
        prompt_uuid: str = "",
        labels: Optional[List[str]] = None,
        interval_seconds: int = 5,
        use_min_threshold: bool = False,
        use_max_threshold: bool = False,
        min_threshold: int = 0,
        max_threshold: int = 0,
        token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    更新告警配置
    
    用途: 创建或更新设备的AI告警配置
    场景: 开启/关闭告警、设置检测标签、调整检测间隔等
    
    Args:
        project_id: 项目 UUID
        drone_sn: **无人机SN**（用于标识具体的飞机）
                 示例: 1581F8HGD24BN0010223 (注意：是无人机SN，不是网关SN)
        payload_index: 负载索引，默认 "99-0-0"
        alert_config_type: 告警配置类型
            1 = 机载检测（Aircraft）
            2 = LLM检测（默认）
            3 = 第三方机载检测
            4 = 第三方LLM检测
        status: 告警状态
            0 = 关闭
            1 = 开启（默认）
        prompt_uuid: 提示词UUID（用于LLM检测）
        labels: 检测标签列表，例如 ["旋转装置", "木质", "大型", "有叶片"]
        interval_seconds: 检测间隔（秒），默认5秒
        use_min_threshold: 是否使用最小阈值（用于人数检测等场景）
        use_max_threshold: 是否使用最大阈值（用于人数检测等场景）
        min_threshold: 最小阈值
        max_threshold: 最大阈值
        token: x-auth-token 认证令牌
    
    Returns:
        {
            "code": 0,
            "message": "OK",
            "data": null
        }
        或错误信息字符串。
    
    示例:
        # 开启LLM告警，检测风车
        result = await update_alert_config(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            payload_index="99-0-0",
            alert_config_type=2,  # LLM检测
            status=1,  # 开启
            prompt_uuid="49e47eaa-339b-4e9d-898f-0008a584c804",
            labels=["旋转装置", "木质", "大型", "有叶片"],
            interval_seconds=5
        )
        
        # 开启机载人数检测，设置人数阈值
        result = await update_alert_config(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            alert_config_type=1,  # 机载检测
            status=1,
            use_min_threshold=True,
            use_max_threshold=True,
            min_threshold=5,
            max_threshold=50,
            interval_seconds=3
        )
        
        # 关闭告警
        result = await update_alert_config(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            status=0  # 关闭
        )
    """
    if labels is None:
        labels = []

    body = {
        "drone_sn": drone_sn,
        "payload_index": payload_index,
        "alert_config_type": alert_config_type,
        "status": status,
        "interval_seconds": interval_seconds,
        "projectId": project_id
    }

    # 添加可选参数
    if prompt_uuid:
        body["prompt_uuid"] = prompt_uuid

    if labels:
        body["labels"] = labels

    # 添加阈值配置
    if use_min_threshold or use_max_threshold:
        body["thresholds"] = {
            "use_min_threshold": use_min_threshold,
            "use_max_threshold": use_max_threshold,
            "min_threshold": min_threshold,
            "max_threshold": max_threshold
        }

    return await put_json(
        f"/ai/api/v1/projects/{project_id}/alert-config",
        token,
        body
    )


## 快速开启LLM告警检测
async def enable_llm_alert(
        project_id: str,
        drone_sn: str,
        labels: List[str],
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        prompt_uuid: str = "49e47eaa-339b-4e9d-898f-0008a584c804",
        interval_seconds: int = 5,
        token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    快速开启LLM告警检测（便捷方法）
    
    用途: 快速开启基于LLM的物体检测告警
    场景: 检测特定物体（如电塔、风车、车辆等）时使用
    
    Args:
        project_id: 项目 UUID
        drone_sn: **无人机SN**（用于标识具体的飞机）
                 示例: 1581F8HGD24BN0010223 (注意：是无人机SN，不是网关SN)
        labels: **检测标签列表**（数组格式），描述要检测的物体特征
               示例: ["金属材质", "高耸", "电力传输设施"] - 检测电塔
                    ["旋转装置", "木质", "大型", "有叶片"] - 检测风车
                    ["车辆", "四轮", "移动"] - 检测汽车
        payload_index: 负载索引，默认 "99-0-0"
        prompt_uuid: 提示词UUID，使用默认值即可
        interval_seconds: 检测间隔（秒），默认5秒
        token: x-auth-token 认证令牌
    
    Returns:
        {
            "code": 0,
            "message": "OK",
            "data": null
        }
        或错误信息字符串。
    
    示例:
        # 检测电塔
        result = await enable_llm_alert(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            labels=["金属材质", "高耸", "电力传输设施"]
        )
    """
    return await update_alert_config(
        project_id=project_id,
        drone_sn=drone_sn,
        payload_index=payload_index,
        alert_config_type=2,  # LLM检测
        status=1,  # 开启
        prompt_uuid=prompt_uuid,
        labels=labels,
        interval_seconds=interval_seconds,
        token=token
    )


## 关闭告警检测
async def disable_alert(
        project_id: str,
        drone_sn: str,
        payload_index: str = DEFAULT_PAYLOAD_INDEX,
        alert_config_type: int = 2,
        token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    关闭告警检测（便捷方法）
    
    用途: 快速关闭指定类型的告警检测
    场景: 停止告警检测时使用
    
    Args:
        project_id: 项目 UUID
        drone_sn: 设备 SN（无人机序列号）
        payload_index: 负载索引，默认 "99-0-0"
        alert_config_type: 告警配置类型
            1 = 机载检测
            2 = LLM检测（默认）
            3 = 第三方机载检测
            4 = 第三方LLM检测
        token: x-auth-token 认证令牌
    
    Returns:
        {
            "code": 0,
            "message": "OK",
            "data": null
        }
        或错误信息字符串。
    
    示例:
        # 关闭LLM告警
        result = await disable_alert(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175"
        )
        
        # 关闭机载检测
        result = await disable_alert(
            project_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            drone_sn="1581F8HHD24B40010175",
            alert_config_type=1
        )
    """
    return await update_alert_config(
        project_id=project_id,
        drone_sn=drone_sn,
        payload_index=payload_index,
        alert_config_type=alert_config_type,
        status=0,  # 关闭
        token=token
    )
