#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - calc - basic
# ==========================================
#
#
#
"""
import copy
import random
import string
import numpy as np
from scipy import stats
from datetime import datetime, timezone, timedelta
import pytz


def utc_dt(dt: datetime, tz: str = "utc", is_dst: bool = False) -> datetime:
    """
    Parameters
    ----------
    dt
    tz
    is_dst: only valid when an ambiguous time inputted

    Returns
    -------

    """
    tz = pytz.timezone(tz)
    return tz.localize(dt, is_dst).astimezone(pytz.utc)


def get_datetime(t_year: int, t_month: int, t_day: int, t_hour: int, t_min: int, t_seconds: int = 0,
                 tz_hour: int = 0, tz_min: int = 0, base=None):
    """
    :param t_year: int
    :param t_month: int
    :param t_day: int
    :param t_hour: int
    :param t_min: int
    :param t_seconds: int, default == 0
    :param tz_hour: int, default == 0
    :param tz_min: int, default == 0
    :param base: base time [y, m, d, h, m]
    :return: seconds since 1970-1-1 0:00
    """
    t_year, t_month, t_day, t_hour, t_min, t_seconds, tz_hour, tz_min = \
        int(t_year), int(t_month), int(t_day), int(t_hour), int(t_min), int(t_seconds), int(tz_hour), int(tz_min)
    if base is None:
        base = [1970, 1, 1, 0, 0]
    base = datetime(*base, tzinfo=timezone.utc).timestamp()
    ts = datetime(t_year, t_month, t_day, t_hour, t_min, t_seconds,
                  tzinfo=timezone(offset=timedelta(hours=tz_hour, minutes=tz_min))).timestamp()
    return ts - base


def merge_dicts(a: dict, b: dict):
    """
    a and b, two dictionary. Return updated a
        For example:
            a = {"1": 1, "2": {"1": 1, "2": 2, "3": 3, "5": {}, "6": [1, 2]}}
            b = {"1": 'b', "2": {"1": 'b', "2": 'b', "3": 'b', "4": 'b', "5": {"1": 'b'}, "6": [1, 2, 3]}}
            Will return {'1': 1, '2': {'1': 1, '2': 2, '3': 3, '5': {'1': 'b'}, '6': [1, 2], '4': 'b'}}
    """
    res = copy.deepcopy(a)
    for key, val in b.items():
        if key not in res.keys() and str(key).isnumeric():
            key = int(key)
        if key not in res.keys():
            res[key] = val
        elif isinstance(val, dict):
            res[key] = merge_dicts(res[key], val)
        else:
            continue
    return res


def update_dicts(a: dict, b: dict):
    """
    a and b, two dictionary. Return updated a
        For example:
            a = {"1": 1, "2": {"1": 1, "2": 2, "3": 3, "5": {}, "6": [1, 2]}}
            b = {"1": 'b', "2": {"1": 'b', "2": 'b', "3": 'b', "4": 'b', "5": {"1": 'b'}, "6": [1, 2, 3]}}
            Will return {'1': 'b', ...}
    """
    res = copy.deepcopy(a)
    for key, val in b.items():
        if key not in res.keys() and key.isnumeric():
            key = int(key)
        if key not in res.keys():
            res[key] = val
        elif isinstance(val, dict):
            res[key] = update_dicts(res[key], val)
        else:
            res[key] = val
    return res


def get_random_digits(length: int = 7) -> str:
    return ''.join(random.choices(string.digits, k=length))


def monte_carlo(func, inputs, confidence_level, **kwargs):
    """

    Parameters
    ----------
    func: Callable
    inputs: array
        two-dimensional array
    confidence_level: float
        [0, 1]

    Returns
    -------

    """
    N = len(inputs)
    l_range = int(0.5 * (1 - confidence_level) * N)
    r_range = N - l_range - 1
    values = np.transpose([func(*each, **kwargs) for each in inputs])
    cov = np.cov(values, rowvar=True)
    values = np.sort(values, axis=1)  # sort to find the lower and upper limitation at the given confidence level
    means = np.mean(values, axis=1).reshape(len(values), 1)
    limits = values[:, [l_range, r_range]]

    return np.concatenate((means, limits), axis=1), cov


def parser(v: str, t: type):
    if t == bool:
        if str(v).lower().rstrip() in ["true", "1"]:
            return True
    return t(v)

