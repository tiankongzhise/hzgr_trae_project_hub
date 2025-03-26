from pydantic import BaseModel, field_validator, Field,FieldValidationInfo,model_validator


from typing import List, Optional, Callable, Any,Literal,Dict


__all__ = [
    "UnclassifiedKeywords",
    "SourceRules",
    'ClassifiedWord',
    'WorkFlowRule',
    'WorkFlowRules',
    'ClassifiedKeyword',
    'UnMatchedKeyword',
    'ClassifiedResult'
]


def _preprocess_text(text, error_callback=None):
    """预处理文本，清除不可见的干扰字符




    Args:




        text: 需要预处理的文本




        error_callback: 错误回调函数，用于将错误信息传递给UI显示




    Returns:




        清除干扰字符后的文本
    """

    if not text:
        return text

    # 定义需要清除的不可见字符列表

    invisible_chars = [
        0x200B,  # 零宽空格
        0x200C,  # 零宽非连接符
        0x200D,  # 零宽连接符
        0x200E,  # 从左至右标记
        0x200F,  # 从右至左标记
        0x202A,  # 从左至右嵌入
        0x202B,  # 从右至左嵌入
        0x202C,  # 弹出方向格式
        0x202D,  # 从左至右覆盖
        0x202E,  # 从右至左覆盖
        0x2060,  # 单词连接符
        0x2061,  # 函数应用
        0x2062,  # 隐形乘号
        0x2063,  # 隐形分隔符
        0x2064,  # 隐形加号
        0xFEFF,  # 零宽非断空格(BOM)
    ]

    """清理规则中的不可见字符并检查编码"""

    # 检查是否包含零宽空格等不可见字符

    has_invisible = False

    cleaned_rule = ""

    for char in text:
        code_point = ord(char)

        if code_point in invisible_chars:
            msg = f"发现不可见字符: U+{code_point:04X} 在规则 '{text}' 中"

            print(msg)

            if error_callback:
                error_callback(msg)

            has_invisible = True

            # 不添加这个字符到清理后的规则

        else:
            cleaned_rule += char

    # 如果规则被清理了，打印出来

    if has_invisible:
        msg1 = f"清理前: '{text}' (长度: {len(text)})"

        msg2 = f"清理后: '{cleaned_rule}' (长度: {len(cleaned_rule)})"

        print(msg1)

        print(msg2)

        if error_callback:
            error_callback(msg1)

            error_callback(msg2)

    return cleaned_rule if has_invisible else text


def _preserve_order_deduplicate(lst: List[str]) -> List[str]:
    """保序去重函数（兼容Python 3.6+）"""

    seen = set()

    return [x for x in lst if not (x in seen or seen.add(x))]


class UnclassifiedKeywords(BaseModel):
    data: List[str]

    trace_data: Optional[List[str]] = Field(
        None, exclude=True, description="原始输入关键词（用于审计跟踪）"
    )

    error_callback: Optional[Callable[[str], None]] = Field(
        None, exclude=True, description="错误信息回调函数"
    )

    @field_validator("data", mode='before')
    def processing_pipeline(cls, v: Any, info: FieldValidationInfo) -> List[str]:
        """处理流水线：类型转换 -> 预处理 -> 空值过滤 -> 保序去重"""

        # 类型安全转换

        if not isinstance(v, (list, tuple, set)):
            raise ValueError("输入必须是可迭代对象")

        # 保留原始数据

        keyword_list = [str(item) for item in v]

        info.data["trace_data"] = keyword_list

        # 预处理流水线

        error_callback = info.data.get("error_callback")

        processed = [
            _preprocess_text(keyword, error_callback).strip()  # 移除首尾空格
            for keyword in keyword_list
        ]

        # 空值过滤（包括空白字符）

        non_empty = [keyword for keyword in processed if keyword]

        # 保序去重逻辑

        return _preserve_order_deduplicate(non_empty)

    class Config:
        validate_assignment = True  # 允许在赋值时触发验证


