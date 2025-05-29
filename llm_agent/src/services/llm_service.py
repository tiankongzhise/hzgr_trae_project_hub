"""LLM服务模块"""

import json
import time
from typing import Optional, Dict, Any, List

from openai import AsyncOpenAI
from pydantic import ValidationError

from ..config import get_settings
from ..models.schemas import (
    LLMAnalysisRequest,
    LLMAnalysisResponse,
    SchoolCreate,
)
from ..utils.decorators import monitor_performance, retry_on_failure
from ..utils.logger import get_logger
from ..utils.retry import retry_llm_call

logger = get_logger(__name__)


class LLMService:
    """LLM服务类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[AsyncOpenAI] = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        self.client = AsyncOpenAI(
            base_url=self.settings.llm.base_url,
            api_key=self.settings.llm.api_key,
            timeout=self.settings.llm.timeout,
        )
        logger.info("LLM客户端已初始化")
    
    def _build_analysis_prompt(self, content: str, school_name: Optional[str] = None) -> str:
        """构建分析提示词"""
        prompt = f"""
你是一个专业的教育信息分析专家，请仔细分析以下招生简章内容，提取出结构化的学校信息。

请从招生简章中提取以下信息：
1. 学校全称（完整的官方名称）
2. 办学地点（具体的地址或所在城市）
3. 主管部门（如教育厅、教育部等）
4. 办学层次（如专科、本科等）
5. 院校代号（招生代码）
6. 办学类型（如公办、民办等）
7. 是否是示范性院校（布尔值）
8. 是否是骨干院校（布尔值）
9. 是否是卓越院校（布尔值）
10. 是否是楚怡高水平院校（布尔值）
11. 优势专业（列出主要的优势专业）
12. 优势专业判断依据（说明为什么这些是优势专业）

请以JSON格式返回结果，格式如下：
{{
    "full_name": "学校全称",
    "location": "办学地点",
    "supervisor": "主管部门",
    "education_level": "办学层次",
    "institution_code": "院校代号",
    "institution_type": "办学类型",
    "is_demonstration": true/false,
    "is_backbone": true/false,
    "is_excellent": true/false,
    "is_chuyi_high_level": true/false,
    "advantage_majors": "优势专业列表",
    "advantage_basis": "优势专业判断依据"
}}

注意事项：
1. 如果某个信息在招生简章中没有明确提及，请设置为null
2. 布尔值字段请根据文档中的明确表述来判断，不确定时设置为null
3. 优势专业请列出文档中明确提到的重点专业、特色专业或优势专业
4. 判断依据请基于文档中的具体描述，如"国家示范性专业"、"省级特色专业"等

