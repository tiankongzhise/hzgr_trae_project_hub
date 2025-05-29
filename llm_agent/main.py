#!/usr/bin/env python3
"""招生简章解析项目主程序"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from src.config import get_settings
from src.models.database import create_tables, close_engine
from src.models.schemas import SchoolCreate, LLMAnalysisRequest, ScrapingResult
from src.services import RecruitmentScraper, DatabaseService
from src.services.enhanced_llm_service import EnhancedLLMService
from src.utils.logger import get_logger
from src.utils.decorators import monitor_performance

logger = get_logger(__name__)


class RecruitmentProcessor:
    """招生简章处理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.scraper = RecruitmentScraper()
        self.llm_service = EnhancedLLMService()
        self.db_service = DatabaseService()
        self.recruitment_dir = Path("招生简章").resolve()
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.scraper.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.scraper.__aexit__(exc_type, exc_val, exc_tb)
        # EnhancedLLMService没有close方法，无需调用
    
    @monitor_performance()
    async def scrape_recruitment_documents(self) -> List[Dict[str, Any]]:
        """爬取招生简章文档"""
        logger.info("开始爬取招生简章")
        
        try:
            # 爬取所有学校的招生简章
            results = await self.scraper.scrape_all_schools()
            
            logger.info(f"爬取完成，共获取 {len(results)} 个学校的招生简章")
            
            # 统计爬取结果
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            logger.info(f"爬取统计: 成功 {successful} 个，失败 {failed} 个")
            
            # 转换为字典格式以保持兼容性
            result_dicts = []
            for r in results:
                result_dict = {
                    'school_name': r.school_name,
                    'recruitment_url': r.recruitment_url,
                    'special_talent_url': r.special_talent_url,
                    'content': r.content,
                    'file_path': r.file_path,
                    'success': r.success,
                    'error_message': r.error_message,
                }
                result_dicts.append(result_dict)
            
            return result_dicts
            
        except Exception as e:
            logger.error(f"爬取招生简章失败: {e}")
            raise
    
    @monitor_performance()
    async def read_local_documents(self) -> List[Dict[str, Any]]:
        """读取本地招生简章文档"""
        logger.info("开始读取本地招生简章文档")
        
        documents = []
        
        if not self.recruitment_dir.exists():
            logger.warning(f"招生简章目录不存在: {self.recruitment_dir}")
            return documents
        
        try:
            # 遍历招生简章目录中的所有文件
            for doc_file in self.recruitment_dir.iterdir():
                if not doc_file.is_file():
                    continue
                
                # 支持多种文件格式
                if doc_file.suffix.lower() not in ['.txt', '.pdf', '.doc', '.docx']:
                    continue
                
                # 从文件名提取学校名称
                filename = doc_file.stem
                if '_' in filename:
                    school_name = filename.split('_')[0]
                else:
                    school_name = filename
                
                logger.debug(f"处理文档: {doc_file.name} (学校: {school_name})")
                
                try:
                    # 根据文件类型读取内容
                    if doc_file.suffix.lower() == '.txt':
                        content = doc_file.read_text(encoding='utf-8')
                    elif doc_file.suffix.lower() == '.pdf':
                        # PDF文件暂时跳过，需要专门的PDF解析
                        logger.info(f"跳过PDF文件: {doc_file.name}")
                        continue
                    elif doc_file.suffix.lower() in ['.doc', '.docx']:
                        # Word文件暂时跳过，需要专门的Word解析
                        logger.info(f"跳过Word文件: {doc_file.name}")
                        continue
                    else:
                        continue
                    
                    if content.strip():
                        documents.append({
                            'school_name': school_name,
                            'file_path': str(doc_file),
                            'content': content,
                            'document_type': self._determine_document_type(doc_file.name),
                            'file_size': doc_file.stat().st_size,
                        })
                        
                        logger.debug(f"读取文档: {doc_file.name} ({len(content)} 字符)")
                    else:
                        logger.warning(f"文档内容为空: {doc_file}")
                        
                except Exception as e:
                    logger.error(f"读取文档失败 {doc_file}: {e}")
            
            logger.info(f"读取完成，共找到 {len(documents)} 个有效文档")
            return documents
            
        except Exception as e:
            logger.error(f"读取本地文档失败: {e}")
            raise
    
    def _determine_document_type(self, filename: str) -> str:
        """根据文件名判断文档类型"""
        filename_lower = filename.lower()
        
        if '特长生' in filename_lower or 'specialty' in filename_lower:
            return 'specialty_recruitment'
        elif '招生简章' in filename_lower or 'recruitment' in filename_lower:
            return 'general_recruitment'
        else:
            return 'unknown'
    
    @monitor_performance()
    async def analyze_documents_with_llm(self, documents: List[Dict[str, Any]], 
                                       progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> List[Dict[str, Any]]:
        """使用大模型分析招生简章文档"""
        logger.info(f"开始使用大模型分析 {len(documents)} 个文档")
        
        # 创建爬取结果格式的数据
        scraping_results = []
        for doc in documents:
            result = ScrapingResult(
                school_name=doc['school_name'],
                recruitment_url=doc.get('file_path', ''),
                content=doc['content'],
                success=True,
                error_message=None,
                file_size=doc.get('file_size', 0)
            )
            scraping_results.append(result)
        
        try:
            # 并发分析
            analysis_results = await self.llm_service.analyze_multiple_concurrent(
                scraping_results,
                max_concurrent=3
            )
            
            logger.info(f"大模型分析完成，共处理 {len(analysis_results)} 个文档")
            
            # 统计分析结果
            successful = sum(1 for r in analysis_results if r is not None and r.confidence > 0)
            failed = len(analysis_results) - successful
            
            logger.info(f"分析统计: 成功 {successful} 个，失败 {failed} 个")
            
            # 转换为字典格式以保持兼容性
            results = []
            for result in analysis_results:
                if result is None:
                    result_dict = {
                        'success': False,
                        'error': '分析失败',
                        'confidence': 0.0,
                        'analysis_time': 0.0
                    }
                else:
                    result_dict = {
                        'success': result.confidence > 0,
                        'school_info': result.school_info.dict(),
                        'confidence': result.confidence,
                        'analysis_time': result.analysis_time,
                        'original_content': result.school_info.raw_content,
                        'source_url': result.school_info.source_url,
                    }
                    if result.confidence == 0:
                        result_dict['error'] = '分析失败'
                results.append(result_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"大模型分析失败: {e}")
            raise
    
    @monitor_performance()
    async def save_to_database(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """保存分析结果到数据库"""
        logger.info(f"开始保存 {len(analysis_results)} 个分析结果到数据库")
        
        school_data_list = []
        
        for result in analysis_results:
            if not result.get('success', False):
                logger.warning(f"跳过失败的分析结果: {result.get('error', 'Unknown error')}")
                continue
            
            try:
                # 构建学校数据
                school_info = result.get('school_info', {})
                
                school_data = SchoolCreate(
                    full_name=school_info.get('full_name', ''),
                    location=school_info.get('location', ''),
                    supervising_department=school_info.get('supervising_department', ''),
                    education_level=school_info.get('education_level', ''),
                    institution_code=school_info.get('institution_code', ''),
                    institution_type=school_info.get('institution_type', ''),
                    is_demonstration=school_info.get('is_demonstration', False),
                    is_backbone=school_info.get('is_backbone', False),
                    is_excellent=school_info.get('is_excellent', False),
                    is_chuyi_high_level=school_info.get('is_chuyi_high_level', False),
                    advantageous_majors=school_info.get('advantageous_majors', []),
                    major_selection_criteria=school_info.get('major_selection_criteria', ''),
                    original_content=result.get('original_content', ''),
                    source_url=result.get('source_url', ''),
                )
                
                school_data_list.append(school_data)
                
            except Exception as e:
                logger.error(f"构建学校数据失败: {e}")
                continue
        
        try:
            # 批量保存到数据库
            save_results = await self.db_service.batch_create_schools(school_data_list)
            
            # 统计保存结果
            successful = sum(1 for r in save_results if r.success)
            failed = len(save_results) - successful
            
            logger.info(f"数据库保存完成: 成功 {successful} 个，失败 {failed} 个")
            
            return {
                'total': len(save_results),
                'successful': successful,
                'failed': failed,
            }
            
        except Exception as e:
            logger.error(f"数据库保存失败: {e}")
            raise
    
    @monitor_performance()
    async def process_from_url(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        """处理招生简章（完整流程）"""
        logger.info("开始完整处理流程")
        
        start_time = datetime.now()
        
        try:
            # 1. 爬取招生简章
            scrape_results = await self.scrape_recruitment_documents()
            
            if not scrape_results:
                logger.warning("没有爬取到任何招生简章")
                return {
                    'success': False,
                    'error': '没有爬取到任何招生简章',
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                }
            
            # 转换爬取结果为文档格式
            documents = []
            for result in scrape_results:
                if result['success'] and result['content']:
                    documents.append({
                        'school_name': result['school_name'],
                        'file_path': result.get('file_path', result['recruitment_url']),
                        'content': result['content'],
                        'document_type': 'recruitment',
                        'file_size': len(result['content']),
                    })
            
            if not documents:
                logger.warning("没有找到可分析的文档")
                return {
                    'success': False,
                    'error': '没有找到可分析的文档',
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                }
            
            # 3. 大模型分析（传递进度回调）
            analysis_results = await self.analyze_documents_with_llm(documents, progress_callback)
            
            # 4. 保存到数据库
            save_stats = await self.save_to_database(analysis_results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'execution_time': execution_time,
                'scrape_results': len(scrape_results),
                'documents_found': len(documents),
                'analysis_results': len(analysis_results),
                'database_stats': save_stats,
            }
            
            logger.info(f"完整处理流程完成: {result}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"完整处理流程失败: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
            }
    
    @monitor_performance()
    async def process_local_documents(self) -> Dict[str, Any]:
        """处理本地文档（仅分析和保存）"""
        logger.info("开始处理本地文档")
        
        start_time = datetime.now()
        
        try:
            # 1. 读取本地文档
            documents = await self.read_local_documents()
            
            if not documents:
                logger.warning("没有找到可分析的文档")
                return {
                    'success': False,
                    'error': '没有找到可分析的文档',
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                }
            
            # 2. 大模型分析
            analysis_results = await self.analyze_documents_with_llm(documents)
            
            # 3. 保存到数据库
            save_stats = await self.save_to_database(analysis_results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'success': True,
                'execution_time': execution_time,
                'documents_found': len(documents),
                'analysis_results': len(analysis_results),
                'database_stats': save_stats,
            }
            
            logger.info(f"本地文档处理完成: {result}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"本地文档处理失败: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
            }


async def main():
    """主函数"""
    logger.info("招生简章解析项目启动")
    
    try:
        # 初始化数据库
        logger.info("初始化数据库...")
        await create_tables()
        
        # 创建处理器
        async with RecruitmentProcessor() as processor:
            
            # 检查命令行参数
            if len(sys.argv) > 1:
                if sys.argv[1] == "--local-only":
                    # 仅处理本地文档
                    logger.info("仅处理本地文档模式")
                    result = await processor.process_local_documents()
                else:
                    # 从指定URL处理
                    url = sys.argv[1]
                    logger.info(f"从URL处理: {url}")
                    result = await processor.process_from_url(url)
            else:
                # 默认URL
                default_url = "https://cs.bendibao.com/job/202525/124791.shtm"
                logger.info(f"使用默认URL: {default_url}")
                result = await processor.process_from_url(default_url)
            
            # 输出结果
            if result['success']:
                logger.info("处理完成！")
                logger.info(f"执行时间: {result['execution_time']:.2f} 秒")
                
                if 'database_stats' in result:
                    stats = result['database_stats']
                    logger.info(f"数据库保存: 成功 {stats['successful']} 个，失败 {stats['failed']} 个")
                
                # 获取数据库统计信息
                db_service = DatabaseService()
                db_stats = await db_service.get_statistics()
                
                if db_stats:
                    logger.info(f"数据库统计: 总计 {db_stats['total_schools']} 个学校")
                    logger.info(f"公办学校: {db_stats['by_type']['public']} 个")
                    logger.info(f"民办学校: {db_stats['by_type']['private']} 个")
                    logger.info(f"示范性院校: {db_stats['special_types']['demonstration']} 个")
                    logger.info(f"骨干院校: {db_stats['special_types']['backbone']} 个")
                    logger.info(f"卓越院校: {db_stats['special_types']['excellent']} 个")
                    logger.info(f"楚怡高水平院校: {db_stats['special_types']['chuyi_high_level']} 个")
            else:
                logger.error(f"处理失败: {result.get('error', 'Unknown error')}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await close_engine()
        logger.info("程序结束")


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())
