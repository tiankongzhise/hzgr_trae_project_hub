
from pydantic import BaseModel, Field


from typing import List

class ClassifiedKeyword(BaseModel):
    '''
    args:
        level:分类层级
        keyword:关键词
        matched_rule:匹配的规则
        output_name:输出文件名称
        output_sheet_name:输出sheet名称
        parent_rule:父级规则
    '''
    level:int = Field(...,ge=1,description="分类层级")
    keyword:str = Field(...,min_length=1,description="关键词")
    matched_rule:str = Field(...,min_length=1,description="匹配的规则")
    output_name:str = Field(...,min_length=1,description="输出文件名称")
    output_sheet_name:str|None = Field(None,min_length=1,description="输出sheet名称")
    parent_rule:str|None = Field(None,min_length=1,description="父级规则")

class UnMatchedKeyword(BaseModel):
    '''
    args:
        keyword:关键词
        output_name:输出文件名称
        output_sheet_name:输出sheet名称
        level:分类层级
        parent_rule:父级规则
    '''
    keyword:str = Field(...,min_length=1,description="关键词")
    output_name:str = Field(...,min_length=1,description="输出文件名称,默认未匹配关键词")
    output_sheet_name:str = Field("未匹配关键词",min_length=1,description="输出sheet名称，默认Sheet1")
    level:int = Field(1,ge=1,description="分类层级")
    parent_rule:None = Field(None,description="容错，防止groupby报错")


class ClassifiedResult(BaseModel):
    classified_keywords: List[ClassifiedKeyword] = Field(..., min_length=1, description="分类结果")
    unclassified_keywords: List[UnMatchedKeyword] = Field(..., description="未分类关键词")
