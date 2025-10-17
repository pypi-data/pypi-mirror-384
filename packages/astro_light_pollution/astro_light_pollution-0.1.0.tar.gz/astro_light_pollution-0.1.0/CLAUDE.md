# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 FastMCP 的天文光污染分析工具包，为 AI 助手提供专业的光污染评估和天文观测条件分析功能。项目使用 Python 3.12+ 开发，采用异步架构处理多个数据源的光污染和海拔数据。

## 常用开发命令

### 依赖管理
```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 代码质量检查
```bash
# 代码格式化
uv run black .

# 代码检查和修复
uv run ruff check --fix .
uv run ruff format .

# 运行 pre-commit hooks
uv run pre-commit run --all-files
```

### 测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_main.py
uv run pytest tests/test_elevation.py
uv run pytest tests/test_pollution.py

# 运行测试并显示覆盖率
uv run pytest --cov=src/geospatial_mcp --cov-report=html

# 运行特定测试
uv run pytest tests/test_elevation.py::test_get_elevation -v
```

### 运行应用
```bash
# 开发模式启动 MCP 服务器
uv run python main.py

# 或使用模块方式
uv run python -m astro_light_pollution

# 安装后运行
uvx astro_light_pollution
```

## 项目架构

### 核心模块结构
- **main.py**: FastMCP 服务器主入口，提供综合分析和多地点对比功能
- **src/elevation.py**: 海拔数据服务引擎，支持多个 API 数据源和网格分析
- **src/pollution.py**: 光污染分析引擎，使用 Selenium 爬取实时光污染数据

### 服务层设计
项目采用分层架构，包含三个主要服务类：
1. **ElevationService**: 处理海拔数据获取，支持 Open-Elevation 和 USGS API
2. **LightPollutionService**: 处理光污染分析，使用 Selenium 爬取 lightpollutionmap.app
3. **FastMCP Server**: 提供 MCP 协议接口，注册工具函数

### 数据流
1. 客户端通过 MCP 协议调用工具函数
2. 工具函数调用相应的服务类方法
3. 服务类处理异步 API 调用或数据爬取
4. 返回结构化的分析结果

## 开发指南

### 异步编程模式
项目大量使用 async/await 模式，所有 API 调用都是异步的：
```python
# 正确的异步调用方式
result = await elevation_service.get_elevation(lat, lon)
pollution_data = await pollution_service.analyze_light_pollution(lat, lon)
```

### 错误处理策略
- 所有 API 调用都有重试机制和回退方案
- 失败时提供默认值或估算数据
- 详细的错误日志记录，使用 logging 模块

### 坐标验证
所有地理坐标函数都包含严格的坐标验证：
- 纬度范围：-90 到 90
- 经度范围：-180 到 180

### 数据源管理
- 海拔数据：Open-Elevation API 为主要源，USGS 为备用源
- 光污染数据：lightpollutionmap.app 实时爬取
- 回退策略：API 失败时使用合成数据

## 测试规范

### 测试结构
- tests/test_main.py: 主服务器功能测试
- tests/test_elevation.py: 海拔服务测试
- tests/test_pollution.py: 光污染服务测试

### 异步测试
所有测试函数必须使用 `@pytest.mark.asyncio` 装饰器：
```python
@pytest.mark.asyncio
async def test_elevation_service():
    service = ElevationService()
    try:
        result = await service.get_elevation(39.9042, 116.4074)
        assert "elevation_m" in result
    finally:
        await service.close()
```

### 资源清理
测试中创建的服务实例必须正确清理资源：
```python
service = ElevationService()
try:
    # 测试代码
    pass
finally:
    await service.close()
```

## 环境要求

### 系统依赖
- Python 3.12+
- Chrome/Chromium 浏览器（用于 Selenium）
- uv 包管理器

### Python 依赖
- fastmcp>=2.12.4: MCP 服务器框架
- aiohttp>=3.13.0: 异步 HTTP 客户端
- selenium>=4.36.0: Web 自动化
- pydantic>=2.12.2: 数据验证

## 性能优化

### 并发处理
- 使用 asyncio.gather() 处理批量查询
- HTTP 会话复用减少连接开销
- 合理的批量查询限制（每批 5 个请求）

### 缓存策略
- Selenium WebDriver 实例复用
- HTTP 会话保持连接
- 网格搜索优化点分布

## 调试技巧

### 日志配置
项目使用标准 logging 模块，可通过修改日志级别查看详细信息：
```python
logging.basicConfig(level=logging.DEBUG)
```

### Selenium 调试
如需调试光污染数据爬取，可以修改 SeleniumManager 配置：
```python
self.is_headless = False  # 显示浏览器窗口
```

### API 测试
单独测试 API 响应：
```bash
curl "https://api.open-elevation.com/api/v1/lookup?locations=39.9042,116.4074"
```