#!/usr/bin/env python3
"""项目运行脚本"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.models.database import create_tables, close_engine
from src.services import DatabaseService
from src.utils.logger import get_logger
from main import RecruitmentProcessor

logger = get_logger(__name__)


class ProjectRunner:
    """项目运行器"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def setup_database(self):
        """设置数据库"""
        logger.info("初始化数据库...")
        try:
            await create_tables()
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def run_scraping(self, url: str):
        """运行爬取任务"""
        logger.info(f"开始爬取任务: {url}")
        
        try:
            async with RecruitmentProcessor() as processor:
                # 仅爬取，不分析
                scrape_results = await processor.scrape_recruitment_documents(url)
                
                successful = sum(1 for r in scrape_results if r.get('success', False))
                failed = len(scrape_results) - successful
                
                logger.info(f"爬取完成: 成功 {successful} 个，失败 {failed} 个")
                
                return {
                    'success': True,
                    'total': len(scrape_results),
                    'successful': successful,
                    'failed': failed,
                }
                
        except Exception as e:
            logger.error(f"爬取任务失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_analysis(self):
        """运行分析任务"""
        logger.info("开始分析任务")
        
        try:
            async with RecruitmentProcessor() as processor:
                result = await processor.process_local_documents()
                
                if result['success']:
                    logger.info(f"分析完成: 处理 {result.get('documents_found', 0)} 个文档")
                    if 'database_stats' in result:
                        stats = result['database_stats']
                        logger.info(f"数据库保存: 成功 {stats['successful']} 个，失败 {stats['failed']} 个")
                else:
                    logger.error(f"分析失败: {result.get('error', 'Unknown error')}")
                
                return result
                
        except Exception as e:
            logger.error(f"分析任务失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_full_pipeline(self, url: str):
        """运行完整流水线"""
        logger.info(f"开始完整流水线: {url}")
        
        try:
            async with RecruitmentProcessor() as processor:
                result = await processor.process_from_url(url)
                
                if result['success']:
                    logger.info("完整流水线执行成功")
                    logger.info(f"执行时间: {result['execution_time']:.2f} 秒")
                    
                    if 'database_stats' in result:
                        stats = result['database_stats']
                        logger.info(f"数据库保存: 成功 {stats['successful']} 个，失败 {stats['failed']} 个")
                else:
                    logger.error(f"完整流水线失败: {result.get('error', 'Unknown error')}")
                
                return result
                
        except Exception as e:
            logger.error(f"完整流水线失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def show_statistics(self):
        """显示数据库统计信息"""
        logger.info("获取数据库统计信息...")
        
        try:
            db_service = DatabaseService()
            stats = await db_service.get_statistics()
            
            if stats:
                print("\n" + "="*50)
                print("数据库统计信息")
                print("="*50)
                print(f"总学校数量: {stats['total_schools']}")
                print(f"公办学校: {stats['by_type']['public']}")
                print(f"民办学校: {stats['by_type']['private']}")
                print("\n特殊类型院校:")
                print(f"  示范性院校: {stats['special_types']['demonstration']}")
                print(f"  骨干院校: {stats['special_types']['backbone']}")
                print(f"  卓越院校: {stats['special_types']['excellent']}")
                print(f"  楚怡高水平院校: {stats['special_types']['chuyi_high_level']}")
                print(f"\n更新时间: {stats['updated_at']}")
                print("="*50)
            else:
                logger.warning("无法获取统计信息")
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
    
    async def list_schools(self, limit: int = 10, filters: dict = None):
        """列出学校信息"""
        logger.info(f"获取学校列表 (限制: {limit})")
        
        try:
            db_service = DatabaseService()
            schools = await db_service.list_schools(limit=limit, filters=filters)
            
            if schools:
                print("\n" + "="*80)
                print(f"学校列表 (显示前 {len(schools)} 个)")
                print("="*80)
                
                for i, school in enumerate(schools, 1):
                    print(f"{i:2d}. {school.full_name}")
                    print(f"    地点: {school.location}")
                    print(f"    类型: {school.institution_type} | 层次: {school.education_level}")
                    
                    special_types = []
                    if school.is_demonstration:
                        special_types.append("示范性")
                    if school.is_backbone:
                        special_types.append("骨干")
                    if school.is_excellent:
                        special_types.append("卓越")
                    if school.is_chuyi_high_level:
                        special_types.append("楚怡高水平")
                    
                    if special_types:
                        print(f"    特殊类型: {', '.join(special_types)}")
                    
                    if school.advantageous_majors:
                        majors = ', '.join(school.advantageous_majors[:3])  # 显示前3个专业
                        if len(school.advantageous_majors) > 3:
                            majors += f" 等{len(school.advantageous_majors)}个专业"
                        print(f"    优势专业: {majors}")
                    
                    print(f"    创建时间: {school.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print("-" * 80)
                    
            else:
                logger.warning("没有找到学校记录")
                
        except Exception as e:
            logger.error(f"获取学校列表失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="招生简章解析项目运行脚本")
    parser.add_argument("command", choices=[
        "scrape", "analyze", "full", "stats", "list", "init"
    ], help="要执行的命令")
    
    parser.add_argument("--url", 
                       default="https://cs.bendibao.com/job/202525/124791.shtm",
                       help="要爬取的URL (默认: 本地宝招生简章页面)")
    
    parser.add_argument("--limit", type=int, default=10,
                       help="列表显示限制 (默认: 10)")
    
    parser.add_argument("--filter-type", 
                       choices=["公办", "民办"],
                       help="按办学类型过滤")
    
    parser.add_argument("--filter-level", 
                       choices=["专科", "本科"],
                       help="按办学层次过滤")
    
    parser.add_argument("--demonstration", action="store_true",
                       help="仅显示示范性院校")
    
    parser.add_argument("--backbone", action="store_true",
                       help="仅显示骨干院校")
    
    args = parser.parse_args()
    
    runner = ProjectRunner()
    
    try:
        # 初始化数据库（除了init命令）
        if args.command != "init":
            await runner.setup_database()
        
        if args.command == "init":
            logger.info("初始化数据库...")
            await runner.setup_database()
            logger.info("数据库初始化完成")
            
        elif args.command == "scrape":
            result = await runner.run_scraping(args.url)
            if not result['success']:
                sys.exit(1)
                
        elif args.command == "analyze":
            result = await runner.run_analysis()
            if not result['success']:
                sys.exit(1)
                
        elif args.command == "full":
            result = await runner.run_full_pipeline(args.url)
            if not result['success']:
                sys.exit(1)
                
        elif args.command == "stats":
            await runner.show_statistics()
            
        elif args.command == "list":
            # 构建过滤条件
            filters = {}
            if args.filter_type:
                filters['institution_type'] = args.filter_type
            if args.filter_level:
                filters['education_level'] = args.filter_level
            if args.demonstration:
                filters['is_demonstration'] = True
            if args.backbone:
                filters['is_backbone'] = True
            
            await runner.list_schools(limit=args.limit, filters=filters or None)
        
        logger.info("任务执行完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await close_engine()


if __name__ == "__main__":
    # Windows兼容性
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
