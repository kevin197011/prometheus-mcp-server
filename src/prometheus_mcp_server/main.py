#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv, find_dotenv
from prometheus_mcp_server.server import mcp, config

def setup_environment():
    # 加载 .env 文件中的环境变量
    if load_dotenv(find_dotenv()):
        print("✅ 已加载 .env 文件中的环境变量")
    else:
        print("⚠️ 未找到 .env 文件，使用系统环境变量")

    # 验证 Prometheus URL 是否设置
    if not config.url:
        print("❌ 错误：未设置 PROMETHEUS_URL 环境变量")
        print("请设置为 Prometheus 服务器的 URL，例如：http://localhost:9090")
        return False

    # 显示配置信息
    print("\n🔧 Prometheus 配置：")
    print(f"  📡 服务器地址：{config.url}")

    # 显示认证方式
    if config.username and config.password:
        print("  🔐 认证方式：基本认证（Basic Auth）")
    elif config.token:
        print("  🔐 认证方式：Bearer Token")
    else:
        print("  ⚠️ 未设置认证信息，可能无法访问受保护的 Prometheus 实例")

    return True

def run_server():
    """启动 Prometheus MCP Server 的主函数"""
    if not setup_environment():
        sys.exit(1)

    print("\n🚀 启动 Prometheus MCP Server...")
    print("📡 使用 SSE 传输模式运行服务器")

    try:
        mcp.run(transport="sse")
    except Exception as e:
        print(f"❌ 服务器启动失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
