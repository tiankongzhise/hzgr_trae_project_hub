# 模块化重构后的智能体创建自动化脚本
import logging
import time
from playwright.sync_api import sync_playwright
from config import Config
from pages.login_page import LoginPage
from pages.qiaocang_page import QiaocangPage
from pages.agent_creation_page import AgentCreationPage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run():
    """执行智能体创建自动化流程"""
    logger.info("开始执行智能体创建自动化流程")
    
    with sync_playwright() as playwright:
        try:
            # 启动浏览器
            browser = playwright.chromium.launch(**Config.BROWSER_CONFIG)
            context = browser.new_context()
            page = context.new_page()
            
            # 登录流程
            login_page = LoginPage(page)
            login_page.navigate(Config.LOGIN["url"])
            login_page.login(Config.LOGIN["username"], Config.LOGIN["password"])
            bcnt_page = login_page.click_bcnt_link()
            
            # 进入巧舱页面
            qiaocang_page = QiaocangPage(bcnt_page)
            agent_page = qiaocang_page.click_qiaocang()
            
            # 处理巧舱页面
            qiaocang_handler = QiaocangPage(agent_page)
            qiaocang_handler.scroll_and_refresh()
            qiaocang_handler.navigate_to_aiagent(Config.AGENT_CREATION["url"])
            qiaocang_handler.scroll_multiple_times(3)
            
            # 创建智能体基本信息
            agent_creation = AgentCreationPage(agent_page)
            agent_creation.complete_basic_setup(
                Config.AGENT_CREATION["agent_name"],
                Config.AGENT_CREATION["company_description"],
                Config.AGENT_CREATION["target_users"]
            )
            
            # 这里可以添加更多的智能体配置步骤，如商家优势、服务标签等
            # 由于这些步骤较为复杂，可以在AgentCreationPage类中添加相应的方法
            
            logger.info("智能体创建流程执行完成")
            
            # 等待一段时间以便查看结果
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"自动化流程执行失败: {e}")
            raise
        finally:
            # 关闭浏览器
            if 'context' in locals():
                context.close()
            if 'browser' in locals():
                browser.close()


if __name__ == "__main__":
    run()