"""Pydantic数据验证模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SchoolBase(BaseModel):
    """学校基础模型"""
    full_name: str = Field(..., min_length=1, max_length=200, description="学校全称")
    location: Optional[str] = Field(None, max_length=200, description="办学地点")
    supervisor: Optional[str] = Field(None, max_length=200, description="主管部门")
    education_level: Optional[str] = Field(None, max_length=100, description="办学层次")
    institution_code: Optional[str] = Field(None, max_length=50, description="院校代号")
    institution_type: Optional[str] = Field(None, max_length=100, description="办学类型")
    is_demonstration: Optional[bool] = Field(None, description="是否是示范性院校")
    is_backbone: Optional[bool] = Field(None, description="是否是骨干院校")
    is_excellent: Optional[bool] = Field(None, description="是否是卓越院校")
    is_chuyi_high_level: Optional[bool] = Field(None, description="是否是楚怡高水平院校")
    advantage_majors: Optional[str] = Field(None, description="优势专业")
    advantage_basis: Optional[str] = Field(None, description="优势专业判断依据")
    raw_content: Optional[str] = Field(None, description="原始招生简章内容")
    source_url: Optional[str] = Field(None, max_length=500, description="招生简章来源URL")


class SchoolCreate(SchoolBase):
    """创建学校模型"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "湖南工业职业技术学院",
                "location": "湖南省长沙市",
                "supervisor": "湖南省教育厅",
                "education_level": "专科",
                "institution_code": "4143012425",
                "institution_type": "公办",
                "is_demonstration": True,
                "is_backbone": False,
                "is_excellent": False,
                "is_chuyi_high_level": True,
                "advantage_majors": "机械制造与自动化、数控技术、汽车检测与维修技术",
                "advantage_basis": "国家示范性高职院校重点建设专业",
                "source_url": "https://example.com/recruitment.pdf"
            }
        }
    )


class SchoolUpdate(BaseModel):
    """更新学校模型"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200, description="学校全称")
    location: Optional[str] = Field(None, max_length=200, description="办学地点")
    supervisor: Optional[str] = Field(None, max_length=200, description="主管部门")
    education_level: Optional[str] = Field(None, max_length=100, description="办学层次")
    institution_code: Optional[str] = Field(None, max_length=50, description="院校代号")
    institution_type: Optional[str] = Field(None, max_length=100, description="办学类型")
    is_demonstration: Optional[bool] = Field(None, description="是否是示范性院校")
    is_backbone: Optional[bool] = Field(None, description="是否是骨干院校")
    is_excellent: Optional[bool] = Field(None, description="是否是卓越院校")
    is_chuyi_high_level: Optional[bool] = Field(None, description="是否是楚怡高水平院校")
    advantage_majors: Optional[str] = Field(None, description="优势专业")
    advantage_basis: Optional[str] = Field(None, description="优势专业判断依据")
    raw_content: Optional[str] = Field(None, description="原始招生简章内容")
    source_url: Optional[str] = Field(None, max_length=500, description="招生简章来源URL")


class SchoolResponse(SchoolBase):
    """学校响应模型"""
    id: int = Field(..., description="学校ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class LLMAnalysisRequest(BaseModel):
    """LLM分析请求模型"""
    content: str = Field(..., min_length=1, description="招生简章内容")
    school_name: Optional[str] = Field(None, description="学校名称")
    source_url: Optional[str] = Field(None, description="来源URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "湖南工业职业技术学院2025年单独招生章程...",
                "school_name": "湖南工业职业技术学院",
                "source_url": "https://example.com/recruitment.pdf"
            }
        }
    )


class LLMAnalysisResponse(BaseModel):
    """LLM分析响应模型"""
    school_info: SchoolCreate = Field(..., description="解析出的学校信息")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    analysis_time: float = Field(..., description="分析耗时（秒）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "school_info": {
                    "full_name": "湖南工业职业技术学院",
                    "location": "湖南省长沙市",
                    "supervisor": "湖南省教育厅",
                    "education_level": "专科",
                    "institution_code": "4143012425",
                    "institution_type": "公办",
                    "is_demonstration": True,
                    "is_backbone": False,
                    "is_excellent": False,
                    "is_chuyi_high_level": True,
                    "advantage_majors": "机械制造与自动化、数控技术、汽车检测与维修技术",
                    "advantage_basis": "国家示范性高职院校重点建设专业"
                },
                "confidence": 0.95,
                "analysis_time": 2.5
            }
        }
    )


class ScrapingResult(BaseModel):
    """爬取结果模型"""
    school_name: str = Field(..., description="学校名称")
    recruitment_url: Optional[str] = Field(None, description="招生简章URL")
    special_talent_url: Optional[str] = Field(None, description="特长生招生简章URL")
    content: Optional[str] = Field(None, description="招生简章内容")
    file_path: Optional[str] = Field(None, description="保存的文件路径")
    success: bool = Field(..., description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "school_name": "湖南工业职业技术学院",
                "recruitment_url": "https://example.com/recruitment.pdf",
                "special_talent_url": "https://example.com/special_talent.pdf",
                "content": "招生简章内容...",
                "file_path": "招生简章/湖南工业职业技术学院_招生简章.txt",
                "success": True,
                "error_message": None
            }
        }
    )


class DatabaseOperationResult(BaseModel):
    """数据库操作结果模型"""
    success: bool = Field(..., description="操作是否成功")
    affected_rows: int = Field(default=0, description="影响的行数")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    execution_time: float = Field(..., description="执行时间（秒）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "affected_rows": 1,
                "error_message": None,
                "retry_count": 0,
                "execution_time": 0.15
            }
        }
    )
