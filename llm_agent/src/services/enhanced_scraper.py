#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

import httpx
import aiofiles
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models.schemas import ScrapingResult, SchoolCreate
from ..services.database_service import DatabaseService
from ..utils.decorators import monitor_performance, retry_on_failure
from ..utils.logger import get_logger
from ..utils.retry import retry_network_request
from ..utils.document_processor import get_document_processor

logger = get_logger(__name__)


class EnhancedRecruitmentScraper:
    """增强版招生简章爬取器 - 支持数据库存储和并发下载"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = "http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/web/ks_index.html"
        self.data_dir = self.settings.data_dir
        self.db_service: Optional[DatabaseService] = None
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._init_client()
        await self._init_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._close_client()
        if self.db_service:
            await self.db_service.close()
    
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
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                },
                follow_redirects=True,
                verify=ssl_context  # 使用自定义SSL上下文
            )
            logger.info("HTTP客户端已初始化（使用宽松SSL配置）")
    
    async def _init_database(self):
        """初始化数据库服务"""
        self.db_service = DatabaseService()
        await self.db_service.test_connection()
        logger.info("数据库服务已初始化")
    
    async def _close_client(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("HTTP客户端已关闭")
    
    @monitor_performance()
    async def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        if not self.client:
            await self._init_client()
        
        try:
            async def _fetch():
                response = await self.client.get(url)
                response.raise_for_status()
                return response.text
            
            content = await retry_network_request(_fetch)
            logger.debug(f"成功获取页面: {url}")
            return content
            
        except Exception as e:
            logger.error(f"获取页面失败 {url}: {e}")
            raise
    
    def parse_school_list_from_html(self, html: str) -> List[Dict[str, Any]]:
        """解析HTML，提取学校信息 - 基于parse_school.py的逻辑"""
        soup = BeautifulSoup(html, "lxml")
        # 定位主表格（通过width=90%匹配）
        main_table = soup.find("table", width="90%")
        if not main_table:
            logger.warning("未找到学校信息表格")
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
                normal_url = urljoin(self.base_url, links[0].get("href", ""))  # 普通简章链接
                if len(links) >= 2:
                    special_url = urljoin(self.base_url, links[1].get("href", ""))  # 特长生简章链接
            
            if school_name and (normal_url or special_url):
                schools.append({
                    "name": school_name,
                    "recruitment_url": normal_url,
                    "special_talent_url": special_url
                })
        
        logger.info(f"解析到 {len(schools)} 所学校的信息")
        return schools
    
    async def get_schools_from_database(self) -> List[Dict[str, Any]]:
        """从数据库获取学校信息"""
        try:
            schools_data = await self.db_service.get_all_schools()
            schools = []
            for school in schools_data:
                schools.append({
                    "name": school.full_name,
                    "recruitment_url": school.source_url,
                    "special_talent_url": None,  # 数据库中暂时没有特长生链接字段
                    "id": school.id
                })
            logger.info(f"从数据库获取到 {len(schools)} 所学校的信息")
            return schools
        except Exception as e:
            logger.error(f"从数据库获取学校信息失败: {e}")
            return []
    
    async def save_schools_to_database(self, schools: List[Dict[str, Any]]) -> None:
        """保存学校信息到数据库"""
        try:
            for school in schools:
                school_data = SchoolCreate(
                    full_name=school["name"],
                    source_url=school.get("recruitment_url"),
                    raw_content=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # 检查是否已存在
                existing = await self.db_service.get_school_by_name(school["name"])
                if not existing:
                    await self.db_service.create_school(school_data)
                    logger.debug(f"保存学校信息到数据库: {school['name']}")
                else:
                    logger.debug(f"学校已存在于数据库: {school['name']}")
            
            logger.info(f"完成学校信息数据库保存")
        except Exception as e:
            logger.error(f"保存学校信息到数据库失败: {e}")
    
    @monitor_performance()
    async def get_or_parse_schools(self) -> List[Dict[str, Any]]:
        """获取或解析学校信息 - 优先从数据库获取，否则重新解析"""
        # 先尝试从数据库获取
        schools = await self.get_schools_from_database()
        
        if not schools:
            logger.info("数据库中没有学校信息，开始解析网页")
            # 从网页解析
            html_content = await self.fetch_page(self.base_url)
            schools = self.parse_school_list_from_html(html_content)
            
            # 保存到数据库
            if schools:
                await self.save_schools_to_database(schools)
        else:
            logger.info("从数据库获取到学校信息")
        
        return schools
    
    @monitor_performance()
    async def download_document(self, url: str, school_name: str, doc_type: str = "招生简章") -> Tuple[Optional[str], Optional[str]]:
        """下载文档并返回内容和文件路径"""
        if not self.client:
            await self._init_client()
        
        try:
            async def _download():
                response = await self.client.get(url)
                response.raise_for_status()
                return response.content, response.headers.get('content-type', '')
            
            content, content_type = await retry_network_request(_download)
            
            # 确定文件扩展名
            parsed_url = urlparse(url)
            file_extension = Path(parsed_url.path).suffix.lower()
            
            if not file_extension:
                if 'pdf' in content_type.lower():
                    file_extension = '.pdf'
                elif 'word' in content_type.lower() or 'msword' in content_type.lower():
                    file_extension = '.doc'
                elif 'officedocument' in content_type.lower():
                    file_extension = '.docx'
                else:
                    file_extension = '.txt'
            
            # 生成文件名
            safe_school_name = re.sub(r'[<>:"/\\|?*]', '_', school_name)
            filename = f"{safe_school_name}_{doc_type}{file_extension}"
            file_path = self.data_dir / filename
            
            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # 提取文本内容
            processor = get_document_processor()
            text_content = await processor.extract_text(file_path)
            
            logger.info(f"成功下载并处理文档: {filename}")
            return text_content, str(file_path)
            
        except Exception as e:
            logger.error(f"下载文档失败 {url}: {e}")
            return None, None
    
    async def scrape_single_school(self, school_info: Dict[str, Any]) -> ScrapingResult:
        """爬取单个学校的招生简章"""
        school_name = school_info['name']
        recruitment_url = school_info.get('recruitment_url')
        special_talent_url = school_info.get('special_talent_url')
        
        try:
            content_parts = []
            file_paths = []
            
            # 下载普通招生简章
            if recruitment_url:
                content, file_path = await self.download_document(recruitment_url, school_name, "招生简章")
                if content:
                    content_parts.append(f"招生简章:\n{content}")
                if file_path:
                    file_paths.append(file_path)
            
            # 下载特长生招生简章
            if special_talent_url:
                content, file_path = await self.download_document(special_talent_url, school_name, "特长生招生简章")
                if content:
                    content_parts.append(f"特长生招生简章:\n{content}")
                if file_path:
                    file_paths.append(file_path)
            
            # 合并内容
            final_content = "\n\n".join(content_parts) if content_parts else None
            final_file_path = "; ".join(file_paths) if file_paths else None
            
            success = bool(final_content)
            error_message = None if success else "无法下载任何文档"
            
            return ScrapingResult(
                school_name=school_name,
                recruitment_url=recruitment_url,
                special_talent_url=special_talent_url,
                content=final_content,
                file_path=final_file_path,
                success=success,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"爬取学校 {school_name} 失败: {e}")
            return ScrapingResult(
                school_name=school_name,
                recruitment_url=recruitment_url,
                special_talent_url=special_talent_url,
                content=None,
                file_path=None,
                success=False,
                error_message=str(e)
            )
    
    @monitor_performance()
    async def scrape_schools_concurrent(self, schools: List[Dict[str, Any]], max_concurrent: int = 5) -> List[ScrapingResult]:
        """并发爬取多个学校的招生简章"""
        if not schools:
            return []
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(school_info):
            async with semaphore:
                return await self.scrape_single_school(school_info)
        
        logger.info(f"开始并发爬取 {len(schools)} 所学校的招生简章，最大并发数: {max_concurrent}")
        
        # 创建任务
        tasks = [scrape_with_semaphore(school) for school in schools]
        
        # 执行并发任务
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
                    error_message=str(result)
                ))
            else:
                scraping_results.append(result)
        
        # 统计结果
        successful = sum(1 for r in scraping_results if r.success)
        failed = len(scraping_results) - successful
        
        logger.info(f"并发爬取完成: 成功 {successful} 所，失败 {failed} 所")
        return scraping_results
    
    @monitor_performance()
    async def scrape_all_schools(self, max_concurrent: int = 5) -> List[ScrapingResult]:
        """爬取所有学校的招生简章"""
        try:
            # 获取学校列表
            schools = await self.get_or_parse_schools()
            
            if not schools:
                logger.warning("未找到任何学校信息")
                return []
            
            # 并发爬取
            results = await self.scrape_schools_concurrent(schools, max_concurrent)
            
            return results
            
        except Exception as e:
            logger.error(f"爬取所有学校失败: {e}")
            raise
    
    async def test_download_sample(self, sample_count: int = 5) -> Dict[str, Any]:
        """测试下载样本学校的招生简章"""
        try:
            schools = await self.get_or_parse_schools()
            
            if not schools:
                return {"success": False, "error": "没有找到学校信息"}
            
            # 选择样本学校
            sample_schools = schools[:sample_count]
            
            # 分别测试普通招生简章和特长生招生简章
            normal_urls = [s for s in sample_schools if s.get('recruitment_url')]
            special_urls = [s for s in sample_schools if s.get('special_talent_url')]
            
            logger.info(f"测试下载 {len(normal_urls)} 个普通招生简章和 {len(special_urls)} 个特长生招生简章")
            
            # 并发测试下载
            results = await self.scrape_schools_concurrent(sample_schools, max_concurrent=3)
            
            # 统计结果
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            return {
                "success": True,
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
                "normal_urls_tested": len(normal_urls),
                "special_urls_tested": len(special_urls)
            }
            
        except Exception as e:
            logger.error(f"测试下载失败: {e}")
            return {"success": False, "error": str(e)}
