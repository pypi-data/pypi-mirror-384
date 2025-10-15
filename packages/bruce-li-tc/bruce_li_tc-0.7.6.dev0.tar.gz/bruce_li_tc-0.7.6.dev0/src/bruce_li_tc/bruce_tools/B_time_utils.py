"""
轻量级时间处理工具库

功能概述:
1. 时间获取：获取当前时间、日期、时间戳等
2. 时间转换：时间戳、字符串、datetime对象互转
3. 时间计算：日期加减、时间差计算、工作日计算
4. 时间判断：闰年、周末、日期范围判断
5. 格式化输出：自定义时间格式输出
6. 时区转换：支持常用时区转换


"""

import datetime
import time
import pytz
from dateutil.relativedelta import relativedelta


class TimeUtils:
    """时间处理工具类"""

    @staticmethod
    def now(fmt: str = None, tz: str = "Asia/Shanghai") -> str:
        """
        获取当前时间

        参数:
            fmt: 格式化字符串，默认None返回datetime对象
            tz: 时区名称，默认'Asia/Shanghai'

        返回:
            格式化字符串或datetime对象

        示例:
            >>> TimeUtils.now()
            datetime.datetime(2025, 6, 30, 14, 30, 25)
            >>> TimeUtils.now('%Y-%m-%d %H:%M:%S')
            '2025-06-30 14:30:25'
        """
        tz_obj = pytz.timezone(tz)
        now = datetime.datetime.now(tz_obj)
        return now.strftime(fmt) if fmt else now

    @staticmethod
    def today(fmt: str = "%Y-%m-%d") -> str:
        """
        获取今天日期

        参数:
            fmt: 日期格式，默认'%Y-%m-%d'

        返回:
            格式化日期字符串

        示例:
            >>> TimeUtils.today()
            '2025-06-30'
        """
        return datetime.datetime.now().strftime(fmt)

    @staticmethod
    def timestamp(ms: bool = False) -> float:
        """
        获取当前时间戳

        参数:
            ms: 是否返回毫秒级时间戳，默认False

        返回:
            时间戳(秒级或毫秒级)

        示例:
            >>> TimeUtils.timestamp()
            1727584225.0
            >>> TimeUtils.timestamp(ms=True)
            1727584225123.0
        """
        return time.time() * 1000 if ms else time.time()

    @staticmethod
    def str_to_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
        """
        字符串转datetime对象

        参数:
            dt_str: 日期时间字符串
            fmt: 字符串格式，默认'%Y-%m-%d %H:%M:%S'

        返回:
            datetime对象

        示例:
            >>> TimeUtils.str_to_datetime("2025-06-30 14:30:25")
            datetime.datetime(2025, 6, 30, 14, 30, 25)
        """
        return datetime.datetime.strptime(dt_str, fmt)

    @staticmethod
    def datetime_to_str(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        datetime对象转字符串

        参数:
            dt: datetime对象
            fmt: 输出格式，默认'%Y-%m-%d %H:%M:%S'

        返回:
            格式化字符串

        示例:
            >>> dt = datetime.datetime(2025, 6, 30, 14, 30, 25)
            >>> TimeUtils.datetime_to_str(dt)
            '2025-06-30 14:30:25'
        """
        return dt.strftime(fmt)

    @staticmethod
    def timestamp_to_datetime(ts: float, tz: str = None) -> datetime.datetime:
        """
        时间戳转datetime对象

        参数:
            ts: 时间戳(秒级)
            tz: 时区名称，默认None(本地时区)

        返回:
            datetime对象

        示例:
            >>> TimeUtils.timestamp_to_datetime(1727584225)
            datetime.datetime(2025, 6, 30, 14, 30, 25)
        """
        dt = datetime.datetime.fromtimestamp(ts)
        if tz:
            return dt.astimezone(pytz.timezone(tz))
        return dt

    @staticmethod
    def datetime_to_timestamp(dt: datetime.datetime) -> float:
        """
        datetime对象转时间戳

        参数:
            dt: datetime对象

        返回:
            时间戳(秒级)

        示例:
            >>> dt = datetime.datetime(2025, 6, 30, 14, 30, 25)
            >>> TimeUtils.datetime_to_timestamp(dt)
            1727584225.0
        """
        return dt.timestamp()

    @staticmethod
    def add_days(days: int, base_date: datetime.datetime = None) -> datetime.datetime:
        """
        日期加减天数

        参数:
            days: 要加减的天数(正数为加，负数为减)
            base_date: 基准日期，默认当前日期

        返回:
            计算后的datetime对象

        示例:
            >>> TimeUtils.add_days(7)  # 7天后
            datetime.datetime(2025, 7, 7, 14, 30, 25)
            >>> TimeUtils.add_days(-30)  # 30天前
            datetime.datetime(2025, 5, 31, 14, 30, 25)
        """
        base = base_date or datetime.datetime.now()
        return base + datetime.timedelta(days=days)

    @staticmethod
    def add_months(months: int, base_date: datetime.datetime = None) -> datetime.datetime:
        """
        日期加减月份

        参数:
            months: 要加减的月数(正数为加，负数为减)
            base_date: 基准日期，默认当前日期

        返回:
            计算后的datetime对象

        示例:
            >>> TimeUtils.add_months(3)  # 3个月后
            datetime.datetime(2025, 9, 30, 14, 30, 25)
            >>> TimeUtils.add_months(-6)  # 半年前
            datetime.datetime(2024, 12, 30, 14, 30, 25)
        """
        base = base_date or datetime.datetime.now()
        return base + relativedelta(months=months)

    @staticmethod
    def time_diff(start: datetime.datetime, end: datetime.datetime, unit: str = "seconds") -> float:
        """
        计算两个时间的差值

        参数:
            start: 开始时间
            end: 结束时间
            unit: 返回单位(seconds/minutes/hours/days)

        返回:
            时间差值

        示例:
            >>> start = datetime.datetime(2025, 6, 30, 10, 0)
            >>> end = datetime.datetime(2025, 6, 30, 14, 30)
            >>> TimeUtils.time_diff(start, end, 'hours')
            4.5
        """
        delta = end - start
        seconds = delta.total_seconds()

        units = {
            "seconds": seconds,
            "minutes": seconds / 60,
            "hours": seconds / 3600,
            "days": seconds / 86400
        }
        return units.get(unit, seconds)

    @staticmethod
    def is_weekend(dt: datetime.datetime = None) -> bool:
        """
        判断是否为周末

        参数:
            dt: 日期时间对象，默认当前时间

        返回:
            True/False

        示例:
            >>> # 2025-06-30 是星期一
            >>> TimeUtils.is_weekend()
            False
        """
        dt = dt or datetime.datetime.now()
        return dt.weekday() in [5, 6]  # 5=周六, 6=周日

    @staticmethod
    def is_leap_year(year: int = None) -> bool:
        """
        判断是否为闰年

        参数:
            year: 年份，默认当前年

        返回:
            True/False

        示例:
            >>> TimeUtils.is_leap_year(2024)
            True
            >>> TimeUtils.is_leap_year(2025)
            False
        """
        year = year or datetime.datetime.now().year
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    @staticmethod
    def business_days(start: datetime.datetime, end: datetime.datetime) -> int:
        """
        计算两个日期之间的工作日数量(排除周末)

        参数:
            start: 开始日期
            end: 结束日期

        返回:
            工作日数量

        示例:
            >>> start = datetime.datetime(2025, 6, 30)  # 周一
            >>> end = datetime.datetime(2025, 7, 4)    # 周五
            >>> TimeUtils.business_days(start, end)
            5
        """
        days = (end - start).days + 1
        full_weeks, extra_days = divmod(days, 7)

        # 完整周的工作日数量
        business_days = full_weeks * 5

        # 计算剩余天数中的工作日
        start_weekday = start.weekday()
        for day in range(extra_days):
            if (start_weekday + day) % 7 < 5:  # 0-4 表示周一到周五
                business_days += 1

        return business_days

    @staticmethod
    def convert_timezone(dt: datetime.datetime, from_tz: str, to_tz: str) -> datetime.datetime:
        """
        时区转换

        参数:
            dt: 原始时间(datetime对象)
            from_tz: 原始时区
            to_tz: 目标时区

        返回:
            转换后的datetime对象

        示例:
            >>> dt = datetime.datetime(2025, 6, 30, 9, 0)
            >>> TimeUtils.convert_timezone(dt, 'Asia/Shanghai', 'America/New_York')
            datetime.datetime(2025, 6, 29, 21, 0)
        """
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)

        # 设置原始时区
        localized = from_zone.localize(dt) if dt.tzinfo is None else dt
        return localized.astimezone(to_zone)

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化时间间隔为易读字符串

        参数:
            seconds: 时间间隔(秒)

        返回:
            易读的时间间隔字符串

        示例:
            >>> TimeUtils.format_duration(3665)
            '1小时1分钟5秒'
        """
        intervals = (
            ('天', 86400),
            ('小时', 3600),
            ('分钟', 60),
            ('秒', 1)
        )

        result = []
        for name, count in intervals:
            value = int(seconds // count)
            if value:
                seconds -= value * count
                result.append(f"{value}{name}")

        return ''.join(result) if result else '0秒'


"""
使用@staticmethod的主要原因

无需实例化即可调用
```python
# 不需要创建实例，直接通过类名调用
TimeUtils.now()
```

如果使用实例方法，每次调用都需要先创建对象：
```python
# 不推荐的写法（需要实例化）
utils = TimeUtils()
utils.now()
```

避免不必要的状态存储

    时间工具方法通常是无状态的（stateless）

    不需要维护实例变量（没有self）

    所有操作都基于输入参数

符合工具类的设计原则

    类似Java的Math类或Python的datetime模块

    作为功能函数的集合而非有状态的对象

更清晰的API设计
```python
# 静态方法明确表示这是工具函数
TimeUtils.add_days(7)

# 对比实例方法（暗示可能有内部状态）
time_util = TimeUtils()
time_util.add_days(7)  # 看起来像在修改实例状态
```
内存效率

    静态方法不会创建实例

    减少内存开销（特别是频繁调用时）
"""