#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Granite Cooling History
# ==========================================
#
#
# 
"""

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
from matplotlib.patches import Rectangle
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
    except:
        return False


def read_data(file):
    data = []
    rows = []
    go = True
    while go:
        go = False
        group = np.zeros([200, 20], dtype='<U64')
        row = 0
        while True:
            try:
                line = file.readline().rstrip("\n")
                print(line)
                if line == "":
                    break
                for col, _ in enumerate([str(l) for l in line.split(',')]):
                    group[row][col] = _
            except (Exception, BaseException) as e:
                print(e)
                break
            else:
                row += 1
        data.append(group)
        rows.append(row)
    return data, rows


def plot_CH(file, sname=None, title="", **params):

    file_IN = open(file, "r")
    [data], [nstep] = read_data(file_IN)


    initial_age = params.pop("initial_age", 0)
    final_age = params.pop("final_age", 20)
    x1_extent = params.pop("x1_extent", [0, 50])
    y1_extent = params.pop("y1_extent", [0, 900])
    x2_extent = params.pop("x2_extent", [initial_age, final_age])
    y2_extent = params.pop("y2_extent", [0, 500])
    x3_extent = params.pop("x3_extent", [4, 16])
    y3_extent = params.pop("y3_extent", [-10, 0])
    x4_extent = params.pop("x4_extent", [0, 1000])
    y4_extent = params.pop("y4_extent", [200, 1600])
    autoscaling = params.pop("autoscaling", False)
    export_PDF = params.pop("export_PDF", False)
    index = params.pop("index", [])

    main_color = ['#397DA1', '#BA5624', '#212121', '#3C6933', '#74757C', '#214193', '#524715']  # blue red black green
    middle_color = ['#83CDFA', '#F1B595', '#737373', '#84B775', '#C1C3CB', '#6D8AE1', '#C0A737']
    shallow_color = ['#E0F1FE', '#FBEBE3', '#DDDDDD', '#CFFEC0', '#EDEEF8', '#D6DFFC', '#FCF0BC']

    print(f"{sname = }, {title = }")

    fig, axs = plt.subplots(1, 1, figsize=(6, 4))

    font_settings = {
        # 'fontsize': 10,
        # 'fontfamily': 'Arial'
    }

    colors = {
        "biotite": {"facecolor": "#F1B595", "edgecolor": "#BA5624"},
        "黑云母": {"facecolor": "#F1B595", "edgecolor": "#BA5624"},
        "zircon": {"facecolor": "#737373", "edgecolor": "#212121"},
        "锆石": {"facecolor": "#737373", "edgecolor": "#212121"},
        "muscovite": {"facecolor": "#83CDFA", "edgecolor": "#397DA1"},
        "白云母": {"facecolor": "#83CDFA", "edgecolor": "#397DA1"},
        "monazite": {"facecolor": "#84B775", "edgecolor": "#3C6933"},
        "独居石": {"facecolor": "#84B775", "edgecolor": "#3C6933"},
        "apatite": {"facecolor": "#D6DFFC", "edgecolor": "#6D8AE1"},
        "磷灰石": {"facecolor": "#D6DFFC", "edgecolor": "#6D8AE1"},
        "xenotime": {"facecolor": "#C0A737", "edgecolor": "#524715"},
        "磷钇矿": {"facecolor": "#C0A737", "edgecolor": "#524715"},
        "电气石": {"facecolor": "white", "edgecolor": "#524715"},
        "角闪石": {"facecolor": "white", "edgecolor": "#524715"},
    }

    axs.set_xlim(*x1_extent, auto=autoscaling)
    axs.set_ylim(*y1_extent, auto=autoscaling)
    body = data[:nstep, 0]
    area = data[:nstep, 1]
    lithology = data[:nstep, 2]
    sample_number = data[:nstep, 3]
    mineral = data[:nstep, 4]
    method = data[:nstep, 5]
    age = data[:nstep, 6].astype(np.float32)
    sage = data[:nstep, 7].astype(np.float32)
    reference = data[:nstep, 8]
    tc = data[:nstep, 9].astype(np.float32)
    stc = data[:nstep, 10].astype(np.float32)
    print(f"{nstep = }")
    for i in np.argsort(sage)[::-1]:
        color = colors[mineral[i]]
        print(f"age = {age[i]} +/- {sage[i]}, Tc = {tc[i]} +/- {stc[i]}")
        linestyle = "solid"
        rect = Rectangle(
            (age[i]-sage[i], tc[i]-stc[i]), width=2 * sage[i], height=2 * stc[i], **color,
            linestyle=linestyle
        )
        axs.add_patch(rect)
    axs.set_title(f'{title}', loc='center', y=1, **font_settings)
    axs.set_xlabel(f'Age (Ma)', **font_settings)
    axs.set_ylabel(f'Temperature (°C)', **font_settings)

    fig.tight_layout()
    plt.show()

    if not export_PDF:
        return

    filename = f"{title} - cooling history - matplotlib"

    params_list = {
        "page_size": 'a4', "ppi": 72, "width": 14, "height": 8,
        "pt_width": 0.8, "pt_height": 0.8, "pt_left": 0.16, "pt_bottom": 0.18,
        "offset_top": 0, "offset_right": 0, "offset_bottom": 20, "offset_left": 30,
        "plot_together": False, "show_frame": False,
        'xlabel_offset': 8, 'ylabel_offset': 2
    }

    plot_data = {
        "data": [
            transform(axs),
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

    for child in ax._children:
        if isinstance(child, Rectangle):
            ld = [*child.get_xy(), child.get_width(), child.get_height()]
            series.append({
                'type': 'series.rect', 'id': f'rect-{child.get_gid()}', 'name': f'rect-{child.get_gid()}',
                'color': child.get_edgecolor()[:3], 'fill_color': child.get_facecolor()[:3], 'fill': True,
                'data': [ld], 'label': child.get_label(), 'clip': True
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
        "final_age": 11,
        "x1_extent": [0, 60],
        "y1_extent": [0, 900],
        "x2_extent": [0, 11],
        "y2_extent": [0, 500],
        "x3_extent": [4, 16],
        "y3_extent": [-10, 0],
        "x4_extent": [0, 1800],
        "y4_extent": [200, 1600],
        "autoscaling": False,
        # "autoscaling": True,
        # "export_PDF": False,
        "export_PDF": True,
        "index": list(range(2, 17)),
    }


    s = 'yalaxiangbo'
    s = 'paiku'
    s = 'kuday'
    s = 'ramba'
    s = 'gaowu'
    s = 'luozha'
    loc = os.path.join("D:\DjangoProjects\webarar\private\mdd", f"{s}.txt")
    plot_CH(file=loc, title=f"{s.capitalize()} - Cooling History", **params)

