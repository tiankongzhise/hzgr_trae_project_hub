from src.jh_report.api.query import query


if __name__ == "__main__":
    start_date = '2025-01-01'
    end_date = '2025-04-24'
    school = ''
    channel = ''
    sub_channel = ''
    rsp = query(start_date,end_date,school,channel,sub_channel)
    print(rsp.json())
