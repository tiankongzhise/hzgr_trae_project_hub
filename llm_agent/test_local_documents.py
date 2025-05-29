#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地文档处理流程
从招生简章文件夹中选择特长生和普通招生简章各3个文件进行测试
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.models.database import create_tables, close_engine
from src.models.schemas import LLMAnalysisRequest, SchoolCreate, ScrapingResult
from src.services.enhanced_llm_service import EnhancedLLMService
from src.services.database_service import DatabaseService
from src.utils.logger import get_logger
from src.utils.document_processor import get_document_processor

logger = get_logger(__name__)


class LocalDocumentTester:
    """本地文档测试器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_service = EnhancedLLMService()
        self.db_service = DatabaseService()
        self.recruitment_dir = Path("招生简章")
        
    async def select_test_files(self) -> Dict[str, List[Path]]:
        """选择测试文件 - 特长生和普通招生简章各3个，包含不同格式"""
        logger.info("选择测试文件...")
        
        if not self.recruitment_dir.exists():
            logger.error(f"招生简章目录不存在: {self.recruitment_dir}")
            return {'normal': [], 'special': []}
        
        normal_files = []
        special_files = []
        
        # 遍历文件，按类型和格式分类
        for file_path in self.recruitment_dir.iterdir():
            if file_path.is_file():
                filename = file_path.name.lower()
                
                # 特长生招生简章
                if '特长生' in filename:
                    special_files.append(file_path)
                # 普通招生简章
                elif '招生简章' in filename and '特长生' not in filename:
                    normal_files.append(file_path)
        
        # 按文件格式优先选择，确保包含不同格式
        def prioritize_by_format(files: List[Path]) -> List[Path]:
            pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
            docx_files = [f for f in files if f.suffix.lower() == '.docx']
            doc_files = [f for f in files if f.suffix.lower() == '.doc']
            txt_files = [f for f in files if f.suffix.lower() == '.txt']
            
            # 优先选择不同格式的文件
            selected = []
            if pdf_files and len(selected) < 3:
                selected.extend(pdf_files[:1])
            if docx_files and len(selected) < 3:
                selected.extend(docx_files[:1])
            if doc_files and len(selected) < 3:
                selected.extend(doc_files[:1])
            if txt_files and len(selected) < 3:
                selected.extend(txt_files[:3-len(selected)])
            
            return selected[:3]
        
        selected_normal = prioritize_by_format(normal_files)
        selected_special = prioritize_by_format(special_files)
        
        logger.info(f"选择的普通招生简章文件 ({len(selected_normal)})：")
        for f in selected_normal:
            logger.info(f"  - {f.name} ({f.suffix})")
        
        logger.info(f"选择的特长生招生简章文件 ({len(selected_special)})：")
        for f in selected_special:
            logger.info(f"  - {f.name} ({f.suffix})")
        
        return {
            'normal': selected_normal,
            'special': selected_special
        }
    
    async def read_document_content(self, file_path: Path) -> Dict[str, Any]:
        """读取文档内容"""
        logger.info(f"读取文档: {file_path.name}")
        
        try:
            # 获取文档处理器
            processor = get_document_processor()
            
            # 根据文件类型读取内容
            if file_path.suffix.lower() == '.txt':
                content = file_path.read_text(encoding='utf-8')
            elif file_path.suffix.lower() in ['.pdf', '.doc', '.docx']:
                content = await processor.extract_text_from_file(str(file_path))
            else:
                logger.warning(f"不支持的文件格式: {file_path.suffix}")
                return None
            
            if not content or not content.strip():
                logger.warning(f"文档内容为空: {file_path.name}")
                return None
            
            # 提取学校名称
            school_name = self._extract_school_name(file_path.name)
            
            # 判断文档类型
            doc_type = 'special_recruitment' if '特长生' in file_path.name else 'general_recruitment'
            
            return {
                'school_name': school_name,
                'file_path': str(file_path),
                'content': content,
                'document_type': doc_type,
                'file_size': file_path.stat().st_size,
                'file_format': file_path.suffix.lower(),
            }
            
        except Exception as e:
            logger.error(f"读取文档失败 {file_path.name}: {e}")
            return None
    
    def _extract_school_name(self, filename: str) -> str:
        """从文件名提取学校名称"""
        # 移除文件扩展名和常见后缀
        name = filename
        for ext in ['.txt', '.pdf', '.doc', '.docx']:
            if name.lower().endswith(ext):
                name = name[:-len(ext)]
                break
        
        # 移除常见后缀
        suffixes = ['_招生简章', '_特长生招生简章', '招生简章', '特长生招生简章']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        return name.strip()
    
    async def analyze_with_llm(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用LLM分析文档"""
        logger.info(f"开始LLM分析 {len(documents)} 个文档")
        
        # 创建爬取结果格式的数据
        scraping_results = []
        for doc in documents:
            result = ScrapingResult(
                school_name=doc['school_name'],
                recruitment_url=doc['file_path'],
                content=doc['content'],
                success=True,
                error_message=None,
                file_size=doc['file_size']
            )
            scraping_results.append(result)
        
        try:
            # 并发分析
            analysis_results = await self.llm_service.analyze_multiple_concurrent(
                scraping_results, 
                max_concurrent=3
            )
            
            logger.info(f"LLM分析完成，共处理 {len(analysis_results)} 个文档")
            
            # 转换结果格式
            results = []
            for i, result in enumerate(analysis_results):
                original_doc = documents[i]
                result_dict = {
                    'success': result.confidence > 0,
                    'school_info': result.school_info.dict(),
                    'confidence': result.confidence,
                    'analysis_time': result.analysis_time,
                    'original_content': result.school_info.raw_content,
                    'source_url': result.school_info.source_url,
                    'file_path': original_doc['file_path'],
                    'file_format': original_doc['file_format'],
                    'document_type': original_doc['document_type'],
                }
                if result.confidence == 0:
                    result_dict['error'] = '分析失败'
                results.append(result_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            raise
    
    def _progress_callback(self, progress_info: Dict[str, Any]):
        """进度回调函数"""
        current = progress_info.get('current', 0)
        total = progress_info.get('total', 0)
        school_name = progress_info.get('school_name', 'Unknown')
        
        logger.info(f"分析进度: {current}/{total} - {school_name}")
    
    async def save_to_database(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """保存分析结果到数据库"""
        logger.info(f"开始保存 {len(analysis_results)} 个分析结果到数据库")
        
        school_data_list = []
        
        for result in analysis_results:
            if not result.get('success', False):
                logger.warning(f"跳过失败的分析结果: {result.get('error', 'Unknown error')}")
                continue
            
            try:
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
    
    async def run_test(self) -> Dict[str, Any]:
        """运行完整测试流程"""
        logger.info("开始本地文档测试流程")
        
        try:
            # 1. 选择测试文件
            selected_files = await self.select_test_files()
            all_files = selected_files['normal'] + selected_files['special']
            
            if not all_files:
                logger.error("没有找到可测试的文件")
                return {'success': False, 'error': '没有找到可测试的文件'}
            
            # 2. 读取文档内容
            logger.info("读取文档内容...")
            documents = []
            for file_path in all_files:
                doc_data = await self.read_document_content(file_path)
                if doc_data:
                    documents.append(doc_data)
            
            if not documents:
                logger.error("没有成功读取任何文档")
                return {'success': False, 'error': '没有成功读取任何文档'}
            
            logger.info(f"成功读取 {len(documents)} 个文档")
            
            # 3. LLM分析
            logger.info("开始LLM分析...")
            analysis_results = await self.analyze_with_llm(documents)
            
            # 4. 保存到数据库
            logger.info("保存到数据库...")
            save_stats = await self.save_to_database(analysis_results)
            
            # 5. 输出测试结果
            logger.info("\n=== 测试结果汇总 ===")
            logger.info(f"选择文件数: {len(all_files)}")
            logger.info(f"成功读取文档数: {len(documents)}")
            logger.info(f"LLM分析结果数: {len(analysis_results)}")
            logger.info(f"数据库保存统计: {save_stats}")
            
            # 详细结果
            logger.info("\n=== 详细分析结果 ===")
            for i, result in enumerate(analysis_results):
                doc = documents[i]
                status = "✅" if result['success'] else "❌"
                logger.info(f"{status} {doc['school_name']} ({doc['file_format']}) - 置信度: {result.get('confidence', 0):.2f}")
                
                if result['success']:
                    school_info = result['school_info']
                    logger.info(f"   学校全称: {school_info.get('full_name', 'N/A')}")
                    logger.info(f"   办学地点: {school_info.get('location', 'N/A')}")
                    logger.info(f"   院校类型: {school_info.get('institution_type', 'N/A')}")
                else:
                    logger.info(f"   错误: {result.get('error', 'Unknown error')}")
            
            return {
                'success': True,
                'files_selected': len(all_files),
                'documents_read': len(documents),
                'analysis_results': len(analysis_results),
                'database_stats': save_stats,
                'results': analysis_results
            }
            
        except Exception as e:
            logger.error(f"测试流程失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        """关闭服务"""
        await self.llm_service.close()
        await self.db_service.close()


async def main():
    """主函数"""
    logger.info("开始本地文档测试")
    
    try:
        # 初始化数据库
        logger.info("初始化数据库...")
        await create_tables()
        
        # 创建测试器
        tester = LocalDocumentTester()
        
        try:
            # 运行测试
            result = await tester.run_test()
            
            if result['success']:
                logger.info("\n🎉 测试成功完成！")
                logger.info(f"处理了 {result['files_selected']} 个文件")
                logger.info(f"成功分析 {result['analysis_results']} 个文档")
                
                db_stats = result['database_stats']
                logger.info(f"数据库保存: 成功 {db_stats['successful']} 个，失败 {db_stats['failed']} 个")
            else:
                logger.error(f"❌ 测试失败: {result.get('error', 'Unknown error')}")
                sys.exit(1)
                
        finally:
            await tester.close()
    
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await close_engine()
        logger.info("测试结束")


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    asyncio.run(main())
