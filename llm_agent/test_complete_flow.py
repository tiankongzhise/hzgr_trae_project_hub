#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流程测试脚本
测试本地文档读取、LLM分析和数据库保存的完整流程
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from src.config import get_settings
from src.models.database import create_tables, close_engine
from src.models.schemas import ScrapingResult
from src.services.enhanced_llm_service import EnhancedLLMService
from src.services.database_service import DatabaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_complete_flow():
    """测试完整流程"""
    logger.info("开始完整流程测试")
    
    try:
        # 初始化数据库
        await create_tables()
        
        # 读取本地文档
        recruitment_dir = Path("招生简章").resolve()
        documents = []
        
        if not recruitment_dir.exists():
            logger.error(f"招生简章目录不存在: {recruitment_dir}")
            return
        
        # 读取txt文件
        for doc_file in recruitment_dir.glob("*.txt"):
            try:
                content = doc_file.read_text(encoding='utf-8')
                if content.strip():
                    filename = doc_file.stem
                    school_name = filename.split('_')[0] if '_' in filename else filename
                    
                    documents.append({
                        'school_name': school_name,
                        'file_path': str(doc_file),
                        'content': content,
                        'file_size': doc_file.stat().st_size,
                    })
                    logger.info(f"读取文档: {doc_file.name} ({len(content)} 字符)")
            except Exception as e:
                logger.error(f"读取文档失败 {doc_file}: {e}")
        
        logger.info(f"共读取 {len(documents)} 个文档")
        
        if not documents:
            logger.warning("没有找到可分析的文档")
            return
        
        # 选择前6个文档进行测试
        test_documents = documents[:6]
        logger.info(f"选择前 {len(test_documents)} 个文档进行测试")
        
        # 创建LLM服务
        llm_service = EnhancedLLMService()
        
        # 转换为ScrapingResult格式
        scraping_results = []
        for doc in test_documents:
            result = ScrapingResult(
                school_name=doc['school_name'],
                recruitment_url=doc['file_path'],
                content=doc['content'],
                success=True,
                error_message=None,
                file_size=doc['file_size']
            )
            scraping_results.append(result)
        
        # LLM分析
        logger.info("开始LLM分析...")
        start_time = datetime.now()
        
        analysis_results = await llm_service.analyze_multiple_concurrent(
            scraping_results,
            max_concurrent=3
        )
        
        analysis_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"LLM分析完成，耗时: {analysis_time:.2f}秒")
        
        # 统计分析结果
        successful = sum(1 for r in analysis_results if r is not None and r.confidence > 0)
        failed = len(analysis_results) - successful
        
        logger.info(f"分析统计: 成功 {successful} 个，失败 {failed} 个")
        
        # 保存到数据库
        if successful > 0:
            logger.info("开始保存到数据库...")
            db_service = DatabaseService()
            
            school_data_list = []
            for result in analysis_results:
                if result is not None and result.confidence > 0:
                    school_data_list.append(result.school_info)
            
            save_results = await db_service.batch_create_schools(school_data_list)
            
            # 统计保存结果
            save_successful = sum(1 for r in save_results if r.success)
            save_failed = len(save_results) - save_successful
            
            logger.info(f"数据库保存完成: 成功 {save_successful} 个，失败 {save_failed} 个")
            
            # 获取数据库统计信息
            db_stats = await db_service.get_statistics()
            if db_stats:
                logger.info(f"数据库统计: 总计 {db_stats['total_schools']} 个学校")
                logger.info(f"公办学校: {db_stats['by_type']['public']} 个")
                logger.info(f"民办学校: {db_stats['by_type']['private']} 个")
        
        # 输出详细结果
        logger.info("\n=== 测试结果汇总 ===")
        logger.info(f"文档读取: {len(documents)} 个")
        logger.info(f"LLM分析: 成功 {successful} 个，失败 {failed} 个")
        if successful > 0:
            logger.info(f"数据库保存: 成功 {save_successful} 个，失败 {save_failed} 个")
        
        # 显示分析详情
        for i, result in enumerate(analysis_results):
            if result is not None:
                logger.info(f"\n文档 {i+1}: {result.school_info.full_name}")
                logger.info(f"  置信度: {result.confidence:.2f}")
                logger.info(f"  位置: {result.school_info.location}")
                logger.info(f"  类型: {result.school_info.institution_type}")
                logger.info(f"  分析时间: {result.analysis_time:.2f}秒")
        
        logger.info("\n✅ 完整流程测试成功完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_engine()
        logger.info("测试结束")


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    asyncio.run(test_complete_flow())
