#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的功能测试脚本
测试基本的解析和下载功能
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.services.enhanced_scraper import EnhancedRecruitmentScraper
    from src.utils.logger import get_logger
    from src.config import get_settings
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请检查项目依赖是否正确安装")
    sys.exit(1)

logger = get_logger(__name__)


async def test_basic_parsing():
    """测试基本的学校信息解析功能"""
    print("\n=== 测试1: 基本解析功能 ===")
    
    try:
        scraper = EnhancedRecruitmentScraper()
        async with scraper:
            # 测试解析学校信息
            schools = await scraper.parse_school_list()
            
            print(f"✅ 成功解析 {len(schools)} 所学校")
            
            # 显示前3个学校的信息
            for i, school in enumerate(schools[:3]):
                print(f"  学校 {i+1}: {school.get('name', 'N/A')}")
                print(f"    普通招生简章: {school.get('normal_url', 'N/A')[:80]}...")
                print(f"    特长生招生简章: {school.get('special_url', 'N/A')[:80]}...")
            
            return schools
            
    except Exception as e:
        print(f"❌ 解析功能测试失败: {e}")
        return []


async def test_single_download(school_info: Dict[str, Any]):
    """测试单个学校的下载功能"""
    print(f"\n=== 测试单个下载: {school_info.get('name', 'Unknown')} ===")
    
    try:
        scraper = EnhancedRecruitmentScraper()
        async with scraper:
            # 测试下载
            result = await scraper.scrape_single_school(school_info)
            
            if result.success:
                content_length = len(result.content) if result.content else 0
                print(f"✅ 下载成功")
                print(f"  内容长度: {content_length} 字符")
                print(f"  文件路径: {result.file_path}")
                
                # 显示内容预览
                if result.content:
                    preview = result.content[:200].replace('\n', ' ').strip()
                    print(f"  内容预览: {preview}...")
            else:
                print(f"❌ 下载失败: {result.error_message}")
            
            return result
            
    except Exception as e:
        print(f"❌ 下载测试失败: {e}")
        return None


async def test_multiple_downloads(schools: List[Dict[str, Any]], count: int = 3):
    """测试多个学校的下载功能"""
    print(f"\n=== 测试多个下载 (前{count}个学校) ===")
    
    if not schools:
        print("❌ 没有学校信息可供测试")
        return []
    
    test_schools = schools[:count]
    results = []
    
    try:
        scraper = EnhancedRecruitmentScraper()
        async with scraper:
            for i, school in enumerate(test_schools):
                print(f"\n下载进度: {i+1}/{len(test_schools)} - {school.get('name', 'Unknown')}")
                
                result = await scraper.scrape_single_school(school)
                results.append(result)
                
                if result.success:
                    content_length = len(result.content) if result.content else 0
                    print(f"  ✅ 成功 - 内容长度: {content_length}")
                else:
                    print(f"  ❌ 失败 - {result.error_message}")
                
                # 添加延迟避免请求过快
                await asyncio.sleep(1)
        
        # 统计结果
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        print(f"\n下载结果统计:")
        print(f"  总计: {len(results)}")
        print(f"  成功: {successful}")
        print(f"  失败: {failed}")
        
        return results
        
    except Exception as e:
        print(f"❌ 多个下载测试失败: {e}")
        return []


async def test_concurrent_downloads(schools: List[Dict[str, Any]], count: int = 3):
    """测试并发下载功能"""
    print(f"\n=== 测试并发下载 (前{count}个学校) ===")
    
    if not schools:
        print("❌ 没有学校信息可供测试")
        return []
    
    test_schools = schools[:count]
    
    try:
        scraper = EnhancedRecruitmentScraper()
        async with scraper:
            start_time = time.time()
            
            # 并发下载
            results = await scraper.scrape_schools_concurrent(test_schools, max_concurrent=2)
            
            end_time = time.time()
            
            # 统计结果
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            print(f"\n并发下载结果:")
            print(f"  总计: {len(results)}")
            print(f"  成功: {successful}")
            print(f"  失败: {failed}")
            print(f"  耗时: {end_time - start_time:.2f}秒")
            
            # 显示详细结果
            for result in results:
                status = "✅" if result.success else "❌"
                content_length = len(result.content) if result.content else 0
                print(f"  {status} {result.school_name}: {content_length} 字符")
            
            return results
            
    except Exception as e:
        print(f"❌ 并发下载测试失败: {e}")
        return []


async def main():
    """主测试函数"""
    print("开始简化功能测试...")
    print("="*50)
    
    try:
        # 测试配置加载
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"  目标URL: {settings.scraper.base_url}")
        print(f"  最大并发数: {settings.scraper.max_concurrent_requests}")
        
        # 1. 测试基本解析
        schools = await test_basic_parsing()
        
        if not schools:
            print("\n❌ 无法获取学校信息，停止后续测试")
            return
        
        # 2. 测试单个下载
        if schools:
            await test_single_download(schools[0])
        
        # 3. 测试多个下载（串行）
        await test_multiple_downloads(schools, 3)
        
        # 4. 测试并发下载
        await test_concurrent_downloads(schools, 3)
        
        print("\n" + "="*50)
        print("✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 使用更简单的事件循环管理
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试执行异常: {e}")
