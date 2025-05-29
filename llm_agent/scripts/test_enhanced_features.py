#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版招生简章下载和LLM分析功能

功能包括：
1. 测试数据库存储和查询
2. 测试并发下载功能
3. 测试并发LLM分析功能
4. 性能对比测试
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.enhanced_scraper import EnhancedRecruitmentScraper
from src.services.enhanced_llm_service import EnhancedLLMService
from src.services.database_service import DatabaseService
from src.models.database import create_tables
from src.utils.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)


class EnhancedFeatureTester:
    """增强功能测试器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.scraper = None
        self.llm_service = None
        self.db_service = None
    
    async def setup(self):
        """初始化测试环境"""
        logger.info("初始化测试环境...")
        
        # 创建数据库表
        await create_tables()
        
        # 初始化服务
        self.scraper = EnhancedRecruitmentScraper()
        self.llm_service = EnhancedLLMService()
        self.db_service = DatabaseService()
        await self.db_service.initialize()
        
        logger.info("测试环境初始化完成")
    
    async def cleanup(self):
        """清理测试环境"""
        if self.db_service:
            await self.db_service.close()
        logger.info("测试环境清理完成")
    
    async def test_database_operations(self) -> Dict[str, Any]:
        """测试数据库操作"""
        logger.info("开始测试数据库操作...")
        
        try:
            start_time = time.time()
            
            # 测试学校信息解析和存储
            async with self.scraper:
                schools = await self.scraper.get_or_parse_schools()
            
            operation_time = time.time() - start_time
            
            # 验证数据库中的数据
            db_schools = await self.db_service.get_all_schools()
            
            result = {
                "success": True,
                "parsed_schools": len(schools),
                "db_schools": len(db_schools),
                "operation_time": operation_time,
                "sample_schools": schools[:3] if schools else []
            }
            
            logger.info(f"数据库操作测试完成: 解析 {len(schools)} 所学校，数据库中 {len(db_schools)} 所学校")
            return result
            
        except Exception as e:
            logger.error(f"数据库操作测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_concurrent_download(self, sample_count: int = 5) -> Dict[str, Any]:
        """测试并发下载功能"""
        logger.info(f"开始测试并发下载功能，样本数量: {sample_count}...")
        
        try:
            async with self.scraper:
                # 测试样本下载
                result = await self.scraper.test_download_sample(sample_count)
                
                if result["success"]:
                    logger.info(f"并发下载测试完成: 总计 {result['total']} 个，成功 {result['successful']} 个，失败 {result['failed']} 个")
                    
                    # 分析下载结果
                    download_details = []
                    for scraping_result in result["results"]:
                        download_details.append({
                            "school_name": scraping_result.school_name,
                            "success": scraping_result.success,
                            "has_content": bool(scraping_result.content),
                            "content_length": len(scraping_result.content) if scraping_result.content else 0,
                            "error": scraping_result.error_message
                        })
                    
                    result["download_details"] = download_details
                
                return result
                
        except Exception as e:
            logger.error(f"并发下载测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_concurrent_llm_analysis(self, scraping_results: List) -> Dict[str, Any]:
        """测试并发LLM分析功能"""
        logger.info("开始测试并发LLM分析功能...")
        
        try:
            # 过滤成功的下载结果
            valid_results = [r for r in scraping_results if r.success and r.content]
            
            if not valid_results:
                return {"success": False, "error": "没有有效的下载结果可供分析"}
            
            # 限制分析数量
            test_results = valid_results[:5]
            
            # 并发分析
            analysis_result = await self.llm_service.test_concurrent_analysis(test_results)
            
            if analysis_result["success"]:
                logger.info(f"并发LLM分析测试完成: 总计 {analysis_result['total']} 个，成功 {analysis_result['successful']} 个")
                logger.info(f"平均置信度: {analysis_result['avg_confidence']:.2f}，总耗时: {analysis_result['total_time']:.2f}秒")
                
                # 分析结果详情
                analysis_details = []
                for analysis_resp in analysis_result["results"]:
                    if analysis_resp:
                        analysis_details.append({
                            "school_name": analysis_resp.school_info.full_name,
                            "confidence": analysis_resp.confidence,
                            "analysis_time": analysis_resp.analysis_time,
                            "location": analysis_resp.school_info.location,
                            "institution_type": analysis_resp.school_info.institution_type,
                            "is_demonstration": analysis_resp.school_info.is_demonstration
                        })
                
                analysis_result["analysis_details"] = analysis_details
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"并发LLM分析测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_performance_comparison(self) -> Dict[str, Any]:
        """测试性能对比"""
        logger.info("开始性能对比测试...")
        
        try:
            results = {}
            
            # 测试串行下载（模拟）
            start_time = time.time()
            async with self.scraper:
                schools = await self.scraper.get_or_parse_schools()
                sample_schools = schools[:3]  # 小样本测试
                
                # 串行下载
                serial_results = []
                for school in sample_schools:
                    result = await self.scraper.scrape_single_school(school)
                    serial_results.append(result)
            
            serial_time = time.time() - start_time
            
            # 测试并发下载
            start_time = time.time()
            async with self.scraper:
                concurrent_results = await self.scraper.scrape_schools_concurrent(sample_schools, max_concurrent=3)
            
            concurrent_time = time.time() - start_time
            
            # 计算性能提升
            speedup = serial_time / concurrent_time if concurrent_time > 0 else 0
            
            results = {
                "success": True,
                "serial_time": serial_time,
                "concurrent_time": concurrent_time,
                "speedup": speedup,
                "sample_count": len(sample_schools),
                "serial_success": sum(1 for r in serial_results if r.success),
                "concurrent_success": sum(1 for r in concurrent_results if r.success)
            }
            
            logger.info(f"性能对比测试完成: 串行耗时 {serial_time:.2f}秒，并发耗时 {concurrent_time:.2f}秒，提升 {speedup:.2f}倍")
            return results
            
        except Exception as e:
            logger.error(f"性能对比测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合测试"""
        logger.info("开始运行综合测试...")
        
        test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # 1. 测试数据库操作
            logger.info("\n=== 测试1: 数据库操作 ===")
            test_results["tests"]["database"] = await self.test_database_operations()
            
            # 2. 测试并发下载
            logger.info("\n=== 测试2: 并发下载 ===")
            download_result = await self.test_concurrent_download(5)
            test_results["tests"]["download"] = download_result
            
            # 3. 测试并发LLM分析
            if download_result["success"] and download_result.get("results"):
                logger.info("\n=== 测试3: 并发LLM分析 ===")
                test_results["tests"]["llm_analysis"] = await self.test_concurrent_llm_analysis(
                    download_result["results"]
                )
            else:
                logger.warning("跳过LLM分析测试，因为没有有效的下载结果")
                test_results["tests"]["llm_analysis"] = {"success": False, "error": "没有有效的下载结果"}
            
            # 4. 测试性能对比
            logger.info("\n=== 测试4: 性能对比 ===")
            test_results["tests"]["performance"] = await self.test_performance_comparison()
            
            test_results["end_time"] = datetime.now().isoformat()
            test_results["overall_success"] = all(
                result.get("success", False) for result in test_results["tests"].values()
            )
            
            return test_results
            
        except Exception as e:
            logger.error(f"综合测试失败: {e}")
            test_results["error"] = str(e)
            test_results["overall_success"] = False
            return test_results


