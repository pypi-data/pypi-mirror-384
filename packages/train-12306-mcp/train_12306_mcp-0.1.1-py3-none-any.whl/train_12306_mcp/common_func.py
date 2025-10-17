from datetime import datetime

#  车票过滤用
class TrainFilter:
    """火车票过滤器类"""

    @staticmethod
    def G(ticket_info):
        """高铁/城际"""
        return ticket_info.get('start_train_code', '').startswith(('G', 'C'))

    @staticmethod
    def D(ticket_info):
        """动车"""
        return ticket_info.get('start_train_code', '').startswith('D')

    @staticmethod
    def Z(ticket_info):
        """直达特快"""
        return ticket_info.get('start_train_code', '').startswith('Z')

    @staticmethod
    def T(ticket_info):
        """特快"""
        return ticket_info.get('start_train_code', '').startswith('T')

    @staticmethod
    def K(ticket_info):
        """快速"""
        return ticket_info.get('start_train_code', '').startswith('K')

    @staticmethod
    def O(ticket_info):
        """其他"""
        return not any([
            TrainFilter.G(ticket_info),
            TrainFilter.D(ticket_info),
            TrainFilter.Z(ticket_info),
            TrainFilter.T(ticket_info),
            TrainFilter.K(ticket_info)
        ])

    @staticmethod
    def F(ticket_info):
        """复兴号"""
        if 'dw_flag' in ticket_info:
            return '复兴号' in ticket_info['dw_flag']
        return '复兴号' in ticket_info.get('ticketList', [{}])[0].get('dw_flag', '')

    @staticmethod
    def S(ticket_info):
        """智能动车组"""
        if 'dw_flag' in ticket_info:
            return '智能动车组' in ticket_info['dw_flag']
        return '智能动车组' in ticket_info.get('ticketList', [{}])[0].get('dw_flag', '')

class TimeComparator:
    """时间比较器类"""

    @staticmethod
    def start_time(ticket_info_a, ticket_info_b):
        """比较出发时间"""
        # 比较日期
        time_a = datetime.strptime(ticket_info_a['start_date'], '%Y-%m-%d')
        time_b = datetime.strptime(ticket_info_b['start_date'], '%Y-%m-%d')

        if time_a != time_b:
            return (time_a - time_b).total_seconds()

        # 比较具体时间
        start_time_a = list(map(int, ticket_info_a['start_time'].split(':')))
        start_time_b = list(map(int, ticket_info_b['start_time'].split(':')))

        if start_time_a[0] != start_time_b[0]:
            return start_time_a[0] - start_time_b[0]

        return start_time_a[1] - start_time_b[1]

    @staticmethod
    def arrive_time(ticket_info_a, ticket_info_b):
        """比较到达时间"""
        # 比较日期
        time_a = datetime.strptime(ticket_info_a['arrive_date'], '%Y-%m-%d')
        time_b = datetime.strptime(ticket_info_b['arrive_date'], '%Y-%m-%d')

        if time_a != time_b:
            return (time_a - time_b).total_seconds()

        # 比较具体时间
        arrive_time_a = list(map(int, ticket_info_a['arrive_time'].split(':')))
        arrive_time_b = list(map(int, ticket_info_b['arrive_time'].split(':')))

        if arrive_time_a[0] != arrive_time_b[0]:
            return arrive_time_a[0] - arrive_time_b[0]

        return arrive_time_a[1] - arrive_time_b[1]

    @staticmethod
    def duration(ticket_info_a, ticket_info_b):
        """比较历时"""
        lishi_time_a = list(map(int, ticket_info_a['lishi'].split(':')))
        lishi_time_b = list(map(int, ticket_info_b['lishi'].split(':')))

        if lishi_time_a[0] != lishi_time_b[0]:
            return lishi_time_a[0] - lishi_time_b[0]

        return lishi_time_a[1] - lishi_time_b[1]

def filter_tickets_info(tickets_info, train_filter_flags=None, earliest_start_time=0,
                        latest_start_time=24, sort_flag='', sort_reverse=False, limited_num=0):
    """
    过滤和排序火车票信息

    Args:
        tickets_info: 火车票信息列表
        train_filter_flags: 火车类型过滤标志列表
        earliest_start_time: 最早出发时间(小时)
        latest_start_time: 最晚出发时间(小时)
        sort_flag: 排序标志
        sort_reverse: 是否反向排序
        limited_num: 限制返回数量，0表示不限制

    Returns:
        过滤和排序后的火车票信息列表
    """
    if train_filter_flags is None:
        train_filter_flags = []

    # 火车类型过滤
    if not train_filter_flags:
        result = tickets_info.copy()
    else:
        result = []
        for ticket_info in tickets_info:
            for filter_flag in train_filter_flags:
                filter_func = getattr(TrainFilter, filter_flag, None)
                if filter_func and filter_func(ticket_info):
                    result.append(ticket_info)
                    break

    # 出发时间过滤
    result = [
        ticket_info for ticket_info in result
        if earliest_start_time <= int(ticket_info['start_time'].split(':')[0]) < latest_start_time
    ]

    # 排序
    if sort_flag and hasattr(TimeComparator, sort_flag):
        comparator = getattr(TimeComparator, sort_flag)
        result.sort(key=lambda x: comparator, reverse=sort_reverse)

    # 数量限制
    if limited_num > 0:
        return result[:limited_num]

    return result


# 使用示例
if __name__ == "__main__":

    # 示例数据
    sample_tickets = [
        {
            'start_train_code': 'G123',
            'start_date': '2024-01-01',
            'start_time': '08:30',
            'arrive_date': '2024-01-01',
            'arrive_time': '12:00',
            'lishi': '03:30',
            'dw_flag': '复兴号',
            'ticketList': [{'dw_flag': '复兴号'}]
        },
        {
            'start_train_code': 'D456',
            'start_date': '2024-01-01',
            'start_time': '09:15',
            'arrive_date': '2024-01-01',
            'arrive_time': '13:45',
            'lishi': '04:30',
            'ticketList': [{'dw_flag': ''}]
        }
    ]

    # 过滤高铁和动车
    filtered = filter_tickets_info(sample_tickets, ['G', 'D'])
    print(f"过滤后数量: {len(filtered)}")