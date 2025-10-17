"""
Astronomy Light Pollution MCP Server

为AI助手提供天文光污染评估和观测条件分析能力的MCP服务器。
基于FastMCP最新版本构建。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .elevation import ElevationService
from .pollution import LightPollutionService

__all__ = ["ElevationService", "LightPollutionService"]