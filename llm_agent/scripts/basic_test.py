#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本
测试解析和下载的核心功能
"""

import asyncio
import sys
import httpx
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config import get_settings
except ImportError as e:
    print(f"导入配置失败: {e}")
    sys.exit(1)


def parse_schools_from_html(html_content: str, base_url: str) -> list:
    """从HTML内容解析学校信息"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有表格
    tables = soup.find_all("table")
    if not tables:
        print("❌ 未找到任何表格")
        return []
    
    print(f"找到 {len(tables)} 个表格")
    
    # 选择最有可能包含学校信息的表格（基于链接数量）
    best_table = None
    max_links = 0
    
    for i, table in enumerate(tables):
        links_count = len(table.find_all("a"))
        print(f"表格 {i+1}: {len(table.find_all('tr'))} 行, {links_count} 个链接")
        
        if links_count > max_links:
            max_links = links_count
            best_table = table
    
    if not best_table:
        print("❌ 未找到包含链接的表格")
        return []
    
    print(f"选择表格，包含 {max_links} 个链接")
    
    schools = []
    rows = best_table.find_all("tr")
    
    # 尝试从不同起始行开始解析
    for start_row in [0, 1, 2]:
        if start_row >= len(rows):
            continue
            
        temp_schools = []
        for i, tr in enumerate(rows[start_row:], start_row):
            # 查找包含.docx链接的行
            docx_links = [a for a in tr.find_all("a") if a.get("href", "").endswith(".docx")]
            
            if docx_links:
                # 提取学校名称（从链接文本或前面的文本中）
                school_name = ""
                
                # 尝试从链接文本中提取学校名称
                link_text = docx_links[0].get_text(strip=True)
                if "招生章程" in link_text or "招生简章" in link_text:
                    # 从链接文本中提取学校名称
                    school_name = link_text.replace("招生章程", "").replace("招生简章", "").replace("2025年", "").strip()
                
                # 如果从链接文本中没有提取到，尝试从行中的其他文本提取
                if not school_name:
                    all_text = tr.get_text(strip=True)
                    # 简单的学校名称提取逻辑
                    if "学院" in all_text or "大学" in all_text or "学校" in all_text:
                        words = all_text.split()
                        for word in words:
                            if "学院" in word or "大学" in word or "学校" in word:
                                school_name = word
                                break
                
                if school_name:
                    # 构建完整URL
                    docx_url = docx_links[0].get("href", "")
                    if not docx_url.startswith("http"):
                        docx_url = urljoin(base_url, docx_url)
                    
                    temp_schools.append({
                        'name': school_name,
                        'normal_url': docx_url,
                        'special_url': None
                    })
        
        if temp_schools:
            schools = temp_schools
            print(f"从第 {start_row+1} 行开始解析，找到 {len(schools)} 所学校")
            break
    
    return schools


async def test_parse_schools():
    """测试学校信息解析"""
    print("\n=== 测试学校信息解析 ===")
    
    try:
        settings = get_settings()
        target_url = settings.scraper.base_url
        
        import ssl
        import os
        
        # 设置OpenSSL配置以降低安全级别
        os.environ['OPENSSL_CONF'] = ''
        
        # 创建更宽松的SSL上下文
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 设置更宽松的加密套件和协议
        try:
            ssl_context.set_ciphers('ALL:@SECLEVEL=0')
        except ssl.SSLError:
            try:
                ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
            except ssl.SSLError:
                ssl_context.set_ciphers('DEFAULT')
        
        # 启用所有协议版本
        ssl_context.minimum_version = ssl.TLSVersion.SSLv3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        async with httpx.AsyncClient(timeout=30.0, verify=ssl_context) as client:
            print(f"正在获取页面: {target_url}")
            response = await client.get(target_url)
            response.raise_for_status()
            
            print(f"页面获取成功，状态码: {response.status_code}")
            print(f"内容长度: {len(response.text)} 字符")
            
            # 解析学校信息
            schools = parse_schools_from_html(response.text, target_url)
            
            print(f"\n✅ 成功解析 {len(schools)} 所学校")
            
            # 显示前5个学校的信息
            for i, school in enumerate(schools[:5]):
                print(f"\n学校 {i+1}: {school['name']}")
                if school['normal_url']:
                    print(f"  普通招生简章: {school['normal_url'][:80]}...")
                if school['special_url']:
                    print(f"  特长生招生简章: {school['special_url'][:80]}...")
            
            return schools
            
    except Exception as e:
        print(f"❌ 解析测试失败: {e}")
        return []


