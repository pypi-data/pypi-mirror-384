# 天文光污染分析 MCP 服务器

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.4-green.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 FastMCP 的天文光污染分析工具包，为 AI 助手提供专业的光污染评估和天文观测条件分析功能。

## 🌟 功能特性

### 核心工具
- **综合天文观测点分析** - 评估任意地点的天文观测条件
- **多地点对比分析** - 对比多个观测点，找出最佳选择
- **海拔数据查询** - 获取精确的海拔信息
- **光污染分析** - 基于 Bortle 等级的光污染评估
- **附近峰值查找** - 寻找周围的制高点

### 数据源
- **海拔数据**: Open-Elevation API, USGS API
- **光污染数据**: lightpollutionmap.app (实时爬取)
- **智能回退**: API 失败时使用合成数据

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Chrome/Chromium 浏览器 (用于 Selenium)
- uv 包管理器

### 安装依赖
```bash
# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -e .
```

### 运行测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_main.py
uv run pytest tests/test_elevation.py
uv run pytest tests/test_pollution.py

# 运行测试并显示覆盖率
uv run pytest --cov=src/astro_light_pollution
```

### 启动 MCP 服务器
```bash
# 开发模式
uv run python -m astro_light_pollution

# 或使用 uvx
uvx astro_light_pollution
```

## 📖 API 使用示例

### 1. 综合天文观测点分析

```python
from main import analyze_astronomy_site

# 分析北京天文馆的观测条件
result = await analyze_astronomy_site(
    latitude=39.9042,
    longitude=116.4074,
    detail_level="detailed"
)

print(f"综合评分: {result['data']['overall_score']}/10")
print(f"海拔: {result['data']['elevation_info']['elevation_m']}m")
print(f"光污染等级: Bortle {result['data']['light_pollution_info']['bortle_scale']}")
print(f"适合观测: {', '.join(result['data']['best_for'])}")
```

### 2. 多地点对比

```python
from main import compare_observation_sites

locations = [
    {"name": "北京天文馆", "latitude": 39.9042, "longitude": 116.4074},
    {"name": "怀柔观测站", "latitude": 40.3719, "longitude": 116.6327},
    {"name": "密云水库", "latitude": 40.3769, "longitude": 116.8419}
]

result = await compare_observation_sites(locations)

print(f"最佳观测点: {result['data']['best_choice']['name']}")
print(f"推荐理由: {result['data']['best_choice']['reasoning']}")
```

### 3. 海拔数据查询

```python
from src.elevation import get_elevation

result = await get_elevation(39.9042, 116.4074)
print(f"海拔: {result['elevation_m']}m (数据源: {result['source']})")
```

### 4. 光污染分析

```python
from src.pollution import analyze_light_pollution

result = await analyze_light_pollution(39.9042, 116.4074, zoom_level=7)
print(f"Bortle 等级: {result['data']['bortle_scale']}")
print(f"可见星星: {result['data']['visible_stars']}")
print(f"银河可见性: {result['data']['milky_way_visibility']}")
```

### 5. 观测条件评估

```python
from src.pollution import get_observation_conditions

result = await get_observation_conditions(39.9042, 116.4074)
print(f"可见性评级: {result['data']['visibility_rating']}")
print(f"最佳观测类型: {', '.join(result['data']['best_observation_types'])}")
print(f"建议: {result['data']['recommendations'][0]}")
```

## 📊 评分系统

### 综合评分算法 (1-10分)
- **光污染影响** (权重 60%): Bortle 等级越低得分越高
- **海拔影响** (权重 20%): 海拔越高得分越高
- **其他因素** (权重 20%): 包含地理位置、交通便利性等

### Bortle 等级说明
| 等级 | 描述 | 适用观测类型 |
|------|------|-------------|
| 1-2 | 优秀暗空地点 | 深空天体摄影、星系观测 |
| 3-4 | 乡村暗空地点 | 亮星团、行星观测 |
| 5-6 | 郊区天空 | 月球观测、亮星观测 |
| 7-8 | 城市天空 | 天象教育、基础认知 |
| 9 | 市中心天空 | 基本无法进行天文观测 |

## 🛠️ 开发指南

### 项目结构
```
astro_light_pollution/
├── main.py                     # FastMCP 服务器核心 (主入口)
├── src/                        # 核心模块
│   ├── __init__.py             # 包初始化
│   ├── elevation.py            # 海拔数据引擎
│   └── pollution.py            # 光污染分析引擎
├── tests/                      # 测试套件
│   ├── test_main.py
│   ├── test_elevation.py
│   └── test_pollution.py
├── pyproject.toml              # 项目配置
├── README.md                   # 项目文档
└── uv.lock                     # 依赖锁定文件
```

### 添加新工具
1. 在相应的模块中实现工具函数
2. 使用 `@mcp.tool` 装饰器注册工具
3. 编写对应的测试用例
4. 更新文档

### 测试规范
```python
@pytest.mark.asyncio
async def test_new_tool_function(self):
    """测试新工具功能"""
    # 准备测试数据
    # 执行工具函数
    # 验证结果
    pass
```

## 📋 依赖列表

### 核心依赖
- **fastmcp>=2.12.4** - MCP 服务器框架
- **aiohttp>=3.13.0** - 异步 HTTP 客户端
- **pydantic>=2.12.2** - 数据验证
- **selenium>=4.36.0** - Web 自动化
- **requests>=2.32.5** - HTTP 请求库

### 开发依赖
- **pytest>=7.4.0** - 测试框架
- **pytest-asyncio>=0.21.0** - 异步测试支持
- **pytest-cov>=4.1.0** - 测试覆盖率

## 🚨 注意事项

### 数据获取限制
- 光污染数据需要 Chrome 浏览器支持
- 部分地区 API 数据可能不准确
- 网络不稳定时会影响数据获取

### 错误处理
- 所有 API 调用都有重试机制
- 失败时提供默认值或估算数据
- 详细的错误日志记录

### 性能优化
- 使用异步并发处理
- HTTP 会话复用
- 合理的批量查询限制

## 🛠️ 配置信息

### 在 Cherry Studio / Cursor / Codex 中配置 MCP 服务器

要在这些支持 MCP 的开发环境中配置 astro_light_pollution 服务器：

```json
{
  "mcpServers": {
    "astro_light_pollution": {
      "command": "uvx",
      "args": [
        "astro_light_pollution"
      ],
      "timeout": 30000,
      "retries": 3
    }
  }
}
```

或者使用 HTTP 模式：

```json
{
  "mcpServers": {
    "astro_light_pollution_http": {
      "url": "http://localhost:8000",
      "startup": {
        "command": "uvx",
        "args": [
          "astro_light_pollution",
          "--transport", 
          "streamable-http",
          "--port", 
          "8000"
        ]
      },
      "timeout": 30000
    }
  }
}
```

将上述配置添加到您的编辑器设置中，即可在 Cherry Studio / Cursor / Codex 中使用 astro_light_pollution 提供的天文观测工具。

注意：Python 包名和命令行工具名均为 astro_light_pollution (下划线)，保持一致。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 编写测试用例
4. 提交代码更改
5. 运行测试确保通过
6. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 服务器框架
- [Open-Elevation](https://api.open-elevation.com/) - 海拔数据 API
- [USGS](https://nationalmap.gov/epqs/) - 美国地质调查局数据
- [Light Pollution Map](https://lightpollutionmap.app/) - 光污染数据可视化

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**让每一次星空观测都有科学数据支撑！** ✨