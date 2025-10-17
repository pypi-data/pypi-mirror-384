import re
import json,traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from dateutil import tz
from dateutil.parser import parse as parse_date
import requests
from fastmcp import FastMCP
from typing import Annotated
from .common_func import filter_tickets_info
from .common_define import *

mcp = FastMCP("12306-mcp-server")

# ======================
# 常量定义
# ======================
VERSION = "0.1.0"
API_BASE = "https://kyfw.12306.cn"
SEARCH_API_BASE = "https://search.12306.cn"
WEB_URL = "https://www.12306.cn/index/"
LCQUERY_INIT_URL = "https://kyfw.12306.cn/otn/lcQuery/init"
QUERY_URL = f"{API_BASE}/otn/leftTicket/queryG"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# 全局变量
STATIONS: Dict[str, Dict] = {}
CITY_STATIONS: Dict[str, List[Dict]] = {}
CITY_CODES: Dict[str, Dict] = {}
NAME_STATIONS: Dict[str, Dict] = {}
LCQUERY_PATH = ""



# ======================
# 工具函数
# ======================

def parse_tickets_data(raw_data):
    '''
    车票查询结果字段解析
    每行数据的字段定义在TicketDataKeys
    提取出的结果：
    {'secret_Sstr': '8IJXBojg8TLhokb50N5oOXvI%2B6s6jw4CYWGog2tjum6LhMpsCbzesT5WUUOKBAXWYXdmUnTOd%2FZ9%0ApafKkloAd7P45RKVr9aXG3LPbTY430s4oDF5Zib81GdEkjNyAuJdpy3NiaZbHUzAldcmiJnZvN3z%0AzMKZeZzecOa6g0%2BRb320FwVT42KERTQ9fvplbAdAM9OQjYwI%2Bml0mW2O%2F10K23CgBiAT2RhcsiGN%0AFymiz1c1HpZHXX1zM7Gh3IKjMBOquNS1gZMhQnwBsYs25B0zIunflN5hzWLX2rhAbSaKw9HMB9DX%0APkwuzy9YyJCI4Bb7nXYqpgdFb2qM11xC%2BP4zTtsW9YdKD%2B9B',
    'button_text_info': '预订', 'train_no': '5500000D1010', 'station_train_code': 'D10', 'start_station_telecode': 'SNH', 'end_station_telecode': 'VNP', 'from_station_telecode': 'NJH', 'to_station_telecode': 'VNP', 'start_time': '00:02', 'arrive_time': '09:24', 'lishi': '09:22', 'canWebBuy': 'Y', 'yp_info': '13C3LRUJyj924GWK9dRczb4kTBQDALRJW4b2MWQ%2BKAbFtONxKsKnJDiaJE8%3D',
    'start_train_date': '20251016', 'train_seat_feature': '3', 'location_code': 'H7', 'from_station_no': '03', 'to_station_no': '04', 'is_support_card': '1', 'controlled_train_flag': '0', 'gg_num': '', 'gr_num': '', 'qt_num': '', 'rw_num': '有', 'rz_num': '', 'tz_num': '', 'wz_num': '有', 'yb_num': '', 'yw_num': '18', 'yz_num': '', 'ze_num': '有', 'zy_num': '', 'swz_num': '', 'srrb_num': '',
    'yp_ex': 'J0O0I0W0', 'seat_types': 'JOIO', 'exchange_train_flag': '1', 'houbu_train_flag': '0', 'houbu_seat_limit': '', 'yp_info_new': 'J037400018O024900021I043900021O024903025', '40': '0', '41': '', '42': '', '43': '', '44': '', '45': '1', 'dw_flag': '0#1#0#0#z#0#JI#z', '47': '', 'stopcheckTime': '7', 'country_flag': 'CHN,CHN', 'local_arrive_time': '', 'local_start_time': '', '52': 'N#N#',
    'bed_level_info': 'J303740J104360J203980I304390I104970', 'seat_discount_info': 'J3070J1070J2070O0070I3065I1065W0070', 'sale_time': '202510030815', '56': ''}
    '''
    result = []
    for item in raw_data:
        values = item.split('|')
        entry = {key: values[i] for i, key in enumerate(TicketDataKeys)}
        result.append(entry)
    return result

