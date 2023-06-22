from urllib.parse import quote

import requests
import json

# 读取配置文件
def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config


def write_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

def get_bfban_playerinfo(names):
    url = f'https://bfban.gametools.network/api/player?personaId={get_PID(names)}'
    response = requests.get(url)
    data = response.json()
    return data
def get_bfban_status(names):
    url = f'https://bfban.gametools.network/api/player?personaId={get_PID(names)}'
    response = requests.get(url)
    data = response.json()
    status = data['data']['status']
    status = int(status)
    bfban_status = ""
    if status == -1:
        bfban_status = "Not reported"
    elif status == 0:
        bfban_status = "Unprocessed"
    elif status == 1:
        bfban_status = "Confirmed hacker"
    elif status == 2:
        bfban_status = "Suspicious"
    elif status == 3:
        bfban_status = "Moss self-certification"
    elif status == 4:
        bfban_status = "Invalid report"
    elif status == 5:
        bfban_status = "Under discussion"
    elif status == 6:
        bfban_status = "Needs more votes"
    elif status == 7:
        bfban_status = "Query failed"
    elif status == 8:
        bfban_status = "Farm weapons"
    return bfban_status

def get_PID(names):
    url = f'https://api.gametools.network/bfv/stats/?format_values=true&name={names}&platform=pc&skip_battlelog=false&lang=en-us'
    response = requests.get(url)
    data = response.json()
    PID = data['id']
    return PID

def get_UID(names):
    url = f'https://api.gametools.network/bfv/stats/?format_values=true&name={names}&platform=pc&skip_battlelog=false&lang=en-us'
    response = requests.get(url)
    data = response.json()
    UID = data['userId']
    return UID

def check_bfban_status(names):
    url = f'https://bfban.gametools.network/api/player?personaId={get_PID(names)}'
    response = requests.get(url)
    data = response.json()
    return data

def get_bfban_dbid(names):
    url = f'https://bfban.gametools.network/api/player?personaId={get_PID(names)}'
    response = requests.get(url)
    data = response.json()
    dbid = data['id']
    return dbid

def generate_bfban_link(origin_persona_id):
    return f'https://bfban.com/player/{origin_persona_id}'

# 定义 check 函数，检查用户是否在允许列表中
def is_allowed_user(ctx):
    discordID = read_config()['discordsuperID']
    return str(ctx.author.id) in discordID

def get_bfv_stats(name):
    url = f'https://api.gametools.network/bfv/stats/?format_values=true&name={name}&platform=pc&lang=en-us'
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

def validate_player_name(name):
    encoded_name = quote(name)
    url = f"https://api.gametools.network/bfv/stats/?format_values=true&name={encoded_name}&platform=pc&lang=en-us"
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return False, data["error"]
    elif "userName" in data and data["userName"] == name:
        return True, ""
    else:
        return False, "The player could not be found."
