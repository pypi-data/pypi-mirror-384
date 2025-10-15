# -*- coding: utf-8 -*-
# @Time    : 2024/03/15 13:53:41
# @Author  : yi
# @Desc    : 时间相关的工具

import time

time_type: str = r"%Y-%m-%d %H:%M:%S"
data_format: str = r"%Y-%m-%d"


def str2timestamp(time_str: str, format_str=time_type) -> int:
    struct_time = time.strptime(time_str, format_str)
    return int(time.mktime(struct_time))


def timestamp2str(timestamp: int, format_str=time_type) -> str:
    struct_time = time.localtime(timestamp)
    return time.strftime(format_str, struct_time)


def delta_day(start_time: str, format_str=time_type) -> int:
    """
    将时间字符串转为时间戳，再计算时间戳的差值，得到的差值即为距离当天开始的秒数
    """
    given_time_tuple = time.strptime(start_time, format_str)  # type: ignore
    given_time_in_seconds = time.mktime(given_time_tuple)  # type: ignore
    # 当天开始的时间
    start_of_day_tuple = (
        given_time_tuple.tm_year,
        given_time_tuple.tm_mon,
        given_time_tuple.tm_mday,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    # 将当天开始的时间转换为自纪元以来的秒数
    start_of_day_in_seconds = time.mktime(start_of_day_tuple)  # type: ignore
    # 计算两个时间戳的差值
    seconds_difference = given_time_in_seconds - start_of_day_in_seconds
    return int(seconds_difference)
