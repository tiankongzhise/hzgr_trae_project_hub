from src.jh_report.api.query import query
from datetime import datetime,timedelta


def create_start_date(date_range) -> str:
    if date_range == '天':
        return (datetime.now().strftime('%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == '周':
        return (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
    elif date_range == '月':
        return (datetime.now() - timedelta(days=datetime.now().day-1)).strftime('%Y-%m-%d')
    elif date_range == '年':
        return (datetime.now() - timedelta(days=datetime.now().day-1)).strftime('%Y-%m-%d')

def  create_end_date(date_range) -> str:
    if date_range == '天':
        return (datetime.now().strftime('%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == '周':
        # return (datetime.now() + timedelta(days=6-datetime.now().weekday())).strftime('%Y-%m-%d')
        return (datetime.now().strftime('%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == '月':
        # return (datetime.now() + timedelta(days=30-datetime.now().day)).strftime('%Y-%m-%d')
        return (datetime.now().strftime('%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == '年':
        # return (datetime.now() + timedelta(days=365-datetime.now().day)).strftime('%Y-%m-%d')
        return (datetime.now().strftime('%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

def get_report_from_query():
    print('请输入查询的日期周期,默认为天,可选为天、周、月、年')
    date_range = input() or '天'
    if date_range not in ['天','周','月','年']:
        print(f'日期周期{date_range}输入错误,仅支持天、周、月、年,默认为天')
        date_range = '天'
    print('请输入查询开始日期(格式为YYYY-MM-DD):')
    start_date = input()
    print('请输入查询结束日期(格式为YYYY-MM-DD):')
    end_date = input()
    print('请输入查询的校区名称(默认无筛选):')
    school = input() or ''
    print('请输入查询的投放渠道(默认无筛选):')
    channel =input() or ''
    print('请输入查询的子渠道(默认无筛选):')
    sub_channel = input() or ''

    if not start_date:
        start_date = create_start_date(date_range)
    if not end_date:
        end_date = create_end_date(date_range)

    rsp = query(start_date,end_date,school,channel,sub_channel)
    print(rsp.json())
