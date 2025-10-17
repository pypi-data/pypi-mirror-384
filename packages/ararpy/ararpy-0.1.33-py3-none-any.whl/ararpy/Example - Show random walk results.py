#  Copyright (C) 2025 Yang. - All Rights Reserved

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2025 Yang 
# ararpy - Example - Show random walk results
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


main_color = ['#397DA1', '#BA5624', '#212121', '#6C5D1E', '#BC3D85', '#3C6933']  # blue red black
middle_color = ['#83CDFA', '#F1B595', '#737373', '#C0A737', '#E9CDE1', '#84B775']
shallow_color = ['#E0F1FE', '#FBEBE3', '#DDDDDD', '#F9E16F', '#CB73B0', '#B8F1A7']

colors =[
    '#397DA1', '#BA5624', '#212121', '#6C5D1E', '#BC3D85', '#3C6933',
    '#83CDFA', '#F1B595', '#737373', '#C0A737', '#E9CDE1', '#84B775',
    '#E0F1FE', '#FBEBE3', '#DDDDDD', '#F9E16F', '#CB73B0', '#B8F1A7',
]


def export_to_pdf(axs, filename="unknown"):

    params_list = {
        "page_size": 'a4', "ppi": 72, "width": 9.5, "height": 6,
        "pt_width": 0.8, "pt_height": 0.8, "pt_left": 0.16, "pt_bottom": 0.18,
        "offset_top": 0, "offset_right": 0, "offset_bottom": 20, "offset_left": 30,
        "plot_together": False, "show_frame": False,
        'xlabel_offset': 8, 'ylabel_offset': 2
    }

    plot_data = {
        "data": [transform(axs)],
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

    return filepath


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
    te = np.array(sample.TotalParam[124], dtype=np.float64)
    ti = (np.array(sample.TotalParam[123], dtype=np.float64) / 60).round(2)  # time in minute
    nindex = {"40": 24, "39": 20, "38": 10, "37": 8, "36": 0}
    argon = "39"
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
    f = np.cumsum(ar) / ar.sum()

    # 组合data
    dr2 = [1 for i in range(nsteps)]
    ln_dr2 = [1 for i in range(nsteps)]
    wt = [1 for i in range(nsteps)]
    data = np.array([sequence.value, te, ti, age, sage, ar, sar, f, dr2, ln_dr2, wt]).tolist()
    data.insert(0, (np.where(np.array(data[3]) > 0, True, False) & np.isfinite(data[3])).tolist())
    data.insert(1, [1 for i in range(nsteps)])
    for row in ap.calc.arr.transpose(data):
        print(row)
    return data, name


def read_ads(ads_file_path):
    released = []
    release_name = []

    ads_released = []
    index = 1
    if os.path.isdir(ads_file_path):
        for (dirpath, dirnames, fs) in os.walk(ads_file_path):
            for f in fs:
                if f.endswith(".ads"):
                    file_path = os.path.join(ads_file_path, f)
                    if not os.path.exists(file_path):
                        continue
                    # if "k=100" not in f:
                    #     continue
                    index += 1
                    release_name.append(f"Released{index}: {f}")
                    diff = ap.thermo.arw.read_ads(file_path)
                    print(f"{f = }, {len(diff.released_per_step) = }, {diff.atom_density = :.0e}")
                    print(f"{'kJ/mol, '.join([str(dom.energy / 1000) for dom in diff.domains])}")
                    print(f"{'kcal/mol, '.join([str(dom.energy / 4.181 / 1000) for dom in diff.domains])}")
                    ads_released.append(np.array(diff.released_per_step) / diff.natoms)


    # for i in range(len(ads_released)):
    #     released.append([i + 1, sum(ar[0:i + 1])  / sum(ar), *ads_released[i]])
    #
    # spectra_data.append(released)

    return ads_released, release_name


def plot_diff(loc, arr_file_path=None, argon=39):
    ads_released, release_name = read_ads(loc)

    fig, axs = plt.subplots(1, 1, figsize=(12, 8))

    index = 0
    for index, each_line in enumerate(ads_released):
        axs.plot(list(range(1, len(each_line) + 1)), each_line, c=colors[index], linewidth=1, label=release_name[index])

    if arr_file_path is not None:
        sample = ap.from_arr(file_path=arr_file_path)
        nindex = {"40": 24, "39": 20, "38": 10, "37": 8, "36": 0}
        argon = str(argon)
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
        axs.plot(list(range(1, len(ar) + 1)), np.cumsum(ar) / np.sum(ar), c=colors[index+1], linewidth=1, label=f"{sample.name()}")

    axs.set_title(f'Ads released', loc='center', y=1,)
    axs.set_xlabel(f'Steps',)
    axs.set_ylabel(f'Aumulative Argon Released (100%)',)
    axs.legend(loc='lower right')
    fig.tight_layout()
    plt.show()

    export_to_pdf(axs, filename="test_ads")


def plot_spectra(loc, arr_file_path=None, argon=39, loc39=""):

    ar = []
    name = ""
    if arr_file_path is not None:
        sample = ap.from_arr(file_path=arr_file_path)
        name = sample.name()
        ar39 = np.array(sample.DegasValues[20], dtype=np.float64)  # 20-21 Argon
        ar40 = np.array(sample.DegasValues[24], dtype=np.float64)
        print(f"{ar40 = }")



    ads_released_ar40, release_name = read_ads(loc)
    ads_released_ar39, release_name = read_ads(loc39)

    fig, axs = plt.subplots(1, 1, figsize=(12, 8))

    index = 0
    for index, each_line in enumerate(ads_released_ar40):
        _ = np.array(each_line) * sum(ar40)
        ar40_model = [_[0]]
        for i in range(1, len(_)):
            ar40_model.append(_[i] - _[i - 1])

        _ = np.array(ads_released_ar39[0]) * sum(ar39)
        ar39_model = [_[0]]
        for i in range(1, len(_)):
            ar39_model.append(_[i] - _[i - 1])
        ar39_model = ar39_model[:58]
        print(f"{len(ar39_model) = }, {len(ar40_model) = }")

        x, y1, y2 = ap.calc.spectra.get_data(np.array(ar40_model)/np.array(ar39_model), np.zeros(len(ar39_model)), ar39_model)
        axs.plot(x, y1, c=colors[index], linewidth=1, label=release_name[index])

    x, y1, y2 = ap.calc.spectra.get_data(ar40/ar39, np.zeros(len(ar40)), ar39)
    axs.plot(x, y1, c=colors[index+1], linewidth=1, label=f"{name}")

    axs.set_title(f'Ads spectra', loc='center', y=1,)
    axs.set_xlabel(f'Steps',)
    axs.set_ylabel(f'Aumulative Argon Released (100%)',)
    axs.set_ylim(0, 8)
    axs.legend(loc='lower right')
    fig.tight_layout()
    plt.show()

    export_to_pdf(axs, filename="test_ads")



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
    loc = r"D:\DjangoProjects\webarar\private\mdd\20240920_24FY88a\1doms"
    loc = r"D:\DjangoProjects\webarar\private\mdd\20240920_24FY88a\2doms"
    loc = r"D:\DjangoProjects\webarar\private\mdd\20240920_24FY88a\5doms"
    loc = r"D:\DjangoProjects\webarar\private\mdd\20240920_24FY88a\6doms"
    # loc = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\thermo-history-0628"
    # loc = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\thermo-history-0628\heating_experiment"
    loc = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\thermo-history-0919\lab"
    loc2 = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\thermo-history-0919\ar39"
    # loc = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\thermo-history-0919\ar39"
    # arr_file_path = r"D:\DjangoProjects\webarar\private\mdd\20240920_24FY88a\20240920_24FY88a.arr"
    arr_file_path = r"D:\DjangoProjects\webarar\private\mdd\24FY88a-Ar40\20240920_24FY88a-smooth.arr"
    # plot_diff(loc, arr_file_path, argon=39)
    plot_spectra(loc, arr_file_path, argon=40, loc39=loc2)
