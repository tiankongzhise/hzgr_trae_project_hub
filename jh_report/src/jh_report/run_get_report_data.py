from .api.card import get_card
from .api.visit import get_visit
from .api.sign_up import get_sign_up
from .database.curd import DbClient


def run():
    print('请输入需要获取的年份(默认2025):')
    year = str(input()) or '2025'
    
    if int(year) < 2010:
        print('仅支持2010年及以后年份,输入错误,请重新输入!')
        return False
    db_client = DbClient()
    print(f'开始读取{year}年的线索数据')
    card_data = get_card(year)
    print(f'线索数据读取完成,共计{len(card_data['data'])}条数据')
    print(f'开始将{year}年的线索数据入库')
    card_insert_result = db_client.insert_jh_card_table(card_data['data'])
    if card_insert_result:
        print('线索数据入库完成')
    else:
        print('线索数据入库失败')
        return False
    print(f'开始读取{year}年的上门数据')
    visit_data = get_visit(year)
    print(f'上门数据读取完成,共计{len(visit_data['data'])}条数据')
    print(f'开始将{year}年的上门数据入库')
    visit_insert_result = db_client.insert_jh_visit_table(visit_data['data'])
    if visit_insert_result:
        print('上门数据入库完成')
    else:
        print('上门数据入库失败')
        return False
    print(f'开始读取{year}年的报名数据')
    sign_up_data = get_sign_up(year)
    print(f'报名数据读取完成,共计{len(sign_up_data['data'])}条数据')
    print(f'开始将{year}年的报名数据入库')
    sign_up_insert_result = db_client.insert_jh_sign_up_table(sign_up_data['data'])
    if sign_up_insert_result:
        print('报名数据入库完成')
    else:
        print('报名数据入库失败')
        return False
    return True
    
    
    
    