class SourceRules(BaseModel):
    """增强版规则模型（包含预处理、去重、空值过滤）"""

    data: List[str] = Field(
        ..., min_length=1, description="经过预处理、去重且非空的规则列表"
    )

    trace_data: Optional[List[str]] = Field(
        None, exclude=True, description="原始输入规则（用于审计跟踪）"
    )

    error_callback: Optional[Callable[[str], None]] = Field(
        None, exclude=True, description="错误信息回调函数"
    )

    @field_validator("data", mode='before')
    def processing_pipeline(cls, v: Any, info:FieldValidationInfo) -> List[str]:
        """处理流水线：类型转换 -> 预处理 -> 空值过滤 -> 保序去重"""

        # 类型安全转换

        if not isinstance(v, (list, tuple, set)):
            raise ValueError("输入必须是可迭代对象")

        # 保留原始数据

        raw_rules = [str(item) for item in v]

        info.data["trace_data"] = raw_rules

        # 预处理流水线

        error_callback = info.data.get("error_callback")

        processed = [
            _preprocess_text(rule, error_callback).strip()  # 移除首尾空格
            for rule in raw_rules
        ]

        # 空值过滤（包括空白字符）

        non_empty = [rule for rule in processed if rule]

        # 保序去重逻辑

        return _preserve_order_deduplicate(non_empty)

    class Config:
        validate_assignment = True

class ClassifiedWord(BaseModel):
    '''中间状态'''
    keyword: str
    matched_rule:str

class WorkFlowRule(BaseModel):
    '''
    args:
        source_sheet_name:来源工作表名称
        rule:分类规则
        output_name:分类结果表名称
        classified_sheet_name:分类结果sheet名称
        parent_rule:父级规则
        level:工作流层级
    '''
    level:int = Field(...,ge=1,description="工作流层级")# 工作流层级
    source_sheet_name:str = Field(...,min_length=1,description="来源工作表名称")# 工作流来源工作表名称
    rule:str = Field(...,min_length=1,description="分类规则")# 分类规则
    output_name:str = Field(...,min_length=1,description="分类结果表名称")# 分类结果表名称
    classified_sheet_name:str|None = Field(None,min_length=1,description="分类结果sheet名称")# 分类结果sheet名称
    parent_rule:str|None = Field(None,min_length=1,description="父级规则")# 父级规则
    
    
    @model_validator(mode = 'after')
    def validate_rules(self)->'WorkFlowRule':
        """验证工作流规则"""
        err_msg = []
        if self.level > 1 and not self.classified_sheet_name:
            err_msg.append(f"工作流规则 {self.rule} 的流程层级大于1，但没有指定分类结果sheet名称,self is {self}")
        if self.level > 3 and not self.parent_rule:
            err_msg.append(f"工作流规则 {self.rule} 的流程层级为2，但指定没有指定父规则,self is {self}")

        if err_msg:
            raise ValueError("\n".join(err_msg))
        return self