招生简章内容：
{content}
"""
        
        if school_name:
            prompt += f"\n\n提示：这是 {school_name} 的招生简章。"
        
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
                    model=self.settings.llm.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的教育信息分析专家，擅长从招生简章中提取结构化信息。请严格按照要求的JSON格式返回结果。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.settings.llm.max_tokens,
                    temperature=self.settings.llm.temperature,
                )
                return response.choices[0].message.content
            
            # 使用重试机制调用LLM
            llm_response = await retry_llm_call(_call_llm)
            
            # 解析JSON响应
            try:
                # 提取JSON部分（可能包含在代码块中）
                json_str = llm_response.strip()
                if json_str.startswith('```json'):
                    json_str = json_str[7:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                json_str = json_str.strip()
                
                parsed_data = json.loads(json_str)
                
                # 添加原始内容和来源URL
                parsed_data['raw_content'] = request.content
                parsed_data['source_url'] = request.source_url
                
                # 验证数据
                school_info = SchoolCreate(**parsed_data)
                
                analysis_time = time.time() - start_time
                
                # 计算置信度（简单的启发式方法）
                confidence = self._calculate_confidence(school_info, request.content)
                
                logger.info(
                    f"LLM分析完成: {school_info.full_name}, 耗时 {analysis_time:.2f}秒, 置信度 {confidence:.2f}"
                )
                
                return LLMAnalysisResponse(
                    school_info=school_info,
                    confidence=confidence,
                    analysis_time=analysis_time,
                )
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"解析LLM响应失败: {e}")
                logger.error(f"LLM原始响应: {llm_response}")
                raise ValueError(f"LLM响应格式错误: {e}")
                
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"LLM分析失败: {e}, 耗时 {analysis_time:.2f}秒")
            raise
    
    def _calculate_confidence(self, school_info: SchoolCreate, original_content: str) -> float:
        """计算分析结果的置信度"""
        confidence_score = 0.0
        total_fields = 0
        
        # 检查必填字段
        if school_info.full_name:
            confidence_score += 0.3
            # 检查学校名称是否在原文中出现
            if school_info.full_name in original_content:
                confidence_score += 0.1
        total_fields += 1
        
        # 检查其他重要字段
        important_fields = [
            'location', 'supervisor', 'education_level', 
            'institution_code', 'institution_type'
        ]
        
        for field in important_fields:
            value = getattr(school_info, field)
            if value:
                confidence_score += 0.1
                # 检查字段值是否在原文中出现
                if str(value) in original_content:
                    confidence_score += 0.02
            total_fields += 1
        
        # 检查布尔字段
        boolean_fields = [
            'is_demonstration', 'is_backbone', 
            'is_excellent', 'is_chuyi_high_level'
        ]
        
        for field in boolean_fields:
            value = getattr(school_info, field)
            if value is not None:
                confidence_score += 0.05
            total_fields += 1
        
        # 检查优势专业相关字段
        if school_info.advantage_majors:
            confidence_score += 0.1
        if school_info.advantage_basis:
            confidence_score += 0.1
        total_fields += 2
        
        # 标准化置信度分数
        max_possible_score = 1.0
        normalized_confidence = min(confidence_score / max_possible_score, 1.0)
        
        return round(normalized_confidence, 2)
    
    @monitor_performance()
    async def batch_analyze(self, requests: List[LLMAnalysisRequest]) -> List[LLMAnalysisResponse]:
        """批量分析招生简章"""
        results = []
        
        for i, request in enumerate(requests):
            try:
                logger.info(f"正在分析第 {i+1}/{len(requests)} 个招生简章: {request.school_name or '未知学校'}")
                result = await self.analyze_recruitment_content(request)
                results.append(result)
                
                # 添加延迟以避免API限流
                if i < len(requests) - 1:  # 不是最后一个
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"分析第 {i+1} 个招生简章失败: {e}")
                # 创建一个失败的响应
                error_response = LLMAnalysisResponse(
                    school_info=SchoolCreate(
                        full_name=request.school_name or "解析失败",
                        raw_content=request.content,
                        source_url=request.source_url,
                    ),
                    confidence=0.0,
                    analysis_time=0.0,
                )
                results.append(error_response)
        
        successful = sum(1 for r in results if r.confidence > 0)
        logger.info(f"批量分析完成: 成功 {successful}/{len(requests)} 个")
        
        return results
    
    @monitor_performance()
    async def validate_analysis_result(self, result: LLMAnalysisResponse) -> Dict[str, Any]:
        """验证分析结果的质量"""
        validation_report = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
        }
        
        school_info = result.school_info
        
        # 检查必填字段
        if not school_info.full_name or len(school_info.full_name.strip()) < 3:
            validation_report["errors"].append("学校全称缺失或过短")
            validation_report["is_valid"] = False
        
        # 检查置信度
        if result.confidence < 0.3:
            validation_report["warnings"].append(f"置信度较低: {result.confidence}")
        
        # 检查关键信息完整性
        missing_fields = []
        if not school_info.location:
            missing_fields.append("办学地点")
        if not school_info.supervisor:
            missing_fields.append("主管部门")
        if not school_info.institution_type:
            missing_fields.append("办学类型")
        
        if missing_fields:
            validation_report["warnings"].append(f"缺少关键信息: {', '.join(missing_fields)}")
        
        # 检查逻辑一致性
        if school_info.education_level and "本科" in school_info.education_level:
            if school_info.institution_code and len(school_info.institution_code) != 10:
                validation_report["warnings"].append("本科院校代码通常为10位数字")
        
        # 提供改进建议
        if not school_info.advantage_majors:
            validation_report["suggestions"].append("建议补充优势专业信息")
        
        if not school_info.advantage_basis:
            validation_report["suggestions"].append("建议补充优势专业判断依据")
        
        return validation_report
    
    async def close(self):
        """关闭LLM客户端"""
        if self.client:
            await self.client.close()
            logger.info("LLM客户端已关闭")


# 导入asyncio（在文件顶部添加）
import asyncio
