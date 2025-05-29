#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析网页内容和结构
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from pathlib import Path


async def analyze_page():
    """分析网页内容"""
    url = "https://cs.bendibao.com/job/202525/124791.shtm"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"正在获取页面: {url}")
            response = await client.get(url)
            response.raise_for_status()
            
            print(f"页面获取成功，状态码: {response.status_code}")
            print(f"内容长度: {len(response.text)} 字符")
            
            # 保存原始内容
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("页面内容已保存到 page_content.html")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有表格
            tables = soup.find_all('table')
            print(f"\n找到 {len(tables)} 个表格")
            
            for i, table in enumerate(tables):
                print(f"\n表格 {i+1}:")
                print(f"  属性: {table.attrs}")
                
                rows = table.find_all('tr')
                print(f"  行数: {len(rows)}")
                
                if rows:
                    # 显示前几行的内容
                    for j, row in enumerate(rows[:3]):
                        cells = row.find_all(['td', 'th'])
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        print(f"    行 {j+1}: {cell_texts}")
                
                # 检查是否包含学校信息
                table_text = table.get_text()
                if '学校' in table_text or '招生' in table_text:
                    print(f"  *** 可能包含学校信息 ***")
            
            # 查找包含特定关键词的元素
            print("\n=== 搜索关键词 ===")
            keywords = ['学校', '招生', '简章', '院校']
            for keyword in keywords:
                elements = soup.find_all(text=lambda text: text and keyword in text)
                print(f"包含'{keyword}'的文本片段: {len(elements)}个")
                if elements:
                    for elem in elements[:3]:
                        print(f"  - {elem.strip()[:50]}...")
            
            # 查找所有链接
            links = soup.find_all('a', href=True)
            print(f"\n找到 {len(links)} 个链接")
            
            # 查找可能的招生简章链接
            recruitment_links = []
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if any(keyword in text.lower() or keyword in href.lower() 
                       for keyword in ['招生', '简章', 'doc', 'pdf']):
                    recruitment_links.append((text, href))
            
            print(f"\n可能的招生简章链接: {len(recruitment_links)}个")
            for text, href in recruitment_links[:10]:
                print(f"  - {text}: {href}")
            
    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_page())
