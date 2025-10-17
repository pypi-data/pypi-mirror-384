# 地理天文观测工具包MCP - 最终版PRD文档

## 📋 产品概述

### **产品名称**
GeoSpatial Astronomy MCP Server (地理天文观测MCP服务器)

### **产品愿景**
为AI助手提供专业的地理天文观测数据获取和分析能力，帮助天文爱好者和研究人员进行观测点选址和天文条件评估。

### **核心价值主张**
- **一站式天文选址**：集成地形、海拔、光污染等多维度数据
- **专业数据支持**：基于权威数据源的科学分析结果
- **AI原生集成**：通过MCP协议无缝集成到AI助手工作流
- **快速决策支持**：为天文观测提供数据驱动的选址建议

## 🎯 目标用户与使用场景

### **主要用户群体**
1. **天文爱好者** - 个人天文观测选址
2. **天文摄影师** - 寻找最佳拍摄地点
3. **天文教育工作者** - 教学和实践支持
4. **业余天文团体** - 集体观测活动规划

### **核心使用场景**
- **观测点评估**：评估特定位置的天文观测条件
- **多地点比较**：对比多个候选地点的观测质量
- **路线规划**：为移动观测规划最佳路线
- **教学演示**：展示地理因素对天文观测的影响

## 🛠️ 技术架构设计

### **技术栈选择**
- **包管理器**：uv (超高性能Python包管理)
- **MCP框架**：FastMCP (最新版本 >= 2.12.4)
- **核心语言**：Python 3.12+ (推荐使用最新稳定版)
- **异步处理**：asyncio + aiohttp
- **数据处理**：原生Python + 最小化依赖

### **FastMCP v2.12.4 最新版本特性**
- **版本要求**：FastMCP >= 2.12.4 (最新稳定版，发布于2025年9月26日)
- **Python要求**：Python 3.10+ (最低要求)
- **简化API**：`@mcp.tool` 装饰器，更Pythonic的接口设计
- **异步支持**：原生支持async/await模式
- **类型安全**：完整的类型提示支持
- **企业级认证**：内置Google、GitHub、Azure、Auth0、WorkOS等认证支持
- **客户端库**：完整的FastMCP客户端实现
- **部署选项**：支持本地、FastMCP Cloud、自托管等多种部署方式
- **测试工具**：内置测试工具和实用程序
- **协议兼容**：严格遵循MCP协议规范

### **uv技术优势**
- **极致性能**：比pip快10-100倍的依赖安装速度
- **现代化设计**：Rust编写的高性能包管理器
- **兼容性好**：完全兼容现有Python生态
- **依赖管理**：精确的依赖版本控制和冲突解决
- **跨平台支持**：Windows、macOS、Linux全平台支持

## 📦 简化项目结构设计

### **极简项目架构** (基于3个核心脚本原则)

```
geospatial-astronomy-mcp/
├── pyproject.toml              # uv项目配置 + 包发布配置
├── README.md                   # 项目文档
├── LICENSE                     # 开源许可证
├── .gitignore                  # Git忽略文件
├── src/
│   └── geospatial_mcp/         # 主包目录
│       ├── __init__.py         # 包初始化，暴露主要API
│       ├── main.py             # 🎯 MCP服务器主入口 (1/3)
│       ├── elevation.py        # 🎯 海拔数据工具 (2/3)
│       └── pollution.py        # 🎯 光污染分析工具 (3/3)
├── reference/                  # 参考实现（现有脚本）
│   ├── elevation_api.py
│   ├── contour_extractor.py
│   └── selenium_light_pollution_scraper.py
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── test_elevation.py
│   ├── test_pollution.py
│   └── test_main.py
└── docs/                       # 简化文档
    ├── README.md               # 快速开始指南
    └── examples.md             # 使用示例
```

### **3个核心脚本职责划分**

#### **1. main.py - MCP服务器核心** (约200行)
- **FastMCP服务器初始化** (使用最新API)
- **工具注册和路由** (基于@tool装饰器)
- **综合分析工具** (组合elevation + pollution功能)
- **多地点对比工具**
- **错误处理和日志配置**
- **服务器启动入口**

#### **2. elevation.py - 地理数据引擎** (约300行)
- **海拔查询API包装** (基于现有elevation_api.py)
- **网格海拔数据获取**
- **峰值信息分析**
- **地理坐标计算工具**
- **数据源故障转移逻辑**

