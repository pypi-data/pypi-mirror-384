#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - calc - age
# ==========================================
#
#
#
"""

# === Internal import ===
from . import arr

# === External import ===
import numpy as np


def calc_age_min(F, sF, **kwargs) -> tuple:
    """
    Calculate ArAr ages using Min et al. (2000) equation.
    Note that the Ar/K of primary standards is not working currently
    Parameters
    ----------
    F : array-like
    sF : array-like
    kwargs :
         keys : [
            'F', 'sF', 'L', 'sL', 'Le', 'sLe', 'Lb', 'sLb', 'A', 'sA', 'Ae', 'sAe', 'Ab', 'sAb',
            't', 'st', 'J', 'sJ', 'W', 'sW', 'No', 'sNo', 'Y', 'sY', 'f', 'sf', 'Min'
        ].
        values :  array-like objects.

    Returns
    -------
    [age, s1, s2, s3] in years

    """
    F, sF = arr.array_as_float([F, sF]).astype(float)
    J = arr.array_as_float(kwargs.pop('J'))
    sJ = arr.array_as_float(kwargs.pop('sJ') * J / 100)
    A = arr.array_as_float(kwargs.pop('A'))
    sA = arr.array_as_float(kwargs.pop('sA') * A / 100)  # total A, A = Aec + (Ab+) + (Ab-). Ab- for Ca
    Ae = arr.array_as_float(kwargs.pop('Ae'))
    sAe = arr.array_as_float(kwargs.pop('sAe') * Ae / 100)  # Aec
    Ab = arr.array_as_float(kwargs.pop('Ab'))
    sAb = arr.array_as_float(kwargs.pop('sAb') * Ab / 100)  # Ab-
    Abp = arr.array_as_float(kwargs.pop('Abp'))
    sAbp = arr.array_as_float(kwargs.pop('sAbp') * Ab / 100)  # Ab+
    W = arr.array_as_float(kwargs.pop('W'))
    sW = arr.array_as_float(kwargs.pop('sW') * W / 100)
    Y = arr.array_as_float(kwargs.pop('Y'))
    sY = arr.array_as_float(kwargs.pop('sY') * Y / 100)
    f = arr.array_as_float(kwargs.pop('f'))
    sf = arr.array_as_float(kwargs.pop('sf') * f / 100)
    No = arr.array_as_float(kwargs.pop('No'))
    sNo = arr.array_as_float(kwargs.pop('sNo') * No / 100)
    L = arr.array_as_float(kwargs.pop('L'))
    sL = arr.array_as_float(kwargs.pop('sL') * L / 100)
    Le = arr.array_as_float(kwargs.pop('Le'))
    sLe = arr.array_as_float(kwargs.pop('sLe') * Le / 100)
    Lb = arr.array_as_float(kwargs.pop('Lb'))
    sLb = arr.array_as_float(kwargs.pop('sLb') * Lb / 100)
    t = arr.array_as_float(kwargs.pop('t'))
    st = arr.array_as_float(kwargs.pop('st'))
    Ap = arr.array_as_float(kwargs.pop('Ap'))
    sAp = arr.array_as_float(kwargs.pop('sAp') * Ap / 100)
    Kp = arr.array_as_float(kwargs.pop('Kp'))
    sKp = arr.array_as_float(kwargs.pop('sKp') * Kp / 100)

    # calculating using Min et al.(2000) equation
    # lmd = A * W * Y / (f * No)
    V = f * No / ((Ab + Ae) * W * Y)
    sV = pow((V / f * sf) ** 2 + (V / No * sNo) ** 2 + (V / (Ab + Ae)) ** 2 * (sAb ** 2 + sAe ** 2) +
             (V / W * sW) ** 2 + (V / Y * sY) ** 2, 0.5)

    # standard age in year, change to Ma
    t = t * 1000000
    st = st * 1000000
    # back-calculating Ar40/Ar39 of the standard
    stdR = (np.exp(t * L) - 1) / J
    # errors of standard age and decay constants were not applied
    sStdR = pow((stdR / J) ** 2 * sJ ** 2, 0.5)
    # normalize the measured 40Ar/39Ar
    R = F / stdR
    sR_1 = np.sqrt((sF / stdR) ** 2 + (F * sStdR / stdR ** 2) ** 2)  # errors of measured 40Ar/39Ar and J value
    sR_2 = np.sqrt((sF / stdR) ** 2)  # error of measured 40Ar/39Ar only

    useStandardAge = True
    if useStandardAge:
        # ln part in Min 2000 equation
        BB = 1
        KK = np.exp(t / V) - 1  # 40Arr / 40K Use standard age
    else:  # use Ar40* and K concentrations of primary standard
        # not fanished, this function is wrong
        BB = (Ab + Ae) / Ae
        KK = Ap / Kp / f
        raise TypeError(f"Not use standard age. Not supported.")

    XX = BB * KK * R + 1
    k0 = V * np.log(XX)

    if useStandardAge:
        # k0 =  V * ln(exp(t/V) - 1 * R + 1)
        e1 = (np.log(XX) - R * (KK + 1) * t / (V * XX)) ** 2 * sV ** 2  # sV
        e2 = (BB * (KK + 1) * R / XX) ** 2 * st ** 2  # st
        e3 = (V * BB * KK / XX) ** 2 * sR_1 ** 2  # sR
    else:
        e1, e2, e3 = 0, 0, 0

    # change to Ma
    # analytical error, error of 40Ar/39Ar only
    s1 = np.sqrt((V * KK * BB / XX) ** 2 * sR_2 ** 2)
    # internal error, errors of 40Ar/39Ar and J value
    s2 = np.sqrt((V * KK * BB / XX) ** 2 * sR_1 ** 2)
    # total external error
    s3 = np.sqrt(e1 + e2 + e3)
    age = k0
    return age, s1, s2, s3


def calc_age_general(F, sF, J, sJ, L, sL, **kwargs):
    """
    All passed args should be array-like with the same length
    Parameters
    ----------
    F : array-like object
    sF : array-like object
    J : array-like object
    sJ : array-like object
    L : array-like object
    sL : array-like object
    kwargs

    Returns
    -------
    tuple of array objects, (age, s1, s2, s3), in years
    """
    F, sF, J, sJ, L, sL = np.array([F, sF, J, sJ, L, sL])
    sJ = sJ * J / 100
    sL = sL * L / 100
    age = np.log(1 + J * F) / L
    v1 = sF ** 2 * (J / (L * (1 + J * F))) ** 2
    v2 = sJ ** 2 * (F / (L * (1 + J * F))) ** 2
    v3 = sL ** 2 * (np.log(1 + J * F) / (L ** 2)) ** 2
    s1 = v1 ** .5  # analytical error, F only
    s2 = (v1 + v2) ** .5  # internal error, F and J
    s3 = (v1 + v2 + v3) ** .5  # full external error. F, J and L
    return age, s1, s2, s3
