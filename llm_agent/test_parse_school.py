#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试parse_school.py的解析功能
"""

import sys
from pathlib import Path

# 导入解析函数
from parse_school import parse_schools

def test_parse_with_saved_html():
    """使用保存的HTML文件测试解析功能"""
    html_file = Path("page_content.html")
    
    if not html_file.exists():
        print(f"错误：找不到文件 {html_file}")
        return False
    
    print(f"读取HTML文件: {html_file}")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"HTML文件大小: {len(html_content)} 字符")
        
        # 调用解析函数
        print("\n开始解析学校信息...")
        schools = parse_schools(html_content)
        
        print(f"\n解析结果: 找到 {len(schools)} 所学校")
        
        if schools:
            print("\n学校列表:")
            for i, school in enumerate(schools, 1):
                print(f"{i}. {school['学校名称']}")
                print(f"   招生简章: {school['普通简章链接']}")
                if school['特长生简章链接']:
                    print(f"   特长生简章: {school['特长生简章链接']}")
                print()
        else:
            print("未找到任何学校信息")
        
        return len(schools) > 0
        
    except Exception as e:
        print(f"解析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 测试parse_school.py解析功能 ===")
    success = test_parse_with_saved_html()
    
    if success:
        print("\n✅ 测试成功！解析功能正常工作")
    else:
        print("\n❌ 测试失败！解析功能需要进一步调试")
        sys.exit(1)
