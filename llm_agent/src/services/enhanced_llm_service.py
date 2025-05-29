#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from openai import AsyncOpenAI
from pydantic import ValidationError

from ..config import get_settings
from ..models.schemas import (
    LLMAnalysisRequest, LLMAnalysisResponse, SchoolCreate, ScrapingResult
)
from ..utils.decorators import monitor_performance, retry_on_failure
from ..utils.logger import get_logger
from ..utils.retry import retry_llm_call

logger = get_logger(__name__)


class EnhancedLLMService:
    """增强版LLM服务 - 支持并发查询"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.llm.api_key,
            base_url=self.settings.llm.base_url
        )
        self.model = self.settings.llm.model
        self.max_tokens = self.settings.llm.max_tokens
        self.temperature = self.settings.llm.temperature
    
    def _build_analysis_prompt(self, content: str, school_name: Optional[str] = None) -> str:
        """构建分析提示词"""
        prompt = f"""
请分析以下招生简章内容，提取关键信息并以JSON格式返回。

招生简章内容：
{content}

请提取以下信息：
1. 学校全称 (full_name)
2. 办学地点 (location)
3. 主管部门 (supervisor)
4. 办学层次 (education_level)
5. 院校代号 (institution_code)
6. 办学类型 (institution_type)
7. 是否是示范性院校 (is_demonstration)
8. 是否是骨干院校 (is_backbone)
9. 是否是卓越院校 (is_excellent)
10. 是否是楚怡高水平院校 (is_chuyi_high_level)
11. 优势专业 (advantage_majors)
12. 优势专业判断依据 (advantage_basis)

请返回标准的JSON格式，布尔值用true/false，字符串用双引号，如果某个字段无法确定请设为null。

