# -*- coding: utf-8 -*-
"""
配置文件 - 项目相关配置项
支持环境变量配置
"""
import os
from typing import Optional

# API 基础配置
BASE_URL = os.getenv("DRC_BASE_URL", "https://pre-prod-flighthub-hz.djigate.com")
TIMEOUT = float(os.getenv("DRC_TIMEOUT", "30.0"))

# 用户 Token - 从环境变量获取，如果没有则使用默认值
USER_TOKEN_FIXED = os.getenv(
    "DRC_USER_TOKEN", 
    ""
)

# 默认负载索引
DEFAULT_PAYLOAD_INDEX = os.getenv("DRC_PAYLOAD_INDEX", "99-0-0")

# 飞行参数默认值
DEFAULT_MAX_SPEED = int(os.getenv("DRC_MAX_SPEED", "14"))
DEFAULT_RTH_ALTITUDE = int(os.getenv("DRC_RTH_ALTITUDE", "153"))
DEFAULT_SECURITY_TAKEOFF_HEIGHT = int(os.getenv("DRC_SECURITY_TAKEOFF_HEIGHT", "153"))

# 起飞等待时间（秒）- 用于等待设备开机和起飞过程
TAKEOFF_WAIT_TIME = int(os.getenv("DRC_TAKEOFF_WAIT_TIME", "30"))

# 项目UUID - 可以通过环境变量设置
DEFAULT_PROJECT_UUID = os.getenv("DRC_PROJECT_UUID", "")

# 设备SN - 可以通过环境变量设置
DEFAULT_DEVICE_SN = os.getenv("DRC_DEVICE_SN", "")

# 验证必要的环境变量
def validate_config() -> None:
    """验证配置是否完整"""
    if not USER_TOKEN_FIXED or USER_TOKEN_FIXED == "":
        raise ValueError("DRC_USER_TOKEN 环境变量未设置或为空")
    
    if not BASE_URL or BASE_URL == "":
        raise ValueError("DRC_BASE_URL 环境变量未设置或为空")
    
    print(f"✅ 配置验证通过:")
    print(f"   - API地址: {BASE_URL}")
    print(f"   - 超时时间: {TIMEOUT}秒")
    print(f"   - 负载索引: {DEFAULT_PAYLOAD_INDEX}")
    print(f"   - 最大速度: {DEFAULT_MAX_SPEED}m/s")
    print(f"   - 返航高度: {DEFAULT_RTH_ALTITUDE}m")
    print(f"   - 安全起飞高度: {DEFAULT_SECURITY_TAKEOFF_HEIGHT}m")
    print(f"   - 起飞等待时间: {TAKEOFF_WAIT_TIME}秒")
    if DEFAULT_PROJECT_UUID:
        print(f"   - 项目UUID: {DEFAULT_PROJECT_UUID}")
    if DEFAULT_DEVICE_SN:
        print(f"   - 设备SN: {DEFAULT_DEVICE_SN}")