#  Copyright (C) 2024 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2024 Yang 
# ararpy - test2
# ==========================================
#
#
# 
"""
import os
import ararpy as ap
import numpy as np
import scipy
from math import exp, log, sqrt

# kfcs = [1.634, 1.639, 1.665, 1.641, 1.639, 1.641]
# skfcs = [0.023, 0.016, 0.023, 0.010, 0.008, 0.009]
#
# res = ap.calc.arr.wtd_mean(kfcs, skfcs, sf=1, adjust_error=False)
# # res =  (1.6408482971738128, 0.004679971790869418, 6, 0.251709745316985, 1.258548726584925, 0.9391386247331938)
# print(res)

LE = 0.580E-10
sLE = 0.007E-10
LB = 4.884E-10
sLB = 0.049E-10
LT = 5.5545E-10
sLT = 0.0109E-10
K = 1.6408E-3
sK = 0.0047E-3

T = [
    0.001919,
    17.42, 125.65, 133.06, 201.27, 242.14, 252.17, 252.4,
    252.6, 253.02, 253.24, 253.68, 257.3, 327.99, 454.59, 1094.2, 2067.5
]

sT = [
    0.0000000001,
    0.03, 0.17, 0.26, 0.13, 0.45, 0.36, 0.33, 0.33, 0.5,
    0.33, 0.3, 0.3, 0.45, 0.56, 1.15, 1.4
]

T[1:] = [i - 0.09 for i in T[1:]]
sT[1:] = [sqrt(i ** 2 + 0.077 ** 2) for i in sT[1:]]

R = [
    6.789E-05,
    0.60556, 4.5494, 4.8205, 7.4636, 9.0619, 9.49831, 9.4918, 9.51018,
    9.4958, 9.52952, 9.53910, 9.69866, 12.60389, 18.09, 52.9011, 135.63893
]

sR = [
    5.50E-07,
    0.00249, 0.0061, 0.01535, 0.0072, 0.0122, 0.01022, 0.0041, 0.00594,
    0.0122, 0.00680, 0.00846, 0.00532, 0.01475, 0.0523, 0.1162, 0.18206
]

Opt_R = [
    6.73E-05, 0.6076, 4.5531, 4.8319, 7.4616, 9.0676, 9.4935, 9.4919, 9.5087, 9.5016, 9.5289, 9.5408, 9.6975, 12.604, 18.114, 52.796, 135.72
]

Opt_LE = 0.5755E-10
Opt_sLE = 0.0016E-10
Opt_LB = 4.9737E-10
Opt_sLB = 0.0093E-10
Opt_LT = 5.5492E-10
Opt_sLT = 0.0093E-10
Opt_K = 1.6418E-3
Opt_sK = 0.0045E-3
# R = 4.82050
# sR = 0.01535
# t = 133.06
# st = 0.26


def square(a, b, sb):
    return ((a - b) / sb) ** 2


def get_ti(_le, _lb, _k, _ri):
    return log((_le + _lb) * _k * _ri / _le + 1) / (_le + _lb) / 1000000


def get_standards(random: bool = False):


    return T, R, LE, LB, K, LT


def func(args):
    le, lb, k = args[:3]

    # r = R
    r = args[3:]
    # ti = args[3:int(3 + len(args[3:]) / 2)]
    # ri = args[int(3 + len(args[3:]) / 2):]

    t = [get_ti(le, lb, k, ri) for ri in r]

    return sum([square(ti, T[i], sT[i]) / 2 + square(r[i], R[i], sR[i]) / 2 for i, ti in enumerate(t)]
               ) + square(le, LE, sLE) + square(lb, LB, sLB) + square(k, K, sK) + square(le + lb, LT, sLT)

    # return sum([(square(ti[i], ti[i], st) + square(ri[i], ri[i], sR)) / 2 for i in range(len(ti))]
    #            ) + square(le, LE, sLE) + square(lb, LB, sLB) + square(k, K, sK) + square(le + lb, LT, sLT)

    # return (square(le, LE, sLE) + square(lb, LB, sLB) + square(k, K, sK) + square(le + lb, LT, sLT)) * 17


def MF_regerssion(x0):
    # print("\n ======== 最小值结果 ======== \n")
    a = scipy.optimize.minimize(fun=func, x0=x0, method="Nelder-Mead", options={"maxiter": 10000}, tol=0.00000000001)
    return a["x"].tolist()


def calc_age(R: float, sR: float, le: list, lb: list, k: list):
    R = np.random.normal(R, sR, len(le))
    res = [1 / (le[i] + lb[i]) * log((le[i] + lb[i]) / le[i] * k[i] * R[i] + 1) / 1000000 for i in range(len(le))]
    return np.mean(res), np.std(res)


def get_statistic(a0):
    k0 = np.mean(a0)
    k1 = np.std(a0)
    k2 = np.var(a0)

    return k0, k1, k2


def this_is_to_identify_that_monte_carlo_is_not_better_than_linear(R = 50, sR = 0.25):
    """
    Renne 2010 conclude that using their results people should using monte carlo method to estimate uncertainty in ages,
    however, it is a fact that their random values of LE, LB and K are generated according to the variances and covariances
    in table 4a and b, so in this way continuing to use monte carlo is just enlarging uncertainly.

    I think with many random parameter sets, the uncertainties determined by the monte carlo method should display variance
    that can be calculated by linear method.
    """

    print("\n========== result 3 ==========\n")

    res = ap.files.basic.read("results3.txt")
    le = [i[0] for i in res]
    lb = [i[1] for i in res]
    k = [i[2] for i in res]

    print(np.cov(le, k))
    print(np.cov(le, k)[1][0] / (np.std(le) * np.std(k)))

    print(f"LE = " + '{0} ± {1}'.format(*get_statistic(le)[:2]))
    print(f"LB = " + '{0} ± {1}'.format(*get_statistic(lb)[:2]))
    print(f"K = " + '{0} ± {1}'.format(*get_statistic(k)[:2]))
    print(f"age = " + '{0} ± {1}'.format(*calc_age(R, sR, le, lb, k)[:2]))


    print("\n========== result 2 ==========\n")

    res = ap.files.basic.read("results2.txt")
    le = [i[0] for i in res]
    lb = [i[1] for i in res]
    k = [i[2] for i in res]

    print(np.cov(le, k))
    print(np.cov(le, k)[1][0] / (np.std(le) * np.std(k)))

    print(f"LE = " + '{0} ± {1}'.format(*get_statistic(le)[:2]))
    print(f"LB = " + '{0} ± {1}'.format(*get_statistic(lb)[:2]))
    print(f"K = " + '{0} ± {1}'.format(*get_statistic(k)[:2]))
    print(f"age = " + '{0} ± {1}'.format(*calc_age(R, sR, le, lb, k)[:2]))


    print("\n========== result 1 ==========\n")

    res = ap.files.basic.read("results.txt")
    le = [i[0] for i in res]
    lb = [i[1] for i in res]
    k = [i[2] for i in res]

    print(np.cov(le, k))
    print(np.cov(le, k)[1][0] / (np.std(le) * np.std(k)))

    print(f"LE = " + '{0} ± {1}'.format(*get_statistic(le)[:2]))
    print(f"LB = " + '{0} ± {1}'.format(*get_statistic(lb)[:2]))
    print(f"K = " + '{0} ± {1}'.format(*get_statistic(k)[:2]))
    print(f"age = " + '{0} ± {1}'.format(*calc_age(R, sR, le, lb, k)[:2]))


def monte_carlo_to_calc_uncertainty():

    R, sR = 50, 0.25

    # print("\n========== result 1 ==========\n")
    #
    # res = ap.files.basic.read("results.txt")
    # le = [i[0] for i in res]
    # lb = [i[1] for i in res]
    # k = [i[2] for i in res]
    #
    # sle = np.std(le)
    # slb = np.std(lb)
    # sk = np.std(k)
    #
    # print(f"Std of LE  = {sle}")
    # print(f"Std of LB  = {slb}")
    # print(f"Std of K  = {sk}")
    #
    # cov_le_lb = np.cov(le, lb)[1][0]
    # cov_le_k = np.cov(le, k)[1][0]
    # cov_lb_k = np.cov(lb, k)[1][0]
    #
    # covariance_matrix = np.array(
    #     [[sle**2, cov_le_lb, cov_le_k],
    #      [cov_le_lb, slb**2, cov_lb_k],
    #      [cov_le_k, cov_lb_k, sk**2]]
    # )
    covariance_matrix = np.array(
        [[(0.0016E-10)**2, -3.4497E-26, 7.1889E-19],
         [-3.4497E-26, (0.0093E-10)**2, -3.4497E-26],
         [7.1889E-19, -3.4497E-26, (0.0045E-3)**2]]
    )

    print(covariance_matrix)

    ages, sages = [], []
    for i in range(4000):
        random_numbers = np.random.multivariate_normal(mean=[0.5755E-10, 4.9739E-10, 1.6418E-3], cov=covariance_matrix, size=4000).transpose()
        try:
            age, sage = calc_age(R, sR, random_numbers[0], random_numbers[1], random_numbers[2])[:2]
        except ValueError:
            continue
        else:
            ages.append(age)
            sages.append(sage)
        if i % 100 == 0:
            print(f"age = " + '{0} ± {1}'.format(str(age), str(sage)))

    print("\n========== final age ==========\n")

    print(f"age = " + '{0} ± {1}'.format(str(np.mean(ages)), str(np.std(ages))))
    print(f"sage = " + '{0} ± {1}'.format(str(np.mean(sages)), str(np.std(sages))))

    print(f"cov = \n{np.cov(ages, sages)}")

    # == == == == == final age == == == == ==
    #
    # age = 1050.7300017256905 ± 0.06448789398340359
    # sage = 4.016417903455615 ± 0.04467695074911889
    # cov =
    # [[4.15972840e-03 - 2.25391959e-05]
    #  [-2.25391959e-05  1.99652906e-03]]

    with open("ages.txt", 'w') as f:  # save serialized json data to a readable text
        f.writelines("\n".join([str(i) for i in ages]))

    with open("sages.txt", 'w') as f:  # save serialized json data to a readable text
        f.writelines("\n".join([str(i) for i in sages]))


def ellipse():
    age = [1050.7300017256905, 0.06448789398340359]
    sage = [4.016417903455615, 0.04467695074911889]
    cov = [[4.15972840E-03, -2.25391959E-05], [-2.25391959E-05, 1.99652906E-03]]
    ellipse_point = ap.calc.isochron.get_ellipse(*age, *sage, cov[0][1] * age[1] * sage[1], plt_sfactor=0, size=60)

    with open("ellipse.txt", 'w') as f:  # save serialized json data to a readable text
        f.writelines("\n".join([str(i) for i in ["{0}, {1}".format(str(j[0]), str(j[1])) for j in ellipse_point]]))

    print(ellipse_point)


if __name__ == "__main__":

    x0 = [
        LE, LB, K,
        6.789E-05,
        0.60556, 4.5494, 4.8205, 7.4636, 9.0619, 9.4983, 9.4918,
        9.5102, 9.4958, 9.5295, 9.5391, 9.6987, 12.6039, 18.09, 52.9011, 135.6389
    ]

    MF_regerssion([
        LE, LB, K,
        6.789E-05,
        0.60556, 4.5494, 4.8205, 7.4636, 9.0619, 9.4983, 9.4918,
        9.5102, 9.4958, 9.5295, 9.5391, 9.6987, 12.6039, 18.09, 52.9011, 135.6389
    ])

    print("\n ======== ti 最优值 （由参数计算而来） ======== \n")
    print([get_ti(Opt_LE, Opt_LB, Opt_K, ri) for ri in Opt_R])


    print("\n ======== MONTE CARLO 模拟 ======== \n")
    res = []
    num = 4000
    count = 0
    random_T = [np.random.normal(t, sT[i], num) for i, t in enumerate(T)]
    random_R = [np.random.normal(r, sR[i], num) for i, r in enumerate(R)]
    random_LE = np.random.normal(LE, sLE, num)
    random_LB = np.random.normal(LB, sLB, num)
    random_LT = np.random.normal(LT, sLT, num)
    random_K = np.random.normal(K, sK, num)

    while count < num:

        T = [random_T[i][count] for i, _ in enumerate(T)]
        R = [random_R[i][count] for i, _ in enumerate(R)]
        LE = random_LE[count]
        LB = random_LB[count]
        LT = random_LT[count]
        K = random_K[count]
        if count % 100 == 0:
            print(count)
        count += 1

        a = scipy.optimize.minimize(fun=func, x0=x0, method="Nelder-Mead", options={"maxiter": 10000}, tol=0.00000000001)
        res.append(a["x"].tolist())

    print("\n ======== 参数最优结果 ======== \n")
    print(res)

    ap.files.basic.write("results-0213.txt", res)

    # this_is_to_identify_that_monte_carlo_is_not_better_than_linear()
    # monte_carlo_to_calc_uncertainty()
    # ellipse()
    pass