def print_test_summary(results: Dict[str, Any]):
    """打印测试摘要"""
    print("\n" + "="*60)
    print("增强功能测试摘要")
    print("="*60)
    
    print(f"测试开始时间: {results.get('start_time', 'N/A')}")
    print(f"测试结束时间: {results.get('end_time', 'N/A')}")
    print(f"总体结果: {'✅ 成功' if results.get('overall_success') else '❌ 失败'}")
    
    if "tests" in results:
        for test_name, test_result in results["tests"].items():
            status = "✅ 成功" if test_result.get("success") else "❌ 失败"
            print(f"\n{test_name.upper()} 测试: {status}")
            
            if test_name == "database" and test_result.get("success"):
                print(f"  - 解析学校数: {test_result.get('parsed_schools', 0)}")
                print(f"  - 数据库学校数: {test_result.get('db_schools', 0)}")
                print(f"  - 操作耗时: {test_result.get('operation_time', 0):.2f}秒")
            
            elif test_name == "download" and test_result.get("success"):
                print(f"  - 总计: {test_result.get('total', 0)}")
                print(f"  - 成功: {test_result.get('successful', 0)}")
                print(f"  - 失败: {test_result.get('failed', 0)}")
                print(f"  - 普通简章测试: {test_result.get('normal_urls_tested', 0)}")
                print(f"  - 特长生简章测试: {test_result.get('special_urls_tested', 0)}")
            
            elif test_name == "llm_analysis" and test_result.get("success"):
                print(f"  - 总计: {test_result.get('total', 0)}")
                print(f"  - 成功: {test_result.get('successful', 0)}")
                print(f"  - 平均置信度: {test_result.get('avg_confidence', 0):.2f}")
                print(f"  - 总耗时: {test_result.get('total_time', 0):.2f}秒")
            
            elif test_name == "performance" and test_result.get("success"):
                print(f"  - 串行耗时: {test_result.get('serial_time', 0):.2f}秒")
                print(f"  - 并发耗时: {test_result.get('concurrent_time', 0):.2f}秒")
                print(f"  - 性能提升: {test_result.get('speedup', 0):.2f}倍")
            
            if not test_result.get("success") and "error" in test_result:
                print(f"  - 错误: {test_result['error']}")
    
    print("\n" + "="*60)


async def main():
    """主函数"""
    tester = EnhancedFeatureTester()
    
    try:
        await tester.setup()
        results = await tester.run_comprehensive_test()
        print_test_summary(results)
        
        # 保存详细结果到文件
        import json
        results_file = Path("test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n详细测试结果已保存到: {results_file}")
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        print(f"❌ 测试执行失败: {e}")
    
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
