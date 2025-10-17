#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - calc - corr
# ==========================================
#
#
#
"""
import traceback

from . import arr, err, basic
import numpy as np
from typing import Tuple, List, Optional, Union
from types import MethodType
from math import exp, log


def blank(a0: list, e0: list, a1: list, e1: list):
    """
    :param a0: a list of tested isotope value
    :param e0: 1 sigma error of a0, list type
    :param a1: a list of blank isotope value
    :param e1: 1 sigma error of a1, list type
    :return: list of corrected data | error list
    """
    # Do not force negative value to zero in correcting blank...
    return arr.sub((a0, e0), (a1, e1))


def gain(a0: list, e0: list, a1: list, e1: list):
    """
    :param a0: a list of tested isotope value
    :param e0: 1 sigma error of a0, list type
    :param a1: a list of blank isotope value
    :param e1: 1 sigma error of a1, list type
    :return: list of corrected data | error list
    """
    # Do not force negative value to zero in correcting blank...
    return arr.div((a0, e0), (a1, e1))


def mdf(rm: float, srm: float, m1: float, m2: float, ra: float = 298.56,
        sra: float = 0):
    """
    :param rm: ratio 40a/36a
    :param srm: error of ratio in one sigma
    :param m1: Ar36 isotopic mass
    :param m2: Ar40 isotopic mass
    :param ra: theoretical 40a/36a
    :param sra: error of theoretical 40a/36a
    :return: linear mdf, error, exp mdf, error, pow mdf, error
    """
    sm1 = 0
    sm2 = 0
    delta_m = m2 - m1
    sdelta_m = err.add(sm2, sm1)
    ratio_m = m2 / m1
    sratio_m = err.div((m2, sm2), (m1, sm1))
    useRyu = False
    if not useRyu:
        # line, D = 1 + (ra / rm - 1) / dm  # Renne2009
        k1 = 1 + (ra / rm - 1) / delta_m
        k2 = err.div(((ra / rm - 1), err.div((ra, sra), (rm, srm))), (delta_m, sdelta_m))
        # exp, D = 1 + ln(ra / rm) / (m1 * ln(m2/m1))  # Renne2009
        try:
            k3 = (np.log(ra / rm) / np.log(ratio_m)) * (1 / m1) + 1
            v1 = err.log((ra / rm, err.div((ra, sra), (rm, srm))))
            v2 = err.log((ratio_m, sratio_m))
            v3 = err.div((np.log(ra / rm), v1), (np.log(ratio_m), v2))
            k4 = err.div((np.log(ra / rm) / np.log(ratio_m), v3), (m1, sm1))
        except Exception:
            k3, k4 = 0, 0
        # pow, D = pow(ra / rm, 1 / dm)  # Renne2009
        try:
            k5 = pow((ra / rm), (1 / delta_m))  # Renne2009, B.D. Turrin2010
            k6 = err.pow((ra / rm, err.div((ra, sra), (rm, srm))),
                         (1 / delta_m, err.div((1, 0), (delta_m, sdelta_m))))
        except Exception:
            k5, k6 = 0, 0
        return k1, k2, k2, k2, k3, k4, k4, k4, k5, k6, k6, k6
    else:
        mdf_line_2 = (rm / ra - 1) / delta_m  # Ryu et al., 2013
        return mdf_line_2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0


def discr(a0: list, e0: list, mdf: list, smdf: list, m: list, m40: list,
          isRelative=True, method="l"):
    """
    :param a0: a list of tested isotope value
    :param e0: 1 sigma error of a0, list type
    :param mdf: mass discrimination factor(MDF), list
    :param smdf: absolute error of MDF, list
    :param m: mass of isotope being corrected
    :param m40: mass of Ar40, default value is defined above
    :param isRelative: errors of params are in a relative format
    :param method: correction method, "l" or "linear", "e" or "exponential", "p" or "power"
    :return: corrected value | error of corrected value
    linear correction, MDF = [(Ar40/Ar36)true / (Ar40/Ar36)measure] * 1 / MD - 1 / MD + 1
    corr = blank_corrected / [MD * MDF - MD +1]
    """
    r0, r1 = [], []
    if isRelative:
        smdf = [smdf[i] * mdf[i] / 100 for i in range(len(smdf))]
    for i in range(min([len(arg) for arg in [a0, e0, mdf, smdf]])):
        delta_m = abs(m40[i] - m[i])
        ratio_m = abs(m40[i] / m[i]) if m[i] != 0 else 1
        if method.lower().startswith("l"):  # linear
            k0 = 1 / (delta_m * mdf[i] - delta_m + 1) if (delta_m * mdf[i] - delta_m + 1) != 0 else 0
            k1 = err.rec((delta_m * mdf[i] - delta_m + 1, smdf[i] * delta_m))
        elif method.lower().startswith("e"):  # exponential
            k0 = 1 / np.exp((mdf - 1) * m * np.log(m40 / m))
            k1 = err.rec((1 / k0, err.pow((np.e, 0), ((mdf - 1) * m * np.log(m40 / m), err.mul((mdf - 1, smdf), (m * np.log(m40 / m), 0))))))
        elif method.lower().startswith("p"):  # power
            k0 = 1 / (mdf[i] ** delta_m)
            k1 = err.rec((mdf[i] ** delta_m, err.pow((mdf[i], smdf[i]), (delta_m, 0))))
        else:
            k0 = 1
            k1 = 0
        r0.append(a0[i] * k0)
        r1.append(err.mul((a0[i], e0[i]), (k0, k1)))
    return [r0, r1]


def decay(a0: list, e0: list, t1: list, t2: list, t3: list, f: list, sf: list,
          unit: str = 'h', isRelative=True):
    """
    Parameters
    ----------
    a0
    e0
    t1 : [year, month, day, hour, min, (second)], test start time
    t2
    t3
    f
    sf
    unit
    isRelative

    Returns
    -------

    """
    r0, r1 = [], []
    if isRelative:
        sf = [sf[i] * f[i] / 100 for i in range(len(sf))]
    for i in range(len(a0)):
        k = get_decay_factor(t1[i], t2[i], t3[i], f[i], sf[i], unit)
        r0.append(a0[i] * k[0])
        r1.append(err.mul((a0[i], e0[i]), (k[0], k[1])))
    return [r0, r1]


def get_decay_factor(t1: list, t2: list, t3: list, f: float, sf: float,
                     unit: str = 'h'):
    """
    :param t1: [year, month, day, hour, min, (second)], test start time
    :param t2: irradiation end time for all cycles, [[year, month, day, hour, min],...]
    :param t3: irradiation durations for all cycles, list for all irradiation cycles, in hour
    :param f: decay constant of K
    :param sf: absolute error of f
    :param unit: unit of decay constant, input 'h' or 'a'
    :return: correction factor | error of factor | stand duration
    """
    v1 = []
    v2 = []
    e1 = []
    # t_year, t_month, t_day, t_hour, t_min = t1
    t_test_start = basic.get_datetime(*t1)  # the time when analysis began
    t2 = [basic.get_datetime(*i) for i in t2]  # the time when irradiation ended for all cycles, in second
    k2 = [t_test_start - i for i in t2]  # standing time in second between irradiation and analysing

    try:
        if unit == 'h':
            k2 = [float(i) / 3600 for i in k2]  # exchange to unit in hour
            t3 = [float(i) for i in t3]
        elif unit == 'a':
            k2 = [i / (3600 * 24 * 365.242) for i in k2]  # exchange to unit in year
            t3 = [float(i) / (24 * 365) for i in t3]
        for i in range(len(t3)):
            iP = 1  # power
            v1.append(iP * (1 - np.exp(-f * t3[i])) / (f * np.exp(f * k2[i])))
            e11 = t3[i] * np.exp(-f * t3[i]) / (f * np.exp(f * k2[i]))
            e12 = (np.exp(-f * t3[i]) - 1) * (1 + f * k2[i]) * np.exp(f * k2[i]) / (f * np.exp(f * k2[i])) ** 2
            e1.append(iP * (e11 + e12))
            v2.append(iP * t3[i])
        k0 = sum(v2) / sum(v1)
        k1 = err.div((sum(v2), 0), (sum(v1), pow(sum(e1) ** 2 * sf ** 2, 0.5)))
        # other error calculation equation in CALC
        # It is calculated based on an assumption that only one irradiation exist with total duration of sum of t3,
        # and the end time is the last irradiation finish time
        k1 = pow(
            ((sum(t3) * np.exp(f * k2[-1]) * (1 - np.exp(-f * sum(t3))) + f * sum(t3) * k2[-1] * np.exp(f * k2[-1]) * (
                    1 - np.exp(-f * sum(t3))) - f * sum(t3) * np.exp(f * k2[-1]) * sum(t3) * np.exp(-f * sum(t3))) / (
                     1 - np.exp(-f * sum(t3))) ** 2) ** 2 * sf ** 2, 0.5)
    except Exception as e:
        print(traceback.format_exc())
        return 1, 0
    else:
        return k0, k1


def get_irradiation_datetime_by_string(datetime_str: str):
    """
    Parameters
    ----------
    datetime_str : datatime string, like "2022-04-19-18-35D13.45S2022-04-19-04-19D6.7"
        return [2022-04-19T18:35:13.45, 2022-04-19T04:19:6.7]

    Returns
    -------

    """
    res = []
    if datetime_str == '' or datetime_str is None or (isinstance(datetime_str, float) and np.isnan(datetime_str)):
        return ['', 0]
    cycles = datetime_str.split('S')
    for cycle in cycles:
        [dt, hrs] = cycle.split('D')
        res = res + [dt, float(hrs)]
    return res


def get_method_fitting_law_by_name(method_str: str):
    """
    Parameters
    ----------
    method_str

    Returns
    -------

    """
    res = [False] * 3
    try:
        res[['Lin', 'Exp', 'Pow'].index(method_str.capitalize()[:3])] = True
    except (ValueError, AttributeError):
        pass
    return res


def random_normal_relative(mu, std, size):
    return np.random.normal(mu, std * mu / 100, size)


def random_normal_absolute(mu, std, size):
    if np.isnan(std):
        std = 0
    return np.random.normal(mu, std, size)


def Monte_Carlo_F(ar40m: Tuple[float, float], ar39m: Tuple[float, float], ar38m: Tuple[float, float],
                  ar37m: Tuple[float, float], ar36m: Tuple[float, float],
                  ar40b: Tuple[float, float], ar39b: Tuple[float, float], ar38b: Tuple[float, float],
                  ar37b: Tuple[float, float], ar36b: Tuple[float, float],
                  t1: List[float], t2: List[List[float]], t3: List[float],
                  R40v36a: Tuple[float, float], R38v36a: Tuple[float, float],
                  R39v37ca: Tuple[float, float], R36v37ca: Tuple[float, float], R38v37ca: Tuple[float, float],
                  R40v39k: Tuple[float, float], R38v39k: Tuple[float, float],
                  R36v38clp: Tuple[float, float],
                  L37ar: Tuple[float, float], L39ar: Tuple[float, float], L36cl: Tuple[float, float],
                  MDFunc: Union[MethodType],
                  MDF: Tuple[float, float],
                  M40: Tuple[float, float], M39: Tuple[float, float], M38: Tuple[float, float],
                  M37: Tuple[float, float], M36: Tuple[float, float],
                  G40: Tuple[float, float], G39: Tuple[float, float], G38: Tuple[float, float],
                  G37: Tuple[float, float], G36: Tuple[float, float],
                  stand_time_year: float, JNFactor: Tuple[float, float],
                  **options):
    """

    Parameters
    ----------
    ar40m
    ar39m
    ar38m
    ar37m
    ar36m
    t1
    t2
    t3
    R40v36a
    R38v36a
    R39v37ca
    R36v37ca
    R40v39k
    R38v39k
    R36v38clp
    L37ar
    L39ar
    L36cl
    MDFunc
    MDF
    JNFactor
    options

    Returns
    -------

    """
    # define parameters

    MDFunc = lambda _M40, _mass, _mdf: 1 / ((_M40 - _mass) * (_mdf - 1) + 1)

    Monte_Carlo_Size = 10000

    # generate random
    ar40m = random_normal_absolute(*ar40m, size=Monte_Carlo_Size)
    ar39m = random_normal_absolute(*ar39m, size=Monte_Carlo_Size)
    ar38m = random_normal_absolute(*ar38m, size=Monte_Carlo_Size)
    ar37m = random_normal_absolute(*ar37m, size=Monte_Carlo_Size)
    ar36m = random_normal_absolute(*ar36m, size=Monte_Carlo_Size)
    ar40b = random_normal_absolute(*ar40b, size=Monte_Carlo_Size)
    ar39b = random_normal_absolute(*ar39b, size=Monte_Carlo_Size)
    ar38b = random_normal_absolute(*ar38b, size=Monte_Carlo_Size)
    ar37b = random_normal_absolute(*ar37b, size=Monte_Carlo_Size)
    ar36b = random_normal_absolute(*ar36b, size=Monte_Carlo_Size)

    MDF =random_normal_relative(*MDF, size=Monte_Carlo_Size)

    M40 = random_normal_relative(*M40, size=Monte_Carlo_Size)
    M39 = random_normal_relative(*M39, size=Monte_Carlo_Size)
    M38 = random_normal_relative(*M38, size=Monte_Carlo_Size)
    M37 = random_normal_relative(*M37, size=Monte_Carlo_Size)
    M36 = random_normal_relative(*M36, size=Monte_Carlo_Size)

    G40 = random_normal_relative(*G40, size=Monte_Carlo_Size)
    G39 = random_normal_relative(*G39, size=Monte_Carlo_Size)
    G38 = random_normal_relative(*G38, size=Monte_Carlo_Size)
    G37 = random_normal_relative(*G37, size=Monte_Carlo_Size)
    G36 = random_normal_relative(*G36, size=Monte_Carlo_Size)

    L36cl = random_normal_relative(*L36cl, size=Monte_Carlo_Size)
    L37ar = random_normal_relative(*L37ar, size=Monte_Carlo_Size)
    L39ar = random_normal_relative(*L39ar, size=Monte_Carlo_Size)

    R40v36a = random_normal_relative(*R40v36a, size=Monte_Carlo_Size)
    R38v36a = random_normal_relative(*R38v36a, size=Monte_Carlo_Size)
    R39v37ca = random_normal_relative(*R39v37ca, size=Monte_Carlo_Size)
    R38v37ca = random_normal_relative(*R38v37ca, size=Monte_Carlo_Size)
    R36v37ca = random_normal_relative(*R36v37ca, size=Monte_Carlo_Size)
    R40v39k = random_normal_relative(*R40v39k, size=Monte_Carlo_Size)
    R38v39k = random_normal_relative(*R38v39k, size=Monte_Carlo_Size)
    R36v38clp = random_normal_relative(*R36v38clp, size=Monte_Carlo_Size)

    JNFactor = random_normal_absolute(*JNFactor, size=Monte_Carlo_Size)

    blank_gain_corr = options.get('blank_gain_corr', True)

    def do_simulation():
        i = 0
        while i < Monte_Carlo_Size:
            P40Mdf = MDFunc(M40[i], M40[i], MDF[i])
            P39Mdf = MDFunc(M40[i], M39[i], MDF[i])
            P38Mdf = MDFunc(M40[i], M38[i], MDF[i])
            P37Mdf = MDFunc(M40[i], M37[i], MDF[i])
            P36Mdf = MDFunc(M40[i], M36[i], MDF[i])
            P37Decay = get_decay_factor(t1, t2, t3, L37ar[i], sf=0)[0]
            P39Decay = get_decay_factor(t1, t2, t3, L39ar[i], sf=0)[0]

            _ar40m = ar40m[i]

            _ar36 = (ar36m[i] / G36[i] - ar36b[i] / (G36[i] if blank_gain_corr else 1)) * P36Mdf
            _ar37 = (ar37m[i] / G37[i] - ar37b[i] / (G37[i] if blank_gain_corr else 1)) * P37Mdf
            _ar38 = (ar38m[i] / G38[i] - ar38b[i] / (G38[i] if blank_gain_corr else 1)) * P38Mdf
            _ar39 = (ar39m[i] / G39[i] - ar39b[i] / (G39[i] if blank_gain_corr else 1)) * P39Mdf
            _ar40 = (ar40m[i] / G40[i] - ar40b[i] / (G40[i] if blank_gain_corr else 1)) * P40Mdf

            _ar37ca = _ar37 * P37Decay
            _ar39k = _ar39 * P39Decay - _ar37ca * R39v37ca[i]
            _ar38res = _ar38 - _ar39k * R38v39k[i] - _ar37ca * R38v37ca[i]
            _ar36res = _ar36 - _ar37ca * R36v37ca[i]
            _ar36cl = (_ar36res - _ar38res / R38v36a[i]) / (1 - 1 / (R36v38clp[i] * (1 - exp(-1 * L36cl[i] * stand_time_year)) * R38v36a[i]))
            _ar36a = _ar36res - _ar36cl
            _ar40r = _ar40 - _ar36a * R40v36a[i] - _ar39k * R40v39k[i]
            _ar40ar = _ar40 - _ar39k * R40v39k[i]
            _ar39k = _ar39k * JNFactor[i]
            _f = _ar40r / _ar39k
            i += 1
            # yield _f, _ar36, _ar37, _ar38, _ar39, _ar40, _ar36a, _ar37ca, _ar39k, _ar40r, _ar36cl
            yield _f, _ar36a, _ar39k, _ar40ar

    simulation = do_simulation()
    F = []
    ar36 = []
    ar37 = []
    ar38 = []
    ar39 = []
    ar40 = []

    ar36a = []
    ar37ca = []
    ar39k = []
    ar40r = []
    ar36cl = []

    nor_x = []
    nor_y = []
    inv_x = []
    inv_y = []
    for each in simulation:
        F.append(each[0])
        nor_x.append(each[2] / each[1])
        nor_y.append(each[3] / each[1])
        inv_x.append(each[2] / each[3])
        inv_y.append(each[1] / each[3])
        # ar36.append(each[1])
        # ar37.append(each[2])
        # ar38.append(each[3])
        # ar39.append(each[4])
        # ar40.append(each[5])
        # ar36a.append(each[6])
        # ar37ca.append(each[7])
        # ar39k.append(each[8])
        # ar40r.append(each[9])
        # ar36cl.append(each[10])

    print(f"{np.mean(F) = }, {np.std(F) = }")

    # print("F = {0} ± {1}".format(np.mean(F), np.std(F)))
    #
    # with open("ar36m.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar36m]))
    # with open("ar37m.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar37m]))
    # with open("ar38m.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar38m]))
    # with open("ar39m.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar39m]))
    # with open("ar40m.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar40m]))
    #
    # with open("ar36.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar36]))
    # with open("ar37.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar37]))
    # with open("ar38.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar38]))
    # with open("ar39.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar39]))
    # with open("ar40.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar40]))
    #
    # with open("ar36a.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar36a]))
    # with open("ar36cl.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar36cl]))
    # with open("ar37ca.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar37ca]))
    # with open("ar39k.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar39k]))
    # with open("ar40r.txt", 'w') as f:  # save serialized json data to a readable text
    #     f.writelines("\n".join([str(i) for i in ar40r]))
    # F, sF,
    return np.mean(F), np.std(F), \
           np.mean(nor_x), np.std(nor_x), np.mean(nor_y), np.std(nor_y), \
           np.cov(nor_x, nor_y)[0][1] / (np.std(nor_x) * np.std(nor_y)), \
           np.mean(inv_x), np.std(inv_x), np.mean(inv_y), np.std(inv_y), \
           np.cov(inv_x, inv_y)[0][1] / (np.std(inv_x) * np.std(inv_y))




