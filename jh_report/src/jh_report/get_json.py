import requests
import datetime


def get_json(url:str)->dict:
    try:
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Host': 'www.jinzhuedu.com',
            'Referer': 'http://www.jinzhuedu.com/mantis/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
        }
        timestamp = int(datetime.datetime.now().timestamp()*1000)
        url = url + f"?v={timestamp}"
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
    
if __name__ == "__main__":
    url = "http://www.jinzhuedu.com/mantis/invest/invest_baidu.json"
    json_data = get_json(url)
    print(type(json_data['data'][0]['消费']))
