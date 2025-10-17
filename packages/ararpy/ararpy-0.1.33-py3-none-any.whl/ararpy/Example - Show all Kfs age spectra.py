#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Show all Kfs age spectra
# ==========================================
#
#
# 
"""
import os
import numpy as np
import ararpy as ap
import pdf_maker as pm
import matplotlib
from matplotlib import cm
from matplotlib.collections import PathCollection

matplotlib.use('TkAgg')
matplotlib.rc('font',family='Arial', size=10)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


heating_schedule = {
    '20240621_24FY56a': 1,
    '20240630_24FY49a': 2,
    '20240705_24FY50a': 2,
    '20240710_24FY51a': 2,
    '20240714_24FY52': 2,
    '20240728_24FY55a': 2,
    '20240821_24FY67a': 2,
    '20240823_24FY71a': 2,
    '20240916_24FY92a': 2,
    '20240920_24FY88a': 2,
    '20240922_24FY89a': 2,
    '20240924_24FY70a': 2,
    '20241005_24FY72a': 3,
    '20241009_24FY62a': 3,
    '20241013_24FY64b': 3,
    '20241016_24FY66a': 4,
    '20241023_24FY68a': 5,
    '20241118_24FY93a': 7,
    '20241204_24FY53b': 7,
    '20241206_24FY54b': 6,
    '20241208_24FY87b': 6,
    '20241209_24FY86b': 6,
}

cc = {
    'Y49': 2,
    'Y50': 2,
    'Y51': 2,
    'Y52': 2,
    'Y53': 7,
    'Y54': 6,
    'Y55': 2,
    'Y56': 1,
    'Y62': 3,
    'Y64': 3,
    'Y66': 4,
    'Y67': 2,
    'Y68': 5,
    'Y70': 2,
    'Y71': 2,
    'Y72': 3,
    'Y86': 6,
    'Y87': 6,
    'Y88': 2,
    'Y89': 2,
    'Y93': 7,
    'Y92': 2,
}


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


def read_sample(arr_file_path):
    # 读取样品信息
    if not arr_file_path.endswith('.arr'):
        for root, dirs, files in os.walk(arr_file_path):
            for file in files:
                if file.endswith('.arr'):
                    arr_file_path = os.path.join(arr_file_path, file)
                    break
    sample = ap.from_arr(file_path=arr_file_path)
    name = sample.name()
    sequence = sample.sequence()
    nsteps = sequence.size
    te = np.array(sample.TotalParam[124], dtype=np.float64)
    ti = (np.array(sample.TotalParam[123], dtype=np.float64) / 60).round(2)  # time in minute
    nindex = {"40": 24, "39": 20, "38": 10, "37": 8, "36": 0}
    argon = "39"
    argon = "40"
    if argon in list(nindex.keys()):
        ar = np.array(sample.DegasValues[nindex[argon]], dtype=np.float64)  # 20-21 Argon
        sar = np.array(sample.DegasValues[nindex[argon] + 1], dtype=np.float64)
    elif argon == 'total':
        all_ar = np.array(sample.CorrectedValues, dtype=np.float64)  # 20-21 Argon
        ar, sar = ap.calc.arr.add(*all_ar.reshape(5, 2, len(all_ar[0])))
        ar = np.array(ar)
        sar = np.array(sar)
    else:
        raise KeyError
    age = np.array(sample.ApparentAgeValues[2], dtype=np.float64)  # 2-3 age
    sage = np.array(sample.ApparentAgeValues[3], dtype=np.float64)
    f = ar / ar.sum() * 100

    ar39 = np.array(sample.DegasValues[20], dtype=np.float64)
    ar40 = np.array(sample.DegasValues[24], dtype=np.float64)

    # f = np.ones(60) * 100 / 60

    x, y1, y2 = ap.calc.spectra.get_data(age, sage, f, cumulative=False)

    X = x + list(reversed(x))
    Y = y1 + list(reversed(y2))

    hs = heating_schedule[name]

    # if hs != 2:
    #     raise ValueError
    print(f"{name = }, {nsteps = }")

    # if max(y1[15:50]) > 50:
    #     print(name)

    only_te = []
    only_f = []
    for i, tei in enumerate(te):
        if tei not in only_te:
            only_te.append(tei)
            only_f.append(0)
        else:
            only_f[-1] += ar[i]

    age_plot = sample.AgeSpectraPlot



    # return np.cumsum(ar39) / sum(ar39), np.cumsum(ar40) / sum(ar40), name
    # return x, y1, name
    return X, Y, name
    # return list(range(nsteps+1)), np.insert(f, 0, 0), name
    # return only_te, np.cumsum(only_f) / np.sum(only_f), name
    # return te, f, name
    # return np.transpose([[i * 100 / 60 for i in range(60)], age - sage, [100 / 60 for i in range(60)], 2 * sage])


def check_name(name):
    samples = ['Y64', 'Y66', 'Y67', 'Y68', 'Y70', 'Y72', 'Y86', 'Y88', 'Y89']
    # samples = ['Y71', 'Y87', 'Y92', 'Y93']
    samples = ['Y49', 'Y55', 'Y56', 'Y62']
    samples = ['Y71', 'Y92', 'Y93', 'Y72', 'Y87']
    # samples = ['Y51', 'Y52', 'Y53', 'Y54', 'Y50']
    for i in samples:
        if i in name:
            return True
    raise ValueError

fig, axs = plt.subplots(1, 1, figsize=(6, 4))

axs.set_xlim(0, 20, auto=False)
axs.set_ylim(0, 10, auto=False)
axs.set_title(f'All Kfs age spectra', loc='center', y=1)
axs.set_ylabel(f'Apparent Age (Ma)')
axs.set_xlabel(f'Cumulative 39Ar released')

i = 0
v = cm.get_cmap('viridis')
colors = [v(i) for i in np.random.random(22)]


loc = r"C:\Users\Young\OneDrive\00-Projects\【2】个人项目\2024-10 Ar-Ar扩散理论\钾长石Arr"
for root, dirs, files in os.walk(loc):
    for file in files:
        if file.endswith('.arr'):
            # for smp in samples:
            #     if smp in file:
            arr_file_path = os.path.join(loc, file)
            try:
                check_name(file)
                x, y, name = read_sample(arr_file_path)
                # axs.plot(x, [yi + i * 10 for yi in y], label=name)
                axs.plot(x, y, label=name)
            except Exception as e:
                print(e)
                continue
            # continue
        i += 1

axs.legend(loc='best')
fig.tight_layout()
plt.show()


filename = f"39argon release excess ar - 2 - matplotlib"

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