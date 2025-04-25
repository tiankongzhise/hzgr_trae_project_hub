from decimal import Decimal
from .models import JhCostNew
from typing import Any
from datetime import date
from .database.models import JhCostNewTable,UniqueConstraint
from collections import defaultdict
def safe_compare(a, b)-> bool:
    if not isinstance(a, Decimal):
        a = Decimal(str(a))
    if not isinstance(b, Decimal):
        b = Decimal(str(b))
        
    # 规范化处理（去除不必要的尾随零）
    normalized_a = a.normalize()
    normalized_b = b.normalize()
    return normalized_a == normalized_b

def format_cost_data(data:Any)->Decimal:
    # 处理amount字段
    cost = data.get('amount',None)
    if cost:
        return Decimal(cost)
    
    # 处理cost字段
    cost = data.get('cost',None)
    if cost:
        return Decimal(cost)
    
    return Decimal(0.00)
def format_query_date(data:Any) -> str:
    date_item = data.get('date',None)
    if isinstance(date_item,str):
        return date_item
    if isinstance(date_item,date):
        return date_item.strftime('%Y-%m-%d')
    raise Exception('日期格式错误')
def format_db_query_data(data:list[JhCostNewTable])->list[JhCostNew]:
    result = []
    for item in data:
        temp_item = JhCostNew()
        temp_item.channel = item.channel
        temp_item.date = item.date.strftime('%Y-%m-%d')
        temp_item.sub_channel = item.sub_channel
        temp_item.school = item.school
        temp_item.cost = item.cost
        result.append(temp_item)
    return result
    

def format_query_data(data:list[dict])->list[JhCostNew]:
    result = []
    for item in data:
        temp_item = JhCostNew()
        temp_item.date = item.get('date')
        amount = item.get('amount','0')
        if amount is None:
            amount = '0'
        temp_item.cost = Decimal(amount)
        temp_item.channel = item.get('channel','')
        temp_item.sub_channel = item.get('subChannel','')
        temp_item.school = item.get('school','')
        result.append(temp_item)
    return result

def filter_data(source_data: list, compare_data: list, compare_cols: dict) -> list:
    # 用于存储新数据的列表
    new_data = []
    # 遍历 source_data 中的每个元素
    for source_item in source_data:
        is_new = True
        # 遍历 compare_data 中的每个元素
        for compare_item in compare_data:
            match = True
            # 遍历 compare_cols 中的每对列名
            for source_col, compare_col in compare_cols.items():
                # 获取 source_item 和 compare_item 中对应列的值
                source_value = source_item.get(source_col)
                compare_value = compare_item.get(compare_col)
                
                # 如果对应列的值不相等，则认为不匹配
                if source_value != compare_value:
                    match = False
                    
                    break
            if match:
                is_new = False
                print(f'source_item:{source_item}已存在,忽略')
                break
            
        # 如果没有找到匹配的元素，则将该元素添加到新数据列表中
        if is_new:
            new_data.append(source_item)
    return new_data

def get_unique_constraints(model):
    """正确获取模型的所有唯一约束"""
    # 方法1：通过表对象获取
    table = model.__table__
    constraints = []
    
    # 获取显式定义的 UniqueConstraint
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            constraints.append({
                'name': constraint.name,
                'columns': [col.name for col in constraint.columns]
            })
    
    # 获取隐式唯一索引 (unique=True 的列或索引)
    for index in table.indexes:
        if index.unique:
            constraints.append({
                'name': index.name,
                'columns': [col.name for col in index.columns]
            })
    
    return constraints

def filter_unique_conflicts(session, model, object_list):
    """
    过滤掉违反唯一约束的对象，保留第一个出现的对象
    
    :param session: SQLAlchemy session
    :param model: ORM 模型类
    :param object_list: 待检查的对象列表
    :return: (保留的对象列表, 冲突的对象列表)
    """
    # 获取模型的所有唯一约束
    unique_constraints = get_unique_constraints(model)
    
    # 如果没有唯一约束，直接返回原始列表
    if not unique_constraints:
        return object_list, []
    
    # 用于存储已存在的唯一键组合
    seen_keys = defaultdict(list)
    kept_objects = []
    conflict_objects = []
    
    for obj in object_list:
        is_conflict = False
        
        # 检查每个唯一约束
        for constraint in unique_constraints:
            # 获取当前对象的约束键值组合
            key_parts = []
            for col_name in constraint.columns:
                col_value = getattr(obj, col_name)
                key_parts.append(f"{col_name}={col_value}")
            
            constraint_key = tuple(key_parts)
            
            # 检查是否已存在相同键值
            if constraint_key in seen_keys[constraint.name]:
                is_conflict = True
                break
            
            # 检查数据库中是否已存在
            filters = []
            for col_name in constraint['columns']:
                col_value = getattr(obj, col_name)
                if col_value is None:
                    filters.append(getattr(model, col_name).is_(None))
                else:
                    filters.append(getattr(model, col_name) == col_value)
            if session.query(model).filter(*filters).first():
                is_conflict = True
                break
            
            # 标记为已存在
            seen_keys[constraint.name].append(constraint_key)
        
        if is_conflict:
            conflict_objects.append(obj)
        else:
            kept_objects.append(obj)
    
    return kept_objects, conflict_objects

# 使用示例
def process_objects_with_conflicts(session, model, objects):
    kept, conflicts = filter_unique_conflicts(session, model, objects)
    
    # 打印冲突警告
    for obj in conflicts:
        print(f"WARNING: 发现冲突对象 - {obj}")
    
    # 返回保留的对象
    return kept
        
    