#### **3. pollution.py - 光污染分析引擎** (约350行)
- **光污染数据爬取** (基于现有selenium脚本)
- **Bortle等级分析**
- **光污染趋势计算**
- **观测条件评估**
- **Selenium优化和错误处理**

## 📋 Python包发布配置

### **pyproject.toml - 统一配置文件**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "geospatial-astronomy-mcp"
version = "0.1.0"
description = "Geospatial and astronomy observation tools for AI assistants via MCP protocol"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["mcp", "astronomy", "geospatial", "elevation", "light-pollution", "fastmcp"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Astronomy",
    "Topic :: Scientific/Engineering :: GIS"
]

dependencies = [
    "fastmcp>=2.12.4",          # FastMCP v2.12.4 最新稳定版
    "aiohttp>=3.13.0",          # 异步HTTP客户端 (最新版)
    "pydantic>=2.12.2",         # 数据验证 (FastMCP依赖，最新版)
    "selenium>=4.36.0",         # 光污染爬虫 (最新版)
    "requests>=2.32.5"          # 备用HTTP客户端 (最新版)
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",            # 测试框架
    "pytest-asyncio>=0.21.0",  # 异步测试支持
    "black>=23.0.0",            # 代码格式化
    "ruff>=0.1.0"               # 代码检查
]

[project.urls]
Homepage = "https://github.com/yourusername/geospatial-astronomy-mcp"
Documentation = "https://github.com/yourusername/geospatial-astronomy-mcp#readme"
Repository = "https://github.com/yourusername/geospatial-astronomy-mcp.git"
"Bug Tracker" = "https://github.com/yourusername/geospatial-astronomy-mcp/issues"

[project.scripts]
geospatial-mcp = "geospatial_mcp.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/geospatial_mcp"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### **包入口配置**

#### **src/geospatial_mcp/__init__.py**
```python
"""
Geospatial Astronomy MCP Server

为AI助手提供地理天文观测数据获取和分析能力的MCP服务器。
基于FastMCP最新版本构建。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .main import main
from .elevation import ElevationService
from .pollution import LightPollutionService

__all__ = [
    "main",
    "ElevationService",
    "LightPollutionService"
]
```

## 🛠️ 简化依赖管理方案

### **最小依赖原则**
基于Linus MVP理念，采用最小化依赖策略：

#### **核心依赖** (必需)
```toml
dependencies = [
    "fastmcp>=2.12.4",          # MCP框架核心 (FastMCP v2.12.4)
    "aiohttp>=3.13.0",          # 异步HTTP客户端 (最新版)
    "pydantic>=2.12.2",         # 数据验证 (FastMCP依赖，最新版)
    "selenium>=4.36.0",         # 光污染爬虫 (最新版)
    "requests>=2.32.5"          # 备用HTTP客户端 (最新版)
]
```

#### **开发依赖** (可选)
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",            # 测试框架
    "pytest-asyncio>=0.21.0",  # 异步测试支持
    "black>=23.0.0",            # 代码格式化
    "ruff>=0.1.0"               # 代码检查
]
```

### **FastMCP v2.12.4 使用要点**
- **装饰器语法**：使用`@mcp.tool`注册工具 (注意：不是@mcp.tool())
- **服务器初始化**：`mcp = FastMCP("server_name")`
- **启动方式**：`mcp.run()` 或 `fastmcp run server.py`
- **异步支持**：工具函数可以是同步或异步
- **类型提示**：强制使用Python类型提示进行参数验证
- **错误处理**：使用FastMCP内置的错误处理机制
- **企业级认证**：内置多种身份验证提供者支持

## 🎯 核心功能规格 (基于FastMCP最新版)

### **MCP工具接口设计**

#### **main.py 提供的工具**
```python
from fastmcp import FastMCP

mcp = FastMCP("geospatial-astronomy")

@mcp.tool
async def analyze_astronomy_site(
    latitude: float,
    longitude: float,
    detail_level: str = "basic"  # "basic" | "detailed"
) -> dict:
    """
    综合分析天文观测点条件

    Args:
        latitude: 纬度坐标 (-90 到 90)
        longitude: 经度坐标 (-180 到 180)
        detail_level: 分析详细程度

    Returns:
        包含海拔、光污染、综合评分的完整分析报告
    """

