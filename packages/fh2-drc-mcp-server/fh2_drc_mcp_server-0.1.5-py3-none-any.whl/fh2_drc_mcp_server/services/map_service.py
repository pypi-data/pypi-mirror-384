# -*- coding: utf-8 -*-
"""
地图服务 - Pin点查询和创建
"""
from typing import Any, Dict, List, Optional
from ..core.http_client import get_json, post_json
from ..config.settings import USER_TOKEN_FIXED


## 查询工作空间的所有Pin点（地图标注点）
async def get_pin_points(
    workspace_id: str,
    token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    查询工作空间的所有Pin点（地图标注点）
    
    用途: 获取工作空间中所有的地图标注点信息
    场景: 查看已标记的目标位置、兴趣点等
    
    Args:
        workspace_id: 工作空间 UUID
        token: x-auth-token 认证令牌
    
    Returns:
        包含所有元素组及其Pin点的完整列表，或错误信息字符串。
    
    示例:
        # 查询所有Pin点
        result = await get_pin_points("a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b")
        if isinstance(result, dict) and result.get("code") == 0:
            for group in result["data"]:
                print(f"分组: {group['name']}")
                for element in group.get("elements", []):
                    if element.get("resource", {}).get("type") == 0:  # Point类型
                        coords = element["resource"]["content"]["geometry"]["coordinates"]
                        print(f"  - {element['name']}: 经度={coords[0]}, 纬度={coords[1]}, 高度={coords[2]}")
    """
    return await get_json(
        f"/map/api/v1/workspaces/{workspace_id}/element-groups",
        token
    )

## 在地图上创建Pin点标记
async def create_pin_point(
    workspace_id: str,
    group_id: str,
    longitude: float,
    latitude: float,
    height: float = 0.0,
    name: str = "新建点",
    color: str = "#2D8CF0",
    clamp_to_ground: bool = True,
    icon: int = 0,
    token: str = USER_TOKEN_FIXED,
) -> Dict[str, Any] | str:
    """
    在地图上创建Pin点标记
    
    用途: 在地图上创建标记点，用于标记目标位置、兴趣点等
    场景: 规划任务前标记关键位置，或在任务执行中动态添加标注
    
    Args:
        workspace_id: 工作空间 UUID
        group_id: 元素组 ID（可通过 get_pin_points 获取，通常使用 "default" 组的ID）
        longitude: 经度
        latitude: 纬度
        height: 高度（米），当 clamp_to_ground=True 时会自动贴地
        name: Pin点名称
        color: 颜色（十六进制格式）
            "#2D8CF0" = 蓝色（默认）
            "#E23C39" = 红色（危险/警告）
            "#19BE6B" = 绿色（安全/允许）
            "#FFBB00" = 黄色（注意）
        clamp_to_ground: 是否贴地（true=贴地，false=悬空在指定高度）
        icon: 图标类型
            0 = 默认图标
            -4 = 危险标记
            -5 = 自定义图标
        token: x-auth-token 认证令牌
    
    Returns:
        创建成功返回新Pin点的UUID，或错误信息字符串。
    
    示例:
        # 创建一个红色的危险标记点
        result = await create_pin_point(
            workspace_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
            group_id="6e4eeb06-27b9-4438-ab23-1abaa7c80a14",
            longitude=114.356593,
            latitude=22.793825,
            height=50.0,
            name="危险区域",
            color="#E23C39",
            icon=-4,
            clamp_to_ground=False
        )
    """
    # 构建请求体
    body = {
        "element_source": 1,
        "resource": {
            "type": 0,  # 0 = Point
            "content": {
                "type": "Feature",
                "properties": {
                    "color": color,
                    "clampToGround": clamp_to_ground,
                    "icon": icon
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude, height]
                }
            }
        }
    }
    
    return await post_json(
        f"/map/api/v1/workspaces/{workspace_id}/element-groups/{group_id}/elements",
        token,
        body
    )

## 获取工作空间的默认元素组ID（"default"分组）
async def get_default_group_id(
    workspace_id: str,
    token: str = USER_TOKEN_FIXED,
) -> str | None:
    """
    获取工作空间的默认元素组ID（"default"分组）
    
    用途: 自动查找 "default" 分组的ID，用于后续创建Pin点
    场景: 当不知道group_id时，可以先调用此方法获取默认分组ID
    
    Args:
        workspace_id: 工作空间 UUID
        token: x-auth-token 认证令牌
    
    Returns:
        默认分组的UUID字符串，如果未找到则返回 None
    
    示例:
        # 先获取默认分组ID，再创建Pin点
        group_id = await get_default_group_id("a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b")
        if group_id:
            result = await create_pin_point(
                workspace_id="a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
                group_id=group_id,
                longitude=114.356593,
                latitude=22.793825,
                height=50.0,
                name="目标点A"
            )
    """
    result = await get_pin_points(workspace_id, token)
    
    if isinstance(result, dict) and result.get("code") == 0:
        groups = result.get("data", [])
        for group in groups:
            if group.get("name") == "default":
                return group.get("id")
    
    return None
