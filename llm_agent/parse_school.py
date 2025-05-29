def parse_schools(html: str) -> list:
    """解析HTML，提取学校信息"""
    soup = BeautifulSoup(html, "lxml")
    # 定位主表格（通过width=90%匹配）
    main_table = soup.find("table", width="90%")
    if not main_table:
        print("未找到学校信息表格")
        return []
    
    schools = []
    # 遍历所有tr（跳过表头行）
    for tr in main_table.find_all("tr")[1:]:  # 第一个tr是表头
        # 跳过合并单元格的标题行（如"省外招生院校"）
        if tr.find("td", colspan="2"):
            continue
        
        # 提取学校名称和链接
        tds = tr.find_all("td")
        if len(tds) != 2:
            continue  # 非学校行（如格式异常）
        
        # 学校名称（第一个td的文本）
        school_name = tds[0].get_text(strip=True)
        
        # 提取所有a标签（普通简章和特长生简章）
        links = tds[1].find_all("a")
        normal_url = None
        special_url = None
        
        if links:
            normal_url = urljoin(TARGET_URL, links[0].get("href", ""))  # 普通简章链接
            if len(links) >= 2:
                special_url = urljoin(TARGET_URL, links[1].get("href", ""))  # 特长生简章链接
        
        schools.append({
            "学校名称": school_name,
            "普通简章链接": normal_url,
            "特长生简章链接": special_url
        })
    
    return schools
