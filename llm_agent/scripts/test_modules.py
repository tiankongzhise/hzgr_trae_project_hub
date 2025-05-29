#!/usr/bin/env python3
"""模块功能测试脚本"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.models.database import create_tables, close_engine
from src.models.schemas import SchoolCreate, LLMAnalysisRequest
from src.services import RecruitmentScraper, LLMService, DatabaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModuleTester:
    """模块测试器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.test_results = {}
    
    async def test_config(self):
        """测试配置模块"""
        logger.info("测试配置模块...")
        
        try:
            settings = get_settings()
            
            # 检查关键配置
            assert settings.database.url, "数据库URL未配置"
            assert settings.llm.api_key, "LLM API Key未配置"
            assert settings.llm.base_url, "LLM Base URL未配置"
            assert settings.llm.model_name, "LLM模型名称未配置"
            
            logger.info("✓ 配置模块测试通过")
            self.test_results['config'] = True
            
        except Exception as e:
            logger.error(f"✗ 配置模块测试失败: {e}")
            self.test_results['config'] = False
    
    async def test_database(self):
        """测试数据库模块"""
        logger.info("测试数据库模块...")
        
        try:
            # 初始化数据库
            await create_tables()
            
            # 测试数据库服务
            db_service = DatabaseService()
            
            # 创建测试数据
            test_school = SchoolCreate(
                full_name="测试学校",
                location="测试地点",
                supervising_department="测试部门",
                education_level="专科",
                institution_code="TEST001",
                institution_type="公办",
                is_demonstration=True,
                is_backbone=False,
                is_excellent=False,
                is_chuyi_high_level=False,
                advantageous_majors=["计算机技术", "软件工程"],
                major_selection_criteria="测试标准",
                original_content="测试招生简章内容",
                source_url="https://test.example.com",
            )
            
            # 测试创建
            create_result = await db_service.create_school(test_school)
            assert create_result.success, f"创建学校失败: {create_result.error_message}"
            
            # 测试查询
            school = await db_service.get_school_by_name("测试学校")
            assert school is not None, "查询学校失败"
            assert school.full_name == "测试学校", "学校名称不匹配"
            
            # 测试统计
            stats = await db_service.get_statistics()
            assert isinstance(stats, dict), "统计信息格式错误"
            assert stats.get('total_schools', 0) >= 1, "学校总数统计错误"
            
            # 清理测试数据
            delete_result = await db_service.delete_school(school.id)
            assert delete_result.success, "删除学校失败"
            
            logger.info("✓ 数据库模块测试通过")
            self.test_results['database'] = True
            
        except Exception as e:
            logger.error(f"✗ 数据库模块测试失败: {e}")
            self.test_results['database'] = False
    
    async def test_llm_service(self):
        """测试LLM服务模块"""
        logger.info("测试LLM服务模块...")
        
        try:
            llm_service = LLMService()
            
            # 测试分析请求
            test_content = """
            湖南工业职业技术学院2024年招生简章
            
            学校全称：湖南工业职业技术学院
            办学地点：湖南省长沙市岳麓区含浦科教园
            主管部门：湖南省教育厅
            办学层次：专科
            院校代号：4343
            办学类型：公办
            
            学校是国家示范性高等职业院校、国家优质专科高等职业院校。
            
            优势专业：
            1. 机械制造与自动化 - 国家重点专业
            2. 数控技术 - 省级特色专业
            3. 电气自动化技术 - 行业领先专业
            """
            
            analysis_request = LLMAnalysisRequest(
                content=test_content,
                school_name="湖南工业职业技术学院",
                source_url="https://test.example.com"
            )
            
            # 测试单个分析
            result = await llm_service.analyze_recruitment_content(analysis_request)
            
            assert result.success, f"LLM分析失败: {result.error_message}"
            assert result.school_info is not None, "学校信息解析失败"
            assert result.school_info.full_name, "学校名称解析失败"
            assert result.confidence > 0, "置信度计算失败"
            
            logger.info(f"✓ LLM服务模块测试通过 (置信度: {result.confidence:.2f})")
            self.test_results['llm_service'] = True
            
            await llm_service.close()
            
        except Exception as e:
            logger.error(f"✗ LLM服务模块测试失败: {e}")
            self.test_results['llm_service'] = False
    
    async def test_scraper(self):
        """测试爬虫模块"""
        logger.info("测试爬虫模块...")
        
        try:
            async with RecruitmentScraper() as scraper:
                
                # 测试获取网页内容
                test_url = "https://httpbin.org/html"
                content = await scraper.get_page_content(test_url)
                
                assert content is not None, "获取网页内容失败"
                assert len(content) > 0, "网页内容为空"
                
                logger.info("✓ 爬虫模块基础功能测试通过")
                self.test_results['scraper'] = True
                
        except Exception as e:
            logger.error(f"✗ 爬虫模块测试失败: {e}")
            self.test_results['scraper'] = False
    
    async def test_utils(self):
        """测试工具模块"""
        logger.info("测试工具模块...")
        
        try:
            from src.utils.decorators import monitor_performance, retry_on_failure
            from src.utils.retry import AsyncRetry, RetryConfig
            from src.utils.logger import get_logger, log_performance
            
            # 测试日志功能
            test_logger = get_logger("test")
            test_logger.info("测试日志消息")
            
            # 测试性能监控装饰器
            @monitor_performance()
            async def test_function():
                await asyncio.sleep(0.1)
                return "test_result"
            
            result = await test_function()
            assert result == "test_result", "装饰器功能异常"
            
            # 测试重试机制
            retry_config = RetryConfig(max_attempts=3, base_delay=0.1)
            retry_handler = AsyncRetry(retry_config)
            
            call_count = 0
            
            async def test_retry_function():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("测试异常")
                return "success"
            
            result = await retry_handler.execute(test_retry_function)
            assert result == "success", "重试机制异常"
            assert call_count == 2, "重试次数不正确"
            
            logger.info("✓ 工具模块测试通过")
            self.test_results['utils'] = True
            
        except Exception as e:
            logger.error(f"✗ 工具模块测试失败: {e}")
            self.test_results['utils'] = False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始模块功能测试...")
        start_time = datetime.now()
        
        # 运行各个测试
        await self.test_config()
        await self.test_utils()
        await self.test_database()
        await self.test_llm_service()
        await self.test_scraper()
        
        # 输出测试结果
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "="*50)
        logger.info("测试结果汇总:")
        logger.info("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for module, result in self.test_results.items():
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"{module:15} : {status}")
        
        logger.info("-" * 50)
        logger.info(f"总计: {total_tests} 个测试")
        logger.info(f"通过: {passed_tests} 个")
        logger.info(f"失败: {failed_tests} 个")
        logger.info(f"执行时间: {execution_time:.2f} 秒")
        
        if failed_tests > 0:
            logger.error("部分测试失败，请检查相关模块配置")
            return False
        else:
            logger.info("所有测试通过！")
            return True


async def main():
    """主函数"""
    try:
        # 初始化数据库
        await create_tables()
        
        # 运行测试
        tester = ModuleTester()
        success = await tester.run_all_tests()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)
    finally:
        # 关闭数据库连接
        await close_engine()


if __name__ == "__main__":
    # Windows兼容性
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
