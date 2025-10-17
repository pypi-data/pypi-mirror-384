"""
光污染分析引擎测试用例
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro_light_pollution.pollution import (
    LightPollutionService,
    SeleniumManager,
)


class TestSeleniumManager:
    """Selenium管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建测试管理器实例"""
        manager = SeleniumManager()
        yield manager
        # 注意：这里不关闭driver，因为在测试中可能没有创建

    def test_create_driver_headless(self, manager):
        """测试创建无头模式驱动"""
        # 由于实际测试中可能没有Chrome，这里只测试参数设置
        assert manager.is_headless is True

    def test_build_url(self, manager):
        """测试URL构建"""
        url = manager._build_url(39.9042, 116.4074, 7)
        expected = "https://lightpollutionmap.app/?lat=39.9042&lng=116.4074&zoom=7"
        assert url == expected

        # 测试不同缩放级别
        url_zoom = manager._build_url(39.9042, 116.4074, 10)
        assert "zoom=10" in url_zoom


class TestLightPollutionService:
    """光污染服务测试"""

    @pytest.fixture
    async def service(self):
        """创建测试服务实例"""
        service = LightPollutionService()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_validate_coordinates_valid(self, service):
        """测试有效坐标验证"""
        # 应该不抛出异常
        service._validate_coordinates(22.3, 114.1)
        service._validate_coordinates(-90, 180)
        service._validate_coordinates(90, -180)

    @pytest.mark.asyncio
    async def test_validate_coordinates_invalid(self, service):
        """测试无效坐标验证"""
        with pytest.raises(ValueError, match="纬度"):
            service._validate_coordinates(91, 0)

        with pytest.raises(ValueError, match="经度"):
            service._validate_coordinates(0, 181)

    def test_extract_bortle_scale(self, service):
        """测试Bortle等级提取"""
        # 测试不同的文本格式
        text1 = "BORTLE 7.6 High pollution"
        scale1, class1 = service._extract_bortle_scale(text1)
        assert scale1 == 7.6
        assert "Suburban/urban transition" in class1

        text2 = "Bortle Scale: 4.8 Moderate"
        scale2, class2 = service._extract_bortle_scale(text2)
        assert scale2 == 4.8
        assert "Rural/suburban transition" in class2

        # 测试无匹配的情况
        text3 = "No bortle information here"
        scale3, class3 = service._extract_bortle_scale(text3)
        assert scale3 == 5.0  # 默认值
        assert class3 == "Unknown"

    def test_extract_visible_stars(self, service):
        """测试可见星星数量提取"""
        text1 = "Visible Stars: 1,000-2,000"
        stars1 = service._extract_visible_stars(text1)
        assert stars1 == "1,000-2,000"

        text2 = "Approximately 200-500 visible stars"
        stars2 = service._extract_visible_stars(text2)
        assert stars2 == "200-500"

        # 测试关键词匹配
        text3 = "Poor visibility, barely visible"
        stars3 = service._extract_visible_stars(text3)
        assert stars3 == "200-500"

    def test_extract_milky_way_visibility(self, service):
        """测试银河可见性提取"""
        text1 = "Milky Way: Good - Structure visible"
        visibility1 = service._extract_milky_way_visibility(text1)
        assert "Good" in visibility1

        text2 = "Poor - Barely visible or not visible"
        visibility2 = service._extract_milky_way_visibility(text2)
        assert "Poor" in visibility2

    def test_extract_trend_info(self, service):
        """测试趋势信息提取"""
        text1 = "Light pollution improving, 1.0% decreasing"
        trend1, percent1 = service._extract_trend_info(text1)
        assert trend1 == "Improving"
        assert percent1 == -1.0

        text2 = "Getting worse, 0.1% increasing"
        trend2, percent2 = service._extract_trend_info(text2)
        assert trend2 == "Worsening"
        assert percent2 == 0.1

        text3 = "Conditions stable"
        trend3, percent3 = service._extract_trend_info(text3)
        assert trend3 == "Stable"
        assert percent3 == 0.0

    def test_generate_description(self, service):
        """测试描述生成"""
        desc1 = service._generate_description(1.5, "Good visibility")
        assert "Excellent dark-sky site" in desc1

        desc2 = service._generate_description(5.5, "Poor visibility")
        assert "Suburban sky" in desc2

        desc3 = service._generate_description(8.5, "Very poor")
        assert "Urban sky" in desc3

    def test_get_observation_recommendations(self, service):
        """测试观测建议生成"""
        recs1 = service._get_observation_recommendations(2.0)
        assert any("深空观测" in rec for rec in recs1)

        recs2 = service._get_observation_recommendations(7.0)
        assert any("光污染严重" in rec for rec in recs2)

    def test_get_optimal_moon_phases(self, service):
        """测试最佳月相生成"""
        phases1 = service._get_optimal_moon_phases(2.0)
        assert "新月" in phases1

        phases2 = service._get_optimal_moon_phases(7.0)
        assert phases2 == ["新月"]  # 严重光污染只有新月适合

    @pytest.mark.asyncio
    async def test_scrape_light_pollution_data_invalid_coordinates(self, service):
        """测试爬取数据无效坐标"""
        with pytest.raises(ValueError):
            await service._scrape_light_pollution_data(91, 0, 7)

    @pytest.mark.asyncio
    async def test_scrape_light_pollution_data_invalid_zoom(self, service):
        """测试爬取数据无效缩放"""
        with pytest.raises(ValueError):
            await service._scrape_light_pollution_data(39.9042, 116.4074, 15)

    @pytest.mark.asyncio
    async def test_analyze_light_pollution_invalid_coordinates(self, service):
        """测试光污染分析无效坐标"""
        result = await service.analyze_light_pollution(91, 0, 7)

        assert result["status"] == "error"
        assert result["error"]["code"] == "LIGHT_POLLUTION_ANALYSIS_FAILED"

    @pytest.mark.asyncio
    async def test_get_observation_conditions_invalid_coordinates(self, service):
        """测试观测条件评估无效坐标"""
        result = await service.get_observation_conditions(91, 0)

        assert result["status"] == "error"
        assert result["error"]["code"] == "OBSERVATION_CONDITIONS_FAILED"


class TestLightPollutionServiceIntegration:
    """光污染服务集成测试"""

    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """测试服务生命周期"""
        service = LightPollutionService()
        try:
            # 测试服务正常创建
            assert service.selenium_manager is not None
            assert service.base_url == "https://lightpollutionmap.app/"
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_coordinates_validation_integration(self):
        """测试坐标验证在真实调用中的行为"""
        service = LightPollutionService()
        try:
            # 测试无效坐标会抛出异常
            with pytest.raises(ValueError, match="纬度"):
                await service.analyze_light_pollution(91, 0, 7)
        finally:
            await service.close()


if __name__ == "__main__":
    pytest.main([__file__])
