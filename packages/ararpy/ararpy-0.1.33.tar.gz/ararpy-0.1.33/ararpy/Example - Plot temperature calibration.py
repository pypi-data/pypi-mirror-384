#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Plot temperature calibration
# ==========================================
#
#
# 
"""
import datetime
import os
import re
import pytz

import numpy as np
import ararpy as ap
import pdf_maker as pm
import matplotlib
from matplotlib import cm
from matplotlib.collections import PathCollection

matplotlib.use('TkAgg')
matplotlib.rc('font',family='Arial', size=10)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


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

def read_libano(file_path):
    res = []

    if os.path.isdir(file_path):
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if "libano" in file:
                    file_path = os.path.join(file_path, file)
                    break
    print(f"{file_path = }")
    if os.path.exists(file_path):
        for line in open(file_path, "r"):
            temp = re.findall(r"Z;\d+;\d+", line)
            setpoint, reading = re.findall(r"\d+", temp[0])
            dt_object = datetime.datetime.strptime(
                re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", line)[0],
                "%Y-%m-%dT%H:%M:%SZ")

            timezone = pytz.utc
            dt_object = timezone.localize(dt_object)

            res.append([dt_object, int(setpoint), int(reading)])
            # res[int(dt_object.timestamp())] = {
            #     "set": int(setpoint), "read": int(reading)
            # }

    return res


def read_test_log(file_path):
    # res = {}
    res = []

    if os.path.isdir(file_path):
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if "Test" in file:
                    file_path = os.path.join(file_path, file)
                    break

    print(f"{file_path = }")
    if os.path.exists(file_path):
        for line in open(file_path, "r"):
            if len(line) <= 20:
                continue
            split = line.split(";")
            time_str = split[0]
            temp_str = split[1]

            dt_object = datetime.datetime.strptime(
                re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", time_str)[0],
                "%Y-%m-%dT%H:%M:%SZ")

            timezone = pytz.utc
            dt_object = timezone.localize(dt_object)

            # res[int(dt_object.timestamp())] = {
            #     "read": int(temp_str)
            # }
            res.append([dt_object, int(temp_str)])

    return res


loc = r"C:\Users\Young\OneDrive\Documents\Libano Data\2024-03-13"

s = r"202403131203-libano.log"

filepath = os.path.join(loc, s)

outside = read_libano(loc)
inside = read_test_log(loc)


fig, axs = plt.subplots(1, 1, figsize=(6, 4))

# axs.set_xlim(0, 20, auto=True)
# axs.set_ylim(0, 10, auto=True)
# axs.set_title(f'Temperature check', loc='center', y=1)
# axs.set_ylabel(f'Time (ms)')
# axs.set_xlabel(f'Temperature (°C)')

i = 0
v = cm.get_cmap('viridis')
colors = [v(i) for i in np.random.random(22)]

x1, y1_set, y1_read = ap.calc.arr.transpose(outside)
x2, y2_read = ap.calc.arr.transpose(inside)

print(x1)
print(y1_set)


axs.plot(x1, y1_set, label="Setpoints", c="green")
axs.plot(x1, y1_read, label="Outside readings", c="blue")
axs.plot(x2, y2_read, label="Inside readings", c="red")

# 设置x轴格式
axs.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
axs.xaxis.set_major_locator(mdates.SecondLocator(interval=7200))  # 每分钟一个主刻度
axs.xaxis.set_minor_locator(mdates.SecondLocator(interval=3600))   # 每10秒一个次刻度
axs.set_xlim(
    datetime.datetime.strptime("2024-03-13T15:40:00Z", "%Y-%m-%dT%H:%M:%SZ"),
    datetime.datetime.strptime("2024-03-13T16:20:00Z", "%Y-%m-%dT%H:%M:%SZ")
)
axs.set_ylim(650, 800)

# axs.legend(loc='best')
fig.tight_layout()
plt.show()

#
#
# filename = f"39argon release excess ar - 2 - matplotlib"
#
# params_list = {
#     "page_size": 'a4', "ppi": 72, "width": 14, "height": 8,
#     "pt_width": 0.8, "pt_height": 0.8, "pt_left": 0.16, "pt_bottom": 0.18,
#     "offset_top": 0, "offset_right": 0, "offset_bottom": 20, "offset_left": 30,
#     "plot_together": False, "show_frame": False,
#     'xlabel_offset': 8, 'ylabel_offset': 2
# }
#
# plot_data = {
#     "data": [
#         transform(axs),
#     ],
#     "file_name": filename,
#     "plot_names": [f"plotname"],
# }
#
# filepath = os.path.join(r"C:\Users\Young\Downloads", f"ceshi.pdf")
# cvs = [[ap.smp.export.get_cv_from_dict(plot, **params_list) for plot in plot_data['data']]]
# for i in range(len(cvs[0])):
#     pt = cvs[0][i]._plot_areas[0]
#     for index, legned in enumerate(list(filter(lambda cp: cp.name() == 'legend', pt._components))):
#         legned._size = 7
#         legned._z_index = 250
#         legned._h_align = "left"
#         legned._v_align = "center"
#         if i == 0:  # age spectra
#             legned._x = 175
#             legned._y = 40 + index * 10
#         elif i == 1:  # cooling history
#             legned._x = 65
#             legned._y = 135 - index * 10
#         elif i == 2:  # arrhenius
#             legned._x = 75
#             legned._y = 40 + index * 10
#         else:
#             legned._x = 65
#             legned._y = 40 + index * 10
#         for comp in pt._components:
#             if legned._text in comp.name() and "legend" in comp.name():
#                 comp._z_index = 250
#                 if isinstance(comp, pm.Scatter):
#                     comp._x = legned._x - 10
#                     comp._y = legned._y
#                 if isinstance(comp, pm.Line):
#                     comp._start = [legned._x - 16, legned._y]
#                     comp._end = [legned._x - 4, legned._y]
#
#
# filepath = ap.smp.export.export_chart_to_pdf(cvs, filename, filepath)