@mcp.tool
async def compare_observation_sites(
    locations: list[dict]  # [{"lat": float, "lon": float, "name": str}]
) -> dict:
    """
    对比多个观测点的条件

    Args:
        locations: 待对比的地点列表

    Returns:
        包含排名、对比表格和最佳推荐的对比报告
    """
```

#### **elevation.py 提供的工具**
```python
@mcp.tool
async def get_elevation(
    latitude: float,
    longitude: float,
    source: str = "auto"
) -> dict:
    """
    获取指定位置的海拔信息

    Args:
        latitude: 纬度
        longitude: 经度
        source: 数据源选择 ("auto", "open_elevation", "usgs")

    Returns:
        海拔高度、数据源和精度信息
    """

@mcp.tool
async def find_nearby_peaks(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0
) -> dict:
    """
    查找附近的最高点

    Args:
        latitude: 中心点纬度
        longitude: 中心点经度
        radius_km: 搜索半径

    Returns:
        峰值信息和位置详情
    """
```

#### **pollution.py 提供的工具**
```python
@mcp.tool
async def analyze_light_pollution(
    latitude: float,
    longitude: float,
    zoom_level: int = 7
) -> dict:
    """
    分析光污染情况

    Args:
        latitude: 纬度
        longitude: 经度
        zoom_level: 地图缩放级别

    Returns:
        Bortle等级、可见星星、光污染趋势等信息
    """

@mcp.tool
async def get_observation_conditions(
    latitude: float,
    longitude: float
) -> dict:
    """
    获取天文观测条件评估

    Args:
        latitude: 纬度
        longitude: 经度

    Returns:
        观测建议、最佳观测类型、限制因素等
    """
```

## 🚀 打包和部署方案

### **uv工作流集成**

#### **1. 开发环境设置**
```bash
# 安装uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建项目
uv init geospatial-astronomy-mcp
cd geospatial-astronomy-mcp

# 安装依赖 (包含FastMCP最新版)
uv sync

# 开发模式安装
uv pip install -e .
```

#### **2. 构建Python包**
```bash
# 构建wheel包
uv build

# 构建结果
dist/
├── geospatial_astronomy_mcp-0.1.0-py3-none-any.whl
└── geospatial-astronomy-mcp-0.1.0.tar.gz
```

#### **3. 发布到PyPI**
```bash
# 安装发布工具
uv pip install twine