示例格式：
{{
    "full_name": "湖南工业职业技术学院",
    "location": "湖南省长沙市",
    "supervisor": "湖南省教育厅",
    "education_level": "专科",
    "institution_code": "4143012425",
    "institution_type": "公办",
    "is_demonstration": true,
    "is_backbone": false,
    "is_excellent": false,
    "is_chuyi_high_level": true,
    "advantage_majors": "机械制造与自动化、数控技术、汽车检测与维修技术",
    "advantage_basis": "国家示范性高职院校重点建设专业"
}}
"""
        return prompt
    
    @monitor_performance()
    async def analyze_recruitment_content(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """分析招生简章内容"""
        start_time = time.time()
        
        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(request.content, request.school_name)
            
            # 调用LLM
            async def _call_llm():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的教育信息分析助手，擅长从招生简章中提取结构化信息。请严格按照要求的JSON格式返回结果。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
                return response
            
            response = await retry_llm_call(_call_llm)
            
            # 解析响应
            content = response.choices[0].message.content
            
            try:
                # 解析JSON
                parsed_data = json.loads(content)
                
                # 验证和转换数据
                school_info = SchoolCreate(
                    full_name=parsed_data.get('full_name', request.school_name or '未知学校'),
                    location=parsed_data.get('location'),
                    supervisor=parsed_data.get('supervisor'),
                    education_level=parsed_data.get('education_level'),
                    institution_code=parsed_data.get('institution_code'),
                    institution_type=parsed_data.get('institution_type'),
                    is_demonstration=parsed_data.get('is_demonstration'),
                    is_backbone=parsed_data.get('is_backbone'),
                    is_excellent=parsed_data.get('is_excellent'),
                    is_chuyi_high_level=parsed_data.get('is_chuyi_high_level'),
                    advantage_majors=parsed_data.get('advantage_majors'),
                    advantage_basis=parsed_data.get('advantage_basis'),
                    raw_content=request.content,
                    source_url=request.source_url
                )
                
                # 计算置信度
                confidence = self._calculate_confidence(parsed_data, request.content)
                
                analysis_time = time.time() - start_time
                
                logger.info(f"LLM分析完成: {school_info.full_name}, 置信度: {confidence:.2f}, 耗时: {analysis_time:.2f}秒")
                
                return LLMAnalysisResponse(
                    school_info=school_info,
                    confidence=confidence,
                    analysis_time=analysis_time
                )
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"解析LLM响应失败: {e}")
                logger.debug(f"原始响应内容: {content}")
                
                # 创建默认响应
                school_info = SchoolCreate(
                    full_name=request.school_name or '解析失败',
                    raw_content=request.content,
                    source_url=request.source_url
                )
                
                return LLMAnalysisResponse(
                    school_info=school_info,
                    confidence=0.0,
                    analysis_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            
            # 创建错误响应
            school_info = SchoolCreate(
                full_name=request.school_name or '分析失败',
                raw_content=request.content,
                source_url=request.source_url
            )
            
            return LLMAnalysisResponse(
                school_info=school_info,
                confidence=0.0,
                analysis_time=time.time() - start_time
            )
    
    def _calculate_confidence(self, parsed_data: Dict[str, Any], content: str) -> float:
        """计算分析置信度"""
        confidence = 0.0
        total_fields = 0
        
        # 重要字段权重
        important_fields = [
            'full_name', 'location', 'supervisor', 'education_level', 
            'institution_code', 'institution_type'
        ]
        
        for field in important_fields:
            total_fields += 1
            if parsed_data.get(field) and parsed_data[field] != 'null':
                confidence += 0.15
        
        # 布尔字段
        bool_fields = [
            'is_demonstration', 'is_backbone', 'is_excellent', 'is_chuyi_high_level'
        ]
        
        for field in bool_fields:
            total_fields += 1
            if parsed_data.get(field) is not None:
                confidence += 0.05
        
        # 专业信息
        if parsed_data.get('advantage_majors'):
            confidence += 0.1
        if parsed_data.get('advantage_basis'):
            confidence += 0.1
        
        # 内容长度加分
        if len(content) > 1000:
            confidence += 0.1
        elif len(content) > 500:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    async def analyze_scraping_result(self, result: ScrapingResult) -> Optional[LLMAnalysisResponse]:
        """分析爬取结果"""
        if not result.success or not result.content:
            logger.warning(f"跳过分析失败的爬取结果: {result.school_name}")
            return None
        
        request = LLMAnalysisRequest(
            content=result.content,
            school_name=result.school_name,
            source_url=result.recruitment_url
        )
        
        return await self.analyze_recruitment_content(request)
    
    @monitor_performance()
    async def analyze_multiple_concurrent(self, 
                                        results: List[ScrapingResult], 
                                        max_concurrent: int = 3) -> List[Optional[LLMAnalysisResponse]]:
        """并发分析多个爬取结果"""
        if not results:
            return []
        
        # 过滤成功的结果
        valid_results = [r for r in results if r.success and r.content]
        
        if not valid_results:
            logger.warning("没有有效的爬取结果可供分析")
            return []
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(result):
            async with semaphore:
                return await self.analyze_scraping_result(result)
        
        logger.info(f"开始并发分析 {len(valid_results)} 个爬取结果，最大并发数: {max_concurrent}")
        
        # 创建任务
        tasks = [analyze_with_semaphore(result) for result in valid_results]
        
        # 执行并发任务
        analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        final_results = []
        for i, result in enumerate(analysis_results):
            if isinstance(result, Exception):
                logger.error(f"分析第 {i+1} 个结果时发生异常: {result}")
                final_results.append(None)
            else:
                final_results.append(result)
        
        # 统计结果
        successful = sum(1 for r in final_results if r is not None)
        failed = len(final_results) - successful
        
        logger.info(f"并发分析完成: 成功 {successful} 个，失败 {failed} 个")
        return final_results
    
    async def test_concurrent_analysis(self, sample_results: List[ScrapingResult]) -> Dict[str, Any]:
        """测试并发分析功能"""
        try:
            start_time = time.time()
            
            # 并发分析
            analysis_results = await self.analyze_multiple_concurrent(sample_results, max_concurrent=3)
            
            total_time = time.time() - start_time
            
            # 统计结果
            successful = sum(1 for r in analysis_results if r is not None)
            failed = len(analysis_results) - successful
            
            # 计算平均置信度
            valid_results = [r for r in analysis_results if r is not None]
            avg_confidence = sum(r.confidence for r in valid_results) / len(valid_results) if valid_results else 0.0
            
            return {
                "success": True,
                "total": len(analysis_results),
                "successful": successful,
                "failed": failed,
                "total_time": total_time,
                "avg_time_per_analysis": total_time / len(analysis_results) if analysis_results else 0,
                "avg_confidence": avg_confidence,
                "results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"测试并发分析失败: {e}")
            return {"success": False, "error": str(e)}
