#  Copyright (C) 2024 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2024 Yang 
# ararpy - test_regression_methods
# ==========================================
#
#
# 
"""

import ararpy as ap
import numpy as np
from math import exp
from scipy.optimize import minimize
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('TkAgg')


# def get_rand_measurment():
#     geological_error = 0.0000001  # relative
#     analytical_error = 0.01  # relative
#     J = 0.01
#     L = 5.53E-10
#     I = 1 / 298.56
#
#     true_age = 100 * 1000000
#     true_F = (exp(true_age * L) - 1) / J
#     size = 10
#     ages = np.random.normal(loc=true_age, scale=geological_error * true_age, size=size)
#     Fs = [(exp(age * L) - 1) / J for age in ages]
#     F = [np.random.normal(loc=(exp(ages[i] * L) - 1) / J, scale=(exp(ages[i] * L) - 1) / J * analytical_error, size=1)[0] for i in range(size)]
#
#     ar36a = np.array([0.1 + 0.1 * i for i in range(size)])
#     sar36a = ar36a * analytical_error
#
#     ar40a = ar36a / I
#     sar40a = sar36a / I
#
#     ar40 = np.array([350 + 10 * i for i in range(size)])
#     sar40 = ar40 * analytical_error
#
#     ar40r = ar40 - ar40a
#     sar40r = (sar40 ** 2 + sar40a ** 2) ** .5
#     ar39k = [ar40r[i] / F[i] for i in range(size)]
#     sar39k = [sar40r[i] / F[i] for i in range(size)]
#
#     [x, sx] = ap.calc.arr.div([ar39k, sar39k], [ar40.tolist(), sar40.tolist()])  # ar39k / ar40
#     [y, sy] = ap.calc.arr.div([ar36a.tolist(), sar36a.tolist()], [ar40.tolist(), sar40.tolist()])  # ar36a / ar40
#
#     r = [ap.calc.err.cor(sar39k[i] / ar39k[i], sar36a[i] / ar36a[i], sar40[i] / ar40[i]) for i in range(size)]
#
#     print(f"{r = }")
#     print(f"{F = }")
#     print(f"{I = }")
#
#     with open(f"test_regression_methods.text", "w") as f:
#         f.write(f"{geological_error = }\n{analytical_error = }\n{J = }\n{L = }\n{I = }\n{true_age = }\n{true_F = }\n{size = }\n")
#         f.write(f"age,F,ar40,s,ar36a,s,ar39k,s,x,sx,y,sy,r\n")
#         f.writelines([f"{ages[i]},{F[i]},{ar40[i]},{sar40[i]},{ar36a[i]},{sar36a[i]},{ar39k[i]},{sar39k[i]},{x[i]},{sx[i]},{y[i]},{sy[i]},{r[i]}\n" for i in range(size)])
#
#     return x, sx, y, sy, r


size = 5
geological_error = [0.001 for i in range(size)]  # relative
analytical_error = [0.001 for i in range(size)]  # relative
geological_error[2] = 0.003  # relative
analytical_error[2] = 0.003  # relative
J = 0.01
L = 5.53E-10
I = 298.56

true_age = 100 * 1000000
true_F = (exp(true_age * L) - 1) / J


def get_rand_measurement(normal: bool = True):

    ages = [np.random.normal(loc=true_age, scale=geological_error[i] * true_age, size=1)[0] for i in range(size)]
    # ages[2] = 110000000
    F = [(exp(age * L) - 1) / J for age in ages]
    # F = [np.random.normal(loc=(exp(ages[i] * L) - 1) / J, scale=(exp(ages[i] * L) - 1) / J * analytical_error, size=1)[0] for i in range(size)]

    ar39k = [300 + i * 50 for i in range(size)]
    sar39k = [ar39k[i] * analytical_error[i] for i in range(size)]

    ar36a = sorted([10 + i * 0.5 for i in range(size)], reverse=True)
    sar36a = [ar36a[i] * analytical_error[i] for i in range(size)]

    ar40 = [ar36a[i] * I + ar39k[i] * F[i] for i in range(size)]
    sar40 = [ap.calc.err.add(I * sar36a[i], F[i] * sar39k[i]) for i in range(size)]

    ar36a = [np.random.normal(loc=val, scale=sar36a[i], size=1)[0] for i, val in enumerate(ar36a)]
    ar39k = [np.random.normal(loc=val, scale=sar39k[i], size=1)[0] for i, val in enumerate(ar39k)]
    ar40 = [np.random.normal(loc=val, scale=sar40[i], size=1)[0] for i, val in enumerate(ar40)]

    if normal:
        [x, sx] = ap.calc.arr.div([ar39k, sar39k], [ar36a, sar36a])  # ar39k / ar40
        [y, sy] = ap.calc.arr.div([ar40, sar40], [ar36a, sar36a])  # ar36a / ar40
        r = [ap.calc.err.cor(sar39k[i] / ar39k[i], sar40[i] / ar40[i], sar36a[i] / ar36a[i]) for i in range(size)]

    else:
        [x, sx] = ap.calc.arr.div([ar36a, sar36a], [ar40, sar40])  # ar39k / ar40
        [y, sy] = ap.calc.arr.div([ar39k, sar39k], [ar40, sar40])  # ar36a / ar40
        r = [ap.calc.err.cor(sar36a[i] / ar36a[i], sar39k[i] / ar39k[i], sar40[i] / ar40[i]) for i in range(size)]
        F = [1/i for i in F]

    # [x, sx] = ap.calc.arr.div([ar39k, sar39k], [ar40, sar40])  # ar39k / ar40
    # [y, sy] = ap.calc.arr.div([ar36a, sar36a], [ar40, sar40])  # ar36a / ar40
    # r = [ap.calc.err.cor(sar39k[i] / ar39k[i], sar36a[i] / ar36a[i], sar40[i] / ar40[i]) for i in range(size)]

    print(f"{ages = }")
    print(f"{r = }")
    print(f"{F = }")
    print(f"{I = }")
    print(f"{true_F = }\n")

    with open(f"test_regression_methods.text", "w") as f:
        f.write(f"{geological_error = }\n{analytical_error = }\n{J = }\n{L = }\n{I = }\n{true_age = }\n{true_F = }\n{size = }\n")
        f.write(f"age,F,ar40,s,ar36a,s,ar39k,s,x,sx,y,sy,r\n")
        f.writelines([f"{ages[i]},{F[i]},{ar40[i]},{sar40[i]},{ar36a[i]},{sar36a[i]},{ar39k[i]},{sar39k[i]},{x[i]},{sx[i]},{y[i]},{sy[i]},{r[i]}\n" for i in range(size)])

    return x, sx, y, sy, r, F


# 定义线性模型
def linear_model(params, x):
    slope, intercept = params
    return slope * x + intercept


# 定义负对数似然函数
def negative_log_likelihood(params, x, y):
    predicted_y = linear_model(params, x)
    # 使用高斯误差进行似然计算
    errors = predicted_y - y
    likelihood = np.sum(-0.5 * np.log(2 * np.pi) - 0.5 * errors**2)
    return -likelihood


def do_repetition():
    york2 = []
    linest = []
    mle = []
    Fs = []
    data = [[], [], [], []]
    for i in range(100):
        [x, sx, y, sy, r, F] = get_rand_measurement(False)

        for j in range(len(x)):
            data[0].append(x[j])
            data[1].append(sx[j])
            data[2].append(y[j])
            data[3].append(sy[j])

        ap.calc.arr.multi_append(Fs, np.mean(F))

        res = ap.calc.regression.york2(x, sx, y, sy, r)
        print(f"Intercept = {res[0]} ± {res[1]}")
        print(f"Slope = {res[2]} ± {res[3]}")
        print(f"MSWD = {res[4]}")
        print(f"diff = {true_F - res[2]}\n")

        york2.append(res[:5])

        res = ap.calc.regression.linest(y, x)
        print(f"Intercept = {res[5][0]} ± {res[6][0]}")
        print(f"Slope = {res[5][1]} ± {res[6][1]}")
        print(f"MSWD = {res[4]}")
        print(f"diff = {true_F - res[5][1]}\n")

        linest.append([res[5][0], res[6][0], res[5][1], res[6][1], res[4]])

        res = minimize(negative_log_likelihood, [res[2], res[0]], args=(np.array(x), np.array(y)))
        print(res.items())
        slope, intercept = res.x
        mle.append([intercept, 0, slope, 0, "MSWD"])

    return york2, linest, mle, Fs, data


fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)

york2, linest, mle, Fs, data = do_repetition()

# for each in york2:
#     ax1.plot((each[0] - each[1], each[0] + each[1]), (each[2], each[2]), '-')

york2, linest, mle = ap.calc.arr.transpose(york2), ap.calc.arr.transpose(linest), ap.calc.arr.transpose(mle)

ax1.scatter(york2[0], york2[2], c="black", s=3)
ax1.scatter(Fs, [np.median(york2[2]) for i in Fs], c="blue", s=1)
ax2.scatter(linest[0], linest[2], c="red", s=3)
ax2.scatter(Fs, [np.median(linest[2]) for i in Fs], c="blue", s=1)
# ax3.scatter(mle[0], mle[2], c="blue", s=3)
# ax3.scatter(Fs, [np.median(mle[2]) for i in Fs], c="blue", s=1)

# ax3.set_ylim(0.150, 0.220)
# ax4.set_ylim(0.150, 0.220)

ax3.set_ylim(0.160, 0.190)
ax4.set_ylim(0.160, 0.190)

ax3_2 = ax3.twinx()

for i in range(len(Fs)):
    ax3.plot([i, i], [york2[0][i]-york2[1][i], york2[0][i]+york2[1][i]], '-', color='black')
    ax3.scatter([i], [Fs[i]], c="red", s=1)

ax3_2.plot([i for i in range(len(Fs))], york2[4], '-', color="blue")


for i in range(len(york2[0])):
    ax5.plot([0.00165, 0.0023], [j * york2[2][i] + york2[0][i] for j in [0.00165, 0.0023]], color='red')

ax5.scatter(data[0], data[2], c="blue", s=2)


for i in range(len(Fs)):
    ax4.plot([i, i], [linest[0][i]-linest[1][i], linest[0][i]+linest[1][i]], '-', color='black')
    ax4.scatter([i], [Fs[i]], c="red", s=1)


for i in range(len(york2[0])):
    ax6.plot([0.00165, 0.0023], [j * linest[2][i] + linest[0][i] for j in [0.00165, 0.0023]], color='red')

ax6.scatter(data[0], data[2], c="blue", s=2)

#
# [x, sx, y, sy, r] = get_rand_measurement()
#
# # for i in range(len(x)):
# #     cov = [[sx[i] ** 2, r[i] * sx[i] * sy[i]], [r[i] * sx[i] * sy[i], sy[i] ** 2]]
# #     _x, _y = np.random.multivariate_normal([x[i], y[i]], cov, 4000).transpose()
# #     plt.scatter(_x, _y, c="b", s=1)
# #
# #
# # plt.scatter(x, y, c="black", s=1)
#
# line_x = np.linspace(20, 60, 50)
#
# res = ap.calc.regression.york2(x, sx, y, sy, r)
# print(f"Intercept = {res[0]} ± {res[1]}")
# print(f"Slope = {res[2]} ± {res[3]}")
# print(f"MSWD = {res[894]}")
# print(f"diff = {true_F - res[2]}\n")
# # plt.plot(line_x, line_x * res[2] + res[0])
#
#
# res = ap.calc.regression.linest(y, x)
# print(f"Intercept = {res[5][0]} ± {res[6][0]}")
# print(f"Slope = {res[5][1]} ± {res[6][1]}")
# print(f"MSWD = {res[4]}")
# print(f"diff = {true_F - res[5][1]}\n")
# plt.plot(line_x, line_x * res[5][1] + res[5][0])


# res = ap.calc.regression.monte_carlo_linest(x, sx, y, sy, r, iteration=1000)
# slope = [i[1] for i in res]
# intercept = [i[0] for i in res]
# cov = [i[2] for i in res]
# print(f"Intercept = {np.mean(intercept)} ± {np.std(intercept)}")
# print(f"Slope = {np.mean(slope)} ± {np.std(slope)}")
# print(f"diff = {true_F - np.mean(slope)}\n")
# plt.plot(line_x, line_x * np.mean(slope) + np.mean(intercept))
#
# k1, k2 = [], []
# for i, val in enumerate(cov):
#     _intercept, _slope = np.random.multivariate_normal([intercept[i], slope[i]], val, 500).transpose()
#     k1 = [*k1, *_intercept]
#     k2 = [*k2, *_slope]
#     ax6.scatter(_slope, _intercept, c="grey")
# _slope = np.mean(slope)
# _intercept = np.mean(intercept)

# print(f"Intercept = {np.mean(k1)} ± {np.std(k1)}")
# print(f"Slope = {np.mean(k2)} ± {np.std(k2)}")
# print(f"diff = {true_F - np.mean(k2)}\n")
# plt.plot(line_x, line_x * np.mean(k2) + np.mean(k1))


#
# e = 0.1
# x = [100, 150, 200, 250, 300]
# sx = [_x * e for _x in x]
# y = [100, 125, 150, 175, 190]
# sy = [_y * e for _y in y]
# r = [0.9, 0.9, 0.9, 0.9, 0.9]
#
#
# res = ap.calc.regression.monte_carlo_linest(x, sx, y, sy, r, iteration=1000)
#
# slope = [i[1] for i in res]
# intercept = [i[0] for i in res]
# cov = [i[2] for i in res]
#
# # for i, val in enumerate(cov):
# #     _intercept, _slope = np.random.multivariate_normal([intercept[i], slope[i]], val, 500).transpose()
# #     plt.scatter(_slope, _intercept, c="grey")
#
# # plt.scatter(slope, intercept, c="blue")
#
# res = ap.calc.regression.linest(y, x)
# intercept, slope = res[5]
# intercepts, slopes = np.random.multivariate_normal([intercept, slope], res[-1], 1000).transpose()
# plt.scatter(slopes, intercepts, c="orange")
# plt.scatter(slope, intercept, c="red")
#
# res = ap.calc.regression.york2(x, sx, y, sy, r)
# plt.scatter(res[2], res[0], c="black")


# 显示图形
plt.show()


