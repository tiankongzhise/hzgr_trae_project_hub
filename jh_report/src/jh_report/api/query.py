import requests

def query(start_date:str,end_date:str,school:str,channel:str,sub_channel:str):
    ...
    query_url = 'http://1.117.222.175:8000/mantis/invest/query'
    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection': 'keep-alive',
    'Content-length':'102',
    'Host': '1.117.222.175:8000',
    'Origin':'http://www.jinzhuedu.com',
    'Referer': 'http://www.jinzhuedu.com/mantis/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
}
    data = {
        'startDate':start_date,
        'endDate':end_date,
        'school':school,
        'channel':channel,
        'subChannel':sub_channel
    }
    rsp = requests.post(query_url,headers=headers,json=data)
    return rsp
    
