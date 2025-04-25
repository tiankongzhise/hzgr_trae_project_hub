from .get_report_from_query import get_report_from_query
from .database.curd import DbClient
from .database.models import JhCostNewTable
from .utils import format_query_data,filter_data


def run():
    data = get_report_from_query()
    try:
        data_json = data.json()
    except Exception as e:
        print(f'数据获取失败,完整错误信息:{e}')
        print(f'data:{data.content}')
    data_format = format_query_data(data_json['data'])
    db_client = DbClient()
    print('正在查询数据库中存在的数据')
    db_data_format = db_client.query_jh_cost_new_table()
    print('数据库查询已完成')
    print('正在过滤出需要入库的数据')
    new_data = filter_data(data_format,db_data_format,{'date':'date','channel':'channel','sub_channel':'sub_channel','school':'school'})
    print('过滤完成')
    print('正在入库中')
    insert_reuslt = db_client.insert_jh_cost_new_table(new_data)
    if insert_reuslt:
        print('数据入库成功')
