#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试招生简章下载模块
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.scraper import RecruitmentScraper
from src.utils.logger import get_logger
from src.utils.document_processor import get_document_processor
from src.config import get_settings

logger = get_logger(__name__)


async def test_document_processor():
    """测试文档处理器"""
    print("\n=== 测试文档处理器 ===")
    
    try:
        processor = get_document_processor()
        print(f"支持的文件格式: {processor.supported_formats}")
        
        # 测试创建一个示例文档
        settings = get_settings()
        test_dir = settings.data_dir / "test"
        test_dir.mkdir(exist_ok=True)
        
        # 创建测试文本文件
        test_txt = test_dir / "test.txt"
        with open(test_txt, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档\n包含中文内容\n用于测试文档处理器")
        
        # 测试提取文本
        text = await processor.extract_text_from_file(test_txt)
        if text:
            print(f"✓ 文本文件提取成功，长度: {len(text)}")
            print(f"内容预览: {text[:100]}...")
        else:
            print("✗ 文本文件提取失败")
        
        # 清理测试文件
        test_txt.unlink(missing_ok=True)
        test_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"✗ 文档处理器测试失败: {e}")
        return False


async def test_scraper_init():
    """测试爬虫初始化"""
    print("\n=== 测试爬虫初始化 ===")
    
    try:
        async with RecruitmentScraper() as scraper:
            print(f"✓ 爬虫初始化成功")
            print(f"基础URL: {scraper.base_url}")
            print(f"数据目录: {scraper.data_dir}")
            
            # 检查数据目录是否存在
            if scraper.data_dir.exists():
                print(f"✓ 数据目录存在: {scraper.data_dir}")
            else:
                print(f"✗ 数据目录不存在: {scraper.data_dir}")
                return False
            
            return True
            
    except Exception as e:
        print(f"✗ 爬虫初始化失败: {e}")
        return False


async def test_fetch_page():
    """测试网页获取"""
    print("\n=== 测试网页获取 ===")
    
    try:
        async with RecruitmentScraper() as scraper:
            # 测试获取一个简单的网页
            test_url = "https://httpbin.org/html"
            print(f"测试URL: {test_url}")
            
            html_content = await scraper.fetch_page(test_url)
            
            if html_content and len(html_content) > 0:
                print(f"✓ 网页获取成功，内容长度: {len(html_content)}")
                print(f"内容预览: {html_content[:200]}...")
                return True
            else:
                print("✗ 网页获取失败或内容为空")
                return False
                
    except Exception as e:
        print(f"✗ 网页获取测试失败: {e}")
        return False


async def test_parse_school_list():
    """测试学校列表解析"""
    print("\n=== 测试学校列表解析 ===")
    
    try:
        async with RecruitmentScraper() as scraper:
            # 创建一个模拟的HTML内容
            mock_html = """
            <html>
            <body>
                <table>
                    <tr><th>学校名称</th><th>招生简章</th></tr>
                    <tr>
                        <td>测试学校1</td>
                        <td><a href="/doc1.pdf">招生简章</a></td>
                    </tr>
                    <tr>
                        <td>测试学校2</td>
                        <td><a href="/doc2.docx">招生简章</a></td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            schools = await scraper.parse_school_list(mock_html)
            
            if schools and len(schools) > 0:
                print(f"✓ 学校列表解析成功，找到 {len(schools)} 所学校")
                for i, school in enumerate(schools[:3]):  # 只显示前3个
                    print(f"  学校{i+1}: {school}")
                return True
            else:
                print("✗ 学校列表解析失败或未找到学校")
                return False
                
    except Exception as e:
        print(f"✗ 学校列表解析测试失败: {e}")
        return False


async def test_download_document():
    """测试文档下载"""
    print("\n=== 测试文档下载 ===")
    
    try:
        async with RecruitmentScraper() as scraper:
            # 测试下载一个小的文本文件
            test_url = "https://httpbin.org/robots.txt"
            school_name = "测试学校"
            doc_type = "测试文档"
            
            print(f"测试下载URL: {test_url}")
            
            file_path = await scraper.download_recruitment_document(
                test_url, school_name, doc_type
            )
            
            if file_path and Path(file_path).exists():
                print(f"✓ 文档下载成功: {file_path}")
                
                # 测试文本提取
                text = await scraper.extract_text_from_file(Path(file_path))
                if text:
                    print(f"✓ 文本提取成功，长度: {len(text)}")
                    print(f"内容预览: {text[:200]}...")
                else:
                    print("✗ 文本提取失败")
                
                # 清理测试文件
                Path(file_path).unlink(missing_ok=True)
                return True
            else:
                print("✗ 文档下载失败")
                return False
                
    except Exception as e:
        print(f"✗ 文档下载测试失败: {e}")
        return False


async def test_get_saved_files():
    """测试获取已保存文件"""
    print("\n=== 测试获取已保存文件 ===")
    
    try:
        async with RecruitmentScraper() as scraper:
            # 创建一些测试文件
            test_files = [
                scraper.data_dir / "test1.txt",
                scraper.data_dir / "test2.html",
                scraper.data_dir / "test3.pdf",
            ]
            
            # 创建测试文件
            for file_path in test_files:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"测试文件内容: {file_path.name}")
            
            # 获取已保存文件列表
            saved_files = await scraper.get_saved_files()
            
            if saved_files and len(saved_files) >= len(test_files):
                print(f"✓ 获取已保存文件成功，找到 {len(saved_files)} 个文件")
                for file_path in saved_files[:5]:  # 只显示前5个
                    print(f"  文件: {file_path.name}")
            else:
                print(f"✗ 获取已保存文件失败，期望至少 {len(test_files)} 个，实际 {len(saved_files) if saved_files else 0} 个")
            
            # 清理测试文件
            for file_path in test_files:
                file_path.unlink(missing_ok=True)
            
            return True
            
    except Exception as e:
        print(f"✗ 获取已保存文件测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("开始测试招生简章下载模块")
    print("=" * 50)
    
    tests = [
        ("文档处理器", test_document_processor),
        ("爬虫初始化", test_scraper_init),
        ("网页获取", test_fetch_page),
        ("学校列表解析", test_parse_school_list),
        ("文档下载", test_download_document),
        ("获取已保存文件", test_get_saved_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n正在测试: {test_name}")
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
                
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        sys.exit(1)
