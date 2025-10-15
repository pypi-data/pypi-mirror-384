# -*- coding: utf-8 -*-
"""
枚举定义 - 状态码和常量定义
"""
from enum import IntEnum


class TaskStatus(IntEnum):
    """任务状态枚举（用于航线飞行等场景）"""
    WAITING = 0          # 待开始
    STARTING_FAILURE = 1 # 启动失败
    EXECUTING = 2        # 执行中-飞行
    PAUSED = 3          # 已暂停
    TERMINATED = 4      # 终止
    SUCCESS = 5         # 成功
    SUSPENDED = 6       # 挂起
    TIMEOUT = 7         # 超时
    PARTIALLY_DONE = 8  # 部分执行状态
    PREPARING = 9       # 准备中的任务
    QUEUE_FOR_TAKEOFF = 10  # 起飞排队中


class FlyToTaskStatus(IntEnum):
    """FlyTo任务状态枚举"""
    PENDING = 0     # 待执行
    EXECUTING = 1   # 执行中
    FINISH = 2      # 完成
    FAILED = 3      # 失败
    TIMEOUT = 4     # 超时


class CommandTaskStatus(IntEnum):
    """命令任务状态枚举"""
    PENDING = 0     # 待执行
    EXECUTING = 1   # 执行中
    FINISH = 2      # 完成
    FAILED = 3      # 失败
    TIMEOUT = 4     # 超时


class FlightType(IntEnum):
    """飞行类型枚举"""
    WAYLINE_FLIGHT = 1  # 航线飞行
    MANUAL_FLIGHT = 2   # 手动飞行


class StrategyId(IntEnum):
    """推荐策略ID枚举"""
    POINT_FLY = 1               # 指点飞行
    NORMAL_WAYLINE_TAKEOFF = 2  # 普通航线起飞
    LEAPFROG_WAYLINE_LAND = 3   # 蛙跳航线降落
    DUAL_ROTATION = 4           # 双机轮转
    LEAPFROG_WAYLINE_TAKEOFF = 5 # 蛙跳航线起飞


# 状态映射字典
TASK_STATUS_MAP = {
    TaskStatus.WAITING: "待开始",
    TaskStatus.STARTING_FAILURE: "启动失败",
    TaskStatus.EXECUTING: "执行中",
    TaskStatus.PAUSED: "已暂停",
    TaskStatus.TERMINATED: "终止",
    TaskStatus.SUCCESS: "成功",
    TaskStatus.SUSPENDED: "挂起",
    TaskStatus.TIMEOUT: "超时",
    TaskStatus.PARTIALLY_DONE: "部分执行",
    TaskStatus.PREPARING: "准备中",
    TaskStatus.QUEUE_FOR_TAKEOFF: "起飞排队中"
}

# 命令任务状态映射（用于 flight_task_data.status）
COMMAND_STATUS_MAP = {
    CommandTaskStatus.PENDING: "待执行",
    CommandTaskStatus.EXECUTING: "执行中",
    CommandTaskStatus.FINISH: "完成",
    CommandTaskStatus.FAILED: "失败",
    CommandTaskStatus.TIMEOUT: "超时"
}

FLYTO_STATUS_MAP = {
    FlyToTaskStatus.PENDING: "待执行",
    FlyToTaskStatus.EXECUTING: "执行中", 
    FlyToTaskStatus.FINISH: "完成",
    FlyToTaskStatus.FAILED: "失败",
    FlyToTaskStatus.TIMEOUT: "超时"
}

FLIGHT_TYPE_MAP = {
    FlightType.WAYLINE_FLIGHT: "航线飞行",
    FlightType.MANUAL_FLIGHT: "手动飞行"
}
