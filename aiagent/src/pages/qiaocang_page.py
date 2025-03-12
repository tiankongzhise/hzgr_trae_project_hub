# 巧舱页面对象模型
import re
import logging
from playwright.sync_api import Page, expect
from typing import Optional

class QiaocangPage:
    """巧舱页面对象模型，封装与巧舱页面相关的所有交互"""
    
    def __init__(self, page: Page):
        """初始化巧舱页面对象
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # 页面元素定位器
        self.qiaocang_button = page.locator("div").filter(has_text=re.compile(r"^巧舱$")).nth(4)
        self.bcnt_scroll_text = page.get_by_text("金蛛-BCNT下滑查看")
    
    def navigate_to_aiagent(self, url: str) -> None:
        """导航到AI智能体页面
        
        Args:
            url: AI智能体页面URL
        """
        self.logger.info(f"导航到AI智能体页面: {url}")
        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            self.logger.error(f"导航到AI智能体页面失败: {e}")
            raise
    
    def click_qiaocang(self) -> Page:
        """点击巧舱按钮，打开新页面
        
        Returns:
            新打开的页面对象
        """
        self.logger.info("点击巧舱按钮")
        try:
            with self.page.expect_popup() as page_info:
                self.qiaocang_button.click()
            return page_info.value
        except Exception as e:
            self.logger.error(f"点击巧舱按钮失败: {e}")
            raise
    
    def scroll_and_refresh(self) -> None:
        """滚动页面并刷新"""
        self.logger.info("滚动页面并刷新")
        try:
            self.bcnt_scroll_text.click()
            self.page.locator("body").press("F5")
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            self.logger.error(f"滚动页面并刷新失败: {e}")
            raise
    
    def scroll_multiple_times(self, times: int = 3) -> None:
        """多次滚动页面
        
        Args:
            times: 滚动次数
        """
        self.logger.info(f"滚动页面 {times} 次")
        try:
            for _ in range(times):
                self.bcnt_scroll_text.click()
                self.page.wait_for_timeout(500)  # 短暂等待以确保滚动生效
        except Exception as e:
            self.logger.error(f"多次滚动页面失败: {e}")
            raise