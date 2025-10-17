from datetime import datetime, timedelta

# 车站字段顺序（对应 12306 的 station_names.js）
STATION_DATA_KEYS = [
    "station_id",
    "station_name",
    "station_code",
    "station_pinyin",
    "station_short",
    "station_index",
    "code",
    "city",
    "r1",
    "r2",
]

# 车票字段顺序（对应 leftTicket 接口返回的 | 分隔字段）
TICKET_DATA_KEYS = [
    "secret_str",
    "train_no",
    "station_train_code",
    "start_station_telecode",
    "end_station_telecode",
    "from_station_telecode",
    "to_station_telecode",
    "start_time",
    "arrive_time",
    "lishi",
    "can_web_buy",
    "yp_info_new",
    "start_train_date",
    "train_seat_feature",
    "location_code",
    "from_station_no",
    "to_station_no",
    "is_support_card",
    "controlled_train_flag",
    "gg_num",
    "gr_num",
    "qt_num",
    "rw_num",
    "rz_num",
    "tz_num",
    "wz_num",
    "yb_num",
    "yw_num",
    "yz_num",
    "ze_num",
    "zy_num",
    "swz_num",
    "srrb_num",
    "dw_flag",
    "seat_discount_info",
    # ... 可能还有更多，但只取前 35 左右即可
]

MISSING_STATIONS = [
    {
        "station_id": "@cdd",
        "station_name": "成  都东",
        "station_code": "WEI",
        "station_pinyin": "chengdudong",
        "station_short": "cdd",
        "station_index": "",
        "code": "1707",
        "city": "成都",
        "r1": "",
        "r2": "",
    }
]


SEAT_SHORT_TYPES = {
    "swz": "商务座",
    "tz": "特等座",
    "zy": "一等座",
    "ze": "二等座",
    "gr": "高软卧",
    "srrb": "动卧",
    "rw": "软卧",
    "yw": "硬卧",
    "rz": "软座",
    "yz": "硬座",
    "wz": "无座",
    "qt": "其他",
    "gg": "",
    "yb": "",
}

SEAT_TYPES = {
    "9": {"name": "商务座", "short": "swz"},
    "P": {"name": "特等座", "short": "tz"},
    "M": {"name": "一等座", "short": "zy"},
    "D": {"name": "优选一等座", "short": "zy"},
    "O": {"name": "二等座", "short": "ze"},
    "S": {"name": "二等包座", "short": "ze"},
    "6": {"name": "高级软卧", "short": "gr"},
    "A": {"name": "高级动卧", "short": "gr"},
    "4": {"name": "软卧", "short": "rw"},
    "I": {"name": "一等卧", "short": "rw"},
    "F": {"name": "动卧", "short": "rw"},
    "3": {"name": "硬卧", "short": "yw"},
    "J": {"name": "二等卧", "short": "yw"},
    "2": {"name": "软座", "short": "rz"},
    "1": {"name": "硬座", "short": "yz"},
    "W": {"name": "无座", "short": "wz"},
    "WZ": {"name": "无座", "short": "wz"},
    "H": {"name": "其他", "short": "qt"},
}

DW_FLAGS = [
    "智能动车组",
    "复兴号",
    "静音车厢",
    "温馨动卧",
    "动感号",
    "支持选铺",
    "老年优惠",
]

TRAIN_FILTERS = {
    # G(高铁/城际),D(动车),Z(直达特快),T(特快),K(快速),O(其他),F(复兴号),S(智能动车组)
    "G": lambda t: t["start_train_code"].startswith(("G", "C")),
    "D": lambda t: t["start_train_code"].startswith("D"),
    "Z": lambda t: t["start_train_code"].startswith("Z"),
    "T": lambda t: t["start_train_code"].startswith("T"),
    "K": lambda t: t["start_train_code"].startswith("K"),
    "O": lambda t: not any(
        f(t) for k, f in TRAIN_FILTERS.items() if k in "GDZTK"
    ),
    "F": lambda t: "复兴号" in t.get("dw_flag", []),
    "S": lambda t: "智能动车组" in t.get("dw_flag", []),
}


def _compare_time(date1: str, time1: str, date2: str, time2: str) -> int:
    dt1 = datetime.strptime(f"{date1} {time1}", "%Y-%m-%d %H:%M")
    dt2 = datetime.strptime(f"{date2} {time2}", "%Y-%m-%d %H:%M")
    return (dt1 - dt2).total_seconds()

def _compare_duration(l1: str, l2: str) -> int:
    h1, m1 = map(int, l1.split(":"))
    h2, m2 = map(int, l2.split(":"))
    return (h1 * 60 + m1) - (h2 * 60 + m2)

TIME_COMPARATORS = {
    "startTime": lambda a, b: _compare_time(a["start_date"], a["start_time"], b["start_date"], b["start_time"]),
    "arriveTime": lambda a, b: _compare_time(a["arrive_date"], a["arrive_time"], b["arrive_date"], b["arrive_time"]),
    "duration": lambda a, b: _compare_duration(a["lishi"], b["lishi"]),
}

# 车票查询接口字段
TicketDataKeys = [
    'secret_Sstr',
    'button_text_info',
    'train_no',
    'station_train_code',
    'start_station_telecode',
    'end_station_telecode',
    'from_station_telecode',
    'to_station_telecode',
    'start_time',
    'arrive_time',
    'lishi',
    'canWebBuy',
    'yp_info',
    'start_train_date',
    'train_seat_feature',
    'location_code',
    'from_station_no',
    'to_station_no',
    'is_support_card',
    'controlled_train_flag',
    'gg_num',
    'gr_num',
    'qt_num',
    'rw_num',
    'rz_num',
    'tz_num',
    'wz_num',
    'yb_num',
    'yw_num',
    'yz_num',
    'ze_num',
    'zy_num',
    'swz_num',
    'srrb_num',
    'yp_ex',
    'seat_types',
    'exchange_train_flag',
    'houbu_train_flag',
    'houbu_seat_limit',
    'yp_info_new',
    '40',
    '41',
    '42',
    '43',
    '44',
    '45',
    'dw_flag',
    '47',
    'stopcheckTime',
    'country_flag',
    'local_arrive_time',
    'local_start_time',
    '52',
    'bed_level_info',
    'seat_discount_info',
    'sale_time',
    '56',
]
