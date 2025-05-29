"""招生简章爬取服务"""

import asyncio
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
import aiofiles
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models.schemas import ScrapingResult
from ..utils.decorators import monitor_performance, retry_on_failure
from ..utils.logger import get_logger
from ..utils.retry import retry_network_request
from ..utils.document_processor import get_document_processor

logger = get_logger(__name__)


class RecruitmentScraper:
    """招生简章爬取器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = self.settings.scraper.base_url
        self.data_dir = self.settings.data_dir
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._init_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._close_client()
    
    async def _init_client(self):
        """初始化HTTP客户端"""
        if self.client is None:
            import ssl
            import os
            
            # 设置OpenSSL配置以降低安全级别
            os.environ['OPENSSL_CONF'] = ''
            
            # 创建更宽松的SSL上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 设置更宽松的加密套件和协议
            try:
                ssl_context.set_ciphers('ALL:@SECLEVEL=0')
            except ssl.SSLError:
                try:
                    ssl_context.set_ciphers('DEFAULT:@SECLEVEL=1')
                except ssl.SSLError:
                    ssl_context.set_ciphers('DEFAULT')
            
            # 启用所有协议版本
            ssl_context.minimum_version = ssl.TLSVersion.SSLv3
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            self.client = httpx.AsyncClient(
                timeout=self.settings.scraper.request_timeout,
                headers={
                    "User-Agent": self.settings.scraper.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                },
                follow_redirects=True,
                verify=ssl_context,  # 使用自定义SSL上下文
            )
            logger.info("HTTP客户端已初始化（使用宽松SSL配置）")
    
    async def _close_client(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("HTTP客户端已关闭")
    
    @monitor_performance()
    async def fetch_page(self, url: str) -> str:
        """获取网页内容"""
        if not self.client:
            await self._init_client()
        
        async def _fetch():
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        
        return await retry_network_request(_fetch)
    
    @monitor_performance()
    async def parse_school_list(self, html_content: str) -> List[Dict[str, Any]]:
        """解析学校列表"""
        soup = BeautifulSoup(html_content, 'lxml')
        schools = []
        
        try:
            # 根据网页结构解析学校信息
            # 这里需要根据实际的HTML结构来调整选择器
            
            # 查找包含学校信息的表格或列表
            school_rows = soup.find_all('tr')[1:]  # 跳过表头
            
            for row in school_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    school_name_cell = cells[0]
                    recruitment_cell = cells[1] if len(cells) > 1 else None
                    
                    # 提取学校名称
                    school_name = school_name_cell.get_text(strip=True)
                    
                    # 提取招生简章链接
                    recruitment_link = None
                    special_talent_link = None
                    
                    if recruitment_cell:
                        links = recruitment_cell.find_all('a')
                        for link in links:
                            link_text = link.get_text(strip=True)
                            href = link.get('href')
                            
                            if href:
                                # 转换为绝对URL
                                absolute_url = urljoin(self.base_url, href)
                                
                                if '特长生' in link_text or '特长' in link_text:
                                    special_talent_link = absolute_url
                                elif '招生章程' in link_text or '招生简章' in link_text:
                                    recruitment_link = absolute_url
                                elif not recruitment_link:  # 如果没有明确的招生简章，使用第一个链接
                                    recruitment_link = absolute_url
                    
                    if school_name and (recruitment_link or special_talent_link):
                        schools.append({
                            'name': school_name,
                            'recruitment_url': recruitment_link,
                            'special_talent_url': special_talent_link,
                        })
            
            logger.info(f"解析到 {len(schools)} 所学校的信息")
            return schools
            
        except Exception as e:
            logger.error(f"解析学校列表失败: {e}")
            raise
    
    @monitor_performance()
    async def download_recruitment_document(self, url: str, school_name: str, doc_type: str = "招生简章") -> Optional[str]:
        """下载招生简章文档"""
        if not self.client:
            await self._init_client()
        
        try:
            async def _download():
                response = await self.client.get(url)
                response.raise_for_status()
                return response.content, response.headers.get('content-type', '')
            
            content, content_type = await retry_network_request(_download)
            
            # 根据内容类型确定文件扩展名
            if 'pdf' in content_type.lower():
                ext = '.pdf'
            elif 'html' in content_type.lower():
                ext = '.html'
            elif 'doc' in content_type.lower():
                ext = '.doc'
            else:
                ext = '.txt'
            
            # 生成文件名
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', school_name)
            filename = f"{safe_name}_{doc_type}{ext}"
            file_path = self.data_dir / filename
            
            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(f"已下载 {school_name} 的 {doc_type}: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"下载 {school_name} 的 {doc_type} 失败: {e}")
            return None
    
    @monitor_performance()
    async def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """从文件中提取文本内容"""
        path = Path(file_path)
        
        try:
            # 使用新的文档处理器
            document_processor = get_document_processor()
            
            if not document_processor.is_supported(file_path):
                logger.warning(f"不支持的文件格式: {file_path}")
                return None
            
            text = await document_processor.extract_text_from_file(file_path)
            
            if text:
                logger.info(f"成功提取文件文本: {file_path.name}，长度: {len(text)}")
                return text
            else:
                logger.warning(f"文件文本提取为空: {file_path}")
                return None
                    
        except Exception as e:
            logger.error(f"提取文件 {file_path} 的文本内容失败: {e}")
            return None
    
    @monitor_performance()
    async def scrape_school_recruitment(self, school_info: Dict[str, Any]) -> ScrapingResult:
        """爬取单个学校的招生简章"""
        school_name = school_info['name']
        recruitment_url = school_info.get('recruitment_url')
        special_talent_url = school_info.get('special_talent_url')
        
        try:
            content_parts = []
            file_paths = []
            
            # 下载普通招生简章
            if recruitment_url:
                file_path = await self.download_recruitment_document(
                    recruitment_url, school_name, "招生简章"
                )
                if file_path:
                    file_paths.append(file_path)
                    text_content = await self.extract_text_from_file(file_path)
                    if text_content:
                        content_parts.append(f"=== 招生简章 ===\n{text_content}")
            
            # 下载特长生招生简章
            if special_talent_url:
                file_path = await self.download_recruitment_document(
                    special_talent_url, school_name, "特长生招生简章"
                )
                if file_path:
                    file_paths.append(file_path)
                    text_content = await self.extract_text_from_file(file_path)
                    if text_content:
                        content_parts.append(f"=== 特长生招生简章 ===\n{text_content}")
            
            # 合并内容
            combined_content = "\n\n".join(content_parts) if content_parts else None
            
            # 保存合并后的文本文件
            if combined_content:
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', school_name)
                text_file_path = self.data_dir / f"{safe_name}_完整招生简章.txt"
                
                async with aiofiles.open(text_file_path, 'w', encoding='utf-8') as f:
                    await f.write(combined_content)
                
                file_paths.append(str(text_file_path))
            
            return ScrapingResult(
                school_name=school_name,
                recruitment_url=recruitment_url,
                special_talent_url=special_talent_url,
                content=combined_content,
                file_path=file_paths[0] if file_paths else None,
                success=bool(combined_content),
                error_message=None,
            )
            
        except Exception as e:
            logger.error(f"爬取 {school_name} 招生简章失败: {e}")
            return ScrapingResult(
                school_name=school_name,
                recruitment_url=recruitment_url,
                special_talent_url=special_talent_url,
                content=None,
                file_path=None,
                success=False,
                error_message=str(e),
            )
    
    @monitor_performance()
    async def scrape_all_schools(self) -> List[ScrapingResult]:
        """爬取所有学校的招生简章"""
        try:
            # 获取主页面
            logger.info(f"开始爬取招生简章页面: {self.base_url}")
            html_content = await self.fetch_page(self.base_url)
            
            # 解析学校列表
            schools = await self.parse_school_list(html_content)
            
            if not schools:
                logger.warning("未找到任何学校信息")
                return []
            
            # 创建信号量限制并发数
            semaphore = asyncio.Semaphore(self.settings.scraper.max_concurrent_requests)
            
            async def scrape_with_semaphore(school_info):
                async with semaphore:
                    return await self.scrape_school_recruitment(school_info)
            
            # 并发爬取所有学校
            logger.info(f"开始并发爬取 {len(schools)} 所学校的招生简章")
            tasks = [scrape_with_semaphore(school) for school in schools]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            scraping_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"爬取第 {i+1} 所学校时发生异常: {result}")
                    scraping_results.append(ScrapingResult(
                        school_name=schools[i]['name'],
                        recruitment_url=schools[i].get('recruitment_url'),
                        special_talent_url=schools[i].get('special_talent_url'),
                        content=None,
                        file_path=None,
                        success=False,
                        error_message=str(result),
                    ))
                else:
                    scraping_results.append(result)
            
            # 统计结果
            successful = sum(1 for r in scraping_results if r.success)
            failed = len(scraping_results) - successful
            
            logger.info(f"爬取完成: 成功 {successful} 所，失败 {failed} 所")
            
            return scraping_results
            
        except Exception as e:
            logger.error(f"爬取所有学校招生简章失败: {e}")
            raise
    
    async def get_saved_files(self) -> List[Path]:
        """获取已保存的招生简章文件列表"""
        try:
            files = []
            document_processor = get_document_processor()
            
            for file_path in self.data_dir.iterdir():
                if file_path.is_file() and document_processor.is_supported(file_path):
                    files.append(file_path)
            
            logger.info(f"找到 {len(files)} 个已保存的招生简章文件")
            return files
            
        except Exception as e:
            logger.error(f"获取已保存文件列表失败: {e}")
            return []
