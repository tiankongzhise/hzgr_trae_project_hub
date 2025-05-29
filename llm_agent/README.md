# 招生简章解析项目

本项目用于自动化解析高校招生简章，提取结构化信息并存储到数据库中。

## 功能特性

- **网页爬取**: 自动爬取招生简章页面和文档
- **智能解析**: 使用大语言模型解析招生简章内容
- **数据验证**: 使用Pydantic进行数据验证和序列化
- **异步数据库**: 基于SQLAlchemy 2.0的异步ORM操作
- **重试机制**: 网络请求和数据库操作的智能重试
- **日志管理**: 完整的日志记录和错误追踪
- **性能监控**: 装饰器实现的性能监控
- **配置管理**: 环境变量和TOML配置文件管理

## 项目结构

```
llm_agent/
├── src/                          # 源代码目录
│   ├── config/                   # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py           # 配置类定义
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py           # SQLAlchemy模型
│   │   └── schemas.py            # Pydantic模型
│   ├── services/                 # 业务服务
│   │   ├── __init__.py
│   │   ├── scraper.py            # 网页爬虫服务
│   │   ├── llm_service.py        # LLM调用服务
│   │   └── database_service.py   # 数据库服务
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       ├── logger.py             # 日志管理
│       ├── decorators.py         # 装饰器
│       └── retry.py              # 重试机制
├── scripts/                      # 脚本目录
│   ├── init_db.py               # 数据库初始化
│   ├── test_modules.py          # 模块测试
│   └── run.py                   # 项目运行脚本
├── 招生简章/                     # 招生简章文档存储目录
├── logs/                         # 日志文件目录
├── main.py                       # 主程序入口
├── run.bat                       # Windows批处理脚本
├── pyproject.toml               # 项目依赖配置
├── config.toml                  # 应用配置文件
├── .env.example                 # 环境变量模板
└── README.md                    # 项目说明文档
```

## 安装和配置

### 1. 环境要求

- Python 3.8+
- PostgreSQL 数据库
- uv (Python包管理工具)

### 2. 安装依赖

#### 使用uv (推荐)

```bash
# 安装uv
pip install uv

# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate

# 安装项目依赖
uv pip install -e .
```

#### 使用pip

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -e .
```

### 3. 配置环境变量

复制环境变量模板并配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数:

```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=recruitment_db
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# LLM API配置
ARK_API_KEY=your_api_key
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL_NAME=ep-20250427172216-g9s4g

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# 重试配置
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
```

### 4. 初始化数据库

```bash
# 初始化数据库表
python scripts/init_db.py

# 或者删除现有表后重新创建
python scripts/init_db.py --drop
```

## 使用方法

### 快速开始 (Windows)

双击运行 `run.bat` 文件，按照菜单提示操作。

### 命令行使用

#### 1. 测试所有模块

```bash
python scripts/test_modules.py
```

#### 2. 完整流程 (爬取+分析+保存)

```bash
# 使用默认URL
python scripts/run.py full

# 使用自定义URL
python scripts/run.py full --url "https://example.com/recruitment"

# 或者直接运行主程序
python main.py
python main.py "https://example.com/recruitment"
```

#### 3. 仅爬取招生简章

```bash
python scripts/run.py scrape --url "https://cs.bendibao.com/job/202525/124791.shtm"
```

#### 4. 仅分析本地文档

```bash
python scripts/run.py analyze
```

#### 5. 查看数据库统计

```bash
python scripts/run.py stats
```

#### 6. 列出学校信息

```bash
# 列出前10个学校
python scripts/run.py list

# 列出前20个学校
python scripts/run.py list --limit 20

# 按条件过滤
python scripts/run.py list --filter-type 公办 --demonstration
python scripts/run.py list --filter-level 专科 --backbone
```

## 数据库表结构

### schools 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键，自增 |
| full_name | String(500) | 学校全称 |
| location | String(200) | 办学地点 |
| supervising_department | String(200) | 主管部门 |
| education_level | String(50) | 办学层次 |
| institution_code | String(20) | 院校代号 |
| institution_type | String(20) | 办学类型 |
| is_demonstration | Boolean | 是否示范性院校 |
| is_backbone | Boolean | 是否骨干院校 |
| is_excellent | Boolean | 是否卓越院校 |
| is_chuyi_high_level | Boolean | 是否楚怡高水平院校 |
| advantageous_majors | JSON | 优势专业列表 |
| major_selection_criteria | Text | 优势专业判断依据 |
| original_content | Text | 原始招生简章内容 |
| source_url | String(500) | 来源URL |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 配置说明

### config.toml 配置文件

```toml
[app]
name = "招生简章解析系统"
version = "1.0.0"
debug = false

[scraper]
max_concurrent_requests = 10
request_timeout = 30
user_agent = "RecruitmentScraper/1.0"
max_retries = 3
retry_delay = 1.0

[llm]
batch_size = 5
max_tokens = 4000
temperature = 0.1
timeout = 60
max_concurrent_requests = 3

[database]
pool_size = 10
max_overflow = 20
pool_timeout = 30
pool_recycle = 3600
echo = false

[logging]
level = "INFO"
format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
rotation = "1 day"
retention = "30 days"
compression = "gz"

[monitoring]
enable_performance_tracking = true
enable_memory_monitoring = true
performance_threshold_seconds = 5.0
memory_threshold_mb = 100.0
```

## 日志管理

项目使用 `loguru` 进行日志管理，支持以下日志类型:

- **应用日志**: `logs/app_{date}.log`
- **错误日志**: `logs/error_{date}.log`
- **数据库错误日志**: `logs/db_error_{date}.log`
- **性能监控日志**: `logs/performance_{date}.log`

## 性能监控

使用装饰器实现性能监控:

```python
from src.utils.decorators import monitor_performance

@monitor_performance()
async def your_function():
    # 函数实现
    pass
```

## 重试机制

项目实现了智能重试机制:

- **数据库操作**: 网络抖动时重试，事务性错误直接失败
- **LLM调用**: API限流时重试，认证错误直接失败
- **网络请求**: 临时网络错误重试，404等直接失败

## 错误处理

- 所有数据库写入失败都会记录到专门的错误日志
- LLM调用失败会记录详细的错误信息和重试次数
- 网络请求失败会记录URL和错误原因

## 开发指南

### 添加新的数据字段

1. 修改 `src/models/database.py` 中的 `School` 模型
2. 修改 `src/models/schemas.py` 中的相关Pydantic模型
3. 更新LLM提示词以解析新字段
4. 运行数据库迁移

### 添加新的爬虫源

1. 在 `src/services/scraper.py` 中添加新的解析方法
2. 更新URL模式匹配逻辑
3. 测试新的爬虫功能

### 自定义LLM提示词

修改 `src/services/llm_service.py` 中的 `_build_analysis_prompt` 方法。

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否启动
   - 验证 `.env` 文件中的数据库配置
   - 确认数据库用户权限

2. **LLM调用失败**
   - 检查API密钥是否正确
   - 验证网络连接
   - 查看API配额是否用完

3. **爬虫失败**
   - 检查目标网站是否可访问
   - 验证网络代理设置
   - 查看是否被反爬虫机制阻止

4. **依赖安装失败**
   - 更新pip: `pip install --upgrade pip`
   - 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 日志查看

```bash
# 查看应用日志
tail -f logs/app_*.log

# 查看错误日志
tail -f logs/error_*.log

# 查看数据库错误日志
tail -f logs/db_error_*.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。
