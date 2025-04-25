from decimal import Decimal
from .models import JhCostNew
from typing import Any
from datetime import date
from .database.models import JhCostNewTable
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

