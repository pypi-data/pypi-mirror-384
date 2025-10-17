"""
光污染分析引擎 - 基于Selenium的光污染数据获取和分析

提供光污染等级查询、观测条件评估等功能。
"""

import asyncio
import logging
import json
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


@dataclass
class LightPollutionData:
    """光污染数据"""

    latitude: float
    longitude: float
    bortle_scale: float
    bortle_class: str
    visible_stars: str
    milky_way_visibility: str
    description: str
    light_pollution_trend: str
    brightness_change_percent: float
    confidence_level: str


@dataclass
class ObservationConditions:
    """观测条件评估"""

    latitude: float
    longitude: float
    bortle_scale: float
    bortle_class: str
    best_observation_types: List[str]
    limitations: List[str]
    recommendations: List[str]
    optimal_moon_phases: List[str]
    visibility_rating: str


class SeleniumManager:
    """Selenium管理器"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.is_headless: bool = True

    async def get_driver(self) -> webdriver.Chrome:
        """获取Chrome驱动"""
        if self.driver is None:
            self.driver = self._create_driver()
        return self.driver

    def _create_driver(self) -> webdriver.Chrome:
        """创建Chrome驱动"""
        chrome_options = Options()

        if self.is_headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"创建Chrome驱动失败: {e}")
            raise

    async def close_driver(self):
        """关闭Chrome驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"关闭Chrome驱动失败: {e}")
            finally:
                self.driver = None


