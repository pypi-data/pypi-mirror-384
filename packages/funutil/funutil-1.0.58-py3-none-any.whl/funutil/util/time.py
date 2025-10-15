import time
from datetime import datetime, timedelta

from funutil.util.log import getLogger

logger = getLogger("funutil")


_DAY_SECOND = 24 * 60 * 60
_HOUR_SECOND = 60 * 60
_TEN_MINUTE_SECOND = 10 * 60
_MINUTE_SECOND = 60


class WorkTime:
    def __init__(self):
        pass

    @staticmethod
    def time_to_end(
        time_str=None,
        format_str="%Y-%m-%d %H:%M:%S",
        circle_time=_DAY_SECOND,
        threshold_time=60,
    ):
        if time_str is None:
            unix = int(time.mktime(datetime.datetime.now().timetuple()))
        elif isinstance(time_str, int) or isinstance(time_str, float):
            unix = int(time_str)
        else:
            localtime = datetime.datetime.strptime(time_str, format_str)
            unix = int(time.mktime(localtime.timetuple()))

        logger.debug(f"本地时间为 :{unix}")

        second_mod = unix % circle_time
        if second_mod > _DAY_SECOND - threshold_time:
            logger.debug("time to end")
            return True
        return False

    def time_to_day_end(self, *args, **kwargs):
        return self.time_to_end(
            circle_time=_DAY_SECOND, threshold_time=60, *args, **kwargs
        )

    def time_to_hour_end(self, *args, **kwargs):
        return self.time_to_end(
            circle_time=_HOUR_SECOND, threshold_time=60, *args, **kwargs
        )

    def time_to_ten_minute_end(self, *args, **kwargs):
        return self.time_to_end(
            circle_time=_TEN_MINUTE_SECOND, threshold_time=30, *args, **kwargs
        )

    def time_to_minute_end(self, *args, **kwargs):
        return self.time_to_end(
            circle_time=_MINUTE_SECOND, threshold_time=10, *args, **kwargs
        )

    def test(self):
        time_str = "2021-01-01 10:32:32"
        self.time_to_day_end(time_str=time_str)
        self.time_to_hour_end(time_str=time_str)
        self.time_to_ten_minute_end(time_str=time_str)

        self.time_to_day_end()
        self.time_to_hour_end()
        self.time_to_ten_minute_end()

        unix = int(time.mktime(datetime.datetime.now().timetuple()))
        self.time_to_day_end(unix)
        self.time_to_hour_end(unix)
        self.time_to_ten_minute_end(unix)


def now2unix():
    """
    当前时间戳
    :return:
    """
    return int(time.mktime(time.localtime()))


def now2time(time_type="%Y-%m-%d %H:%M:%S"):
    """
    当前时间
    :return:
    """
    return time.strftime(time_type, time.localtime())


def time2unix(time_str, time_type="%Y-%m-%d %H:%M:%S"):
    """
    > str2unix('2013-10-10 23:40:00')

    '2013-10-10 23:40:00'
    :param time_str:
    :param time_type: '%Y-%m-%d %H:%M:%S'
    :return:
    """
    return int(time.mktime(time.strptime(time_str, time_type)))


def unix2time(time_stamp, time_type="%Y-%m-%d %H:%M:%S"):
    return time.strftime(time_type, time.localtime(time_stamp))


def month_first_datetime(months):
    today = datetime.today()
    months = today.month + months - 1
    years = -int((months % 12 - months) / 12)
    months = months % 12 + 1

    return datetime(today.year + years, months, 1)


def month_during(months):
    first = month_first_datetime(months)
    last = month_first_datetime(months + 1) - timedelta(seconds=1)
    return months, first, last


def week_during(weeks):
    today = datetime.today()
    first = today + timedelta(weeks=weeks) - timedelta(days=today.weekday())
    first = datetime(first.year, first.month, first.day)
    last = first + timedelta(weeks=1) - timedelta(seconds=1)
    return first, last


def day_during(days):
    today = datetime.today()
    first = today + timedelta(days=days)
    first = datetime(first.year, first.month, first.day)
    last = first + timedelta(days=1) - timedelta(seconds=1)
    return first, last


def example():
    print(now2unix())
    print(now2time())
    print(time2unix(now2time()))
    print(unix2time(now2unix()))
