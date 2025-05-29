#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试解析器，分析实际的HTML结构
"""

from bs4 import BeautifulSoup
from pathlib import Path


def analyze_html_structure():
    """分析HTML结构"""
    html_file = Path('page_content.html')
    
    if not html_file.exists():
        print("❌ 页面文件不存在")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    print("=== HTML结构分析 ===")
    print(f"页面标题: {soup.title.string if soup.title else 'N/A'}")
    
    # 查找所有表格
    tables = soup.find_all('table')
    print(f"\n找到 {len(tables)} 个表格")
    
    for i, table in enumerate(tables):
        print(f"\n--- 表格 {i+1} ---")
        print(f"属性: {table.attrs}")
        
        rows = table.find_all('tr')
        print(f"行数: {len(rows)}")
        
        if rows:
            print("前5行内容:")
            for j, row in enumerate(rows[:5]):
                cells = row.find_all(['td', 'th'])
                if cells:
                    cell_texts = []
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        # 检查是否包含链接
                        links = cell.find_all('a')
                        if links:
                            link_info = f"[{len(links)}个链接]"
                            text = f"{text} {link_info}"
                        cell_texts.append(text)
                    print(f"  行{j+1}: {cell_texts}")
        
        # 检查表格内容
        table_text = table.get_text()
        keywords = ['学校', '招生', '简章', '院校', '湖南']
        found_keywords = [kw for kw in keywords if kw in table_text]
        if found_keywords:
            print(f"包含关键词: {found_keywords}")
            
            # 如果包含学校相关信息，详细分析
            if '学校' in found_keywords or '院校' in found_keywords:
                print("*** 这可能是目标表格 ***")
                analyze_target_table(table)
    
    # 查找其他可能的容器
    print("\n=== 其他容器分析 ===")
    
    # 查找div容器
    divs = soup.find_all('div')
    school_divs = []
    for div in divs:
        div_text = div.get_text()
        if '学校' in div_text or '院校' in div_text:
            school_divs.append(div)
    
    print(f"包含学校信息的div: {len(school_divs)}个")
    
    # 查找ul/li列表
    lists = soup.find_all(['ul', 'ol'])
    school_lists = []
    for lst in lists:
        list_text = lst.get_text()
        if '学校' in list_text or '院校' in list_text:
            school_lists.append(lst)
    
    print(f"包含学校信息的列表: {len(school_lists)}个")


def analyze_target_table(table):
    """详细分析目标表格"""
    print("\n=== 目标表格详细分析 ===")
    
    rows = table.find_all('tr')
    
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        print(f"\n行 {i+1} ({len(cells)}列):")
        
        for j, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            links = cell.find_all('a')
            
            print(f"  列{j+1}: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            if links:
                print(f"    链接数: {len(links)}")
                for k, link in enumerate(links):
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    print(f"      链接{k+1}: {link_text} -> {href}")
        
        # 如果这一行包含学校名称，尝试提取信息
        if cells and len(cells) >= 3:
            school_name = cells[0].get_text(strip=True)
            if school_name and '学校' not in school_name and '院校' not in school_name and school_name != '':
                print(f"    可能的学校: {school_name}")
                
                # 检查第二列和第三列的链接
                for col_idx, col_name in [(1, '普通招生'), (2, '特长生招生')]:
                    if len(cells) > col_idx:
                        col_links = cells[col_idx].find_all('a')
                        if col_links:
                            for link in col_links:
                                href = link.get('href', '')
                                if href:
                                    print(f"      {col_name}链接: {href}")


def test_improved_parser():
    """测试改进的解析器"""
    print("\n=== 测试改进的解析器 ===")
    
    html_file = Path('page_content.html')
    if not html_file.exists():
        print("❌ 页面文件不存在")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # 尝试不同的表格选择器
    selectors = [
        'table[width="90%"]',
        'table',
        'table[border]',
        'table[cellpadding]'
    ]
    
    for selector in selectors:
        print(f"\n尝试选择器: {selector}")
        tables = soup.select(selector)
        print(f"找到 {len(tables)} 个表格")
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 10:  # 假设学校表格应该有较多行
                print(f"  表格有 {len(rows)} 行，可能是目标表格")
                
                # 检查是否包含学校信息
                table_text = table.get_text()
                if '学校' in table_text or '院校' in table_text:
                    print("  ✅ 包含学校信息")
                    
                    # 尝试解析前几行
                    schools_found = 0
                    for i, row in enumerate(rows[1:6]):  # 跳过表头，检查前5行
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            school_name = cells[0].get_text(strip=True)
                            if school_name and len(school_name) > 2 and '学校' not in school_name:
                                schools_found += 1
                                print(f"    找到学校: {school_name}")
                                
                                # 检查链接
                                for col_idx in [1, 2]:
                                    if len(cells) > col_idx:
                                        links = cells[col_idx].find_all('a')
                                        if links:
                                            for link in links:
                                                href = link.get('href')
                                                if href:
                                                    print(f"      列{col_idx+1}链接: {href[:60]}...")
                    
                    print(f"  在前5行中找到 {schools_found} 个学校")


if __name__ == "__main__":
    analyze_html_structure()
    test_improved_parser()
