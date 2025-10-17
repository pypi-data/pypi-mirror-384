"""
海拔数据引擎测试用例
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astro_light_pollution.elevation import ElevationService


class TestElevationService:
    """海拔服务测试"""

    @pytest.fixture
    async def service(self):
        """创建测试服务实例"""
        service = ElevationService()
        yield service
        await service.close()

    @pytest.mark.asyncio
    async def test_validate_coordinates_valid(self, service):
        """测试有效坐标验证"""
        # 应该不抛出异常
        service._validate_coordinates(39.9042, 116.4074)
        service._validate_coordinates(-90, 180)
        service._validate_coordinates(90, -180)

    @pytest.mark.asyncio
    async def test_validate_coordinates_invalid(self, service):
        """测试无效坐标验证"""
        with pytest.raises(ValueError, match="纬度"):
            service._validate_coordinates(91, 0)

        with pytest.raises(ValueError, match="纬度"):
            service._validate_coordinates(-91, 0)

        with pytest.raises(ValueError, match="经度"):
            service._validate_coordinates(0, 181)

        with pytest.raises(ValueError, match="经度"):
            service._validate_coordinates(0, -181)

    def test_calculate_distance(self, service):
        """测试距离计算"""
        # 北京到上海的距离大约是 1000km
        beijing_lat, beijing_lon = 39.9042, 116.4074
        shanghai_lat, shanghai_lon = 31.2304, 121.4737

        distance = service._calculate_distance(
            beijing_lat, beijing_lon, shanghai_lat, shanghai_lon
        )

        # 应该在合理范围内 (900-1200km)
        assert 900 <= distance <= 1200

    def test_generate_synthetic_elevation(self, service):
        """测试合成海拔生成"""
        # 测试不同纬度的海拔估算
        elevation_eq = service._generate_synthetic_elevation(0, 0)  # 赤道
        elevation_high = service._generate_synthetic_elevation(80, 0)  # 高纬度

        # 高纬度应该有更高的海拔
        assert elevation_high > elevation_eq

        # 应该都是正值
        assert elevation_eq >= 0
        assert elevation_high >= 0

    @pytest.mark.asyncio
    async def test_parse_open_elevation_success(self, service):
        """测试Open-Elevation响应解析成功"""
        data = {"results": [{"elevation": 432.1}]}
        result = service._parse_open_elevation(data)
        assert result == 432.1

    @pytest.mark.asyncio
    async def test_parse_open_elevation_empty(self, service):
        """测试Open-Elevation响应解析空结果"""
        data = {"results": []}
        result = service._parse_open_elevation(data)
        assert result is None

    @pytest.mark.asyncio
    async def test_parse_usgs_success(self, service):
        """测试USGS响应解析成功"""
        data = {
            "USGS_Elevation_Point_Query_Service": {
                "Elevation_Query": {"Elevation": "1234.5"}
            }
        }
        result = service._parse_usgs(data)
        assert result == 1234.5

    @pytest.mark.asyncio
    async def test_parse_usgs_invalid(self, service):
        """测试USGS响应解析无效数据"""
        data = {"USGS_Elevation_Point_Query_Service": {}}
        result = service._parse_usgs(data)
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_search_grid(self, service):
        """测试搜索网格生成"""
        grid = service._generate_search_grid(39.9042, 116.4074, 10, 5)

        # 应该生成 25 个点 (5x5)
        assert len(grid) == 25

        # 检查中心点是否包含在内
        center_found = any(
            abs(lat - 39.9042) < 0.01 and abs(lon - 116.4074) < 0.01
            for lat, lon in grid
        )
        assert center_found

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_elevation_api_success(self, mock_get, service):
        """测试海拔查询API成功"""
        # 模拟API响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {"results": [{"elevation": 500.0}]}
        mock_response.raise_for_status.return_value = None

        mock_get.return_value.__aenter__.return_value = mock_response

        await service._ensure_session()
        result = await service.get_elevation(39.9042, 116.4074)

        assert "elevation_m" in result
        assert result["elevation_m"] == 500.0
        assert result["source"] == "open_elevation"

    @pytest.mark.asyncio
    async def test_get_elevation_invalid_coordinates(self, service):
        """测试海拔查询无效坐标"""
        result = await service.get_elevation(91, 0)

        assert result["status"] == "error"
        assert result["error"]["code"] == "ELEVATION_QUERY_FAILED"

    @pytest.mark.asyncio
    async def test_find_nearby_peaks_invalid_radius(self, service):
        """测试峰值查找无效半径"""
        result = await service.find_nearby_peaks(39.9042, 116.4074, -5)

        assert result["status"] == "error"
        assert result["error"]["code"] == "PEAK_SEARCH_FAILED"

    @pytest.mark.asyncio
    async def test_find_nearby_peaks_invalid_coordinates(self, service):
        """测试峰值查找无效坐标"""
        result = await service.find_nearby_peaks(91, 0, 10)

        assert result["status"] == "error"
        assert result["error"]["code"] == "PEAK_SEARCH_FAILED"


class TestElevationServiceIntegration:
    """海拔服务集成测试"""

    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """测试服务生命周期"""
        service = ElevationService()
        try:
            # 测试服务正常创建
            assert service.session is None or service.session.closed
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_coordinates_validation(self):
        """测试坐标验证在真实调用中的行为"""
        service = ElevationService()
        try:
            # 测试无效坐标会抛出异常
            with pytest.raises(ValueError, match="纬度"):
                await service.get_elevation(91, 0)
        finally:
            await service.close()


if __name__ == "__main__":
    pytest.main([__file__])
