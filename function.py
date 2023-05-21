import requests

def get_ban_status(names):
    url = f'https://api.gametools.network/bfban/checkban?names={names}'
    response = requests.get(url)
    data = response.json()
    return data


def generate_bfban_link(origin_persona_id):
    return f'https://bfban.com/player/{origin_persona_id}'


def get_bfv_stats(name):
    url = f'https://api.gametools.network/bfv/stats/?format_values=true&name={name}&platform=pc&lang=zh-cn'
    response = requests.get(url)
    data = response.json()
    return data


def convert_time_to_hours(time_string):
    # 移除字符串中的空格
    time_string = time_string.replace(" ", "")

    # 分割时间字符串
    days, time = time_string.split('days,')

    # 提取小时、分钟和秒数部分
    hours, minutes, seconds = map(int, time.split(':'))

    # 计算总小时数
    total_hours = int(days) * 24 + hours + minutes / 60 + seconds / 3600
    return total_hours