class LightPollutionService:
    """光污染数据服务"""

    def __init__(self):
        self.selenium_manager = SeleniumManager()
        self.base_url = "https://lightpollutionmap.app/"

    async def close(self):
        """关闭服务资源"""
        await self.selenium_manager.close_driver()

    def _validate_coordinates(self, latitude: float, longitude: float):
        """验证坐标有效性"""
        if not -90 <= latitude <= 90:
            raise ValueError(f"纬度必须在-90到90之间，当前值: {latitude}")
        if not -180 <= longitude <= 180:
            raise ValueError(f"经度必须在-180到180之间，当前值: {longitude}")

    def _build_url(self, latitude: float, longitude: float, zoom: int = 7) -> str:
        """构建查询URL"""
        return f"{self.base_url}?lat={latitude}&lng={longitude}&zoom={zoom}"

    def _extract_bortle_scale(self, page_text: str) -> Tuple[float, str]:
        """从页面文本中提取Bortle等级"""
        # 查找Bortle等级模式
        patterns = [
            r"BORTLE\s+(\d+\.?\d*)",  # BORTLE 7.6
            r"Bortle\s+Scale[:\s]+(\d+\.?\d*)",  # Bortle Scale: 4.8
            r"Bortle\s*(\d+\.?\d*)",  # Bortle 4.8
        ]

        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                scale = float(match.group(1))
                if scale <= 1:
                    return scale, "Excellent dark-sky site"
                elif scale <= 2:
                    return scale, "Typical truly dark site"
                elif scale <= 3:
                    return scale, "Rural dark sky site"
                elif scale <= 4:
                    return scale, "Rural/suburban transition"
                elif scale <= 5:
                    return scale, "Suburban sky"
                elif scale <= 6:
                    return scale, "Bright suburban sky"
                elif scale <= 7:
                    return scale, "Suburban/urban transition"
                elif scale <= 8:
                    return scale, "Urban sky"
                else:
                    return scale, "Inner-city sky"

        return 5.0, "Unknown"  # 默认值

    def _extract_visible_stars(self, page_text: str) -> str:
        """提取可见星星数量"""
        patterns = [
            r"Visible\s+Stars[:\s]*([^,\n]+)",
            r"Visible\s+stars[:\s]*([^,\n]+)",
            r"(\d+(?:,\d{3})*(?:-\d+(?:,\d{3})*)?\s+visible?\s*stars?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 根据页面中的关键词估算
        if re.search(r"poor|barely|not visible", page_text, re.IGNORECASE):
            return "200-500"
        elif re.search(r"fair|visible|lacks detail", page_text, re.IGNORECASE):
            return "1,000-2,000"
        elif re.search(r"good|clear|detailed", page_text, re.IGNORECASE):
            return "2,000-5,000"
        elif re.search(r"excellent|outstanding|spectacular", page_text, re.IGNORECASE):
            return "5,000+"

        return "Unknown"

    def _extract_milky_way_visibility(self, page_text: str) -> str:
        """提取银河可见性"""
        if re.search(r"poor|barely|not visible", page_text, re.IGNORECASE):
            return "Poor - Barely visible or not visible"
        elif re.search(r"fair|visible|lacks detail", page_text, re.IGNORECASE):
            return "Fair - Visible but lacks detail"
        elif re.search(r"good|clear|structure visible", page_text, re.IGNORECASE):
            return "Good - Structure visible"
        elif re.search(r"excellent|outstanding|spectacular", page_text, re.IGNORECASE):
            return "Excellent - Spectacular view"

        return "Unknown"

    def _extract_trend_info(self, page_text: str) -> Tuple[str, float]:
        """提取光污染趋势信息"""
        # 查找趋势关键词
        if re.search(r"improving|getting better|decreasing", page_text, re.IGNORECASE):
            # 尝试提取百分比变化
            percent_match = re.search(
                r"(\d+\.?\d*)%\s*decreasing", page_text, re.IGNORECASE
            )
            if percent_match:
                return "Improving", -float(percent_match.group(1))
            return "Improving", 0.0
        elif re.search(r"worsening|getting worse|increasing", page_text, re.IGNORECASE):
            # 尝试提取百分比变化
            percent_match = re.search(
                r"(\d+\.?\d*)%\s*increasing", page_text, re.IGNORECASE
            )
            if percent_match:
                return "Worsening", float(percent_match.group(1))
            return "Worsening", 0.0
        elif re.search(r"stable|no change|constant", page_text, re.IGNORECASE):
            return "Stable", 0.0

        return "Unknown", 0.0

    def _generate_description(self, bortle_scale: float, visibility: str) -> str:
        """生成描述信息"""
        descriptions = {
            1: "Excellent dark-sky site. Perfect for deep-sky observation.",
            2: "Typical truly dark site. Great for all types of astronomy.",
            3: "Rural dark sky site. Good for most astronomical observations.",
            4: "Rural/suburban transition. Light pollution visible in several directions.",
            5: "Suburban sky. Milky Way very weak or invisible.",
            6: "Bright suburban sky. Significant light pollution.",
            7: "Suburban/urban transition. Poor conditions for deep-sky work.",
            8: "Urban sky. Very difficult to observe anything but the brightest objects.",
            9: "Inner-city sky. Essentially no astronomical observation possible.",
        }

        for scale, desc in sorted(descriptions.items(), reverse=True):
            if bortle_scale <= scale:
                return desc

        return "Unknown site conditions."

    async def _scrape_light_pollution_data(
        self, latitude: float, longitude: float, zoom: int = 7
    ) -> Dict[str, Any]:
        """使用Selenium爬取光污染数据"""
        driver = None
        try:
            driver = await self.selenium_manager.get_driver()
            url = self._build_url(latitude, longitude, zoom)

            logger.debug(f"访问光污染地图: {url}")
            driver.get(url)

            # 等待页面加载
            wait = WebDriverWait(driver, 10)

            # 等待页面基本加载完成
            await asyncio.sleep(5)

            # 获取页面文本
            page_text = driver.execute_script("return document.body.innerText;")

            if not page_text:
                raise ValueError("页面内容为空")

            # 解析数据
            bortle_scale, bortle_class = self._extract_bortle_scale(page_text)
            visible_stars = self._extract_visible_stars(page_text)
            milky_way_visibility = self._extract_milky_way_visibility(page_text)
            trend, percent_change = self._extract_trend_info(page_text)
            description = self._generate_description(bortle_scale, milky_way_visibility)

            # 确定置信度
            confidence = "Low"
            if "Bortle" in page_text and visible_stars != "Unknown":
                confidence = "Medium"
            if len(page_text) > 1000 and milky_way_visibility != "Unknown":
                confidence = "High"

            result = {
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "zoom": zoom,
                },
                "bortle_scale": bortle_scale,
                "bortle_class": bortle_class,
                "visible_stars": visible_stars,
                "milky_way_visibility": milky_way_visibility,
                "description": description,
                "light_pollution_trend": trend,
                "brightness_change_percent": percent_change,
                "confidence_level": confidence,
                "data_source": "lightpollutionmap.app",
                "scrape_timestamp": asyncio.get_event_loop().time(),
                "page_content_length": len(page_text),
            }

            logger.debug(
                f"光污染数据解析完成: Bortle {bortle_scale}, 置信度 {confidence}"
            )
            return result

        except TimeoutException:
            error_msg = "页面加载超时"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except WebDriverException as e:
            error_msg = f"浏览器操作失败: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"光污染数据爬取失败: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        finally:
            # 注意：不要在这里关闭driver，因为它会被复用
            pass

    async def analyze_light_pollution(
        self, latitude: float, longitude: float, zoom_level: int = 7
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
        try:
            self._validate_coordinates(latitude, longitude)

            if not 1 <= zoom_level <= 10:
                raise ValueError("缩放级别必须在1-10之间")

            logger.info(
                f"开始分析光污染: ({latitude}, {longitude}), 缩放: {zoom_level}"
            )

            # 爬取数据
            pollution_data = await self._scrape_light_pollution_data(
                latitude, longitude, zoom_level
            )

            return {
                "status": "success",
                "data": pollution_data,
                "metadata": {
                    "source": "lightpollution-scraper",
                    "method": "selenium",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            }

        except Exception as e:
            logger.error(f"光污染分析失败: {e}")
            return {
                "status": "error",
                "error": {"code": "LIGHT_POLLUTION_ANALYSIS_FAILED", "message": str(e)},
                "metadata": {
                    "source": "lightpollution-scraper",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            }

    def _get_observation_recommendations(self, bortle_scale: float) -> List[str]:
        """根据Bortle等级生成观测建议"""
        recommendations = []

        if bortle_scale <= 2:
            recommendations.extend(
                ["极佳的深空观测地点", "建议在新月期间进行观测", "可以使用大口径望远镜"]
            )
        elif bortle_scale <= 4:
            recommendations.extend(
                ["良好的观测地点", "适合进行基础天文观测", "建议避开满月时期"]
            )
        elif bortle_scale <= 6:
            recommendations.extend(
                ["观测条件一般", "建议主要观测亮星和行星", "需要使用光污染滤镜"]
            )
        else:
            recommendations.extend(
                ["光污染严重", "建议寻找更暗的观测地点", "主要适合亮星观测和天文教育"]
            )

        if bortle_scale > 4:
            recommendations.append("建议使用窄带滤镜改善观测效果")

        return recommendations

    def _get_optimal_moon_phases(self, bortle_scale: float) -> List[str]:
        """根据Bortle等级确定最佳月相"""
        if bortle_scale <= 3:
            return ["新月", "娥眉月", "上弦月", "下弦月"]
        elif bortle_scale <= 6:
            return ["新月", "娥眉月"]
        else:
            return ["新月"]

    async def get_observation_conditions(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """
        获取天文观测条件评估

        Args:
            latitude: 纬度 (-90 到 90)
            longitude: 经度 (-180 到 180)

        Returns:
            观测建议、最佳观测类型、限制因素等
        """
        try:
            self._validate_coordinates(latitude, longitude)

            logger.info(f"评估观测条件: ({latitude}, {longitude})")

            # 获取光污染数据
            pollution_result = await self.analyze_light_pollution(
                latitude, longitude, 7
            )

            if pollution_result["status"] != "success":
                return pollution_result

            pollution_data = pollution_result["data"]
            bortle_scale = pollution_data["bortle_scale"]

            # 确定最佳观测类型
            best_types = []
            if bortle_scale <= 2:
                best_types.extend(["深空天体", "星系观测", "星团观测", "行星摄影"])
            elif bortle_scale <= 4:
                best_types.extend(["亮星团", "行星观测", "月球观测", "双星观测"])
            elif bortle_scale <= 6:
                best_types.extend(["行星观测", "亮星观测", "星座认知"])
            else:
                best_types.extend(["亮星观测", "天象教育", "基础认知"])

            # 识别限制因素
            limitations = []
            if bortle_scale >= 5:
                limitations.append("银河观测困难")
            if bortle_scale >= 6:
                limitations.append("深空天体观测受限")
            if bortle_scale >= 8:
                limitations.append("大部分天体观测困难")

            # 生成观测建议
            recommendations = self._get_observation_recommendations(bortle_scale)

            # 确定最佳月相
            optimal_phases = self._get_optimal_moon_phases(bortle_scale)

            # 评估可见性等级
            if bortle_scale <= 2:
                visibility_rating = "优秀"
            elif bortle_scale <= 4:
                visibility_rating = "良好"
            elif bortle_scale <= 6:
                visibility_rating = "一般"
            else:
                visibility_rating = "较差"

            result = {
                "status": "success",
                "data": {
                    "coordinates": {"latitude": latitude, "longitude": longitude},
                    "bortle_scale": bortle_scale,
                    "bortle_class": pollution_data["bortle_class"],
                    "visibility_rating": visibility_rating,
                    "best_observation_types": best_types,
                    "limitations": limitations,
                    "recommendations": recommendations,
                    "optimal_moon_phases": optimal_phases,
                    "milky_way_visibility": pollution_data.get(
                        "milky_way_visibility", "Unknown"
                    ),
                    "visible_stars_estimate": pollution_data.get(
                        "visible_stars", "Unknown"
                    ),
                },
                "metadata": {
                    "source": "lightpollution-analyzer",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            }

            logger.info(
                f"观测条件评估完成: Bortle {bortle_scale}, 可见性 {visibility_rating}"
            )
            return result

        except Exception as e:
            logger.error(f"观测条件评估失败: {e}")
            return {
                "status": "error",
                "error": {"code": "OBSERVATION_CONDITIONS_FAILED", "message": str(e)},
                "metadata": {
                    "source": "lightpollution-analyzer",
                    "timestamp": asyncio.get_event_loop().time(),
                },
            }


