from datetime import datetime
def parse_datetime(time_str):
    if time_str:
        try:
            return datetime.strptime(time_str, '%Y-%m-%d%H:%M:%S')
        except ValueError:
            return None
    return None

print(parse_datetime("2023-10-2509:24:15"))
