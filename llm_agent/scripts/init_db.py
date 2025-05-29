#!/usr/bin/env python3
"""数据库初始化脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.models.database import create_tables, drop_tables, get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def init_database(drop_existing: bool = False):
    """初始化数据库"""
    settings = get_settings()
    
    logger.info("开始初始化数据库...")
    logger.info(f"数据库URL: {settings.database.url.replace(settings.database.password, '***')}")
    
    try:
        if drop_existing:
            logger.warning("删除现有表...")
            await drop_tables()
        
        logger.info("创建数据库表...")
        await create_tables()
        
        logger.info("数据库初始化完成！")
        
        # 验证表是否创建成功
        engine = get_engine()
        if engine:
            logger.info("数据库连接正常")
        else:
            logger.error("数据库连接失败")
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="删除现有表后重新创建"
    )
    
    args = parser.parse_args()
    
    try:
        await init_database(drop_existing=args.drop)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Windows兼容性
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
