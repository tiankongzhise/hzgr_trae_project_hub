from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_URL = "https://cs.bendibao.com/job/202525/124791.shtm"

def parse_schools(html: str) -> list:
    """解析HTML，提取学校信息"""
    soup = BeautifulSoup(html, "lxml")
    
    # 查找所有表格
    tables = soup.find_all("table")
    if not tables:
        print("未找到任何表格")
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
        print("未找到包含链接的表格")
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
                        docx_url = urljoin(TARGET_URL, docx_url)
                    
                    temp_schools.append({
                        "学校名称": school_name,
                        "普通简章链接": docx_url,
                        "特长生简章链接": None
                    })
                    
                    print(f"找到学校: {school_name} -> {docx_url}")
        
        if temp_schools:
            schools = temp_schools
            print(f"从第 {start_row+1} 行开始解析，找到 {len(schools)} 所学校")
            break
    
    if not schools:
        print("未能提取到学校信息")
    
    return schools
