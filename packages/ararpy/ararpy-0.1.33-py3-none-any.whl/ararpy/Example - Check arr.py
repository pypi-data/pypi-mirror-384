#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Check arr
# ==========================================
#
#
# 
"""
import os
import ararpy as ap
import numpy as np
import pdf_maker as pm


def read_sample(arr_file_path):
    # 读取样品信息
    if not arr_file_path.endswith('.arr'):
        for root, dirs, files in os.walk(arr_file_path):
            for file in files:
                if file.endswith('.arr'):
                    arr_file_path = os.path.join(arr_file_path, file)
                    break
    print(f"arr file: {arr_file_path}")
    sample = ap.from_arr(file_path=arr_file_path)
    name = sample.name()
    sequence = sample.sequence()
    nsteps = sequence.size
    arratio = sample.TotalParam[0][0]
    if sample.Info.sample.type == "Unknown":
        print(f"{name = }, {arratio = }")
        # sample.TotalParam[0] = [298.56 for i in sample.TotalParam[0]]
        sample.Info.preference["confidenceLevel"] = 2
        # ap.smp.calculation.recalculate(sample, re_plot=True, re_plot_style=True, re_set_table=True, re_table_style=True)
        ap.save(sample, arr_file_path)


loc = r"C:\Users\Young\OneDrive\00-Projects\【2】个人项目\2022-05论文课题\【3】分析测试\ArAr\01-VU实验数据和记录\Arr Data"
# read_sample(os.path.join(loc, "20240918_24FY87.arr"))
# read_sample(loc)

for root, dirs, files in os.walk(loc):
    for file in files:
        if file.endswith('.arr'):
            arr_file_path = os.path.join(loc, file)
            read_sample(arr_file_path)


