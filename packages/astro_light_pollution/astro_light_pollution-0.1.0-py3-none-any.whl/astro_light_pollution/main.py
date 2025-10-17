"""
地理天文观测MCP服务器主入口

提供综合分析和多地点对比功能。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fastmcp import FastMCP

from .elevation import ElevationService
from .pollution import LightPollutionService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化FastMCP服务器
mcp = FastMCP("astro-light-pollution")
mcp.description = "天文光污染分析工具包"

# 初始化服务
elevation_service = ElevationService()
pollution_service = LightPollutionService()


@dataclass
class SiteAnalysis:
    """观测点分析结果"""

    name: str
    latitude: float
    longitude: float
    elevation_info: Optional[Dict[str, Any]] = None
    pollution_info: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = None
    best_for: List[str] = None
    limitations: List[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.best_for is None:
            self.best_for = []
        if self.limitations is None:
            self.limitations = []
        if self.recommendations is None:
            self.recommendations = []


def _calculate_overall_score(elevation_info: Dict, pollution_info: Dict) -> float:
    """计算综合评分 (1-10分)"""
    score = 10.0

    # 光污染影响 (权重: 60%)
    if pollution_info:
        bortle_scale = pollution_info.get("bortle_scale", 5.0)
        # Bortle等级越低越好 (1-9分制)
        pollution_penalty = (bortle_scale - 1) * 0.6
        score -= pollution_penalty

    # 海拔影响 (权重: 20%)
    if elevation_info:
        elevation = elevation_info.get("elevation_m", 0)
        # 海拔越高越好 (最高加2分)
        elevation_bonus = min(elevation / 1000, 2.0) * 0.2
        score += elevation_bonus

    # 其他因素 (权重: 20%)
    # 这里可以加入天气、交通等因素，暂时给基础分
    score *= 0.8

    return max(1.0, min(10.0, score))


def _determine_best_for(score: float, pollution_info: Dict) -> List[str]:
    """确定最适合的观测类型"""
    best_for = []

    if score >= 7.0:
        best_for.extend(["深空天体摄影", "行星观测", "星系观测"])
    elif score >= 5.0:
        best_for.extend(["月球观测", "明亮行星观测", "星座观测"])
    else:
        best_for.extend(["亮星观测", "天象教育", "初学者天文"])

    # 根据光污染等级调整
    if pollution_info:
        bortle = pollution_info.get("bortle_scale", 5)
        if bortle <= 3:
            best_for.append("银河观测")
        elif bortle <= 5:
            best_for.append("亮星团观测")

    return list(set(best_for))


def _identify_limitations(
    score: float, pollution_info: Dict, elevation_info: Dict
) -> List[str]:
    """识别观测限制因素"""
    limitations = []

    if score < 5.0:
        limitations.append("光污染严重")

    if pollution_info:
        bortle = pollution_info.get("bortle_scale", 5)
        if bortle >= 7:
            limitations.append("银河基本不可见")
        if bortle >= 8:
            limitations.append("深空天体观测困难")

    if elevation_info:
        elevation = elevation_info.get("elevation_m", 0)
        if elevation < 100:
            limitations.append("地势较低，视野可能受限")

    if len(limitations) == 0:
        limitations.append("无明显限制")

    return limitations


async def _perform_site_analysis(
    latitude: float, longitude: float, detail_level: str = "basic"
) -> Dict[str, Any]:
    """
    (Private Helper) Performs the actual comprehensive analysis for a single astronomy site.
    """
    try:
        # 参数验证
        if not -90 <= latitude <= 90:
            raise ValueError("纬度必须在-90到90之间")
        if not -180 <= longitude <= 180:
            raise ValueError("经度必须在-180到180之间")
        if detail_level not in ["basic", "detailed"]:
            raise ValueError("detail_level必须是'basic'或'detailed'")

        logger.info(f"开始分析观测点: ({latitude}, {longitude})")

        # 获取海拔信息
        elevation_info = None
        try:
            elevation_info = await elevation_service.get_elevation(latitude, longitude)
            logger.info("海拔数据获取成功")
        except Exception as e:
            logger.warning(f"海拔数据获取失败: {e}")

        # 获取光污染信息
        pollution_info = None
        try:
            pollution_info = await pollution_service.analyze_light_pollution(
                latitude, longitude
            )
            logger.info("光污染数据获取成功")
        except Exception as e:
            logger.warning(f"光污染数据获取失败: {e}")

        # 计算综合评分
        score = 5.0  # 默认评分
        if elevation_info and pollution_info:
            score = _calculate_overall_score(elevation_info, pollution_info)

        # 生成分析结果
        best_for = []
        limitations = []
        recommendations = []

        if pollution_info:
            best_for = _determine_best_for(score, pollution_info)
            limitations = _identify_limitations(score, pollution_info, elevation_info)

        # 生成建议
        if score >= 7.0:
            recommendations.append("优秀的观测地点，适合各种天文观测活动")
        elif score >= 5.0:
            recommendations.append("较好的观测地点，适合基础天文观测")
        else:
            recommendations.append("观测条件一般，建议寻找更好的观测地点")

        if pollution_info and pollution_info.get("bortle_scale", 5) > 6:
            recommendations.append("光污染较严重，建议选择新月期间观测")

        # 构建响应
        result = {
            "status": "success",
            "data": {
                "coordinates": {"latitude": latitude, "longitude": longitude},
                "overall_score": round(score, 1),
                "elevation_info": elevation_info,
                "light_pollution_info": pollution_info,
                "best_for": best_for,
                "limitations": limitations,
                "recommendations": recommendations,
                "detail_level": detail_level,
            },
            "metadata": {
                "source": "astro-light-pollution",
                "timestamp": asyncio.get_event_loop().time(),
                "analysis_type": "comprehensive",
            },
        }

        logger.info(f"观测点分析完成: 评分={score:.1f}")
        return result

    except Exception as e:
        logger.error(f"观测点分析失败: {e}")
        return {
            "status": "error",
            "error": {"code": "ANALYSIS_FAILED", "message": str(e)},
            "metadata": {
                "source": "astro-light-pollution",
                "timestamp": asyncio.get_event_loop().time(),
            },
        }


@mcp.tool
async def analyze_astronomy_site(
    latitude: float, longitude: float, detail_level: str = "basic"
) -> Dict[str, Any]:
    """
    综合分析天文观测点条件

    Args:
        latitude: 纬度坐标 (-90 到 90)
        longitude: 经度坐标 (-180 到 180)
        detail_level: 分析详细程度 ("basic" | "detailed")

    Returns:
        包含海拔、光污染、综合评分的完整分析报告
    """
    return await _perform_site_analysis(latitude, longitude, detail_level)


@mcp.tool
async def compare_observation_sites(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    对比多个观测点的条件

    Args:
        locations: 待对比的地点列表，每个地点包含name, latitude, longitude

    Returns:
        包含排名、对比表格和最佳推荐的对比报告
    """
    try:
        # 参数验证
        if not locations or len(locations) < 2:
            raise ValueError("至少需要提供2个地点进行对比")

        if len(locations) > 10:
            raise ValueError("最多支持同时对比10个地点")

        # 验证地点格式
        for i, location in enumerate(locations):
            if not isinstance(location, dict):
                raise ValueError(f"地点{i+1}必须是字典格式")
            if "name" not in location:
                raise ValueError(f"地点{i+1}缺少name字段")
            if "latitude" not in location or "longitude" not in location:
                raise ValueError(f"地点{i+1}缺少经纬度坐标")

            lat = location["latitude"]
            lon = location["longitude"]
            if not -90 <= lat <= 90:
                raise ValueError(f"地点{i+1}纬度无效: {lat}")
            if not -180 <= lon <= 180:
                raise ValueError(f"地点{i+1}经度无效: {lon}")

        logger.info(f"开始并发对比{len(locations)}个观测点")

        # 使用Semaphore限制并发数为3，避免API速率限制
        semaphore = asyncio.Semaphore(3)

        async def analyze_with_semaphore(location):
            async with semaphore:
                logger.info(f"开始分析地点: {location['name']}")
                try:
                    analysis = await _perform_site_analysis(
                        location["latitude"], location["longitude"], "basic"
                    )
                    if analysis["status"] == "success":
                        return (location, analysis)
                    else:
                        logger.warning(f"地点 '{location['name']}' 分析失败")
                        return (location, None)
                except Exception as e:
                    logger.error(f"地点 '{location.get('name', 'Unknown')}' 分析异常: {e}")
                    return (location, None)

        # 并发执行所有地点的分析任务
        tasks = [analyze_with_semaphore(loc) for loc in locations]
        results = await asyncio.gather(*tasks)

        # 处理并发执行的结果
        site_analyses = []
        for location, analysis in results:
            if analysis:
                site_analysis = SiteAnalysis(
                    name=location["name"],
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    elevation_info=analysis["data"].get("elevation_info"),
                    pollution_info=analysis["data"].get("light_pollution_info"),
                    overall_score=analysis["data"].get("overall_score"),
                    best_for=analysis["data"].get("best_for", []),
                    limitations=analysis["data"].get("limitations", []),
                    recommendations=analysis["data"].get("recommendations", []),
                )
                site_analyses.append(site_analysis)

        if not site_analyses:
            raise ValueError("所有地点分析均失败，无法进行对比")

        # 按评分排序
        site_analyses.sort(key=lambda x: x.overall_score or 0, reverse=True)

        # 生成对比表格
        comparison_table = []
        for i, site in enumerate(site_analyses):
            comparison_table.append(
                {
                    "rank": i + 1,
                    "name": site.name,
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "overall_score": site.overall_score,
                    "elevation_m": (
                        site.elevation_info.get("elevation_m")
                        if site.elevation_info
                        else None
                    ),
                    "bortle_scale": (
                        site.pollution_info.get("bortle_scale")
                        if site.pollution_info
                        else None
                    ),
                    "best_for": site.best_for[:3],  # 只显示前3个
                    "limitations_count": len(site.limitations),
                }
            )

        # 最佳推荐
        best_site = site_analyses[0]

        # 生成统计信息
        scores = [
            site.overall_score
            for site in site_analyses
            if site.overall_score is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        result = {
            "status": "success",
            "data": {
                "comparison_count": len(site_analyses),
                "comparison_table": comparison_table,
                "best_choice": {
                    "name": best_site.name,
                    "overall_score": best_site.overall_score,
                    "reasoning": f"综合评分最高({best_site.overall_score:.1f}分)，{best_site.best_for[0] if best_site.best_for else '适合天文观测'}",
                    "recommendations": best_site.recommendations,
                },
                "statistics": {
                    "average_score": round(avg_score, 1),
                    "highest_score": max_score,
                    "lowest_score": min_score,
                    "score_range": round(max_score - min_score, 1),
                },
            },
            "metadata": {
                "source": "astro-light-pollution",
                "timestamp": asyncio.get_event_loop().time(),
                "analysis_type": "comparison",
            },
        }

        logger.info(f"多地点对比完成，最佳地点: {best_site.name}")
        return result

    except Exception as e:
        logger.error(f"多地点对比失败: {e}")
        return {
            "status": "error",
            "error": {"code": "COMPARISON_FAILED", "message": str(e)},
            "metadata": {
                "source": "astro-light-pollution",
                "timestamp": asyncio.get_event_loop().time(),
            },
        }


@mcp.tool
async def get_elevation(
    latitude: float, longitude: float, source: str = "auto"
) -> Dict[str, Any]:
    """
    获取指定位置的海拔信息

    Args:
        latitude: 纬度 (-90 到 90)
        longitude: 经度 (-180 到 180)
        source: 数据源选择 ("auto", "open_elevation", "usgs")

    Returns:
        海拔高度、数据源和精度信息
    """
    return await elevation_service.get_elevation(latitude, longitude, source)


@mcp.tool
async def find_nearby_peaks(
    latitude: float, longitude: float, radius_km: float = 10.0
) -> Dict[str, Any]:
    """
    查找附近的最高点

    Args:
        latitude: 中心点纬度 (-90 到 90)
        longitude: 中心点经度 (-180 到 180)
        radius_km: 搜索半径 (0-100公里)

    Returns:
        峰值信息和位置详情
    """
    return await elevation_service.find_nearby_peaks(latitude, longitude, radius_km)


@mcp.tool
async def analyze_light_pollution(
    latitude: float, longitude: float, zoom_level: int = 7
) -> Dict[str, Any]:
    """
    分析光污染情况

    Args:
        latitude: 纬度 (-90 到 90)
        longitude: 经度 (-180 到 180)
        zoom_level: 地图缩放级别 (1-10)

    Returns:
        Bortle等级、可见星星、光污染趋势等信息
    """
    return await pollution_service.analyze_light_pollution(
        latitude, longitude, zoom_level
    )


@mcp.tool
async def get_observation_conditions(
    latitude: float, longitude: float
) -> Dict[str, Any]:
    """
    获取天文观测条件评估

    Args:
        latitude: 纬度 (-90 到 90)
        longitude: 经度 (-180 到 180)

    Returns:
        观测建议、最佳观测类型、限制因素等
    """
    return await pollution_service.get_observation_conditions(latitude, longitude)


def main():
    """启动MCP服务器"""
    import argparse

    parser = argparse.ArgumentParser(description="地理天文观测MCP服务器")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="传输协议 (默认: stdio)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="主机地址 (HTTP模式)")
    parser.add_argument("--port", type=int, default=8000, help="端口 (HTTP模式)")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 配置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"启动地理天文观测MCP服务器 (传输: {args.transport})")

    # 根据传输方式启动服务器
    if args.transport == "stdio":
        # 标准 MCP 协议 (默认)
        mcp.run()
    elif args.transport == "sse":
        # Server-Sent Events 模式
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port,
            show_banner=True
        )
    elif args.transport == "streamable-http":
        # HTTP 流式模式
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            show_banner=True
        )


if __name__ == "__main__":
    main()
