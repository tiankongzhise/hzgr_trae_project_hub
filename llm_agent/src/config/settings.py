"""应用配置设置"""

import os
import toml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.toml"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = Field(..., description="数据库连接URL")
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="连接池最大溢出")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接池回收时间")


class LLMConfig(BaseModel):
    """LLM配置"""
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    model: str = Field(..., description="模型名称")
    max_tokens: int = Field(default=4000, description="最大token数")
    temperature: float = Field(default=0.1, description="温度参数")
    timeout: int = Field(default=60, description="请求超时时间")
    max_retries: int = Field(default=3, description="最大重试次数")


class ScraperConfig(BaseModel):
    """爬虫配置"""
    base_url: str = Field(..., description="目标网站URL")
    request_timeout: int = Field(default=30, description="请求超时时间")
    max_concurrent_requests: int = Field(default=5, description="最大并发请求数")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="用户代理"
    )


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    dir: str = Field(default="logs", description="日志目录")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="日志格式"
    )
    rotation: str = Field(default="1 day", description="日志轮转")
    retention: str = Field(default="30 days", description="日志保留时间")
    compression: str = Field(default="gz", description="日志压缩格式")


class MonitoringConfig(BaseModel):
    """监控配置"""
    enable_performance_tracking: bool = Field(default=True, description="启用性能跟踪")
    log_function_calls: bool = Field(default=True, description="记录函数调用")
    log_execution_time: bool = Field(default=True, description="记录执行时间")
    log_parameters: bool = Field(default=False, description="记录参数")
    log_return_values: bool = Field(default=False, description="记录返回值")


class RetryConfig(BaseModel):
    """重试配置"""
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟时间")


class Settings(BaseModel):
    """应用设置"""
    # 基础配置
    app_name: str = Field(default="recruitment-analyzer", description="应用名称")
    version: str = Field(default="0.1.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")
    
    # 各模块配置
    database: DatabaseConfig
    llm: LLMConfig
    scraper: ScraperConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    retry: RetryConfig
    
    # 目录配置
    project_root: Path = Field(default=PROJECT_ROOT, description="项目根目录")
    data_dir: Path = Field(default=PROJECT_ROOT / "招生简章", description="数据目录")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs", description="日志目录")

    def __init__(self, **kwargs):
        # 加载TOML配置文件
        toml_config = {}
        if CONFIG_FILE.exists():
            toml_config = toml.load(CONFIG_FILE)
        
        # 从环境变量和TOML配置构建配置
        config_data = {
            "database": {
                "url": os.getenv("DATABASE_URL", ""),
                "pool_size": toml_config.get("database", {}).get("pool_size", 10),
                "max_overflow": toml_config.get("database", {}).get("max_overflow", 20),
                "pool_timeout": toml_config.get("database", {}).get("pool_timeout", 30),
                "pool_recycle": toml_config.get("database", {}).get("pool_recycle", 3600),
            },
            "llm": {
                "api_key": os.getenv("ARK_API_KEY", ""),
                "base_url": os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                "model": os.getenv("LLM_MODEL", "ep-20250427172216-g9s4g"),
                "max_tokens": toml_config.get("llm", {}).get("max_tokens", 4000),
                "temperature": toml_config.get("llm", {}).get("temperature", 0.1),
                "timeout": toml_config.get("llm", {}).get("timeout", 60),
                "max_retries": toml_config.get("llm", {}).get("max_retries", 3),
            },
            "scraper": {
                "base_url": toml_config.get("scraper", {}).get("base_url", "https://cs.bendibao.com/job/202525/124791.shtm"),
                "request_timeout": toml_config.get("scraper", {}).get("request_timeout", 30),
                "max_concurrent_requests": toml_config.get("scraper", {}).get("max_concurrent_requests", 5),
                "user_agent": toml_config.get("scraper", {}).get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "dir": os.getenv("LOG_DIR", "logs"),
                "format": toml_config.get("logging", {}).get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"),
                "rotation": toml_config.get("logging", {}).get("rotation", "1 day"),
                "retention": toml_config.get("logging", {}).get("retention", "30 days"),
                "compression": toml_config.get("logging", {}).get("compression", "gz"),
            },
            "monitoring": toml_config.get("monitoring", {
                "enable_performance_tracking": True,
                "log_function_calls": True,
                "log_execution_time": True,
                "log_parameters": False,
                "log_return_values": False,
            }),
            "retry": {
                "max_retries": int(os.getenv("MAX_RETRIES", "3")),
                "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
            },
            "app_name": toml_config.get("app", {}).get("name", "recruitment-analyzer"),
            "version": toml_config.get("app", {}).get("version", "0.1.0"),
            "debug": toml_config.get("app", {}).get("debug", False),
        }
        
        # 合并传入的参数
        config_data.update(kwargs)
        
        super().__init__(**config_data)
        
        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)


# 全局设置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局设置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