async def test_download_single(url: str, school_name: str):
    """测试单个文件下载"""
    print(f"\n=== 测试下载: {school_name} ===")
    print(f"URL: {url[:80]}...")
    
    try:
        # 使用相同的SSL配置
        import ssl
        import os
        os.environ['OPENSSL_CONF'] = ''
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        try:
            ssl_context.set_ciphers('ALL:@SECLEVEL=0')
        except ssl.SSLError:
            try:
                ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
            except ssl.SSLError:
                ssl_context.set_ciphers('DEFAULT')
        ssl_context.minimum_version = ssl.TLSVersion.SSLv3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        async with httpx.AsyncClient(timeout=30.0, verify=ssl_context) as client:
            response = await client.get(url)
            
            print(f"响应状态码: {response.status_code}")
            print(f"内容类型: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"✅ 下载成功，内容长度: {content_length} 字节")
                
                # 如果是文本内容，显示预览
                content_type = response.headers.get('content-type', '').lower()
                if 'text' in content_type or 'html' in content_type:
                    text_content = response.text[:200].replace('\n', ' ').strip()
                    print(f"内容预览: {text_content}...")
                
                return True
            else:
                print(f"❌ 下载失败，状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ 下载异常: {e}")
        return False


async def test_multiple_downloads(schools: list, count: int = 5):
    """测试多个文件下载"""
    print(f"\n=== 测试多个下载 (前{count}个) ===")
    
    if not schools:
        print("❌ 没有学校信息可供测试")
        return
    
    test_schools = schools[:count]
    results = {'normal': [], 'special': []}
    
    for i, school in enumerate(test_schools):
        print(f"\n进度: {i+1}/{len(test_schools)} - {school['name']}")
        
        # 测试普通招生简章
        if school['normal_url']:
            print("  测试普通招生简章...")
            success = await test_download_single(school['normal_url'], school['name'])
            results['normal'].append(success)
        
        # 测试特长生招生简章
        if school['special_url']:
            print("  测试特长生招生简章...")
            success = await test_download_single(school['special_url'], school['name'])
            results['special'].append(success)
        
        # 添加延迟避免请求过快
        await asyncio.sleep(1)
    
    # 统计结果
    normal_success = sum(results['normal'])
    special_success = sum(results['special'])
    
    print(f"\n下载结果统计:")
    print(f"  普通招生简章: {normal_success}/{len(results['normal'])} 成功")
    print(f"  特长生招生简章: {special_success}/{len(results['special'])} 成功")
    print(f"  总成功率: {(normal_success + special_success)}/{(len(results['normal']) + len(results['special']))}")


async def test_concurrent_downloads(schools: list, count: int = 3):
    """测试并发下载"""
    print(f"\n=== 测试并发下载 (前{count}个) ===")
    
    if not schools:
        print("❌ 没有学校信息可供测试")
        return
    
    # 收集所有要下载的URL
    download_tasks = []
    for school in schools[:count]:
        if school['normal_url']:
            download_tasks.append({
                'url': school['normal_url'],
                'name': f"{school['name']}-普通",
                'type': 'normal'
            })
        if school['special_url']:
            download_tasks.append({
                'url': school['special_url'],
                'name': f"{school['name']}-特长生",
                'type': 'special'
            })
    
    print(f"准备并发下载 {len(download_tasks)} 个文件")
    
    async def download_task(task_info):
        """单个下载任务"""
        try:
            # 使用相同的SSL配置
            import ssl
            import os
            os.environ['OPENSSL_CONF'] = ''
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            try:
                ssl_context.set_ciphers('ALL:@SECLEVEL=0')
            except ssl.SSLError:
                try:
                    ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
                except ssl.SSLError:
                    ssl_context.set_ciphers('DEFAULT')
            ssl_context.minimum_version = ssl.TLSVersion.SSLv3
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            async with httpx.AsyncClient(timeout=30.0, verify=ssl_context) as client:
                response = await client.get(task_info['url'])
                return {
                    'name': task_info['name'],
                    'type': task_info['type'],
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'content_length': len(response.content) if response.status_code == 200 else 0
                }
        except Exception as e:
            return {
                'name': task_info['name'],
                'type': task_info['type'],
                'success': False,
                'error': str(e),
                'content_length': 0
            }
    
    # 执行并发下载
    import time
    start_time = time.time()
    
    # 限制并发数为3
    semaphore = asyncio.Semaphore(3)
    
    async def limited_download(task_info):
        async with semaphore:
            return await download_task(task_info)
    
    results = await asyncio.gather(*[limited_download(task) for task in download_tasks])
    
    end_time = time.time()
    
    # 统计结果
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n并发下载结果:")
    print(f"  总计: {len(results)}")
    print(f"  成功: {successful}")
    print(f"  失败: {failed}")
    print(f"  耗时: {end_time - start_time:.2f}秒")
    
    # 显示详细结果
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['name']}: {result.get('content_length', 0)} 字节")
        if not result['success'] and 'error' in result:
            print(f"    错误: {result['error']}")


async def main():
    """主测试函数"""
    print("开始基础功能测试...")
    print("="*60)
    
    try:
        # 测试配置
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"  目标URL: {settings.scraper.base_url}")
        
        # 1. 测试学校信息解析
        schools = await test_parse_schools()
        
        if not schools:
            print("\n❌ 无法获取学校信息，停止后续测试")
            return
        
        # 2. 测试多个下载（串行）
        await test_multiple_downloads(schools, 5)
        
        # 3. 测试并发下载
        await test_concurrent_downloads(schools, 3)
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
