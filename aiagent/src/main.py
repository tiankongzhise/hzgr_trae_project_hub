# 主脚本文件 - 整合所有页面对象模型
import logging
import time
from typing import Optional
from playwright.sync_api import sync_playwright, Page
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


def setup_browser():
    """设置浏览器"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(**Config.BROWSER_CONFIG)
    context = browser.new_context()
    page = context.new_page()
    return playwright, browser, context, page


def login_process(page: Page) -> Optional[Page]:
    """登录流程
    
    Args:
        page: 浏览器页面对象
        
    Returns:
        登录后的BCNT页面
    """
    try:
        login_page = LoginPage(page)
        login_page.navigate(Config.LOGIN["url"])
        login_page.login(Config.LOGIN["username"], Config.LOGIN["password"])
        bcnt_page = login_page.click_bcnt_link()
        return bcnt_page
    except Exception as e:
        logger.error(f"登录过程失败: {e}")
        raise


def navigate_to_agent_creation(bcnt_page: Page) -> Optional[Page]:
    """导航到智能体创建页面
    
    Args:
        bcnt_page: BCNT页面对象
        
    Returns:
        智能体创建页面
    """
    try:
        qiaocang_page = QiaocangPage(bcnt_page)
        agent_page = qiaocang_page.click_qiaocang()
        qiaocang_page = QiaocangPage(agent_page) #noqa
        qiaocang_page.scroll_and_refresh()
        qiaocang_page.navigate_to_aiagent(Config.AGENT_CREATION["url"])
        qiaocang_page.scroll_multiple_times(3)
        return agent_page
    except Exception as e:
        logger.error(f"导航到智能体创建页面失败: {e}")
        raise


def create_agent(agent_page: Page) -> None:
    """创建智能体
    
    Args:
        agent_page: 智能体创建页面
    """
    try:
        agent_creation_page = AgentCreationPage(agent_page)
        agent_creation_page.complete_basic_setup(
            Config.AGENT_CREATION["agent_name"],
            Config.AGENT_CREATION["company_description"],
            Config.AGENT_CREATION["target_users"]
        )
        # 这里可以添加更多的智能体配置步骤
        logger.info("智能体创建成功")
    except Exception as e:
        logger.error(f"创建智能体失败: {e}")
        raise


def main():
    """主函数"""
    logger.info("开始自动化流程")
    playwright = None
    try:
        # 设置浏览器
        playwright, browser, context, page = setup_browser()
        
        # 登录流程
        bcnt_page = login_process(page)
        if not bcnt_page:
            logger.error("登录失败，无法获取BCNT页面")
            return
        
        # 导航到智能体创建页面
        agent_page = navigate_to_agent_creation(bcnt_page)
        if not agent_page:
            logger.error("导航失败，无法获取智能体创建页面")
            return
        
        # 创建智能体
        create_agent(agent_page)
        
        # 等待一段时间以便查看结果
        time.sleep(5)
        
        logger.info("自动化流程完成")
    except Exception as e:
        logger.error(f"自动化流程失败: {e}")
    finally:
        # 关闭浏览器
        if playwright:
            playwright.stop()


if __name__ == "__main__":
    main()