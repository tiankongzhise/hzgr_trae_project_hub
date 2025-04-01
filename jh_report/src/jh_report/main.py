from .database.models import JhCostTable
from tkzs_bd_db_tool import init_db,get_session
from .get_json import get_json
from datetime import datetime,timedelta
from decimal import Decimal
import re
import traceback

def get_url_list()->list[str]:
    url_list = [
        'http://www.jinzhuedu.com/mantis/invest/invest_baidu.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_meituan.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_meituan_w.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_xhs_jh.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_xhs_xs.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_douyin.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_douyin_w.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_alkb.json',
        'http://www.jinzhuedu.com/mantis/invest/invest_58zp.json'
    ]
    return url_list 

def format_date(excel_date:int) -> datetime.date:
        # Excel的基准日期是1900-1-1（Windows版）
    # 注意：Excel错误地将1900年视为闰年，所以需要调整
    if excel_date > 59:
        excel_date -= 1  # 调整1900年2月29日的错误
    
    base_date = datetime(1899, 12, 30)
    delta = timedelta(days=excel_date)
    result_date = base_date + delta
    return result_date.strftime('%Y-%m-%d')  # 格式化为YYYY MM DD
def get_db_data()->dict:
    db_data_map = {}
    with get_session() as session:
        db_data = session.query(JhCostTable).all()
        for item in db_data:
            db_data_map.setdefault(item.channel,{}).update({item.date.strftime('%Y-%m-%d'):item.cost})
    return db_data_map
            
    
def get_channel(url:str) -> str:
    channel = re.compile(r'invest_(.*?)\.json')
    return channel.findall(url)[0]

def safe_compare(a, b)-> bool:
    if not isinstance(a, Decimal):
        a = Decimal(str(a))
    if not isinstance(b, Decimal):
        b = Decimal(str(b))
        
    # 规范化处理（去除不必要的尾随零）
    normalized_a = a.normalize()
    normalized_b = b.normalize()
    return normalized_a == normalized_b


def transfer_data(data:list[dict],channel:str):
    result = []
    db_data_map = get_db_data()
    for item in data:
        # 去除无效数据
        if item.get('消费') is None:
            continue
        temp_date = format_date(item['日期'])
        # 去重
        if db_data_map.get(channel,{}).get(temp_date) is not None:
            if safe_compare(db_data_map.get(channel,{}).get(temp_date),item['消费']):
                continue
        temp_dict = {}
        temp_dict['channel'] = channel
        temp_dict['date'] = temp_date
        temp_dict['cost'] = item['消费']
        temp_dict['click'] = item.get('点击')
        temp_dict['impression'] = item.get('展现')
        temp_dict['consult'] = item.get('对话')
        result.append(temp_dict)
    return result

def main() -> None:
    init_db()
    url_list = get_url_list()
    with get_session() as session:
        for url in url_list:
            try:
                channel = get_channel(url)
                json_data = get_json(url)
                if json_data:
                    data = transfer_data(json_data['data'],channel=channel)
                    if data:
                        session.bulk_insert_mappings(JhCostTable, data)
                        session.commit()
                        print(f"{channel}数据入库成功")
                    else:
                        print(f"{channel}没有新增数据")
            except Exception as e:
                session.rollback()
                print(f"{channel}数据入库失败,完整错误信息:")
                print(traceback.format_exc())
                break
            
            