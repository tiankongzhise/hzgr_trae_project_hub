#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细解析器，深入分析表格结构
"""

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin


def analyze_table_structure():
    """详细分析表格结构"""
    html_file = Path('page_content.html')
    
    if not html_file.exists():
        print("❌ 页面文件不存在")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    base_url = "https://cs.bendibao.com/job/202525/124791.shtm"
    
    # 找到所有表格
    tables = soup.find_all('table')
    print(f"找到 {len(tables)} 个表格")
    
    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) < 10:  # 跳过小表格
            continue
            
        print(f"\n=== 分析表格 {table_idx + 1} (共{len(rows)}行) ===")
        
        # 分析前10行的详细内容
        for row_idx, row in enumerate(rows[:10]):
            cells = row.find_all(['td', 'th'])
            print(f"\n行 {row_idx + 1} - {len(cells)} 列:")
            
            for cell_idx, cell in enumerate(cells):
                # 获取单元格文本
                text = cell.get_text(strip=True)
                
                # 获取单元格属性
                attrs = cell.attrs
                
                # 查找链接
                links = cell.find_all('a')
                
                print(f"  列 {cell_idx + 1}:")
                print(f"    文本: '{text}'")
                if attrs:
                    print(f"    属性: {attrs}")
                
                if links:
                    print(f"    链接数: {len(links)}")
                    for link_idx, link in enumerate(links):
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True)
                        full_url = urljoin(base_url, href) if href else ''
                        print(f"      链接 {link_idx + 1}: '{link_text}' -> {full_url}")
                
                # 检查是否可能是学校名称
                if cell_idx == 0 and text and len(text) > 2:
                    # 排除表头和无效内容
                    if not any(keyword in text for keyword in ['学校', '院校', '序号', '编号', '名称']):
                        if any(char in text for char in ['学', '院', '校', '大']):
                            print(f"    *** 可能的学校名称: {text} ***")
        
        # 如果这个表格看起来有学校信息，尝试解析所有行
        if len(rows) > 20:  # 假设学校表格应该有很多行
            print(f"\n=== 尝试解析整个表格 {table_idx + 1} ===")
            schools = parse_schools_from_table(table, base_url)
            print(f"解析结果: {len(schools)} 所学校")
            
            # 显示前5个结果
            for i, school in enumerate(schools[:5]):
                print(f"  {i+1}. {school['name']}")
                if school['normal_url']:
                    print(f"     普通: {school['normal_url'][:60]}...")
                if school['special_url']:
                    print(f"     特长: {school['special_url'][:60]}...")


def parse_schools_from_table(table, base_url):
    """从表格解析学校信息"""
    schools = []
    rows = table.find_all('tr')
    
    # 尝试不同的起始行
    for start_row in [0, 1, 2, 3]:
        print(f"\n  尝试从第 {start_row + 1} 行开始解析...")
        temp_schools = []
        
        for i, row in enumerate(rows[start_row:]):
            cells = row.find_all(['td', 'th'])
            
            # 至少需要3列
            if len(cells) < 3:
                continue
            
            # 获取学校名称（第一列）
            school_name = cells[0].get_text(strip=True)
            
            # 跳过表头和无效行
            if not school_name or len(school_name) < 2:
                continue
            
            # 跳过明显的表头
            if any(keyword in school_name for keyword in ['学校', '院校', '序号', '编号', '名称', '单位']):
                continue
            
            # 获取招生简章链接（第二列）
            normal_url = None
            if len(cells) > 1:
                links = cells[1].find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        normal_url = urljoin(base_url, href)
                        break
            
            # 获取特长生招生简章链接（第三列）
            special_url = None
            if len(cells) > 2:
                links = cells[2].find_all('a')
                for link in links:
                    href = link.get('href')
                    if href:
                        special_url = urljoin(base_url, href)
                        break
            
            # 如果有学校名称和至少一个链接，则认为是有效记录
            if school_name and (normal_url or special_url):
                temp_schools.append({
                    'name': school_name,
                    'normal_url': normal_url,
                    'special_url': special_url
                })
        
        print(f"    从第 {start_row + 1} 行开始解析到 {len(temp_schools)} 所学校")
        
        # 选择解析结果最多的起始行
        if len(temp_schools) > len(schools):
            schools = temp_schools
    
    return schools


def test_different_parsing_strategies():
    """测试不同的解析策略"""
    html_file = Path('page_content.html')
    
    if not html_file.exists():
        print("❌ 页面文件不存在")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    base_url = "https://cs.bendibao.com/job/202525/124791.shtm"
    
    print("\n=== 测试不同解析策略 ===")
    
    # 策略1: 查找包含最多链接的表格
    print("\n策略1: 查找包含最多链接的表格")
    tables = soup.find_all('table')
    best_table = None
    max_links = 0
    
    for table in tables:
        links = table.find_all('a')
        if len(links) > max_links:
            max_links = len(links)
            best_table = table
    
    if best_table:
        print(f"找到包含 {max_links} 个链接的表格")
        schools = parse_schools_from_table(best_table, base_url)
        print(f"解析结果: {len(schools)} 所学校")
    
    # 策略2: 查找包含特定关键词的表格
    print("\n策略2: 查找包含招生简章关键词的表格")
    for table in tables:
        table_text = table.get_text()
        if '招生' in table_text and '简章' in table_text:
            print("找到包含'招生简章'的表格")
            schools = parse_schools_from_table(table, base_url)
            print(f"解析结果: {len(schools)} 所学校")
            break
    
    # 策略3: 直接查找所有包含.docx的链接
    print("\n策略3: 直接查找所有.docx链接")
    all_links = soup.find_all('a', href=True)
    docx_links = []
    
    for link in all_links:
        href = link.get('href', '')
        if '.docx' in href.lower():
            link_text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)
            docx_links.append((link_text, full_url))
    
    print(f"找到 {len(docx_links)} 个.docx链接")
    for i, (text, url) in enumerate(docx_links[:10]):
        print(f"  {i+1}. {text}: {url}")


if __name__ == "__main__":
    analyze_table_structure()
    test_different_parsing_strategies()
