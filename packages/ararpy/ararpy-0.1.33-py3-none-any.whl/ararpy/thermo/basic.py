#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - basic
# ==========================================
#
#
# 
"""
import numpy as np
from math import log

SEC2YEAR = 3600 * 24 * 365.2425
CAL2JOULE = 4.184
CM2UM = 10000
GAS_CONSTANT = 8.31446261815324  # in J / (mol K)


def gammq(a, x):
    if x < 0 or a <= 0:
        raise ValueError("ERROR(GAMMQ): x < 0 or a <= 0")

    if x < a + 1:
        gamser, gln = gser(a, x)
        return 1.0 - gamser
    else:
        gammcf, gln = gcf(a, x)
        return gammcf

def gser(a, x, itmax=100, eps=3e-7):
    gln = gammln(a)
    if x <= 0:
        if x < 0:
            raise ValueError("ERROR(GSER): x < 0")
        return 0.0, gln

    ap = a
    sum_ = 1.0 / a
    delta = sum_
    for n in range(1, itmax + 1):
        ap += 1
        delta *= x / ap
        sum_ += delta
        if abs(delta) < abs(sum_) * eps:
            break
    else:
        raise RuntimeError("ERROR(GSER): a too large, itmax too small")

    gamser = sum_ * np.exp(-x + a * np.log(x) - gln)
    return gamser, gln

def gcf(a, x, itmax=100, eps=3e-7):
    gln = gammln(a)
    gold = 0.0
    a0 = 1.0
    a1 = x
    b0 = 0.0
    b1 = 1.0
    fac = 1.0
    for n in range(1, itmax + 1):
        an = float(n)
        ana = an - a
        a0 = (a1 + a0 * ana) * fac
        b0 = (b1 + b0 * ana) * fac
        anf = an * fac
        a1 = x * a0 + anf * a1
        b1 = x * b0 + anf * b1
        if a1 != 0:
            fac = 1.0 / a1
            g = b1 * fac
            if abs((g - gold) / g) < eps:
                return g * np.exp(-x + a * np.log(x) - gln), gln
            gold = g
    else:
        raise RuntimeError("ERROR(GCF): a too large, itmax too small")

def gammln(xx):
    cof = np.array([76.18009173, -86.50532033, 24.01409822,
                    -1.231739516, 0.00120858003, -0.00000536382])
    stp = 2.50662827465
    half = 0.5
    one = 1.0
    fpf = 5.5

    x = xx - one
    tmp = x + fpf
    tmp = (x + half) * np.log(tmp) - tmp
    ser = one
    for j in range(6):
        x += one
        ser += cof[j] / x

    return tmp + np.log(stp * ser)


def fit(x, y, sigx, sigy, pho=None):
    """
    equivalent to York2 regression
    y = a + bx

    Parameters
    ----------
    x
    y
    sigx
    sigy
    pho

    Returns
    -------
    a: intercept
    b: slope
    siga: intercept uncertainty
    sigb: slope uncertainty
    chi2: chi-square value
    q: the incomplete gamma function value, should be large for the best fitting.

    """

    print(f"{x = }")
    print(f"{y = }")
    print(f"{sigx = }")
    print(f"{sigy = }")
    print(f"{pho = }")

    ndata = len(x)
    if pho is None:
        pho = np.zeros(ndata)
    nd = 20
    imax = 20
    xerr = 0.001
    wt = []
    a = 0
    b = -1.
    siga = 0
    sigb = 0
    chi2 = 0
    q = 0
    iter = 0

    while iter <= imax:
        sx = 0.
        sy = 0.
        st2 = 0.
        st3 = 0.
        ss = 0.
        b0 = b

        for i in range(ndata):
            wt.append(0)
            wt[i] = 1. / (sigy[i] ** 2 + b ** 2 * sigx[i] ** 2 - 2 * pho[i] * sigx[i] * sigy[i])
            ss = ss + wt[i]
            sx = sx + x[i] * wt[i]
            sy = sy + y[i] * wt[i]

            # print(f"{x[i] = }, {y[i] = }, {wt[i] = }")

        sxoss = sx / ss
        syoss = sy / ss

        for i in range(ndata):
            t1 = (x[i] - sxoss) * sigy[i] ** 2
            t2 = (y[i] - syoss) * sigx[i] ** 2 * b
            t3 = sigx[i] * sigy[i] * pho[i]
            st2 = st2 + wt[i] ** 2 * (y[i] - syoss) * (t1 + t2 - t3 * (y[i] - syoss))
            st3 = st3 + wt[i] ** 2 * (x[i] - sxoss) * (t1 + t2 - b * t3 * (x[i] - sxoss))

        b = st2 / st3
        iter = iter + 1

        # print(f"{sxoss = }, {syoss = }, {b = }, {abs(b0 - b) = }")

        if abs(b0 - b) > xerr:
            continue

        a = (syoss - sxoss * b)
        # print(f"{a = }, {b = }")
        sgt1 = 0.
        sgt2 = 0.

        for i in range(ndata):
            sgt1 = sgt1 + wt[i] * (x[i] - sxoss) ** 2
            sgt2 = sgt2 + wt[i] * x[i] ** 2

        sigb = (1. / sgt1) ** 0.5
        siga = sigb * (sgt2 / ss) ** 0.5
        chi2 = 0.

        for i in range(ndata):
            chi2 = chi2 + wt[i] * (y[i] - a - b * x[i]) ** 2

        q = gammq(0.5 * (ndata - 2), 0.5 * chi2)

        if abs(b0 - b) <= xerr:
            break

    return a, b, siga, sigb, chi2, q


def get_tc(da2, sda2, E, sE, cooling_rate=10, temp_in_celsius=True, temp=None, A: float = 27.0, R=None, pho=0):
    """
    E / (R Tc) = ln(A t D0/a2)
    E: diffusion activation energy
    R: gas constant, 8.314 J/(K*mol)
    Tc: closure temperature
    A: geometric constant, A is 55, 27, or 8.7 for volume diffusion from a sphere, cylinder or plane sheet respectively
    tau: time constant, can be determined by
        (1) a pre-defined cooling rate following t = -R Tc2 / E * dT / dt, where dT / dt is the average cooling rate of the local geological body
        (2) the age of dated sample following t = R * age * E * (Tp - Tc), where Tp is the temperature at present that could be 300 K.
    D0: the diffusion coefficient at the given temperature, which will be the frequency factor (the pre-exponential factor) whe the temperature is infinite high
    a: the effective diffusion radius, the characteristic dimension of the system, or the domain size, or roughly the grain size


    In either way of them, a equation with Tc in both right and left hand will be yielded. Then using iterative calculation, the Tc can be determined.

    Parameters
    -------
    da2: D/a2 in 1/a, pear year
    sda2:
    E: diffusion activation energy
    sE:
    pho: covariance of da2 and E
    temp: temperature of the given diffusion coefficient, in K
    A: geometric constant
    R: gas constant
    cooling_rate: in degree/m.y., degrees per million year
    temp_in_celsius: temperature in celsius, True, else in K, False

    Returns
    -------

    """
    R = 8.314 if R is None else R # in J/K mol
    Tc = 600
    sTc = 0
    Tm = 9999999999 if temp is None else temp
    Tm = Tm + 273.15 if temp_in_celsius else Tm
    cooling_rate = cooling_rate / 1000000

    iter_num = 0
    iter_diff = 100
    while abs(iter_diff) > 0.01 and iter_num < 100:
        tau = R * Tc ** 2 / (E * cooling_rate)
        new_Tc = (R / E) * log(A * tau * da2) + 1 / Tm  #
        # new_Tc = (R / E) * log(A * tau * da2)
        d1 = cooling_rate / (A * da2 * Tc ** 2)
        s1 = d1 ** 2 * sda2 ** 2  # da2
        d2 = R / E ** 2 * (log(A * tau * da2) + 1)
        s2 = d2 ** 2 * sE ** 2  # E
        d3 = 2 * R / (E * Tc)
        s3 = d3 ** 2 * sTc ** 2  # Tc
        new_Tc = 1 / new_Tc
        iter_diff = abs(new_Tc - Tc)
        Tc = new_Tc
        sTc = Tc ** 2 * np.sqrt(s1 + s2 + s3 + 2 * d1 * d2 * pho)
        iter_num += 1
        # print(f"Get Tc: {iter_num = }, {Tc = }, {tau = }, {Tm = }")
    return Tc - 273.15 if temp_in_celsius else Tc, sTc


if __name__ == "__main__":
    """
    tests
    """
    # 柴田贤, 钾长石
    print("# 柴田贤, 钾长石")
    print(get_tc(da2=5.6 * 3600 * 24 * 365.24, sda2=0, E=28.8 * 1000, R=1.987, sE=0, cooling_rate=5, A=8.7))
    print(get_tc(da2=5.6 * 3600 * 24 * 365.24, sda2=0, E=28.8 * CAL2JOULE * 1000, sE=0, cooling_rate=5, A=8.7))
    print(get_tc(da2=5.6 * 3600 * 24 * 365.24, sda2=0, E=28.8 * CAL2JOULE * 1000, sE=0, cooling_rate=30, A=8.7))
    # 杨静, 斜钾铁矾 K101-1
    print("# 杨静, 斜钾铁矾 K101-1")
    print(get_tc(da2=10 ** 15.07 * 3600 * 24 * 365.24, sda2=0, E=76.17 * 1000 * CAL2JOULE, sE=0, cooling_rate=5, A=55))  # 这里跟文章中吻合
    print(get_tc(da2=10 ** 15.07 * 3600 * 24 * 365.24, sda2=0, E=76.17 * 1000 * CAL2JOULE, sE=0, cooling_rate=10, A=55))  # 10冷却速率不吻合
    # 杨静, 斜钾铁矾 K101-2
    print("# 杨静, 斜钾铁矾 K101-2")
    print(get_tc(da2=10 ** 12.35 * 3600 * 24 * 365.24, sda2=0, E=66.43 * 1000 * CAL2JOULE, sE=0, cooling_rate=5, A=55))  # 这里跟文章中吻合
    print(get_tc(da2=10 ** 12.35 * 3600 * 24 * 365.24, sda2=0, E=66.43 * 1000 * CAL2JOULE, sE=0, cooling_rate=10, A=55))  # 10冷却速率不吻合
    # 芦武长
    print("# 芦武长")
    print(get_tc(da2=3e-4 * 3600 * 24 * 365.24, sda2=0, E=35 * 1000 * CAL2JOULE, sE=0, cooling_rate=0.1, A=27, temp=600))  # 缺乏样品特征尺寸参数，da2不对，结果不对
    print(get_tc(da2=3e-4 * 3600 * 24 * 365.24, sda2=0, E=35 * 1000 * CAL2JOULE, sE=0, cooling_rate=1, A=27, temp=600))  # 缺乏样品特征尺寸参数，da2不对，结果不对
    # Harrison 1981, 角闪石, A = 55
    print("# Harrison 1981, 角闪石, A = 55")
    print(get_tc(da2=0.024 * SEC2YEAR / 0.0080 ** 2, sda2=0, E=64.1 * 1000 * CAL2JOULE, sE=0, cooling_rate=500, A=55))
    print(get_tc(da2=0.024 * SEC2YEAR / 0.0080 ** 2, sda2=0, E=64.1 * 1000 * CAL2JOULE, sE=0, cooling_rate=5, A=55))
    # Harrison 1985, 黑云母, A = 27
    print("# Harrison 1985, 黑云母, A = 27")
    print(get_tc(da2=0.077 * SEC2YEAR / 0.0150 ** 2, sda2=0, E=47.0 * 1000 * CAL2JOULE, sE=0, cooling_rate=100, A=27))
    print(get_tc(da2=0.077 * SEC2YEAR / 0.0150 ** 2, sda2=0, E=47.0 * 1000 * CAL2JOULE, sE=0, cooling_rate=1, A=27))
    print("# Blereau 2019, 大隅石，Osumilite, A = 8.7")
    print(get_tc(da2=8.34e8 * SEC2YEAR / (0.0175 ** 2), sda2=0, E=461 * 1000, sE=0, cooling_rate=10, A=8.7))
    print(get_tc(da2=6.70e8 * SEC2YEAR / (0.0175 ** 2), sda2=0, E=453 * 1000, sE=0, cooling_rate=10, A=8.7))  # 这两个与原文对不上，且原文描述表格与文字不符
    print(get_tc(da2=4.49e5 * SEC2YEAR / (0.0175 ** 2), sda2=0, E=369 * 1000, sE=0, cooling_rate=10, A=8.7))  # 这两个与原文对不上，且原文描述表格与文字不符
    print("# Thern 2020, 电气石, A = 55")  # 大部分都对或者接近，不完全一致的原因大概是他们采用蒙特卡洛方法计算且正负误差不一样
    print(get_tc(da2=4.86e22 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=678 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=8.99e23 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=756 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=3.95e19 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=604 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=6.95e27 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=815 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=2.70e14 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=519 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=1.65e15 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=505 * 1000, sE=0, cooling_rate=10, A=55))
    print(get_tc(da2=9.09e21 * SEC2YEAR / (0.0100 ** 2), sda2=0, E=656 * 1000, sE=0, cooling_rate=10, A=55))
    print("# Shi 2020, 黑云母, A = 55")  # 大部分都对或者接近，不完全一致的原因大概是他们采用蒙特卡洛方法计算且正负误差不一样
    print(get_tc(da2=10 ** 18 * SEC2YEAR, sda2=0, E=87 * 1000 * CAL2JOULE, sE=0, cooling_rate=10, A=6))  # 文中的参数可能是cooling_rate=100, A=8.7，但是10和6的组合与文中报导的结果一致
    print(get_tc(da2=10 ** 16.6 * SEC2YEAR, sda2=0, E=81.5 * 1000 * CAL2JOULE, sE=0, cooling_rate=10, A=6))