class WorkFlowRules(BaseModel):
    '''
    args:
        rules:工作流规则列表
        workFlowRlue:
            args:
                source_sheet_name:来源工作表名称
                rule:分类规则
                output_name:分类结果表名称
                classified_sheet_name:分类结果sheet名称
                parent_rule:父级规则
                level:工作流层级
    '''
    rules:List[WorkFlowRule] = Field(...,min_length=1,description="工作流规则") 
    
    def __getitem__(self, key: str) -> 'WorkFlowRules':
        """通过sheet名称获取对应的工作流规则列表"""
        rules = [rule for rule in self.rules if rule.source_sheet_name == key]
        if rules:
            return WorkFlowRules(rules=rules)
    
    def get_rules_by_level(self, level: int) -> 'WorkFlowRules':
        """通过层级获取对应的工作流规则列表"""
        rules = [rule for rule in self.rules if rule.level == level]
        if rules:
            return WorkFlowRules(rules=rules)
    
    def get_child_rules(self, parent_rule: str) -> 'WorkFlowRules':
        """获取指定父规则的所有子规则"""
        rules = [rule for rule in self.rules if rule.parent_rule == parent_rule]
        if rules:
            return WorkFlowRules(rules=rules)
    def filter_rules(self, **conditions: Any) -> 'WorkFlowRules':
        """
        返回满足任意条件组合的 WorkFlowRule 列表。
        Conditions:
            source_sheet_name: 来源工作表名称

            rule: 分类规则

            output_name: 分类结果表名称

            classified_sheet_name: 分类结果sheet名称

            parent_rule: 父级规则

            level: 工作流层级

        Args:
            **conditions: 条件字典，键为 WorkFlowRule 的字段名，值为期望的值或条件函数。
                         例如: `source_sheet_name="Sheet1"` 或 `level=lambda x: x > 2`
        
        Returns:
            WorkFlowRules: 满足条件的WorkFlowRules
        """
        filtered_rules = []
        
        for rule in self.rules:
            match = True
            for field, condition in conditions.items():
                if not hasattr(rule, field):
                    raise ValueError(f"Invalid field: '{field}' is not a valid field of WorkFlowRule")
                
                value = getattr(rule, field)
                # 如果条件是函数（如 lambda），则调用它进行判断
                if callable(condition):
                    if not condition(value):
                        match = False
                        break
                # 否则直接比较值
                elif value != condition:
                    match = False
                    break
            
            if match:
                filtered_rules.append(rule)
        
        return WorkFlowRules(rules=filtered_rules)  

    @model_validator(mode = 'after')    
    def validate_rules(self)->'WorkFlowRules':
        """验证工作流规则"""
        err_msg = []
        check = []
        for rule in self.rules:
            check.append(f'{rule.output_name}-{rule.rule}-{rule.classified_sheet_name}')
        if len(check) != len(set(check)):
            count = [ check[i] for i, x in enumerate(check) if check.count(x) > 1]
            err_msg.append(f"工作流规则有重复{set(count)}")
        if err_msg:
            raise ValueError("\n".join(err_msg))
        return self


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
    
    def group_by_output_name(self,match_type:Literal['match','unmatch']='match') -> dict[str, List[ClassifiedKeyword]]:
        """按输出文件名聚类"""
        result = {}
        data = None
        if match_type == 'match':
            data = self.classified_keywords
        elif match_type == 'unmatch':
            data = self.unclassified_keywords
        for keyword in data:
            if keyword.output_name not in result:
                result[keyword.output_name] = []
            result[keyword.output_name].append(keyword)
        return result
    
    def group_by_output_name_and_sheet(self,match_type:Literal['match','unmatch']='match') -> dict[tuple[str, str], List[ClassifiedKeyword]]:
        """按输出文件名和sheet名聚类"""
        result = {}
        data = None
        if match_type == 'match':
            data = self.classified_keywords
        elif match_type == 'unmatch':
            data = self.unclassified_keywords
        for keyword in data:
            key = (keyword.output_name, keyword.output_sheet_name or "默认sheet")
            if key not in result:
                result[key] = []
            result[key].append(keyword)
        return result
    
    def group_by_output_name_sheet_and_parent(self,match_type:Literal['match','unmatch']='match') -> dict[tuple[str, str, str], List[ClassifiedKeyword]]:
        """按输出文件名、sheet名和父规则聚类"""
        result = {}
        data = None
        if match_type == 'match':
            data = self.classified_keywords
        elif match_type == 'unmatch':
            data = self.unclassified_keywords
        
        
        for keyword in data:
            key = (
                keyword.output_name, 
                keyword.output_sheet_name or "默认sheet",
                keyword.parent_rule or "无父规则"
            )
            if key not in result:
                result[key] = []
            result[key].append(keyword)
        return result
    
    def get_grouped_keywords(self, group_by: Literal['output_name','sheet','parent_rule'] = "output_name",match_type:Literal['match','unmatch']='match') -> dict[str|tuple,List[ClassifiedKeyword|UnclassifiedKeywords]]:
        """获取聚类结果
        
        Args:
            group_by: 聚类方式，可选值：
                - output_name: 按输出文件名聚类
                - sheet: 按输出文件名和sheet名聚类
                - parent_rule: 按输出文件名、sheet名和父规则聚类
        """
        group_methods = {
            "output_name": self.group_by_output_name,
            "sheet": self.group_by_output_name_and_sheet,
            "parent_rule": self.group_by_output_name_sheet_and_parent
        }
        
        if group_by not in group_methods:
            raise ValueError(f"不支持的聚类方式: {group_by}，支持的聚类方式: {list(group_methods.keys())}")
            
        return group_methods[group_by](match_type)
    
    
