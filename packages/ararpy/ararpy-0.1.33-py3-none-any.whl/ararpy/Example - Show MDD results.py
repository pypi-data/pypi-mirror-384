#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Show MDD results
# ==========================================
#
#
# 
"""
import ararpy as ap
import numpy as np
import pdf_maker as pm
import os

import matplotlib
from matplotlib.collections import PathCollection

matplotlib.use('TkAgg')
matplotlib.rc('font',family='Arial', size=10)
import matplotlib.pyplot as plt
# 设置全局字体，确保中文正常显示
# plt.rcParams["font.family"] = ["SimHei"]  # 中文字体
# plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题



def conf(input_x, input_y, num=None, using_binom=False, using_normal=False, start=None, end=None):
    """
    Calculate 90% confident interval of the given distribution of cooling histories.
    Parameters
    ----------
    input_x: x, array like 2D
    input_y: y, array like 2D
    count:

    Returns
    -------

    """

    if len(input_x) != len(input_y):
        raise ValueError("length of input x does not equal to that of input y")

    ns = len(input_x)
    if start is None:
        start = min([min(i) for i in input_x])
    if end is None:
        end = max([max(i) for i in input_x])
    nt = 18 if num is None else num

    if not (using_normal or using_binom):
        using_binom = True

    x_conf = np.linspace(start, end, num=nt)
    y_conf = np.zeros((nt, 4))
    ytemp = np.zeros((nt, ns))
    # 初始化数组
    xmed = np.zeros(nt)
    ave = np.zeros(nt)
    adev = np.zeros(nt)
    sdev = np.zeros(nt)
    var = np.zeros(nt)
    skew = np.zeros(nt)
    curt = np.zeros(nt)

    # 计算每个曲线的温度值
    for k, out_x in enumerate(x_conf):
        for i in range(ns):
            xs = input_x[i]
            ys = input_y[i]
            for j in range(len(xs)-1):
                if xs[j] >= out_x >= xs[j+1]:
                    ytemp[k, i] = (ys[j+1] - ys[j]) / (xs[j+1] - xs[j]) * (out_x - xs[j]) + ys[j]
                    break
        # 排序
        ytemp[k] = np.sort(ytemp[k])
        # 计算均值、中位数
        ave[k], adev[k], sdev[k], var[k], skew[k], curt[k], xmed[k] = stats = moment(ytemp[k])
        # 计算置信区间索引
        if using_binom:
            j1, j2 = ap.smp.diffusion_funcs.binom(ns)  #
            j3, j4 = int(round(ns * 0.05)) - 1, int(ns - round(ns * 0.05)) - 1  # 95%
            y1, y2, y3, y4 = ytemp[k][j1], ytemp[k][j2], ytemp[k][j3], ytemp[k][j4]
        elif using_normal:
            y1, y2, y3, y4 = ave[k] - sdev[k], ave[k] + sdev[k], ave[k] - 2 * sdev[k], ave[k] + 2 * sdev[k]
        else:
            raise KeyError("use binom or using normal")
        y_conf[k] = [y1, y2, y3, y4]
    return x_conf, y_conf


def moment(data):
    """ 计算分布的统计矩阵：均值、平均偏差、标准差、方差、偏度、峰度、中位数 """
    # 去除NaN值
    data = data[~np.isnan(data)]
    n = len(data)
    if n == 0:
        return [np.nan] * 7

    mean = np.mean(data)
    adev = np.mean(np.abs(data - mean))  # 平均偏差
    sdev = np.std(data, ddof=1)  # 样本标准差
    var = sdev ** 2  # 方差
    med = np.median(data)  # 中位数

    # 偏度 (三阶矩)
    if sdev == 0:
        skew = 0.0
    else:
        skew = np.sum(((data - mean) / sdev) ** 3) / n

    # 峰度 (四阶矩)
    if sdev == 0:
        curt = 0.0
    else:
        curt = np.sum(((data - mean) / sdev) ** 4) / n - 3.0  # 减去3使正态分布峰度为0

    return mean, adev, sdev, var, skew, curt, med


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_mages_in(file):
    mf = np.zeros([1000, 200], dtype=np.float64)
    mage = np.zeros([1000, 200], dtype=np.float64)

    cyc_count = 0
    max_step = 0
    new_cyc = True
    while new_cyc:
        new_cyc = False
        for step in range(200):
            try:
                line = file.readline().rstrip("\n")
                # print(f"{step = }, {line = }")
                if line == "":
                    break
                if "&" in line:
                    raise KeyError
                f, age = [float(l) for l in filter(lambda x: is_number(x), [m for k in line.split('\t') for m in str(k).split(' ')])]
            except KeyError as e:
                new_cyc = True
                break
            except (Exception, BaseException) as e:
                break
            else:
                mf[cyc_count, step], mage[cyc_count, step] = f, age
                max_step = [max_step, step+1][(step+1) > max_step]
        cyc_count += 1
    return mf, mage, cyc_count, max_step


def read_IN(file):
    data = []
    rows = []
    go = True
    while go:
        go = False
        group = np.zeros([200, 20], dtype=np.float64)
        row = 0
        while True:
            try:
                line = file.readline().rstrip("\n")
                if line == "":
                    break
                if "&" in line:
                    go = True
                    raise KeyError
                for col, _ in enumerate([float(l) for l in filter(lambda x: is_number(x), [l for k in line.split('\t') for m in str(k).split(',') for l in str(m).split(' ')])]):
                    group[row][col] = _
            except (Exception, BaseException) as e:
                break
            else:
                row += 1
        data.append(group)
        rows.append(row)
    return data, rows


def plot_MDD_res(loc, sname=None, title="", **params):


    # file_agesd_in = open(os.path.join(loc, f"{sname}_ages-sd.samp"), "r")
    # file_mages_in = open(os.path.join(loc, f"{sname}_mages-out.dat"), "r")
    # file_mch_in = open(os.path.join(loc, f"{sname}_mch-out.dat"), "r")
    # file_IN = open(os.path.join(loc, f"{sname}.IN"), "r")
    # lab_arr = open(os.path.join(loc, f"{sname}.ar0"), "r")
    # auto_arr = open(os.path.join(loc, f"{sname}.ar1"), "r")

    initial_age = params.pop("initial_age", 0)
    final_age = params.pop("final_age", 20)
    x1_extent = params.pop("x1_extent", [0, 100])
    y1_extent = params.pop("y1_extent", [0, final_age])
    x2_extent = params.pop("x2_extent", [initial_age, final_age])
    y2_extent = params.pop("y2_extent", [0, 500])
    x3_extent = params.pop("x3_extent", [4, 16])
    y3_extent = params.pop("y3_extent", [-10, 0])
    x4_extent = params.pop("x4_extent", [0, 1000])
    y4_extent = params.pop("y4_extent", [200, 1600])
    autoscaling = params.pop("autoscaling", False)
    export_PDF = params.pop("export_PDF", True)
    index = params.pop("index", [])

    main_color = ['#397DA1', '#BA5624', '#212121', '#6C5D1E', '#BC3D85', '#3C6933']  # blue red black
    middle_color = ['#83CDFA', '#F1B595', '#737373', '#C0A737', '#E9CDE1', '#84B775']
    shallow_color = ['#E0F1FE', '#FBEBE3', '#DDDDDD', '#F9E16F', '#CB73B0', '#B8F1A7']

    if sname is None:
        for root, dirs, files in os.walk(loc):
            for file in files:
                if file.lower().endswith('.ame'):
                    sname = file.split('.')[0]
    if sname is None:
        raise ValueError(f"{sname = }, is not allowed")

    print(f"{sname = }, {title = }")

    file_IN = open(os.path.join(loc, f"{sname}.IN"), "r")
    [data], [nstep] = read_IN(file_IN)

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    font_settings = {
        # 'fontsize': 10,
        # 'fontfamily': 'Arial'
    }

    try:
        # file_agesd_in = open(os.path.join(loc, f"{sname}_ages-sd.samp"), "r")
        # f, age, _, n2 = read_mages_in(file_agesd_in)
        # axs[0, 0].plot(f[0][:n2], age[0][:n2], c='blue', linewidth=2, label='Lab. Age spectrum')
        file_mages_in = open(os.path.join(loc, f"{sname}_mages-out.dat"), "r")
        mf, mage, cyc_count, max_step = read_mages_in(file_mages_in)
        axs[0, 0].set_xlim(*x1_extent, auto=autoscaling)
        axs[0, 0].set_ylim(*y1_extent, auto=autoscaling)
        for cyc in range(cyc_count):
            if cyc == 0:
                axs[0, 0].plot(mf[cyc][:max_step], mage[cyc][:max_step], c=main_color[1], label=f'MDD calculation (n={cyc_count})')
            else:
                axs[0, 0].plot(mf[cyc][:max_step], mage[cyc][:max_step], c=main_color[1])
        k0, k1, k2 = ap.calc.spectra.get_data(y=data[:nstep,6], sy=data[:nstep,7], x=np.cumsum(data[:nstep,3]) / np.sum(data[:nstep,3]) * 100, cumulative=True)
        axs[0, 0].plot(k0, k1, c=middle_color[2], linewidth=2, label='Lab. Age spectrum')
        axs[0, 0].plot(k0, k2, c=middle_color[2], linewidth=2)
        axs[0, 0].set_title(f'Age Spectra - {title}', loc='center', y=1, **font_settings)
        axs[0, 0].set_xlabel(f'Cumulative 39Ar Released (%)', **font_settings)
        axs[0, 0].set_ylabel(f'Apparent Age (Ma)', **font_settings)
        axs[0, 0].legend(loc='lower right')
    except FileNotFoundError:
        pass

    try:
        time = np.cumsum(data[:nstep, 2])
        # temp = data[:nstep, 1]
        temp = data[:nstep, 5]
        axs[1, 1].set_xlim(*x4_extent, auto=autoscaling)
        axs[1, 1].set_ylim(*y4_extent, auto=autoscaling)
        axs[1, 1].plot(time, temp, c=main_color[0], linewidth=2, marker="s", markerfacecolor=shallow_color[0])
        axs[1, 1].set_title(f'Heating Schedule - {title}', loc='center', pad=-20, **font_settings)
        axs[1, 1].set_xlabel(f'Time (min)', **font_settings)
        axs[1, 1].set_ylabel(f'Temperature (°C)', **font_settings)  #
    except:
        pass

    try:
        lab_arr = open(os.path.join(loc, f"{sname}.ar0"), "r")
        auto_arr = open(os.path.join(loc, f"{sname}.ar1"), "r")
        [lab_data], [lab_row] = read_IN(lab_arr)
        axs[1, 0].set_xlim(*x3_extent, auto=autoscaling)
        axs[1, 0].set_ylim(*y3_extent, auto=autoscaling)
        axs[1, 0].scatter(lab_data[:lab_row, 0], lab_data[:lab_row, 1], c=middle_color[2], marker="s", label='Lab. Arrhenius')
        data, rows = read_IN(auto_arr)
        for i, row in enumerate(rows):
            if i == 0:
                axs[1, 0].scatter(data[i][:row, 0].flatten(), data[i][:row, 1].flatten(), c=main_color[1], marker="s", label='MDD calculation')
            else:
                axs[1, 0].scatter(data[i][:row, 0].flatten(), data[i][:row, 1].flatten(), c=main_color[1], marker="s")
        if index:
            index = np.s_[index]
            axs[1, 0].scatter(lab_data[index, 0], lab_data[index, 1], c=main_color[0], marker="s", label='Lab. values used for linear fit')
            b, sb, _, r2, mswd, [b, m], [sb, sm], _, _ = ap.calc.regression.linest(lab_data[index, 1], lab_data[index, 0])
            d0r2 = 10 ** b * ap.thermo.basic.SEC2YEAR  # k1: da2
            e = -10 * m * ap.thermo.basic.GAS_CONSTANT * np.log(10)  # activation energy, kJ
            tc, _ = ap.thermo.basic.get_tc(da2=d0r2, sda2=0, E=e * 1000, sE=0, pho=0, cooling_rate=20, A=27)  # plane
            axs[1, 0].plot(axs[1, 0].get_xlim(), [axs[1, 0].get_xlim()[0] * m + b, axs[1, 0].get_xlim()[1] * m + b], c=main_color[0], linewidth=2)
            axs[1, 0].text(11, -3, f"log(D0/r2) = {b:.2f}\nE = {e/4.184:.2f} kcal/mol\nTc = {tc:.2f} °C", **font_settings)
        axs[1, 0].set_title(f'Arrhenius Plot - {title}', loc='center', pad=-20, **font_settings)
        axs[1, 0].set_xlabel(f'10000 / T (10000/K)', **font_settings)
        axs[1, 0].set_ylabel(f'log(D/r2)', **font_settings)  #
        axs[1, 0].legend(loc='lower left')
    except FileNotFoundError:
        pass

    try:
        start = initial_age
        end = final_age
        file_mch_in = open(os.path.join(loc, f"{sname}_mch-out.dat"), "r")
        data, rows = read_IN(file_mch_in)
        input_x = []
        input_y = []
        axs[0, 1].set_xlim(*x2_extent, auto=autoscaling)
        axs[0, 1].set_ylim(*y2_extent, auto=autoscaling)
        for i, row in enumerate(rows):
            if row < 5:
                continue
            input_x.append(data[i][:row, 0].flatten())
            input_y.append(data[i][:row, 1].flatten())
            if i == 0:
                axs[0, 1].plot(input_x[-1], input_y[-1], c=shallow_color[2], marker="none", label=f'Cooling history simulations (n={len(rows)})')
            else:
                axs[0, 1].plot(input_x[-1], input_y[-1], c=shallow_color[2], marker="none")
        axs[0, 1].set_title(f'Cooling History - {title}', loc='center', **font_settings)
        axs[0, 1].set_xlabel(f'Age (Ma)', **font_settings)
        axs[0, 1].set_ylabel(f'Temperature (°C)', **font_settings)  #
        # confidence
        x, y = conf(input_x, input_y, start=start, end=end, num=40, using_binom=True)
        # file_mch_in = open(os.path.join(loc, f"confmed.dat"), "w")
        # for i in range(len(x)):
        #     file_mch_in.writelines(f"{x[i]}\t{y[i][0]}\t{y[i][2]}\n")
        # for i in range(len(x)):
        #     file_mch_in.writelines(f"{x[len(x) - i - 1]}\t{y[len(x) - i - 1][1]}\t{y[len(x) - i - 1][3]}\n")
        # file_mch_in = open(os.path.join(loc, f"confmed.dat"), "r")
        # [data], rows = read_IN(file_mch_in)
        # axs[0, 1].plot(data[:rows[0], 0], data[:rows[0], 1], c='#333333', marker="none", label="90% conf. interval of distribution")
        # axs[0, 1].plot(data[:rows[0], 0], data[:rows[0], 2], c='green', marker="none", label="90% conf. interval of mediam")
        axs[0, 1].plot(x, y[:, 0], c=main_color[1], marker="none", label="90% conf. interval for median")
        axs[0, 1].plot(x, y[:, 1], c=main_color[1], marker="none")
        axs[0, 1].plot(x, y[:, 2], c=middle_color[1], marker="none", label="90% conf. interval of distribution")
        axs[0, 1].plot(x, y[:, 3], c=middle_color[1], marker="none")
        axs[0, 1].legend(loc='upper left')
    except FileNotFoundError:
        pass

    fig.tight_layout()
    plt.show()

    if not export_PDF:
        return

    filename = f"{title}-matplotlib"

    params_list = {
        "page_size": 'a4', "ppi": 72, "width": 9.5, "height": 6,
        "pt_width": 0.8, "pt_height": 0.8, "pt_left": 0.16, "pt_bottom": 0.18,
        "offset_top": 0, "offset_right": 0, "offset_bottom": 20, "offset_left": 30,
        "plot_together": False, "show_frame": False,
        'xlabel_offset': 8, 'ylabel_offset': 2
    }

    plot_data = {
        "data": [
            transform(axs[0, 0]), transform(axs[0, 1]), transform(axs[1, 0]), transform(axs[1, 1]),
        ],
        "file_name": filename,
        "plot_names": [f"plotname"],
    }

    filepath = os.path.join(r"C:\Users\Young\Downloads", f"{filename}.pdf")
    cvs = [[ap.smp.export.get_cv_from_dict(plot, **params_list) for plot in plot_data['data']]]
    for i in range(len(cvs[0])):
        pt = cvs[0][i]._plot_areas[0]
        title = pt.get_comp(comp_name="title")
        title._y -= 2
        title._z_index = 999
        pt.text(50, title._y, text=f"({['a', 'b', 'c', 'd'][i]})", coordinate='pt', clip=False, size=8, z_index=299, v_align='top')
        for comp in pt._components:
            if isinstance(comp, pm.Scatter):
                comp._type = 'rec'
                comp._size = 1.5
        for index, legned in enumerate(list(filter(lambda cp: cp.name() == 'legend', pt._components))):
            legned._size = 7
            legned._z_index = 250
            legned._h_align = "left"
            legned._v_align = "center"
            if i == 0:  # age spectra
                legned._x = 175
                legned._y = 40 + index * 10
            elif i == 1:  # cooling history
                legned._x = 65
                legned._y = 135 - index * 10
            elif i == 2:  # arrhenius
                legned._x = 75
                legned._y = 40 + index * 10
            else:
                legned._x = 65
                legned._y = 40 + index * 10
            for comp in pt._components:
                if legned._text in comp.name() and "legend" in comp.name():
                    comp._z_index = 250
                    if isinstance(comp, pm.Scatter):
                        comp._x = legned._x - 10
                        comp._y = legned._y
                    if isinstance(comp, pm.Line):
                        comp._start = [legned._x - 16, legned._y]
                        comp._end = [legned._x - 4, legned._y]


    filepath = ap.smp.export.export_chart_to_pdf(cvs, filename, filepath)


def transform(ax: plt.Axes):
    xlabels = [i.get_text().replace('−', '-') for i in ax.get_xticklabels()]
    ylabels = [i.get_text().replace('−', '-') for i in ax.get_yticklabels()]
    linestyles = {'-': 'solid', '--': 'dashed', '-.': 'dashdot', ':': 'dotted'}

    series = []
    for i, line in enumerate(ax.lines):
        xy_data = line.get_xydata()  # [[x1, y1], [x2, y2], ...]
        line_style = linestyles.get(line.get_linestyle(), 'solid')
        series.append({
            'type': 'series.line', 'id': f'line-{i}', 'name': f'line-{i}',
            'color': line.get_color(), 'line_width': 1, 'line_style': line_style,
            'data': xy_data, 'line_caps': 'none'
        })
        if bool(line._marker):
            series.append({
                'type': 'series.scatter', 'id': f'line-marker-{i}', 'name': f'line-marker-{i}',
                'stroke_color': line.get_markeredgecolor(), 'fill_color': line.get_markerfacecolor(),
                'data': xy_data, 'size': 2,
                # 'symbol': line._marker.markers.get(line.get_marker(), 'square'),
                'symbol': 'rec'
            })
    for i, collection in enumerate(ax.collections):
        series.append({
            'type': 'series.scatter', 'id': f'scatter-{i}', 'name': f'{collection.get_label()}',
            'stroke_color': collection.get_edgecolor()[0][:3], 'fill_color': collection.get_edgecolor()[0][:3],
            'data': collection.get_offsets(), 'size': 2,
            'symbol': 'rec'
        })

    for i, text in enumerate(ax.texts):
        xy_data = text.get_position()  # [[x1, y1], [x2, y2], ...]
        series.append({
            'type': 'series.text', 'id': f'text-{i}', 'name': f'text-{i}',
            'color': text.get_color(), 'data': [xy_data], 'text': text.get_text().replace('\n', '<r>'),
            'size': 8
        })

    series.append({
        'type': 'series.text', 'id': f'title', 'name': f'title',
        'color': 'black', 'data': [[sum(ax.get_xlim()) / 2, ax.get_ylim()[1]]],
        'h_align': "middle", 'v_align': "top",
        'text': ax.get_title(), 'size': 8
    })

    if ax.legend_ is not None:
        for handle, text in zip(ax.legend_.legend_handles, ax.legend_.texts):
            series.append({
                'type': 'series.text', 'id': f'legend', 'name': f'legend',
                'color': text.get_color(), 'data': [[ax.get_xlim()[0], ax.get_ylim()[0]]],
                'h_align': "left", 'v_align': "bottom",
                'text': text.get_text(), 'size': 8
            })
            if isinstance(handle, plt.Line2D):
                series.append({
                    'type': 'series.line', 'id': f'legend-line', 'name': f'legend-line-{text.get_text()}',
                    'color': handle.get_color(), 'data':[[ax.get_xlim()[0], ax.get_ylim()[0]], [ax.get_xlim()[1], ax.get_ylim()[1]]],
                    'line_width': 1, 'line_style': linestyles.get(handle.get_linestyle(), 'solid')
                })
            if isinstance(handle, PathCollection):
                stroke_c = handle.get_edgecolor()[0][:3]
                stroke_c = f"#{int(stroke_c[0]*255):02x}{int(stroke_c[1]*255):02x}{int(stroke_c[2]*255):02x}"
                fill_c = handle.get_facecolor()[0][:3]
                fill_c = f"#{int(fill_c[0]*255):02x}{int(fill_c[1]*255):02x}{int(fill_c[2]*255):02x}"
                series.append({
                    'type': 'series.scatter', 'id': f'legend-scatter', 'name': f'legend-scatter-{text.get_text()}',
                    'stroke_color': stroke_c, 'fill_color': fill_c,
                    'data': [[sum(ax.get_xlim()) / 2, sum(ax.get_ylim()) / 2]],
                    'size': 2, 'symbol': 'rec'
                })

    data = {
        'xAxis': [{
            'extent': ax.get_xlim(), 'interval': xlabels, 'title': ax.get_xlabel(),
            'nameLocation': 'middle', 'show_frame': True, 'label_size': 8, 'title_size': 8,
        }],
        'yAxis': [{
            'extent': ax.get_ylim(), 'interval': ylabels, 'title': ax.get_ylabel(),
            'nameLocation': 'middle', 'show_frame': True, 'label_size': 8, 'title_size': 8,
        }],
        'series': series
    }

    # print(data)
    return data



if __name__ == "__main__":

    params = {
        "initial_age": 0,
        "final_age": 14,
        "x1_extent": [0, 100],
        "y1_extent": [0, 30],
        "x2_extent": [0, 14],
        "y2_extent": [0, 500],
        "x3_extent": [4, 16],
        "y3_extent": [-10, 0],
        "x4_extent": [0, 2000],
        "y4_extent": [0, 100],
        "autoscaling": False,
        # "autoscaling": True,
        # "export_PDF": False,
        "export_PDF": True,
        "index": list(range(1, 12)),
    }

    s = ""
    # s = "24FY51-remove 1st"
    # s = "24FY49-remove 1st"
    # s = "24FY49-smooth"
    # s = "24FY55-smooth"
    # s = "24FY50-smooth - Copy"
    # s = "24FY07"
    # s = "24FY07-smooth"
    # s = "24FY49"
    # s = "24FY50"
    # s = "24FY51-900C"
    # s = "24FY51"
    # s = "24FY52"
    # s = r"24FY53"
    s = r"24FY53-smooth"
    # s = "24FY54"
    # s = "24FY55"
    # s = "24FY55-smooth-2"
    # s = "24FY55-remove 1st"
    # s = "24FY56"
    # s = "24FY62"
    # s = "24FY64"
    # s = r"24FY67"
    # s = "24FY68"
    # s = r"24FY70"
    # s = r"24FY71"
    # s = r"24FY72"
    # s = "24FY86b"
    # s = "24FY87"
    # s = "24FY88"
    # s = "24FY89"
    # s = "24FY90"
    # s = r"24FY92"
    # s = r"24FY93"
    # s = "WCG-2New"
    # s = r"MDDprograms\WCG-2 - Copy"
    # s = r"4908963"
    # s = r"5096179"
    # s = r"4412795"
    s = r"6950150"

    loc = os.path.join("D:\DjangoProjects\webarar\private\mdd", s)
    plot_MDD_res(loc=loc, title=s + "release plot", **params)

