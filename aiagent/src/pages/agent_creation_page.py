# 智能体创建页面对象模型
import re
import logging
from playwright.sync_api import Page, expect
from typing import Optional, List

class AgentCreationPage:
    """智能体创建页面对象模型，封装与智能体创建相关的所有交互"""
    
    def __init__(self, page: Page):
        """初始化智能体创建页面对象
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 页面元素定位器
        self.agent_name_input = page.get_by_role("textbox", name="请输入智能体名称")
        self.avatar_setting = page.locator("div").filter(has_text=re.compile(r"^设置头像$")).first
        self.avatar_selector = page.locator(".vi > div > div > .vi")
        self.album_first = page.locator(".cc-album").first
        self.confirm_button = page.get_by_role("button", name="​ 确定")
        self.next_step_button = page.get_by_text("下一步")
        self.company_desc_input = page.get_by_role("textbox", name="本公司是一家专门做xx的公司，主要经营产品有A、B、C等。")
        self.target_users_input = page.get_by_role("textbox", name="目标用户是有xx需求的网民。")
        self.create_agent_button = page.get_by_text("创建智能体")
        self.agreement_checkbox = page.locator("span").filter(has_text="我已阅读并同意").first
    
    def navigate(self, url: str) -> None:
        """导航到智能体创建页面
        
        Args:
            url: 智能体创建页面URL
        """
        self.logger.info(f"导航到智能体创建页面: {url}")
        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            self.logger.error(f"导航到智能体创建页面失败: {e}")
            raise
    
    def set_agent_name(self, name: str) -> None:
        """设置智能体名称
        
        Args:
            name: 智能体名称
        """
        self.logger.info(f"设置智能体名称: {name}")
        try:
            self.agent_name_input.click()
            self.agent_name_input.dblclick()
            self.agent_name_input.press("ControlOrMeta+a")
            self.agent_name_input.fill(name)
        except Exception as e:
            self.logger.error(f"设置智能体名称失败: {e}")
            raise
    
    def set_avatar(self) -> None:
        """设置智能体头像"""
        self.logger.info("设置智能体头像")
        try:
            self.avatar_setting.click()
            self.avatar_selector.click()
            self.album_first.click()
            self.confirm_button.click()
        except Exception as e:
            self.logger.error(f"设置智能体头像失败: {e}")
            raise
    
    def set_company_description(self, description: str) -> None:
        """设置公司描述
        
        Args:
            description: 公司描述文本
        """
        self.logger.info("设置公司描述")
        try:
            self.company_desc_input.click()
            self.company_desc_input.fill(description)
        except Exception as e:
            self.logger.error(f"设置公司描述失败: {e}")
            raise
    
    def set_target_users(self, target_users: str) -> None:
        """设置目标用户
        
        Args:
            target_users: 目标用户描述
        """
        self.logger.info("设置目标用户")
        try:
            self.target_users_input.click()
            self.target_users_input.fill(target_users)
        except Exception as e:
            self.logger.error(f"设置目标用户失败: {e}")
            raise
    
    def proceed_to_next_step(self) -> None:
        """进行下一步"""
        self.logger.info("点击下一步按钮")
        try:
            self.next_step_button.click()
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            self.logger.error(f"点击下一步按钮失败: {e}")
            raise
    
    def create_agent(self) -> None:
        """创建智能体"""
        self.logger.info("创建智能体")
        try:
            self.create_agent_button.click()
            # 处理同意协议
            try:
                self.agreement_checkbox.click()
                self.page.wait_for_timeout(500)
                self.agreement_checkbox.click()  # 有时需要点击两次
                self.create_agent_button.click()
            except Exception:
                self.logger.info("无需处理协议或已处理")
            
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            self.logger.error(f"创建智能体失败: {e}")
            raise
    
    def complete_basic_setup(self, agent_name: str, company_description: str, target_users: str) -> None:
        """完成基本设置
        
        Args:
            agent_name: 智能体名称
            company_description: 公司描述
            target_users: 目标用户
        """
        self.logger.info("完成智能体基本设置")
        try:
            self.set_agent_name(agent_name)
            self.set_avatar()
            self.set_company_description(company_description)
            self.set_target_users(target_users)
            self.proceed_to_next_step()
            self.create_agent()
        except Exception as e:
            self.logger.error(f"完成基本设置失败: {e}")
            raise