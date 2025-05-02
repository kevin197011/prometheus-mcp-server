#!/usr/bin/env python

import os
import sys
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

import dotenv
import requests
from mcp.server.fastmcp import FastMCP

# 加载环境变量
dotenv.load_dotenv()

# 初始化 FastMCP 实例
mcp = FastMCP(name="Prometheus MCP", host="0.0.0.0", port=8000)

@dataclass
class PrometheusConfig:
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None

def load_config() -> PrometheusConfig:
    url = os.environ.get("PROMETHEUS_URL")
    if not url:
        print("❌ 错误：未设置 PROMETHEUS_URL 环境变量。")
        sys.exit(1)
    return PrometheusConfig(
        url=url,
        username=os.environ.get("PROMETHEUS_USERNAME"),
        password=os.environ.get("PROMETHEUS_PASSWORD"),
        token=os.environ.get("PROMETHEUS_TOKEN"),
    )

config = load_config()

def get_prometheus_auth():
    """根据提供的凭据获取 Prometheus 的认证信息。"""
    if config.token:
        return {"Authorization": f"Bearer {config.token}"}
    elif config.username and config.password:
        return requests.auth.HTTPBasicAuth(config.username, config.password)
    return None

def make_prometheus_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """使用适当的认证信息向 Prometheus API 发起请求。"""
    url = f"{config.url.rstrip('/')}/api/v1/{endpoint}"
    auth = get_prometheus_auth()

    try:
        if isinstance(auth, dict):  # 使用 Bearer Token
            response = requests.get(url, params=params, headers=auth)
        else:  # 使用 Basic Auth 或无认证
            response = requests.get(url, params=params, auth=auth)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 请求 Prometheus API 时出错: {e}")
        raise

    result = response.json()
    if result.get("status") != "success":
        error_msg = result.get("error", "未知错误")
        print(f"❌ Prometheus API 返回错误: {error_msg}")
        raise ValueError(f"Prometheus API 错误: {error_msg}")

    return result["data"]

@mcp.tool(description="执行 PromQL 即时查询")
async def execute_query(query: str, time: Optional[str] = None) -> Dict[str, Any]:
    """执行 PromQL 即时查询。

    参数:
        query: PromQL 查询字符串
        time: 可选的 RFC3339 或 Unix 时间戳（默认：当前时间）

    返回:
        查询结果，包括类型（vector、matrix、scalar、string）和数值
    """
    params = {"query": query}
    if time:
        params["time"] = time

    data = make_prometheus_request("query", params=params)
    return {
        "resultType": data["resultType"],
        "result": data["result"]
    }

@mcp.tool(description="执行 PromQL 范围查询")
async def execute_range_query(query: str, start: str, end: str, step: str) -> Dict[str, Any]:
    """执行 PromQL 范围查询。

    参数:
        query: PromQL 查询字符串
        start: 开始时间（RFC3339 或 Unix 时间戳）
        end: 结束时间（RFC3339 或 Unix 时间戳）
        step: 查询分辨率步长（例如 '15s', '1m', '1h'）

    返回:
        范围查询结果，包括类型（通常为 matrix）和随时间变化的数值
    """
    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step
    }

    data = make_prometheus_request("query_range", params=params)
    return {
        "resultType": data["resultType"],
        "result": data["result"]
    }

@mcp.tool(description="列出所有可用的 Prometheus 指标")
async def list_metrics() -> List[str]:
    """检索 Prometheus 中所有可用的指标名称。

    返回:
        指标名称列表
    """
    data = make_prometheus_request("label/__name__/values")
    return data

@mcp.tool(description="获取特定指标的元数据")
async def get_metric_metadata(metric: str) -> List[Dict[str, Any]]:
    """获取特定指标的元数据信息。

    参数:
        metric: 要检索元数据的指标名称

    返回:
        指标的元数据条目列表
    """
    params = {"metric": metric}
    data = make_prometheus_request("metadata", params=params)
    return data.get("metadata", [])

@mcp.tool(description="获取所有抓取目标的信息")
async def get_targets() -> Dict[str, List[Dict[str, Any]]]:
    """获取所有 Prometheus 抓取目标的信息。

    返回:
        包含活动和已丢弃目标信息的字典
    """
    data = make_prometheus_request("targets")
    return {
        "activeTargets": data.get("activeTargets", []),
        "droppedTargets": data.get("droppedTargets", [])
    }

if __name__ == "__main__":
    print("🚀 启动 Prometheus MCP Server...")
    mcp.run()