# 发布到测试PyPI
uv run twine upload --repository testpypi dist/*

# 发布到正式PyPI
uv run twine upload dist/*
```

### **用户安装和使用**

#### **方式1：直接安装运行**
```bash
# 使用pip安装
pip install geospatial-astronomy-mcp

# 使用uv安装 (推荐)
uv add geospatial-astronomy-mcp

# 启动MCP服务器
geospatial-mcp

# 或Python模块方式
python -m geospatial_mcp.main
```

#### **方式2：开发者模式**
```bash
# 克隆源码
git clone https://github.com/yourusername/geospatial-astronomy-mcp.git
cd geospatial-astronomy-mcp

# 使用uv安装开发依赖
uv sync --dev

# 运行服务器
uv run geospatial-mcp

# 或直接运行
uv run python -m geospatial_mcp.main
```

### **MCP客户端配置示例**

#### **Claude Desktop配置**
```json
{
  "mcpServers": {
    "geospatial-astronomy": {
      "command": "geospatial-mcp",
      "args": []
    }
  }
}
```

#### **其他AI助手配置**
```yaml
# 示例：其他支持MCP的AI助手配置
mcp_servers:
  - name: geospatial-astronomy
    command: geospatial-mcp
    description: "Geospatial and astronomy observation tools powered by FastMCP"
```

## 📊 数据模型简化

### **统一响应格式**
```python
{
    "status": "success" | "error",
    "data": {...},           # 实际数据
    "metadata": {            # 元数据
        "source": str,       # 数据源
        "timestamp": str,    # 时间戳
        "coordinates": {     # 坐标信息
            "latitude": float,
            "longitude": float
        }
    },
    "error": {               # 错误信息 (如有)
        "code": str,
        "message": str
    }
}
```

### **核心数据结构**
```python
# 海拔数据
ElevationData = {
    "elevation_m": float,
    "source": str,
    "accuracy": str
}

# 光污染数据
LightPollutionData = {
    "bortle_scale": float,
    "bortle_class": str,
    "visible_stars": str,
    "milky_way_visibility": str
}

# 综合评分
SiteRating = {
    "overall_score": float,      # 1-10分
    "best_for": list[str],       # 适合的观测类型
    "limitations": list[str]     # 限制因素
}
```

## 📈 数据质量标准

### **数据源可靠性**
- **海拔数据**：Open-Elevation API (主), USGS API (备)
- **光污染数据**：Light Pollution Map (基于NOAA VIIRS)
- **地理计算**：WGS84坐标系，Haversine距离公式

### **数据准确性指标**
- **海拔精度**：±10米 (城市地区), ±30米 (偏远地区)
- **光污染等级**：基于最新卫星数据，年更新
- **地理坐标**：6位小数精度 (约1米精度)

### **错误处理机制**
- **API故障转移**：主数据源失败时自动切换备用数据源
- **数据验证**：输入参数范围检查和合理性验证
- **异常恢复**：网络超时重试和优雅降级

## ⚡ MVP开发计划 (72小时版)

### **Day 1: 基础框架 (8小时)**
- **上午 (4h)**：uv项目设置 + FastMCP最新版集成
- **下午 (4h)**：elevation.py核心功能 + 基础测试

### **Day 2: 核心功能 (8小时)**
- **上午 (4h)**：pollution.py光污染分析功能
- **下午 (4h)**：main.py综合分析工具

### **Day 3: 完善优化 (8小时)**
- **上午 (4h)**：多地点对比功能 + 错误处理
- **下午 (4h)**：测试完善 + 文档编写 + 打包测试

## 🎯 成功指标

### **技术指标**
- **响应时间**：单次查询 < 5秒，综合分析 < 15秒
- **可用性**：99%+ 服务可用性
- **数据准确性**：海拔误差 < 50米，光污染等级准确率 > 95%

### **用户指标**
- **易用性**：AI助手能够独立完成完整的观测点分析流程
- **实用性**：分析结果对实际观测选址具有指导价值
- **满意度**：用户反馈评分 > 4.0/5.0

### **业务指标**
- **集成度**：成功集成到主流AI助手平台
- **使用率**：周活跃用户数稳定增长
- **口碑**：在天文社区获得积极反馈

## 🎯 成功标准

### **MVP验收标准**
- ✅ 3个核心脚本功能完整可用
- ✅ 使用FastMCP最新版本 (>=2.12.4)
- ✅ 可通过uv打包成Python包
- ✅ 支持pip/uv安装和运行
- ✅ MCP协议通信正常
- ✅ 基础测试覆盖主要功能
- ✅ README文档包含安装使用说明

### **发布就绪标准**
- ✅ PyPI包发布成功
- ✅ GitHub Actions自动化测试
- ✅ 文档完整 (API + 使用示例)
- ✅ 社区反馈收集机制

## 📋 总结

这个最终版PRD文档体现了**极简主义**和**实用主义**的设计理念：

### **核心优化点**
1. **FastMCP最新版本**：基于>=0.4.0，利用最新特性
2. **3个脚本原则**：main.py(服务器) + elevation.py(地理) + pollution.py(光污染)
3. **极简依赖**：最小化外部依赖，优先使用原生Python功能
4. **标准化打包**：完整的pyproject.toml配置，支持PyPI发布
5. **uv原生支持**：从开发到发布的完整uv工作流

### **技术优势**
- **简单可靠**：减少复杂度，提高稳定性
- **易于维护**：清晰的职责划分，便于后续扩展
- **用户友好**：标准pip/uv安装，开箱即用
- **开发高效**：72小时MVP，渐进式改进

### **部署灵活性**
- **本地安装**：`pip install geospatial-astronomy-mcp`
- **开发者模式**：`uv sync && uv run geospatial-mcp`
- **容器化部署**：支持Docker部署
- **MCP集成**：标准MCP协议，广泛兼容

这个方案完美平衡了**简单性**和**实用性**，既符合Linus MVP理念的快速验证要求，又为后续的功能扩展和商业化留下了充足空间。基于"Talk is cheap. Show me the code"的实用主义哲学，专注于快速实现可用的核心功能，通过实际使用收集反馈，渐进式改进完善。