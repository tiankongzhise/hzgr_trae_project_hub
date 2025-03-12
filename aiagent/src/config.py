import os
from dotenv import load_dotenv
load_dotenv()



# 配置文件

class Config:
    # 浏览器配置
    BROWSER_CONFIG = {
        "headless": False,
        "slow_mo": 50,  # 减慢操作速度，增加稳定性
        "timeout": 30000  # 默认超时时间（毫秒）
    }
    
    # 登录信息
    LOGIN = {
        "url": "https://cas.baidu.com/?tpl=www2&fromu=https%3A%2F%2Fwww2.baidu.com%2Fcommon%2Fappinit.ajax",
        "username": os.getenv('BD_USERNAME'),
        "password": os.getenv('BD_PASSWORD') # 注意：实际应用中应使用环境变量或安全存储
    }
    
    # 智能体创建页面
    AGENT_CREATION = {
        "url": "https://aiagent.baidu.com/mbot/user/64261946/creatorChat?relationSource=mbotIndex&ucUserId=64261946",
        "agent_name": "深圳北大青鸟教师助理",
        "company_description": '专注IT培训教育26年，培养100W学员从事IT互联网行业。学AI，好工作，就找北大青鸟。 北大青鸟始终践行"职业教育就是就业教育"的教育本质， 坚持帮助学员成功就业，永远是硬道理，始终保持回归职业教育的本真，即坚守"教学为本，师爱为魂"的教育理念， 以及"内育职业素养，外塑专业技能"的青鸟校训，主要业务有软件开发培训，网络工程培训，AI开发培训，Java培训，大数据培训，Python培训，电商培训，新媒体培训，UI培训等。',
        "target_users": "目标用户是希望通过学一门技术获得好发展的人群。"
    }
    
    # 商家优势信息
    BUSINESS_ADVANTAGES = {
        "network": "全国60多个城市200余家分校，800+所合作学校，20000+家合作用人企业。",
        "textbook": '教材被纳入国家"十三五"和"十四五"规划高校教学用书',
        "talent_training": "26年培养了100万+IT互联网技术人才，与华/阿等企业深度合作，参与大数据等岗位行业标准制定。",
        "rd_team": "拥有200余人的研发团队，覆盖教育学、软件开发、网络安全等多个领域，课程每10-18个月更新一次，确保技术前沿性。",
        "facilities": "配备青鸟AI实验室、NovaAI开放平台等先进教学设施，提供真实企业项目实训环境。",
        "service": "入学签订协议，提供全程就业跟踪服务，​技能学历双认证。",
        "policy": "完善奖助学金政策，提供先学后付，特殊群体专项补贴或学费减免。"
    }
    
    # 服务标签
    SERVICE_TAGS = [
        "权威教材",
        "26年教学沉淀",
        "100W+学员选择",
        "行业定制标准",
        "全真项目实战",
        "AI+全新升级"
    ]
    
    # 线索收集配置
    LEAD_COLLECTION = {
        "phone_plan": "转18806662618",
        "wechat_plan": "挂机短信默认方案_2618"
    }
    
    # 文件路径
    FILES = {
        "address_template": "addressTemplate.xlsx"
    }