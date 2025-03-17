# 登录页面对象模型
import logging
from playwright.sync_api import Page, expect
from typing import Optional

class LoginPage:
    """登录页面对象模型，封装与登录页面相关的所有交互"""
    
    def __init__(self, page: Page):
        """初始化登录页面对象
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 页面元素定位器
        self.username_input = page.get_by_role("textbox", name="请输入账号")
        self.password_input = page.get_by_role("textbox", name="请输入密码")
        self.login_button = page.get_by_role("button", name="登录")
        
    
    def navigate(self, url: str) -> None:
        """导航到登录页面
        
        Args:
            url: 登录页面URL
        """
        self.logger.info(f"导航到登录页面: {url}")
        try:
            self.page.goto(url)
        except Exception as e:
            self.logger.error(f"导航到登录页面失败: {e}")
            raise
    
    def login(self, username: str, password: str) -> None:
        """执行登录操作
        
        Args:
            username: 用户名
            password: 密码
        """
        self.logger.info(f"使用账号 {username} 登录")
        try:
            # 输入用户名
            self.username_input.click()
            self.username_input.fill(username)
            
            # 输入密码
            self.password_input.click()
            self.password_input.fill(password)
            
            # 点击登录按钮
            self.login_button.click()
            
            # 等待登录成功
            self.page.wait_for_load_state("networkidle")
            self.logger.info("登录成功")
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            raise
    
    def click_account_link(self,account_name:str) -> Optional[Page]:
        """点击账户名称链接，打开新页面
        
        Returns:
            新打开的页面对象
        """
        self.logger.info(f"点击{account_name}链接")
        try:
            with self.page.expect_popup() as page_info:
                self.page.get_by_text(account_name).first.click()
            return page_info.value
        except Exception as e:
            self.logger.error(f"点击金蛛-BCNT链接失败: {e}")
            raise
