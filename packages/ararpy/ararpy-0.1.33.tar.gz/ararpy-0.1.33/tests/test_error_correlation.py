#  Copyright (C) 2024 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2024 Yang 
# ararpy - test_error_correlation.py
# ==========================================
#
#
# 
"""
import numpy as np

ar36 = [float(line.rstrip("\n")) for line in open("ar36.txt").readlines()]
ar37 = [float(line.rstrip("\n")) for line in open("ar37.txt").readlines()]
ar38 = [float(line.rstrip("\n")) for line in open("ar38.txt").readlines()]
ar39 = [float(line.rstrip("\n")) for line in open("ar39.txt").readlines()]
ar40 = [float(line.rstrip("\n")) for line in open("ar40.txt").readlines()]

cov_40_39 = np.cov(ar40, ar39)
cov_40_36 = np.cov(ar40, ar36)
cov_39_36 = np.cov(ar39, ar36)

pho_40_39 = cov_40_39[0][1] / (np.std(ar40) * np.std(ar39))
pho_40_36 = cov_40_36[0][1] / (np.std(ar40) * np.std(ar36))
pho_39_36 = cov_39_36[0][1] / (np.std(ar39) * np.std(ar36))

print(f"{cov_40_39 = }")
print(f"{pho_40_39 = }\n")
print(f"{cov_40_36 = }")
print(f"{pho_40_36 = }\n")
print(f"{cov_39_36 = }")
print(f"{pho_39_36 = }\n")


ar36m = [float(line.rstrip("\n")) for line in open("ar36m.txt").readlines()]
ar37m = [float(line.rstrip("\n")) for line in open("ar37m.txt").readlines()]
ar38m = [float(line.rstrip("\n")) for line in open("ar38m.txt").readlines()]
ar39m = [float(line.rstrip("\n")) for line in open("ar39m.txt").readlines()]
ar40m = [float(line.rstrip("\n")) for line in open("ar40m.txt").readlines()]

cov_40m_39m = np.cov(ar40m, ar39m)
cov_40m_36m = np.cov(ar40m, ar36m)
cov_39m_36m = np.cov(ar39m, ar36m)

pho_40m_39m = cov_40m_39m[0][1] / (np.std(ar40m) * np.std(ar39m))
pho_40m_36m = cov_40m_36m[0][1] / (np.std(ar40m) * np.std(ar36m))
pho_39m_36m = cov_39m_36m[0][1] / (np.std(ar39m) * np.std(ar36m))

print(f"{cov_40m_39m = }")
print(f"{pho_40m_39m = }\n")
print(f"{cov_40m_36m = }")
print(f"{pho_40m_36m = }\n")
print(f"{cov_39m_36m = }")
print(f"{pho_39m_36m = }\n")


ar36a = [float(line.rstrip("\n")) for line in open("ar36a.txt").readlines()]
ar36cl = [float(line.rstrip("\n")) for line in open("ar36cl.txt").readlines()]
ar37ca = [float(line.rstrip("\n")) for line in open("ar37ca.txt").readlines()]
ar39k = [float(line.rstrip("\n")) for line in open("ar39k.txt").readlines()]
ar40r = [float(line.rstrip("\n")) for line in open("ar40r.txt").readlines()]

cov_40r_39k = np.cov(ar40r, ar39k)
cov_40r_36a = np.cov(ar40r, ar36a)
cov_39k_36a = np.cov(ar39k, ar36a)

pho_40r_39k = cov_40r_39k[0][1] / (np.std(ar40r) * np.std(ar39k))
pho_40r_36a = cov_40r_36a[0][1] / (np.std(ar40r) * np.std(ar36a))
pho_39k_36a = cov_39k_36a[0][1] / (np.std(ar39k) * np.std(ar36a))


print(f"{cov_40r_39k = }")
print(f"{pho_40r_39k = }\n")
print(f"{cov_40r_36a = }")
print(f"{pho_40r_36a = }\n")
print(f"{cov_39k_36a = }")
print(f"{pho_39k_36a = }\n")

"""
cov = array([[98.75793884, -0.31788865],
       [-0.31788865,  0.25810407]])
pho = -0.06297019225126861

误差相关性为负数

"""