def extract_dw_flags(dw_flag_str, dw_flags):
    dw_flag_list = dw_flag_str.split('#')
    result = []

    if dw_flag_list[0] == '5':
        result.append(dw_flags[0])

    if len(dw_flag_list) > 1 and dw_flag_list[1] == '1':
        result.append(dw_flags[1])

    if len(dw_flag_list) > 2:
        if dw_flag_list[2][0] == 'Q':
            result.append(dw_flags[2])
        elif dw_flag_list[2][0] == 'R':
            result.append(dw_flags[3])

    if len(dw_flag_list) > 5 and dw_flag_list[5] == 'D':
        result.append(dw_flags[4])

    if len(dw_flag_list) > 6 and dw_flag_list[6] != 'z':
        result.append(dw_flags[5])

    if len(dw_flag_list) > 7 and dw_flag_list[7] != 'z':
        result.append(dw_flags[6])

    return result

def extract_prices(yp_info, seat_discount_info, ticket_data, seat_types):
    PRICE_STR_LENGTH = 10
    DISCOUNT_STR_LENGTH = 5
    prices = []
    discounts = {}

    # 解析折扣信息
    for i in range(len(seat_discount_info) // DISCOUNT_STR_LENGTH):
        start_idx = i * DISCOUNT_STR_LENGTH
        end_idx = (i + 1) * DISCOUNT_STR_LENGTH
        discount_str = seat_discount_info[start_idx:end_idx]
        discounts[discount_str[0]] = int(discount_str[1:])

    # 解析价格信息
    for i in range(len(yp_info) // PRICE_STR_LENGTH):
        start_idx = i * PRICE_STR_LENGTH
        end_idx = (i + 1) * PRICE_STR_LENGTH
        price_str = yp_info[start_idx:end_idx]

        # 确定座位类型代码
        if int(price_str[6:10]) >= 3000:
            seat_type_code = 'W'  # 无座
        elif price_str[0] not in seat_types:
            seat_type_code = 'H'  # 其他坐席
        else:
            seat_type_code = price_str[0]

        seat_type = seat_types[seat_type_code]
        price = int(price_str[1:6]) / 10
        discount = discounts.get(seat_type_code)

        prices.append({
            'seat_name': seat_type['name'],
            'short': seat_type['short'],
            'seat_type_code': seat_type_code,
            'num': ticket_data.get(f"{seat_type['short']}_num"),
            'price': price,
            'discount': discount,
        })

    return prices

def parse_tickets_info(tickets_data, station_map):
    '''
    station_map: ex  {'FTP': '北京丰台', 'VNP': '北京南', 'BJP': '北京', 'NKH': '南京南', 'NJH': '南京'}
    '''
    result = []

    for ticket in tickets_data:
        prices = extract_prices(
            ticket['yp_info_new'],
            ticket['seat_discount_info'],
            ticket,
            seat_types=SEAT_TYPES
        )

        dw_flag = extract_dw_flags(ticket['dw_flag'], DW_FLAGS)

        # 解析时间
        start_hours, start_minutes = map(int, ticket['start_time'].split(':'))
        duration_hours, duration_minutes = map(int, ticket['lishi'].split(':'))

        start_date = datetime.strptime(ticket['start_train_date'], '%Y%m%d')
        start_date = start_date.replace(hour=start_hours, minute=start_minutes)

        arrive_date = start_date + timedelta(
            hours=duration_hours,
            minutes=duration_minutes
        )

        result.append({
            'train_no': ticket['train_no'],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'arrive_date': arrive_date.strftime('%Y-%m-%d'),
            'start_train_code': ticket['station_train_code'],
            'start_time': ticket['start_time'],
            'arrive_time': ticket['arrive_time'],
            'lishi': ticket['lishi'],
            'from_station': station_map.get(ticket['from_station_telecode']),
            'to_station': station_map.get(ticket['to_station_telecode']),
            'from_station_telecode': ticket['from_station_telecode'],
            'to_station_telecode': ticket['to_station_telecode'],
            'prices': prices,
            'dw_flag': dw_flag,
        })

    return result

def extract_lishi(all_lishi: str) -> str:
    """
    从历时字符串中提取小时和分钟，并格式化为 HH:MM 格式
    Args:
        all_lishi: 历时字符串，如 "2小时30分钟" 或 "45分钟"
    Returns:
        格式化后的历时字符串，如 "02:30" 或 "00:45"
    Raises:
        ValueError: 当无法从字符串中提取历时信息时
    """
    # 匹配模式：可选的小时部分和必需的分钟部分
    pattern = r'(?:(\d+)小时)?(\d+?)分钟'
    match = re.search(pattern, all_lishi)

    if not match:
        raise ValueError('extract_lishi失败，没有匹配到关键词')

    # 提取小时和分钟
    hours = match.group(1)  # 可能为 None
    minutes = match.group(2)

    # 如果没有小时部分，则小时为 00
    if not hours:
        return f"00:{minutes}"

    # 格式化小时为两位数
    formatted_hours = hours.zfill(2)
    return f"{formatted_hours}:{minutes}"

def parse_interlines_ticket_info(interline_tickets_data: List[Dict]) -> List[Dict]:
    """
    解析中转票详细信息
    Args:
        interline_tickets_data: 中转票数据列表
    Returns:
        解析后的中转票信息列表
    """
    result = []

    for interline_ticket_data in interline_tickets_data:
        # 提取价格信息
        prices = extract_prices(
            interline_ticket_data.get('yp_info'),
            interline_ticket_data.get('seat_discount_info'),
            interline_ticket_data,
            seat_types=SEAT_TYPES
        )

        # 解析出发时间
        start_time_str = interline_ticket_data['start_time']
        start_hours = int(start_time_str.split(':')[0])
        start_minutes = int(start_time_str.split(':')[1])

        # 解析历时
        lishi_str = interline_ticket_data['lishi']
        lishi_parts = lishi_str.split(':')
        duration_hours = int(lishi_parts[0])
        duration_minutes = int(lishi_parts[1])

        # 计算出发和到达日期时间
        start_date_str = interline_ticket_data['start_train_date']
        start_date = datetime.strptime(start_date_str, '%Y%m%d')

        # 设置出发时间
        start_datetime = start_date.replace(hour=start_hours, minute=start_minutes)

        # 计算到达时间
        arrive_datetime = start_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)

        # 构建结果
        ticket_info = {
            'train_no': interline_ticket_data['train_no'],
            'start_train_code': interline_ticket_data['station_train_code'],
            'start_date': start_datetime.strftime('%Y-%m-%d'),
            'arrive_date': arrive_datetime.strftime('%Y-%m-%d'),
            'start_time': interline_ticket_data['start_time'],
            'arrive_time': interline_ticket_data['arrive_time'],
            'lishi': interline_ticket_data['lishi'],
            'from_station': interline_ticket_data['from_station_name'],
            'to_station': interline_ticket_data['to_station_name'],
            'from_station_telecode': interline_ticket_data['from_station_telecode'],
            'to_station_telecode': interline_ticket_data['to_station_telecode'],
            'prices': prices,
            'dw_flag': extract_dw_flags(interline_ticket_data.get('dw_flag'),DW_FLAGS),
        }

        result.append(ticket_info)

    return result

def parse_interlines_info(interline_data: List[Dict]) -> List[Dict]:
    """
    解析中转票信息
    """
    result = []
    for ticket in interline_data:
        interline_tickets = parse_interlines_ticket_info(ticket['fullList'])
        lishi = extract_lishi(ticket['all_lishi'])

        result.append({
            'lishi': lishi,
            'start_time': ticket['start_time'],
            'start_date': ticket['train_date'],
            'middle_date': ticket['middle_date'],
            'arrive_date': ticket['arrive_date'],
            'arrive_time': ticket['arrive_time'],
            'from_station_code': ticket['from_station_code'],
            'from_station_name': ticket['from_station_name'],
            'middle_station_code': ticket['middle_station_code'],
            'middle_station_name': ticket['middle_station_name'],
            'end_station_code': ticket['end_station_code'],
            'end_station_name': ticket['end_station_name'],
            'start_train_code': interline_tickets[0]['start_train_code'],
            'first_train_no': ticket['first_train_no'],
            'second_train_no': ticket['second_train_no'],
            'train_count': ticket['train_count'],
            'ticketList': interline_tickets,
            'same_station': ticket['same_station'] == '0',
            'same_train': ticket['same_train'] == 'Y',
            'wait_time': ticket['wait_time'],
        })
    return result

def format_tickets_info(tickets_info: List[Dict]) -> str:
    """
    格式化票务信息为可读的文本格式

    Args:
        tickets_info: 票务信息列表

    Returns:
        格式化后的票务信息字符串
    """
    if not tickets_info:
        return '没有查询到相关车次信息'

    result = '车次|出发站 -> 到达站|出发时间 -> 到达时间|历时\n'

    for ticket_info in tickets_info:
        info_str = ''
        info_str += f"{ticket_info['start_train_code']} {ticket_info['from_station']}(telecode:{ticket_info['from_station_telecode']}) -> {ticket_info['to_station']}(telecode:{ticket_info['to_station_telecode']}) {ticket_info['start_time']} -> {ticket_info['arrive_time']} 历时：{ticket_info['lishi']}"

        # 添加价格信息
        for price in ticket_info['prices']:
            ticket_status = format_ticket_status(price['num'])
            info_str += f"\n- {price['seat_name']}: {ticket_status} {price['price']}元"

        result += f"{info_str}\n"

    return result

def format_interlines_info(interlines_info: List[Dict]) -> str:
    """
    格式化中转票信息为文本输出
    """
    result = '出发时间 -> 到达时间 | 出发车站 -> 中转车站 -> 到达车站 | 换乘标志 |换乘等待时间| 总历时\n\n'

    for interline_info in interlines_info:
        result += f"{interline_info['start_date']} {interline_info['start_time']} -> {interline_info['arrive_date']} {interline_info['arrive_time']} | "
        result += f"{interline_info['from_station_name']} -> {interline_info['middle_station_name']} -> {interline_info['end_station_name']} | "

        if interline_info['same_train']:
            transfer_type = '同车换乘'
        elif interline_info['same_station']:
            transfer_type = '同站换乘'
        else:
            transfer_type = '换站换乘'

        result += f"{transfer_type} | {interline_info['wait_time']} | {interline_info['lishi']}\n\n"

        # 格式化票务信息
        ticket_info = format_tickets_info(interline_info['ticketList'])
        result += '\t' + ticket_info.replace('\n', '\n\t') + '\n'

    return result

def format_ticket_status(num: str) -> str:
    if num.isdigit():
        count = int(num)
        return "无票" if count == 0 else f"剩余{count}张票"
    if num in ("有", "充足"):
        return "有票"
    if num in ("无", "--", ""):
        return "无票"
    if num == "候补":
        return "无票需候补"
    return f"{num}票"

def check_date(date_str: str) -> bool:
    shanghai_tz = tz.gettz("Asia/Shanghai")
    now = datetime.now(shanghai_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    input_date = parse_date(date_str).replace(tzinfo=shanghai_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    return input_date >= now

def format_cookies(cookies: Dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items())

def get_cookie():
    """获取 12306 的初始 Cookie"""
    try:

        response = requests.get(f"{API_BASE}/otn/leftTicket/init", headers=HEADERS, timeout=10)
        cookies = response.cookies
        return cookies
    except Exception as e:
        print(f"[Error] 获取 Cookie 失败: {e}")
        return None

def parse_stations_data(raw_data: str) -> Dict[str, Dict[str, str]]:
    """解析原始车站字符串，返回以 station_code 为键的字典"""
    parts = raw_data.split("|")
    stations = {}
    # 每10个字段一组
    for i in range(0, len(parts) - 9, 10):
        group = parts[i:i+10]
        station = dict(zip(STATION_DATA_KEYS, group))
        code = station.get("station_code")
        if code:
            stations[code] = station
    return stations

def parse_tickets(data):
    """简单解析余票数据，打印车次和二等座余票"""
    if not data or "result" not in data:
        return

    map_info = data.get("map", {})
    results = data["result"]

    # print(f"{'车次':<10} {'出发站':<10} {'到达站':<10} {'出发时间':<8} {'到达时间':<8} {'历时':<8} {'二等座'}")
    # print("-" * 70)

    result_data=[]
    for item in results:
        fields = item.split('|')
        # 根据 12306 的字段顺序解析（参考 TicketDataKeys）
        # 简化：只取关键字段，假设 ze_num 是第 31 位（实际可能有偏移，需根据真实结构调整）
        try:
            train_code = fields[3]      # 车次
            from_code = fields[6]       # 出发站 telecode
            to_code = fields[7]         # 到达站 telecode
            start_time = fields[8]
            arrive_time = fields[9]
            lishi = fields[10]          # 历时
            ze_num = fields[30]         # 二等座余票（字段位置可能变化！）

            from_name = map_info.get(from_code, from_code)
            to_name = map_info.get(to_code, to_code)

            # 简单格式化余票状态
            if ze_num == "有" or ze_num == "充足":
                status = "有票"
            elif ze_num == "无" or ze_num == "--" or ze_num == "":
                status = "无票"
            elif ze_num.isdigit():
                status = f"{ze_num}张"
            else:
                status = ze_num

            # print(f"{train_code:<10} {from_name:<10} {to_name:<10} {start_time:<8} {arrive_time:<8} {lishi:<8} {status}")
            result_data.append({"train_code":train_code,"from_name":from_name,"to_name":to_name,"start_time":start_time,"arrive_time":arrive_time,"lishi":lishi,"ze_num":ze_num})
        except IndexError:
            continue  # 跳过格式异常的行
    return result_data

def getStations() -> Dict[str, Dict[str, Any]]:
    """
    模拟原始 JS 逻辑：从 12306 首页提取 station_name.js 并解析车站数据。
    注意：该方法在 2025 年已大概率失效，仅保留逻辑结构。
    """
    # Step 1: 获取首页 HTML
    try:
        response = requests.get(WEB_URL)
        html = response.text
    except Exception as e:
        raise RuntimeError("Error: get 12306 web page failed.") from e

    # Step 2: 尝试匹配 station_name.js 路径
    # 注意：原始 JS 正则 '.(/script/...' 有误，这里修正为合理正则
    match = re.search(r'(/script/core/common/station_name[^"]*\.js)', html)
    if not match:
        # 尝试更宽松的匹配
        match = re.search(r'(station_name[^"]*\.js)', html)
        if not match:
            raise RuntimeError("Error: get station name js file failed.")

    station_js_path = match.group(1)
    # 补全 URL（确保以 / 开头）
    if not station_js_path.startswith("http"):
        if station_js_path.startswith("/"):
            station_js_path = station_js_path[1:]
        station_js_url = urljoin(WEB_URL, station_js_path) # 如果 station_js_path 以/开头，拼接时WEB_URL结尾的index会被去除，切记！！
    else:
        station_js_url = station_js_path

    # Step 3: 请求 JS 文件
    try:
        js_response = requests.get(station_js_url)
        js_content = js_response.text
    except Exception as e:
        raise RuntimeError("Error: get station name js file failed.") from e

    # Step 4: 提取原始车站字符串（避免使用 eval！）
    # 原始：eval(js.replace('var station_names =', ''))
    # 安全做法：用正则提取引号内容
    raw_data_match = re.search(r"station_names\s*=\s*[\"']([^\"']*)[\"']", js_content)
    if not raw_data_match:
        # 尝试无引号形式（极少见）
        raw_data_match = re.search(r"station_names\s*=\s*([^;\n]*)", js_content)
        if not raw_data_match:
            raise RuntimeError("Error: failed to extract station_names string from JS.")

    raw_data = raw_data_match.group(1).strip().strip("'\"")

    # Step 5: 解析数据
    stations_data = parse_stations_data(raw_data)
    # print(stations_data)

    # Step 6: 补充缺失车站
    for station in MISSING_STATIONS:
        code = station.get("station_code")
        if code and code not in stations_data:
            stations_data[code] = station

    return stations_data

def get_lc_query_path() -> str:
        html = requests.get(LCQUERY_INIT_URL).text
        match = re.search(r"var lc_search_url = '(.+?)'", html)
        if not match:
            raise RuntimeError("Failed to get lc_query path")
        return match.group(1)


# ======================
# 全局变量初始化:获取站点信息
# ======================
STATIONS = getStations()
LCQUERY_PATH = get_lc_query_path()
# CITY_STATIONS
for station in STATIONS.values():
    city = station['city']
    if city not in CITY_STATIONS:
        CITY_STATIONS[city] = []
    CITY_STATIONS[city].append({
        'station_code': station['station_code'],
        'station_name': station['station_name'],
    })
#  CITY_CODES
for city, stations in CITY_STATIONS.items():
    for station in stations:
        if station['station_name'] == city:
            CITY_CODES[city] = station
            break

# NAME_STATIONS
for station in STATIONS.values():
    station_name = station['station_name']
    NAME_STATIONS[station_name] = {
        'station_code': station['station_code'],
        'station_name': station['station_name'],
    }


# ======================
# 工具路由
# ======================

@mcp.tool(name="get-current-date",description='获取当前日期，以上海时区（Asia/Shanghai, UTC+8）为准，返回格式为 "yyyy-MM-dd"。主要用于解析用户提到的相对日期（如“明天”、“下周三”），提供准确的日期输入。')
def get_current_date():
    shanghai_tz = tz.gettz("Asia/Shanghai")
    now = datetime.now(shanghai_tz)
    return {"date": now.strftime("%Y-%m-%d")}

@mcp.tool(name="get-stations-code-in-city",description="通过中文城市名查询该城市 **所有** 火车站的名称及其对应的 `station_code`，结果是一个包含多个车站信息的列表。")
def get_stations_code_in_city(city: Annotated[str, "要查询天气的城市名称，例如 '北京' 或 'New York'"]):
    '''
    通过中文城市名查询该城市 **所有** 火车站的名称及其对应的 `station_code`，结果是一个包含多个车站信息的列表。
    city: 中文城市名称，例如："北京", "上海"
    '''
    if city not in CITY_STATIONS:
        return "City not found"
    return CITY_STATIONS[city]

@mcp.tool(name="get-station-code-of-citys",description="通过中文城市名查询代表该城市的 `station_code`。此接口主要用于在用户提供**城市名**作为出发地或到达地时，为接口准备 `station_code` 参数。")
def get_station_code_of_citys(citys: Annotated[str,'要查询的城市，比如"北京"。若要查询多个城市，请用|分割，比如"北京|上海"']):
    '''
    通过中文城市名查询代表该城市的 `station_code`。此接口主要用于在用户提供**城市名**作为出发地或到达地时，为接口准备 `station_code` 参数。
    citys:要查询的城市，比如"北京"。若要查询多个城市，请用|分割，比如"北京|上海"
    '''
    result = {}
    for city in citys.split("|"):
        result[city] = CITY_CODES.get(city, {"error": "未检索到城市。"})
    return result

@mcp.tool(name="get-station-code-by-names",description="通过具体的中文车站名查询其 `station_code` 和车站名。此接口主要用于在用户提供**具体车站名**作为出发地或到达地时，为接口准备 `station_code` 参数。")
def get_station_code_by_names(station_names: Annotated[str,'具体的中文车站名称，例如："北京南", "上海虹桥"。若要查询多个站点，请用|分割，比如"北京南|上海虹桥"。']):
    '''
    通过具体的中文车站名查询其 `station_code` 和车站名。此接口主要用于在用户提供**具体车站名**作为出发地或到达地时，为接口准备 `station_code` 参数。
    station_names:具体的中文车站名称，例如："北京南", "上海虹桥"。若要查询多个站点，请用|分割，比如"北京南|上海虹桥"。
    '''
    result = {}
    for name in station_names.split("|"):
        clean_name = name.rstrip("站")
        result[name] = NAME_STATIONS.get(clean_name, {"error": "未检索到车站。"})
    return result

@mcp.tool(name="get-station-by-telecode",description="通过车站的 `station_telecode` 查询车站的详细信息，包括名称、拼音、所属城市等。此接口主要用于在已知 `telecode` 的情况下获取更完整的车站数据，或用于特殊查询及调试目的。一般用户对话流程中较少直接触发。")
def get_station_by_telecode(station_telecode: Annotated[str,"车站的 `station_telecode` (3位字母编码)"]):
    '''
    通过车站的 `station_telecode` 查询车站的详细信息，包括名称、拼音、所属城市等。此接口主要用于在已知 `telecode` 的情况下获取更完整的车站数据，或用于特殊查询及调试目的。一般用户对话流程中较少直接触发。
    station_telecode:车站的 `station_telecode` (3位字母编码)
    '''
    station = STATIONS.get(station_telecode)
    if not station:
        return "Station not found"
    return station


@mcp.tool(name="get-tickets",description="查询12306余票信息。")
def get_tickets(
    date:Annotated[str, '查询日期，格式为 "yyyy-MM-dd"。如果用户提供的是相对日期（如“明天”），请务必先调用 `get-current-date` 接口获取当前日期，并计算出目标日期。'],
    from_station:Annotated[str, '出发地的 `station_code` 。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。'],
    to_station:Annotated[str, '到达地的 `station_code` 。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。'],
    train_filter_flags:Annotated[Optional[str], '车次筛选条件，默认为空，即不筛选。支持多个标志同时筛选。例如用户说“高铁票”，则应使用 "G"。可选标志：[G(高铁/城际),D(动车),Z(直达特快),T(特快),K(快速),O(其他),F(复兴号),S(智能动车组)]'] = "",
    earliest_start_time:Annotated[Optional[int], '最早出发时间（0-24），默认为0。'] = 0,
    latest_start_time:Annotated[Optional[int], '最迟出发时间（0-24），默认为24。'] = 24,
    sort_flag:Annotated[Optional[str], '排序方式，默认为空，即不排序。仅支持单一标识。可选标志：[startTime(出发时间从早到晚), arriveTime(抵达时间从早到晚), duration(历时从短到长]'] = "",
    sort_reverse:Annotated[Optional[bool], '是否逆向排序结果，默认为false。仅在设置了sortFlag时生效。'] = False,
    limited_num:Annotated[Optional[int], '返回的余票数量限制，默认为0，即不限制。'] = 0,
    format:Annotated[Optional[str], '返回结果格式，默认为text，建议使用text与csv。可选标志：[text, csv, json]'] = "text",
):
    '''
    查询12306余票信息。
    :param req:
    :return:
    '''
    if not check_date(date):
        return "The date cannot be earlier than today."
    if from_station not in STATIONS or to_station not in STATIONS:
        return "Station not found."

    cookies = get_cookie()
    if not cookies:
        return "Failed to get cookies"

    params = {
        "leftTicketDTO.train_date": date,
        "leftTicketDTO.from_station": from_station,
        "leftTicketDTO.to_station": to_station,
        "purpose_codes": "ADULT",
    }

    try:
        response = requests.get(
            QUERY_URL,
            params=params,
            cookies=cookies,
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") and data.get("data"):
                ticketsData = parse_tickets_data(data.get("data").get("result"))
                ticketsInfo = parse_tickets_info(ticketsData, data.get("data").get("map"))
                filteredTicketsInfo=filter_tickets_info(ticketsInfo, train_filter_flags, earliest_start_time,
                        latest_start_time, sort_flag, sort_reverse, limited_num)
                return {"result":filteredTicketsInfo}
            else:
                print("[Error] 查询返回异常:", data.get("messages", "未知错误"))
                return {"result": "没有查询到相关车次信息"}
        else:
            print(f"[Error] HTTP {response.status_code}")
            return {"result": "没有查询到相关车次信息"}
    except Exception as e:
        print(f"[Error] 查询余票失败: {traceback.format_exc()}")
        return {"result": "查询余票失败: {e}"}

@mcp.tool(name="get-interline-tickets",description="查询12306中转余票信息。尚且只支持查询前十条。")
def get_interline_tickets(
        date: Annotated[str, '查询日期，格式为 "yyyy-MM-dd"。如果用户提供的是相对日期（如“明天”），请务必先调用 `get-current-date` 接口获取当前日期，并计算出目标日期。'],
        from_station: Annotated[str, '出发地的 `station_code` 。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。'],
        to_station: Annotated[str, '目的地的 `station_code` 。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。'],
        middle_station: Annotated[str, '中转地的 `station_code` ，可选。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。'] = '',
        show_wz: Annotated[bool, '是否显示无座车，默认不显示无座车。'] = False,
        train_filter_flags: Annotated[str, '车次筛选条件，默认为空。从以下标志中选取多个条件组合[G(高铁/城际),D(动车),Z(直达特快),T(特快),K(快速),O(其他),F(复兴号),S(智能动车组)]'] = '',
        earliest_start_time: Annotated[int, '最早出发时间（0-24），默认为0。'] = 0,
        latest_start_time: Annotated[int, '最迟出发时间（0-24），默认为24。'] = 24,
        sort_flag: Annotated[str, '排序方式，默认为空，即不排序。仅支持单一标识。可选标志：[startTime(出发时间从早到晚), arriveTime(抵达时间从早到晚), duration(历时从短到长)]'] = '',
        sort_reverse: Annotated[bool, '是否逆向排序结果，默认为false。仅在设置了sortFlag时生效。'] = False,
        limited_num: Annotated[int, '返回的中转余票数量限制，默认为10。'] = 10,
        format_type: Annotated[str, '返回结果格式，默认为text，建议使用text。可选标志：[text, json]'] = 'text'
) -> Dict[str, Any]:
    """
    查询12306中转余票信息
    Args:
        date: 查询日期，格式为 "yyyy-MM-dd"
        from_station: 出发地的station_code
        to_station: 目的地的station_code
        middle_station: 中转地的station_code，可选
        show_wz: 是否显示无座车，默认不显示
        train_filter_flags: 车次筛选条件
        earliest_start_time: 最早出发时间（0-24）
        latest_start_time: 最迟出发时间（0-24）
        sort_flag: 排序方式
        sort_reverse: 是否逆向排序
        limited_num: 返回的中转余票数量限制
        format_type: 返回结果格式，text或json
    """
    # 检查日期是否早于当前日期
    if not check_date(date):
        return {
            'content': [{
                'type': 'text',
                'text': 'Error: The date cannot be earlier than today.'
            }]
        }

    # 检查车站是否存在
    if (from_station not in STATIONS or
            to_station not in STATIONS):
        return {
            'content': [{
                'type': 'text',
                'text': 'Error: Station not found.'
            }]
        }

    # 获取cookies
    cookies = get_cookie()
    if not cookies:
        return {
            'content': [{
                'type': 'text',
                'text': 'Error: get cookie failed. Check your network.'
            }]
        }

    interline_data = []
    query_params = {
        'train_date': date,
        'from_station_telecode': from_station,
        'to_station_telecode': to_station,
        'middle_station': middle_station,
        'result_index': '0',
        'can_query': 'Y',
        'isShowWZ': 'Y' if show_wz else 'N',
        'purpose_codes': '00',  # 00: 成人票 0X: 学生票
        'channel': 'E',  # 没搞清楚什么用
    }

    while len(interline_data) < limited_num:
        query_url = f"{API_BASE}{LCQUERY_PATH}"
        query_response = requests.get(
            query_url,
            params=query_params,
            cookies=cookies,
            headers=HEADERS.update({'Cookie': format_cookies(cookies)}),
            timeout=10
        ).json()

        # 处理请求错误
        if query_response is None:
            return {
                'content': [{
                    'type': 'text',
                    'text': 'Error: request interline tickets data failed.'
                }]
            }

        # 请求成功，但查询有误
        if isinstance(query_response.get('data'), str):
            error_msg = query_response.get('errorMsg', 'Unknown error')
            return {
                'content': [{
                    'type': 'text',
                    'text': f'很抱歉，未查到相关的列车余票。({error_msg})'
                }]
            }

        interline_data.extend(query_response['data']['middleList'])

        if query_response['data']['can_query'] == 'N':
            break

        query_params['result_index'] = str(query_response['data']['result_index'])

    # 解析中转票信息
    try:
        interline_tickets_info = parse_interlines_info(interline_data)
    except Exception as error:
        print(f"解析中转票出错:{traceback.format_exc()}")
        return {"result": 'parse tickets info failed. {error}'}


    # 过滤和排序票务信息
    filtered_interline_tickets_info = filter_tickets_info(
        interline_tickets_info, train_filter_flags, earliest_start_time,
        latest_start_time, sort_flag, sort_reverse, limited_num
    )
    return {"result": filtered_interline_tickets_info}

    # # 格式化结果
    # if format_type.lower() == 'json':
    #     formatted_result = json.dumps(filtered_interline_tickets_info, ensure_ascii=False)
    # else:
    #     formatted_result = format_interlines_info(filtered_interline_tickets_info)
    #
    # return {
    #     'content': [{
    #         'type': 'text',
    #         'text': formatted_result
    #     }]
    # }

if __name__ == "__main__":
    mcp.run(transport="sse")

    # # 函数调试， 注释装饰器行
    # ret=get_tickets(date="2025-10-17",from_station="NJH",to_station="BJP",earliest_start_time=12)
    # print(ret)

    # print(get_station_code_by_names("南京|拉萨"))
    # ret=get_interline_tickets(date="2025-10-17",from_station="NJH",to_station="LSO")
    # print(ret)




