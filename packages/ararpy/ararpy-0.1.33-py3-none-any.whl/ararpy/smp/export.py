#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ==========================================
# Copyright 2023 Yang
# webarar - export
# ==========================================
#
#
#

from re import findall
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet
from xlsxwriter.chartsheet import Chartsheet
from xlsxwriter.format import Format
import os
import sys
import pickle
import traceback
import pdf_maker as pm
import numpy as np
from math import log
from decimal import Decimal

from ..calc import arr, isochron, spectra, err
from ..calc.basic import get_random_digits, merge_dicts
from ..calc.plot import get_axis_scale
from . import basic, sample, consts

Sample = sample.Sample
Plot = sample.Plot

title_size = 8
label_size = 8

colors_map = {
    'red': "#EF661B",
    'blue': "#189CCA",
    'red80': "#FFB593",
    'blue80': "#6BD2FF",
}

try:
    from webarar.settings import SETTINGS_ROOT
except ModuleNotFoundError:
    SETTINGS_ROOT = ""


def to_excel(smp: Sample, file_path: str, *args, **kwargs):
    excel = WritingWorkbook(sample=smp, filepath=file_path, *args, **kwargs)
    excel.get_xls()


def to_pdf(file_path: str, figure: str, smp: Sample):
    pdf = CreatePDF(filepath=file_path, sample=smp)
    pdf.save(figure=figure)


def get_cv_from_dict(data: dict, **kwargs):
    # create a canvas
    cv = pm.Canvas(width=kwargs.get("width", 17), height=kwargs.get("height", 12),
                   unit="cm", show_frame=False, clip_outside_plot_areas=False)
    # change frame outline style
    if kwargs.get("show_frame", False):
        cv.show_frame(color="grey", line_width=0.5)
    # stick length
    stick_length = kwargs.get("stick_length", 3)
    ylabel_offset = kwargs.get("ylabel_offset", 2)
    xlabel_offset = kwargs.get("xlabel_offset", 8)
    axis_num = min([len(data['xAxis']), len(data['yAxis'])])
    # draw axis
    plots = []
    for i in range(axis_num):
        scale = [*data['xAxis'][i]['extent'], *data['yAxis'][i]['extent']]
        scale = (float(scale[0]), float(scale[1]), float(scale[2]), float(scale[3]))
        # create plot area based on axis scale
        plot_area = (kwargs.get("pt_left", 0.15), kwargs.get("pt_bottom", 0.15), kwargs.get("pt_width", 0.8), kwargs.get("pt_height", 0.8))
        pt = cv.add_plot_area(name=f"PlotArea{i}", plot_area=plot_area, plot_scale=scale, **data['xAxis'][i])
        for stick in data['xAxis'][i]['interval']:
            start = pt.scale_to_points(float(stick), scale[2])
            end = pt.scale_to_points(float(stick), scale[2])
            end = (end[0], end[1] - stick_length)
            if pt.line(start=start, end=end, width=data['xAxis'][i].get('line_width', 1), line_style="solid", y_clip=False, coordinate="pt", z_index=100):
                pt.text(x=start[0], y=end[1] - xlabel_offset, text=f"{stick}", clip=False, size=int(data['xAxis'][i].get('label_size', 8)),
                        coordinate="pt", h_align="middle", z_index=150)
        for stick in data['yAxis'][i]['interval']:
            start = pt.scale_to_points(scale[0], float(stick))
            end = pt.scale_to_points(scale[0], float(stick))
            end = (end[0] - stick_length, end[1])
            if pt.line(start=start, end=end, width=data['xAxis'][i].get('line_width', 1), line_style="solid", x_clip=False, coordinate="pt", z_index=100):
                pt.text(x=end[0] - ylabel_offset, y=end[1], text=f"{stick}", clip=False, size=int(data['yAxis'][i].get('label_size', 8)),
                        coordinate="pt", h_align="right", v_align="center", z_index=150)
        # axis titles
        nloc = pt.scale_to_points(sum(scale[:2]) / 2, scale[2])
        pt.text(x=nloc[0], y=nloc[1] - kwargs.get("offset_bottom", 30), text=data['xAxis'][i].get('title', 'title'), clip=False, coordinate="pt",
                h_align="middle", v_align="center", z_index=150, size=int(data['xAxis'][i].get('title_size', 8)))
        nloc = pt.scale_to_points(scale[0], sum(scale[2:4]) / 2)
        pt.text(x=nloc[0] - kwargs.get("offset_left", 50), y=nloc[1], text=data['yAxis'][i].get('title', 'title'), clip=False, coordinate="pt",
                h_align="middle", v_align="center", rotate=90, z_index=150, size=int(data['yAxis'][i].get('title_size', 8)))
        plots.append(pt)
    # draw series
    for se in data['series']:
        data = np.array(se.get('data', []), dtype=np.float64)
        for key, val in se.items():
            if str(val).isnumeric():
                se[key] = int(val)
            else:
                try:
                    se[key] = float(val)
                except (ValueError, TypeError):
                    pass
        try:
            pt = plots[se.get('axis_index', 0)]
        except IndexError:
            continue
        if 'line' in se['type']:
            se['width'] = se.get('line_width', 1)
            se['line_style'] = se.get('line_style', 'solid')
            se['color'] = se.get('color', 'black')
            se['line_caps'] = se.get('line_caps', 'none')
            se['z_index'] = int(se.get('z_index', 9))
            for index in range(1, len(data)):
                pt.line(start=data[index - 1], end=data[index], **se)
        if 'scatter' in se['type'] and se['name'] != 'Text':
            se['fill_color'] = se.get('fill_color', 'black')
            se['size'] = se.get('size', 5)
            se['stroke_color'] = se.get('stroke_color', se.get('color', 'black'))
            se['z_index'] = int(se.get('z_index', 9))
            se['marker'] = se.get('marker', 'rec')
            for each in data:
                pt.scatter(each[0], each[1], **se)
        if 'scatter' in se['type'] and se['name'] == 'Text' or 'text' in se['type']:
            se.update({'size': 10})
            for each in data:
                pt.text(*each[:2], **se)
        if 'rect' in se['type']:
            for each in data:
                lb = each[:2]; width, height = each[2:4]
                pt.rect(lb, width, height, **se)

    return cv


def export_chart_to_pdf(cvs, file_name: str = "", file_path: str = "", **kwargs):
    """

    Parameters
    ----------
    file_path: str
    data: dict
        - file_name: string
            file name, like "24WHA0001"
        - data: list of dicts
            properties:
            - name: string
                diagram name, like "Age spectra"

            - xAxis: list
                properties:
                - extend: list
                    limits of values of axis, like [0, 100]
                - interval: list
                    sticks location, like [0, 20, 40, 60, 80, 100]
                - title: string
                - name_location: string
                    axis title location, 'middle'

            - yAxis: same as xAxis

            - series: list
                properties:
                - type: string
                    series type, 'line', 'scatter', 'text', and any string contains these characters
                - id: string
                - name: string
                - color: string or list
                    color for outlines, color name | RGB triplet | Hex color code
                - fill_color: string or list
                    color for filling markers, format is similar to that of color
                - data: 2-dimensional array
                    [[x1, y1], [x2, y2], ...]
                - axis_index: int
                    index of axis to combine with, which is useful for plotting on different scales.

                optional:
                - line_caps: string
                    for lines only, 'square', 'none', 'butt'
                - text: string
                    for texts only
                - size: int
                    for scatters only
    **kwargs:
        author, producer, creator, page_size, ppi, ...

    Returns
    -------

    """
    # capital letter for label
    def get_label(l="", num=0):
        if num // 26 > 0:
            return get_label(get_label(l, num // 26 - 1), num % 26)
        return l + chr(num % 26 + 65)

    # write pdf
    show_label = kwargs.get('show_label', False)
    num_cols = kwargs.get('num_columns', 2)
    file = pm.NewPDF(filepath=file_path, title=f"{file_name}", **kwargs)
    page_size = {
        "a3": (297, 420),
        "a4": (210, 297),
        "b5": (176, 250),
        "a5": (148, 210),
    }
    for i in file.get_page_indexes():
        file.del_obj(i)
    file.add_page(size=page_size[kwargs.get('page_size', 'a4').lower()], unit='mm')
    for page_index, page in enumerate(cvs):
        for cv_index, cv in enumerate(page):
            left = 10 + cv_index % num_cols * cv.width()
            top = 20 + cv_index // num_cols * cv.height()
            if show_label:
                cv._plot_areas[1].text(
                    x=5, y=95, text=f"({str(get_label(num=cv_index)).lower()})",
                    id=f'text-label-{page_index}-{cv_index}',
                    name=f'text-label-{page_index}-{cv_index}',
                    color='black', size=title_size, axis_index=1, h_align='middle', v_align='center'
                )
            file.canvas(page=page_index, base=0, margin_left=left, margin_top=top, canvas=cv, unit="pt")
        if page_index + 1 < len(cvs):
            file.add_page()

    # save pdf
    file.save()

    return file_path


def get_plot_data(smp: Sample, diagram: str = 'age spectra', **options):
    """

    Parameters
    ----------
    smp
    diagram
    options

    Returns
    -------

    """
    xAxis, yAxis = get_plot_axis_data(smp, diagram=diagram.lower(), **options)
    series = get_plot_series_data(smp, diagram=diagram.lower(), xAxis=xAxis, yAxis=yAxis, **options)
    return {'name': smp.name(), 'xAxis': xAxis, 'yAxis': yAxis, 'series': series}


def get_plot_axis_data(smp: Sample, diagram: str = 'age spectra', **options):
    """

    Parameters
    ----------
    smp
    diagram
    color
    options

    Returns
    -------

    """
    if diagram.lower() == "age spectra":
        xAxis, yAxis = _get_plot_data_age_spectra_axis(smp, **options)
    elif diagram.lower() == "inverse isochron":
        xAxis, yAxis = _get_plot_data_inv_isochron_axis(smp, **options)
    elif "degas spectra" in diagram.lower():
        xAxis, yAxis = _get_plot_data_degas_spectra_axis(smp, diagram_name = diagram.lower(), **options)
    elif "degas curve" in diagram.lower():
        xAxis, yAxis = _get_plot_data_degas_curve_axis(smp, diagram_name = diagram.lower(), **options)
    else:
        raise KeyError
    return xAxis, yAxis


def get_plot_series_data(smp: Sample, diagram: str = 'age spectra', **options):
    """

    Parameters
    ----------
    smp
    diagram
    color
    options

    Returns
    -------

    """
    if diagram.lower() == "age spectra":
        series = _get_plot_data_age_spectra_series(smp, **options)
    elif diagram.lower() == "inverse isochron":
        series = _get_plot_data_inv_isochron_series(smp, **options)
    elif "degas spectra" in diagram.lower():
        series = _get_plot_data_degas_spectra_series(smp, diagram_name=diagram.lower(), **options)
    elif "degas curve" in diagram.lower():
        series = _get_plot_data_degas_curve_series(smp, diagram_name=diagram.lower(), **options)
    else:
        raise KeyError
    series.append(_get_additional_text_series(smp.name()))
    return series


def spectraData2Sgima(data, sigma=2):
    return list(map(lambda row: [row[0], (row[1] - row[2]) / 2 * (sigma - 1) + row[1], (row[2] - row[1]) / 2 * (sigma - 1) + row[2]], data))


def getRectFromSpectra(data):
    """
    Parameters
    ----------
    data: [x, y1, y2]

    Returns
    -------

    """
    data = np.array(data)
    return list(filter(lambda rect: rect[2] != 0 and rect[3] != 0, map(lambda index: [data[index,0], min(data[index,[1,2]]), abs(data[index+1,0] - data[index,0]), abs(data[index,1] - data[index,2])], list(range(len(data) - 1)))))


def _get_additional_text_series(name):
    return {
        'type': 'text', 'id': f'text-{name}-{get_random_digits()}',
        'name': f'text-{name}-{get_random_digits()}', 'color': 'black',
        'text': "", 'size': title_size,
        'data': [[50, 50]], 'axis_index': 1,
        'h_align': "middle", 'v_align': "center",
    }


def _get_plot_data_age_spectra_series(smp: sample, **options):
    color = options.get('color', 'black')
    sigma = options.get('sigma', smp.Info.preference['confidenceLevel'])
    unit = options.get('unit', smp.Info.preference['ageUnit'])
    xAxis = options.get('xAxis', [{}])
    yAxis = options.get('yAxis', [{}])
    line_width = options.get('line_width', 1)
    line_caps = options.get('line_caps', 'none')
    series = []
    # apparent spectra lines
    age = smp.ApparentAgeValues[2:4]
    ar = smp.DegasValues[20]
    x, y1, y2 = spectra.get_data(*age, ar, cumulative=False, sigma=sigma)
    X = x + list(reversed(x))
    Y = y1 + list(reversed(y2))
    series.append({
        'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}', 'name': f'line-{smp.name()}-{get_random_digits()}',
        'color': color, 'fill_color': color, 'line_width': line_width, 'line_style': 'solid', 'z_index': 19,
        'data': np.transpose([X, Y]).tolist(),
        'line_caps': line_caps,
        # 'line_caps': 'none',
        'axis_index': 0,
    })
    # initial values corrected spectra lines and rect
    text1 = smp.AgeSpectraPlot.text1
    text2 = smp.AgeSpectraPlot.text2
    set_data = [spectraData2Sgima(smp.AgeSpectraPlot.set1.data, sigma),
                spectraData2Sgima(smp.AgeSpectraPlot.set2.data, sigma)]
    for index, text in enumerate([text1, text2]):
        res = smp.Info.results.age_plateau[index]
        if not np.isnan(res['age']):
            selection = np.array(smp.Info.results.selection[index]['data']) * 2 + 1
            plateau_data = np.array(set_data[index])
            # spectra_fill_data = list(map(lambda each: [data[0][each - 1], min(data[1][each], data[2][each]), data[0][each + 1] - data[0][each], sigma * abs(data[1][each] - data[2][each])], selection))
            spectra_fill_data = getRectFromSpectra(plateau_data)
            series.append({
                'type': 'series.rect', 'id': f'rect-{smp.name()}-{get_random_digits()}', 'name': f'rect-{smp.name()}-{get_random_digits()}',
                'color': [colors_map['red'], colors_map['blue']][index], 'fill_color': [colors_map['red'], colors_map['blue']][index],   'line_style': 'none', 'z_index': 9,
                'data': spectra_fill_data, 'line_caps': 'none', 'fill': True,
                'axis_index': 0,
            })
            x, y1, y2 = np.transpose(plateau_data).tolist()[:3]
            X = x + list(reversed(x))
            Y = y1 + list(reversed(y2))
            series.append({
                'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}',
                'name': f'line-{smp.name()}-{get_random_digits()}',
                'color': [colors_map['red'], colors_map['blue']][index], 'line_width': line_width, 'line_style': 'solid', 'z_index': 9,
                'data': np.transpose([X, Y]).tolist(),
                'line_caps': line_caps,
                # 'line_caps': 'none',
                'axis_index': 0,
            })
            # plateau line
            series.append({
                'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}',
                'name': f'line-{smp.name()}-{get_random_digits()}',
                'color': '#A9A9A9', 'line_width': line_width, 'line_style': 'solid', 'z_index': 9,
                'data': [[0, res['age']], [100, res['age']]],
                'line_caps': line_caps,
                # 'line_caps': 'none',
                'axis_index': 0,
            })
            series.append({
                'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}', 'name': f'text-{smp.name()}-{get_random_digits()}',
                'color': [colors_map['red'], colors_map['blue']][index], 'fill_color': [colors_map['red'], colors_map['blue']][index],
                'text': f"Corrected = {res['age']:.2f} ± {(sigma * res['s2']):.2f} {unit} ({sigma}s)<r>"
                        f"MSWD = {res['MSWD']:.2f}, n = {res['Num']:.0f}<r>"
                        f"<sup>39</sup>Ar = {res['Ar39']:.2f}%",
                'size': title_size,
                # 'data': [text.pos],
                'data': [[50, 50]],
                'axis_index': 1, 'z_index': 29,
                'h_align': "middle",
                'v_align': "center",
            })
        spe = smp.Info.results.age_spectra[index]
        if not np.isnan(res['age']):
            series.append({
                'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}',
                'name': f'text-{smp.name()}-{get_random_digits()}',
                'color': color, 'fill_color': color,
                'text': f"WMPA = {spe['age']:.2f} ± {(sigma * spe['s2']):.2f} {unit} ({sigma}s)",
                'size': title_size,
                'data': [[50, 10+10*index]],
                'axis_index': 1,
                'h_align': "middle",
                'v_align': "bottom",
            })

    # TGA
    tga = smp.Info.results.age_spectra['TGA']
    if not np.isnan(tga['age']):
        series.append({
            'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}', 'name': f'text-{smp.name()}-{get_random_digits()}',
            'color': color, 'fill_color': color,
            'text': f"TGA = {tga['age']:.2f} ± {(sigma * tga['s2']):.2f} {unit} ({sigma}s)",
            'size': title_size,
            'data': [[50, 3]],
            'axis_index': 1,
            'h_align': "middle",
            'v_align': "bottom",
        })
    # Max
    age = np.array(smp.ApparentAgeValues[2:8]).transpose()
    age = np.where(age is None, np.nan, age)
    valid_mask = np.isfinite(age[:, 0])
    age = age[valid_mask]
    age = age[age[:, 5] >= 0.1]
    try:
        max_index = np.argmax(age[20:, 0]) + 20
    except ValueError:
        max_index = np.argmax(age[10:, 0]) + 10
    min_index = np.argmin(age[:20, 0])
    # print(f"{max_index = }")
    # print(f"{min_index = }")

    series.append({
        'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}', 'name': f'text-{smp.name()}-{get_random_digits()}',
        'color': color, 'fill_color': color,
        'text': f"Max. = {age[max_index, 0]:.2f} ± {(sigma * age[max_index, 2]):.2f} {unit}",
        'size': title_size,
        'data': [[50, 70]],
        'axis_index': 1,
        'h_align': "middle",
        'v_align': "bottom",
    })

    series.append({
        'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}', 'name': f'text-{smp.name()}-{get_random_digits()}',
        'color': color, 'fill_color': color,
        'text': f"Min. = {age[min_index, 0]:.2f} ± {(sigma * age[min_index, 2]):.2f} {unit}",
        'size': title_size,
        'data': [[50, 75]],
        'axis_index': 1,
        'h_align': "middle",
        'v_align': "bottom",
    })

    series.append({
        'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}',
        'name': f'line-{smp.name()}-{get_random_digits()}',
        'color': '#A9A9A9', 'line_width': line_width, 'line_style': 'solid', 'z_index': 9,
        'data': [[0, age[max_index, 0]], [100, age[max_index, 0]]],
        'line_caps': line_caps,
        # 'line_caps': 'none',
        'axis_index': 0,
    })
    series.append({
        'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}',
        'name': f'line-{smp.name()}-{get_random_digits()}',
        'color': '#A9A9A9', 'line_width': line_width, 'line_style': 'solid', 'z_index': 9,
        'data': [[0, age[min_index, 0]], [100, age[min_index, 0]]],
        'line_caps': line_caps,
        # 'line_caps': 'none',
        'axis_index': 0,
    })
    # title
    series.append({
        'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}',
        'name': f'text-{smp.name()}-{get_random_digits()}', 'color': color,
        'text': smp.name(), 'size': title_size,
        'data': [[50, 95]], 'axis_index': 1, 'z_index': 29,
        'h_align': "middle", 'v_align': "center",
    })

    return series


def _get_plot_data_age_spectra_axis(smp: sample, **options):
    color = options.get('color', 'black')
    line_width = options.get('line_width', 1)
    xAxis, yAxis = [], []
    age = smp.ApparentAgeValues[2:4]
    ar = smp.DegasValues[20]
    data = spectra.get_data(*age, ar, cumulative=False)

    # y_low_limit, y_up_limit, stick_num, inc = get_axis_scale(np.array(data[1:3]).flatten())
    # y_extent = [y_low_limit, y_up_limit]
    # y_interval = [y_low_limit + i * inc for i in range(stick_num + 1)]
    # y_interval.extend([y_up_limit * 10] * 3)
    # dp = int(np.log10(abs(y_up_limit - y_low_limit)) - 1)
    # dp = 0 if dp >= 0 else abs(dp)
    # y_interval = [f"{i:.{dp}f}" for i in y_interval]
    try:
        y_low_limit = float(smp.AgeSpectraPlot.yaxis.min)
        y_up_limit = float(smp.AgeSpectraPlot.yaxis.max)
        y_extent = [y_low_limit, y_up_limit]
        stick_num = int(smp.AgeSpectraPlot.yaxis.split_number)
        inc = float(smp.AgeSpectraPlot.yaxis.interval)
        y_interval = [y_low_limit + i * inc for i in range(stick_num + 1)]
        dp = int(np.log10(abs(y_up_limit - y_low_limit)) - 1)
        dp = 0 if dp >= 0 else abs(dp)
        y_interval = [f"{i:.{dp}f}" for i in y_interval]
    except (BaseException, Exception):
        y_extent = [0, 250]
        y_interval = ['0', '50', '100', '150', '200', '250', '600', '700', '800', '900', '1000']

    xAxis.append({
        'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100], 'id': 0, 'show_frame': True,
        'title': 'Cumulative <sup>39</sup>Ar released (%)', 'name_location': 'middle',
        'line_width': line_width, 'line_style': 'solid', 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
    })
    xAxis.append({
        'extent': [0, 100], 'interval': [], 'id': 1, 'show_frame': False,
        'title': '', 'name_location': 'middle',
        'line_width': 0, 'line_style': 'none', 'z_index': 0, 'label_size': label_size, 'title_size': title_size,
    })
    yAxis.append({
        'extent': y_extent, 'interval': y_interval,
        'id': 0, 'show_frame': True,
        'title': 'Apparent age (Ma)', 'name_location': 'middle',
        'line_width': line_width, 'line_style': 'solid', 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
    })
    yAxis.append({
        'extent': [0, 100], 'interval': [], 'id': 1, 'show_frame': False,
        'title': '', 'name_location': 'middle',
        'line_width': 0, 'line_style': 'none', 'z_index': 0, 'label_size': label_size, 'title_size': title_size,
    })
    return xAxis, yAxis


def _get_plot_data_inv_isochron_axis(smp: sample, **options):
    color = options.get('color', 'black')
    line_width = options.get('line_width', 1)
    xAxis, yAxis = [], []
    data = np.array(smp.InvIsochronPlot.data)
    set1 = smp.InvIsochronPlot.set1.data
    set2 = smp.InvIsochronPlot.set2.data
    set3 = smp.InvIsochronPlot.set3.data

    low_limit, up_limit, stick_num, inc = get_axis_scale(data[0])
    x_extent = [low_limit, up_limit]
    interval = [float("{:g}".format(low_limit + i * inc)) for i in range(stick_num + 1)]

    x_extent = [0, 1]
    interval = ['0', '0.2', '0.4', '0.6', '0.8', '1', '6', '7', '8']

    xAxis.append({
        'extent': x_extent,
        'interval': interval,
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': '<sup>39</sup>Ar<sub>K</sub> / <sup>40</sup>Ar<sup>*</sup>', 'name_location': 'middle',
        'line_width': line_width,
    })
    xAxis.append({
        'extent': [0, 100], 'interval': [], 'id': 1, 'show_frame': False,
        'title': '', 'name_location': 'middle', 'z_index': 0, 'label_size': label_size, 'title_size': title_size,
        'line_width': 0,
    })

    low_limit, up_limit, stick_num, inc = get_axis_scale(data[2])
    y_extent = [low_limit, up_limit]
    interval = [float("{:g}".format(low_limit + i * inc)) for i in range(stick_num + 1)]

    y_extent = [0, 0.004]
    interval = ['0', '0.001', '0.002', '0.003', '0.004', '0.005', '0.006', '0.007', '0.008']

    yAxis.append({
        'extent': y_extent,
        'interval': interval,
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': '<sup>36</sup>Ar<sub>a</sub> / <sup>40</sup>Ar<sup>*</sup>', 'name_location': 'middle',
    })
    yAxis.append({
        'extent': [0, 100], 'interval': [], 'id': 1, 'show_frame': False,
        'title': '', 'name_location': 'middle', 'z_index': 0, 'label_size': label_size, 'title_size': title_size,
    })

    return xAxis, yAxis


def _get_plot_data_inv_isochron_series(smp: sample, **options):
    color = options.get('color', 'black')
    marker_size = options.get('marker_szie', 2)
    xAxis = options.get('xAxis', [{}])
    yAxis = options.get('yAxis', [{}])
    sigma = options.get('sigma', 2)
    series = []
    age = smp.ApparentAgeValues[2:4]
    ar = smp.DegasValues[20]
    data = np.array(smp.InvIsochronPlot.data)
    set1 = smp.InvIsochronPlot.set1.data
    set2 = smp.InvIsochronPlot.set2.data
    set3 = smp.InvIsochronPlot.set3.data
    # set 1
    series.append({
        'type': 'series.scatter', 'id': f'scatter-{smp.name()}-{get_random_digits()}', 'name': f'scatter-{smp.name()}-{get_random_digits()}',
        'stroke_color': colors_map['red'], 'fill_color': colors_map['red80'], 'myType': 'scatter', 'size': marker_size, 'line_width': 0,
        'data': (data[[0, 2], :][:, set1]).transpose().tolist(),
        'axis_index': 0, 'z_index': 99
    })
    # set 2
    series.append({
        'type': 'series.scatter', 'id': f'scatter-{smp.name()}-{get_random_digits()}', 'name': f'scatter-{smp.name()}-{get_random_digits()}',
        'stroke_color': colors_map['blue'], 'fill_color': colors_map['blue80'], 'myType': 'scatter', 'size': marker_size, 'line_width': 0,
        'data': (data[[0, 2], :][:, set2]).transpose().tolist(),
        'axis_index': 0, 'z_index': 99
    })
    # set 3
    series.append({
        'type': 'series.scatter', 'id': f'scatter-{smp.name()}-{get_random_digits()}', 'name': f'scatter-{smp.name()}-{get_random_digits()}',
        'stroke_color': 'black', 'fill_color': 'white', 'myType': 'scatter', 'size': marker_size, 'line_width': 0,
        'data': (data[[0, 2], :][:, set3]).transpose().tolist(),
        'axis_index': 0, 'z_index': 0
    })

    text1 = smp.InvIsochronPlot.text1
    text2 = smp.InvIsochronPlot.text2
    for index, text in enumerate([text1, text2]):
        if not np.isnan(smp.Info.results.isochron['figure_3'][index]['age']):
            isochron_data = [
                            (float(xAxis[0]['extent'][0]), float(xAxis[0]['extent'][0]) * smp.Info.results.isochron['figure_3'][index]['m1'] + smp.Info.results.isochron['figure_3'][index]['k']),
                            (float(xAxis[0]['extent'][1]), float(xAxis[0]['extent'][1]) * smp.Info.results.isochron['figure_3'][index]['m1'] + smp.Info.results.isochron['figure_3'][index]['k']),
            ]
            series.append({
                'type': 'series.line', 'id': f'line-{smp.name()}-{get_random_digits()}', 'name': f'line-{smp.name()}-{get_random_digits()}',
                'color': [colors_map['red'], colors_map['blue']][index], 'fill_color': [colors_map['red'], colors_map['blue']][index],
                'line_width': 1, 'line_style': 'solid',
                'data': isochron_data,
                'axis_index': 0,
            })
            series.append({
                'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}', 'name': f'text-{smp.name()}-{get_random_digits()}',
                'color': [colors_map['red'], colors_map['blue']][index], 'fill_color': [colors_map['red'], colors_map['blue']][index],
                'text': f"IIA = {smp.Info.results.isochron['figure_3'][index]['age']:.2f} ± {(sigma * smp.Info.results.isochron['figure_3'][index]['s2']):.2f} Ma ({sigma}s)<r>"
                        f"(40Ar/36Ar)0 = {smp.Info.results.isochron['figure_3'][index]['initial']:.2f} ± {(sigma * smp.Info.results.isochron['figure_3'][index]['sinitial']):.2f}<r>"
                        f"MSWD = {smp.Info.results.isochron['figure_3'][index]['MSWD']:.2f}<r>",
                'size': title_size,
                'data': [text.pos],
                'axis_index': 1,
                'h_align': "middle",
                'v_align': "center",
            })

    series.append({
        'type': 'text', 'id': f'text-{smp.name()}-{get_random_digits()}',
        'name': f'text-{smp.name()}-{get_random_digits()}', 'color': color,
        'text': smp.name(), 'size': title_size,
        'data': [[50, 95]], 'axis_index': 1,
        'h_align': "middle", 'v_align': "center",
    })

    return series


def _get_plot_data_degas_pattern(smp: sample, **options):
    color = options.get('color', 'black')
    plot = smp.DegasPatternPlot
    xAxis, yAxis, series = [], [], []
    argon = smp.DegasValues[20]  # Ar39K as default
    while argon[-1] == 0:
        argon = argon[:-1]
    y = [argon[i] / sum(argon[i:]) * 100 for i in range(len(argon))]
    x = list(range(1, len(argon) + 1))
    data = np.array([x, y])
    # set 1
    series.append({
        'type': 'series.scatter', 'id': f'scatter-{smp.name()}-{get_random_digits()}', 'name': f'scatter-{smp.name()}-{get_random_digits()}',
        'stroke_color': color, 'fill_color': 'white', 'myType': 'scatter', 'size': 4, 'line_width': 1,
        'data': data.transpose().tolist(), 'axis_index': 0, 'z_index': 99
    })

    xaxis = plot.xaxis
    yaxis = plot.yaxis

    xaxis.min = 0
    xaxis.max = 100
    xaxis.interval = 20
    xaxis.split_number = 5
    yaxis.min = 0
    yaxis.max = 20
    yaxis.interval = 5
    yaxis.split_number = 4

    xAxis.append({
        'extent': [float(xaxis.min), float(xaxis.max)],
        'interval': [float("{:g}".format(float(xaxis.min) + i * float(xaxis.interval))) for i in range(int(xaxis.split_number) + 1)],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'XXXX', 'name_location': 'middle',
    })
    yAxis.append({
        'extent': [float(yaxis.min), float(yaxis.max)],
        'interval': [float("{:g}".format(float(yaxis.min) + i * float(yaxis.interval))) for i in range(int(yaxis.split_number) + 1)],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'YYYY', 'name_location': 'middle',
    })
    return xAxis, yAxis, series


def _get_plot_data_degas_spectra_axis(smp: sample, **options):
    name = options.get('diagram_name', '39Ar')
    color = options.get('color', 'black')
    plot = smp.DegasPatternPlot
    xAxis, yAxis = [], []

    xaxis = plot.xaxis
    yaxis = plot.yaxis
    xaxis.min = 0
    xaxis.max = 100
    xaxis.interval = 20
    xaxis.split_number = 5
    yaxis.min = 0
    yaxis.max = 20
    yaxis.interval = 5
    yaxis.split_number = 4

    xAxis.append({
        'extent': [float(xaxis.min), float(xaxis.max)],
        'interval': [float("{:g}".format(float(xaxis.min) + i * float(xaxis.interval))) for i in range(int(xaxis.split_number) + 1)],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'Steps [n]', 'name_location': 'middle',
    })
    yAxis.append({
        'extent': [float(yaxis.min), float(yaxis.max)],
        'interval': [float("{:g}".format(float(yaxis.min) + i * float(yaxis.interval))) for i in range(int(yaxis.split_number) + 1)],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'Argon Released [%]', 'name_location': 'middle',
    })
    return xAxis, yAxis


def _get_plot_data_degas_spectra_series(smp: sample, **options):
    name = options.get('diagram_name', '39Ar')
    color = options.get('color', 'black')
    plot = smp.DegasPatternPlot
    xAxis = options.get('xAxis', [{}])
    yAxis = options.get('yAxis', [{}])
    series = []
    nindex = {"40": 24, "39": 20, "38": 10, "37": 8, "36": 0}
    if name[:2] in list(nindex.keys()):
        ar = np.array(smp.DegasValues[nindex[name[:2]]], dtype=np.float64)  # 20-21 Ar39
        sar = np.array(smp.DegasValues[nindex[name[:2]] + 1], dtype=np.float64)
    elif 'total' in name:
        all_ar = np.array(smp.CorrectedValues, dtype=np.float64)  # 20-21 Ar39
        ar, sar = arr.add(*all_ar.reshape(5, 2, len(all_ar[0])))
        ar = np.array(ar); sar = np.array(sar)
    else:
        raise KeyError

    while ar[-1] == 0:
        ar = ar[:-1]
    x = list(range(0, len(ar)))
    y = [0 for i in range(len(ar))]
    width = [1 for i in range(len(ar))]
    height = [ar[i] / sum(ar) * 100 for i in range(len(ar))]
    data = np.array([x, y, width, height])

    # set 1
    series.append({
        'type': 'rect', 'id': f'rect-{smp.name()}-{get_random_digits()}', 'name': f'rect-{smp.name()}-{get_random_digits()}',
        'color': color, 'myType': 'rect', 'line_width': 1,
        'data': data.transpose().tolist(),
        'axis_index': 0, 'z_index': 99
    })

    return series


def _get_plot_data_degas_curve_axis(smp: sample, **options):
    name = options.get('diagram_name', '39Ar')
    color = options.get('color', 'black')
    xAxis, yAxis = [], []
    xAxis.append({
        'extent': [0, 100],
        'interval': [0, 20, 40, 60, 80, 100],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'Steps [n]', 'name_location': 'middle',
    })
    yAxis.append({
        'extent': [0, 100],
        'interval': [0, 20, 40, 60, 80, 100],
        'id': 0, 'show_frame': True, 'z_index': 9, 'label_size': label_size, 'title_size': title_size,
        'title': 'Argon [%]', 'name_location': 'middle',
    })
    return xAxis, yAxis


def _get_plot_data_degas_curve_series(smp: sample, **options):
    name = options.get('diagram_name', '39Ar')
    color = options.get('color', 'black')
    xAxis = options.get('xAxis', [{}])
    yAxis = options.get('yAxis', [{}])
    series = []
    nindex = {"40": 24, "39": 20, "38": 10, "37": 8, "36": 0}
    if name[:2] in list(nindex.keys()):
        ar = np.array(smp.DegasValues[nindex[name[:2]]], dtype=np.float64)  # 20-21 Ar39
        sar = np.array(smp.DegasValues[nindex[name[:2]] + 1], dtype=np.float64)
    elif 'total' in name:
        all_ar = np.array(smp.CorrectedValues, dtype=np.float64)  # 20-21 Ar39
        ar, sar = arr.add(*all_ar.reshape(5, 2, len(all_ar[0])))
        ar = np.array(ar); sar = np.array(sar)
    else:
        raise KeyError

    while ar[-1] == 0:
        ar = ar[:-1]
    x = list(range(0, len(ar) + 1))
    f = ar / sum(ar) * 100
    released = np.zeros(len(ar) + 1)
    remained = np.zeros(len(ar) + 1) + 100
    for i in range(1, len(ar) + 1):
        released[i] = sum(f[:i])
        remained[i] = 100 - released[i]

    # line
    series.append({
        'type': 'line', 'id': f'line-{smp.name()}-{get_random_digits()}', 'name': f'line-{smp.name()}-{get_random_digits()}',
        'color': color, 'myType': 'line', 'line_width': 1, 'line_style': 'solid',
        'data': np.array([x, released]).transpose().tolist(),
        'axis_index': 0, 'z_index': 99
    })
    series.append({
        'type': 'line', 'id': f'line-{smp.name()}-{get_random_digits()}', 'name': f'line-{smp.name()}-{get_random_digits()}',
        'color': color, 'myType': 'line', 'line_width': 1, 'line_style': 'solid',
        'data': np.array([x, remained]).transpose().tolist(),
        'axis_index': 0, 'z_index': 99
    })

    return series


class ExcelTemplate:
    def __init__(self, **kwargs):
        self.name = ""
        self.worksheets = {}
        self.save_path = ''
        for key, value in kwargs.items():
            setattr(self, key, value)

    def sheetnames(self):
        return self.worksheets.keys()

    def sheet(self):
        # sheet name, sheet property name, (col, row, name, arr cls property name), (), ...
        return self.worksheets.items()

    def save(self):
        with open(self.save_path, 'wb') as f:
            f.write(pickle.dumps(self))


class WritingWorkbook:
    def __init__(self, **kwargs):
        self.style = None
        self.filepath = None  #
        self.template = None
        self.template_filepath = None  #
        self.sample = None  #

        self.chartarea_color = '#FFFFFF'  # white = '#FFFFFF'
        self.plotarea_color = '#FFFFFF'  # yellow = '#FFE4B5'
        self.border_color = '#000000'  # black = '#000000'
        self.font_color = '#000000'  # black = '#000000'
        self.color_map = ['#d61a1a', '#0268bd', '#f3f0eb', '#ffffff']
        self.plot_border_width = 1.25
        self.font_name = 'Microsoft Sans Serif'
        self.title_font_size = 16
        self.axis_font_size = 14
        self.axis_font_bold = False
        self.axis_num_font_size = 10
        self.line_width = 1.25
        self.default_fmt_prop = {
            'font_name': 'Times New Roman', "font_size": 10, 'num_format': '0.000000',
            'align': 'center', 'valign': 'vcenter',
        }
        self.formats = {'default': Format({'font_name': 'Times New Roman', "font_size": 10, })}

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.template_filepath is not None:
            self.read_template()

    def read_template(self):
        # print(self.template_filepath)
        self.template = CustomUnpickler(open(self.template_filepath, 'rb')).load()

    def get_xls(self):
        # TypeError: NAN/INF not supported in write_number() without 'nan_inf_to_errors' Workbook() option
        xls = Workbook(self.filepath, {"nan_inf_to_errors": True})

        style = xls.add_format(self.default_fmt_prop)

        sigma = int(self.sample.Info.preference['confidenceLevel'])

        sht_reference = xls.add_worksheet("Reference")  # Data used to plot
        sht_reference.hide_gridlines(2)  # 0 = show grids, 1 = hide print grid, else = hide print and screen grids
        start_row = 3
        reference_header = [
            "x1", "y1", "y2", "x2", "y1", "y2", "x3", "y1", "y2", "x[bar]", "y[bar]", None, None, None,  # age spectra
            "x[set1]", "y[set1]", "x[set2]", "y[set2]", "x[unselected]", "y[unselected]",
            "point1[set1]", "point2[set1]", "point1[set2]", "point2[set2]",
            "x[set1]", "y[set1]", "x[set2]", "y[set2]", "x[unselected]", "y[unselected]",
            "point1[set1]", "point2[set1]", "point1[set2]", "point2[set2]",
            "x[set1]", "y[set1]", "x[set2]", "y[set2]", "x[unselected]", "y[unselected]",
            "point1[set1]", "point2[set1]", "point1[set2]", "point2[set2]",
            "x[set1]", "y[set1]", "x[set2]", "y[set2]", "x[unselected]", "y[unselected]",
            "point1[set1]", "point2[set1]", "point1[set2]", "point2[set2]",
            "x[set1]", "y[set1]", "x[set2]", "y[set2]", "x[unselected]", "y[unselected]",
            "point1[set1]", "point2[set1]", "point1[set2]", "point2[set2]",
        ]
        # writing header
        sht_reference.write_row(row=start_row - 3, col=0, data=reference_header, cell_format=style)

        # total rows, sequence number
        total_rows = len(self.sample.SequenceName)

        # Data for age spectra
        try:
            spectra_data = arr.transpose(spectraData2Sgima(self.sample.AgeSpectraPlot.data, sigma))
            spectra_set1_data = arr.transpose(spectraData2Sgima(self.sample.AgeSpectraPlot.set1.data, sigma)) or [[]] * 3
            spectra_set2_data = arr.transpose(spectraData2Sgima(self.sample.AgeSpectraPlot.set2.data, sigma)) or [[]] * 3
            sht_reference.write_column(f"A{start_row}", spectra_data[0], style)
            sht_reference.write_column(f"B{start_row}", spectra_data[1], style)
            sht_reference.write_column(f"C{start_row}", spectra_data[2], style)
            sht_reference.write_column(f"D{start_row}", spectra_set1_data[0], style)
            sht_reference.write_column(f"E{start_row}", spectra_set1_data[1], style)
            sht_reference.write_column(f"F{start_row}", spectra_set1_data[2], style)
            sht_reference.write_column(f"G{start_row}", spectra_set2_data[0], style)
            sht_reference.write_column(f"H{start_row}", spectra_set2_data[1], style)
            sht_reference.write_column(f"I{start_row}", spectra_set2_data[2], style)
            sht_reference.write_column(f"J{start_row}", [], style)
            sht_reference.write_column(f"K{start_row}", [], style)
        except IndexError:
            pass

        # Data for normal isochron
        try:
            set_data = [set1_data, set2_data, set3_data] = isochron.get_set_data(
                self.sample.NorIsochronPlot.data, self.sample.SelectedSequence1, self.sample.SelectedSequence2,
                self.sample.UnselectedSequence)
            sht_reference.write_column(f"O{start_row}", set1_data[0], style)
            sht_reference.write_column(f"P{start_row}", set1_data[2], style)
            sht_reference.write_column(f"Q{start_row}", set2_data[0], style)
            sht_reference.write_column(f"R{start_row}", set2_data[2], style)
            sht_reference.write_column(f"S{start_row}", set3_data[0], style)
            sht_reference.write_column(f"T{start_row}", set3_data[2], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"U{start_row}", self.sample.NorIsochronPlot.line1.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"V{start_row}", self.sample.NorIsochronPlot.line1.data[1], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"W{start_row}", self.sample.NorIsochronPlot.line2.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"X{start_row}", self.sample.NorIsochronPlot.line2.data[1], style)
        except IndexError:
            pass

        # Data for inverse isochron
        try:
            set_data = [set1_data, set2_data, set3_data] = isochron.get_set_data(
                self.sample.InvIsochronPlot.data, self.sample.SelectedSequence1, self.sample.SelectedSequence2,
                self.sample.UnselectedSequence)
            sht_reference.write_column(f"Y{start_row}", set1_data[0], style)
            sht_reference.write_column(f"Z{start_row}", set1_data[2], style)
            sht_reference.write_column(f"AA{start_row}", set2_data[0], style)
            sht_reference.write_column(f"AB{start_row}", set2_data[2], style)
            sht_reference.write_column(f"AC{start_row}", set3_data[0], style)
            sht_reference.write_column(f"AD{start_row}", set3_data[2], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AE{start_row}", self.sample.InvIsochronPlot.line1.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AF{start_row}", self.sample.InvIsochronPlot.line1.data[1], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AG{start_row}", self.sample.InvIsochronPlot.line2.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AH{start_row}", self.sample.InvIsochronPlot.line2.data[1], style)
        except IndexError:
            pass

        # Data for Cl 1 isochron
        try:
            set_data = [set1_data, set2_data, set3_data] = isochron.get_set_data(
                self.sample.KClAr1IsochronPlot.data, self.sample.SelectedSequence1, self.sample.SelectedSequence2,
                self.sample.UnselectedSequence)
            sht_reference.write_column(f"AI{start_row}", set1_data[0], style)
            sht_reference.write_column(f"AJ{start_row}", set1_data[2], style)
            sht_reference.write_column(f"AK{start_row}", set2_data[0], style)
            sht_reference.write_column(f"AL{start_row}", set2_data[2], style)
            sht_reference.write_column(f"AM{start_row}", set3_data[0], style)
            sht_reference.write_column(f"AN{start_row}", set3_data[2], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AO{start_row}", self.sample.KClAr1IsochronPlot.line1.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AP{start_row}", self.sample.KClAr1IsochronPlot.line1.data[1], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AQ{start_row}", self.sample.KClAr1IsochronPlot.line2.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AR{start_row}", self.sample.KClAr1IsochronPlot.line2.data[1], style)
        except IndexError:
            pass

        # Data for Cl 2 isochron
        try:
            set_data = [set1_data, set2_data, set3_data] = isochron.get_set_data(
                self.sample.KClAr2IsochronPlot.data, self.sample.SelectedSequence1, self.sample.SelectedSequence2,
                self.sample.UnselectedSequence)
            sht_reference.write_column(f"AS{start_row}", set1_data[0], style)
            sht_reference.write_column(f"AT{start_row}", set1_data[2], style)
            sht_reference.write_column(f"AU{start_row}", set2_data[0], style)
            sht_reference.write_column(f"AV{start_row}", set2_data[2], style)
            sht_reference.write_column(f"AW{start_row}", set3_data[0], style)
            sht_reference.write_column(f"AX{start_row}", set3_data[2], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AY{start_row}", self.sample.KClAr2IsochronPlot.line1.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"AZ{start_row}", self.sample.KClAr2IsochronPlot.line1.data[1], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BA{start_row}", self.sample.KClAr2IsochronPlot.line2.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BB{start_row}", self.sample.KClAr2IsochronPlot.line2.data[1], style)
        except IndexError:
            pass

        # Data for Cl 3 isochron
        try:
            set_data = [set1_data, set2_data, set3_data] = isochron.get_set_data(
                self.sample.KClAr3IsochronPlot.data, self.sample.SelectedSequence1, self.sample.SelectedSequence2,
                self.sample.UnselectedSequence)
            sht_reference.write_column(f"BC{start_row}", set1_data[0], style)
            sht_reference.write_column(f"BD{start_row}", set1_data[2], style)
            sht_reference.write_column(f"BE{start_row}", set2_data[0], style)
            sht_reference.write_column(f"BF{start_row}", set2_data[2], style)
            sht_reference.write_column(f"BG{start_row}", set3_data[0], style)
            sht_reference.write_column(f"BH{start_row}", set3_data[2], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BI{start_row}", self.sample.KClAr3IsochronPlot.line1.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BJ{start_row}", self.sample.KClAr3IsochronPlot.line1.data[1], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BK{start_row}", self.sample.KClAr3IsochronPlot.line2.data[0], style)
        except IndexError:
            pass
        try:
            sht_reference.write_column(f"BL{start_row}", self.sample.KClAr3IsochronPlot.line2.data[1], style)
        except IndexError:
            pass

        # Data for degas pattern
        try:
            degas_data = self.sample.DegasPatternPlot.data
            sht_reference.write_column(f"BM{start_row}", degas_data[0], style)
            sht_reference.write_column(f"BN{start_row}", degas_data[1], style)
            sht_reference.write_column(f"BO{start_row}", degas_data[2], style)
            sht_reference.write_column(f"BP{start_row}", degas_data[3], style)
            sht_reference.write_column(f"BQ{start_row}", degas_data[4], style)
            sht_reference.write_column(f"BR{start_row}", degas_data[5], style)
            sht_reference.write_column(f"BS{start_row}", degas_data[6], style)
            sht_reference.write_column(f"BT{start_row}", degas_data[7], style)
            sht_reference.write_column(f"BU{start_row}", degas_data[8], style)
            sht_reference.write_column(f"BV{start_row}", degas_data[9], style)
            sht_reference.write_column(f"BW{start_row}", [i+1 for i in range(len(self.sample.SequenceName))], style)
        except IndexError:
            pass

        # write result sheet
        sht_summary = self.write_sht_summary("Summary", xls)

        # write tables and charts
        for sht_name, [prop_name, sht_type, row, col, _, smp_attr_name, header_name] in self.template.sheet():
            try:
                if sht_type == "table":
                    self.write_sht_table(sht_name, prop_name, sht_type, row, col, _, smp_attr_name, header_name,
                                         style, xls, sigma)
                elif sht_type == "chart":
                    self.write_sht_chart(sht_name, prop_name, sht_type, row, col, _, smp_attr_name, header_name,
                                         style, xls, start_row, total_rows)
                else:
                    raise ValueError
            except (BaseException, Exception):
                print(traceback.format_exc())
                return None

        xls.get_worksheet_by_name("Reference").hide()
        # xls.get_worksheet_by_name("Isochrons").hidden = 0  # unhiden isochrons worksheet
        xls.get_worksheet_by_name("Summary").activate()
        xls.close()
        print('导出完毕，文件路径:%s' % self.filepath)
        return True

    def set_cell_format(self):
        pass

    def get_cell_format(self, class_name):
        return self.formats.get(class_name, self.formats['default'])

    def write_sht_summary(self, sht_name, xls):
        sht = xls.add_worksheet(sht_name)
        sht.hide_gridlines(2)  # 0 = show grids, 1 = hide print grid, else = hide print and screen grids
        sht.set_column(0, 21, width=12)  # column width
        sht.set_column(0, 0, width=16)  # column width
        sht.set_column(2, 2, width=8.5)  # column width

        method = f"{self.sample.Info.sample.method}"
        name = self.sample.Info.sample.name
        material = self.sample.Info.sample.material
        weight = self.sample.Info.sample.weight
        J_value = self.sample.TotalParam[67][0]
        J_error = self.sample.TotalParam[68][0] * self.sample.TotalParam[67][0] / 100
        sigma = self.sample.Info.preference['confidenceLevel']
        sequence_type = {"StepLaser": "Laser", "StepFurnace": "Temperature", "StepCrusher": "Drop", }.get(method, "Step Value")
        sequence_unit = self.sample.Info.sample.sequence_unit if self.sample.Info.sample.sequence_unit != "" else "Unit"
        age_unit = self.sample.Info.preference['ageUnit']
        num_step = len(self.sample.SequenceName)
        set1_ratio = [self.sample.Info.results.isochron['figure_3'][0]['initial'], self.sample.Info.results.isochron['figure_2'][0]['initial'], self.sample.TotalParam[116][0]][int(self.sample.TotalParam[115][0])]
        set2_ratio = [self.sample.Info.results.isochron['figure_3'][1]['initial'], self.sample.Info.results.isochron['figure_2'][1]['initial'], self.sample.TotalParam[118][0]][int(self.sample.TotalParam[115][0])]

        content = [
            [(0, 0), f"Table 1. 40Ar/39Ar dating results", {'bold': 1, 'top': 1, 'align': 'left'}],
            [(1, 0, 2, 0), f"Step", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 1), f"{sequence_type}", {'bold': 1, 'top': 1}],
            [(2, 1), f"({sequence_unit})", {'bold': 1, 'bottom': 6}],
            [(1, 2, 2, 2), f"Set", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 3, 2, 3), f"36Arair", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 4, 2, 4), f"37ArCa", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 5, 2, 5), f"38ArCl", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 6, 2, 6), f"39ArK", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 7, 2, 7), f"40Ar*", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 8, 2, 8), f"39Ar/40Ar", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 9, 2, 9), f"36Ar/40Ar", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(1, 10), f"Apparent Age", {'bold': 1, 'top': 1}],
            [(1, 11), f"± {sigma} σ", {'bold': 1, 'top': 1}],
            [(2, 10, 2, 11), f"({age_unit})", {'bold': 1, 'bottom': 6}],
            [(1, 12), f"40Ar*", {'bold': 1, 'top': 1}],
            [(2, 12), f"(%)", {'bold': 1, 'bottom': 6}],
            [(1, 13), f"39ArK", {'bold': 1, 'top': 1}],
            [(2, 13), f"(%)", {'bold': 1, 'bottom': 6}],
            [(1, 14, 2, 14), f"Ca/K", {'bold': 1, 'top': 1, 'bottom': 6}],
            [(3, 0), f"Sample {name} ({material}){' by ' if method != '' else ''}{method}, weight = {weight} mg, J = {J_value} ± {J_error}", {'bold': 1, 'italic': 1, 'align': 'left'}],
            [(4, 0, 1), self.sample.SequenceName, {'align': 'left'}],
            [(4, 1, 1), self.sample.SequenceValue, {'num_format': 'General'}],
            [(4, 2, 1), list(map(lambda x: int(x) if str(x).isnumeric() else "", self.sample.IsochronMark)), {'num_format': 'General'}],
            [(4, 3, 1), self.sample.DegasValues[0], {}],
            [(4, 4, 1), self.sample.DegasValues[8], {}],
            [(4, 5, 1), self.sample.DegasValues[10], {}],
            [(4, 6, 1), self.sample.DegasValues[20], {}],
            [(4, 7, 1), self.sample.DegasValues[24], {}],
            [(4, 8, 1), self.sample.IsochronValues[6], {}],
            [(4, 9, 1), self.sample.IsochronValues[8], {}],
            [(4, 10, 1), self.sample.ApparentAgeValues[2], {}],
            [(4, 11, 1), list(map(lambda x: 2*x, self.sample.ApparentAgeValues[3])), {'num_format': '± ' + self.default_fmt_prop['num_format']}],
            [(4, 12, 1), self.sample.ApparentAgeValues[6], {}],
            [(4, 13, 1), self.sample.ApparentAgeValues[7], {}],
            [(4, 14, 1), self.sample.PublishValues[9], {}],
            [(4 + num_step, 0, 0), [''] * 15, {'bold': 1, 'top': 1}],

            [(5 + num_step, 0), "Table 2. 40Ar/39Ar age summary", {'bold': 1, 'align': 'left'}],
            [(6 + num_step, 0, 7 + num_step, 0), "Group", {'bold': 1, 'top': 1}],
            [(6 + num_step, 1, 7 + num_step, 1), "40Arr/39K", {'bold': 1, 'top': 1}],
            [(6 + num_step, 2, 7 + num_step, 2), f"± {sigma} σ", {'bold': 1, 'top': 1}],
            [(6 + num_step, 3), "Age", {'bold': 1, 'top': 1}],
            [(7 + num_step, 3), f"({age_unit})", {'bold': 1, 'top': 0}],
            [(6 + num_step, 4), f"Analytical", {'bold': 1, 'top': 1, 'align': 'left'}],
            [(7 + num_step, 4), f"± {sigma} σ", {'bold': 1, 'top': 0, 'align': 'left'}],
            [(6 + num_step, 5), f"Internal", {'bold': 1, 'top': 1, 'align': 'left'}],
            [(7 + num_step, 5), f"± {sigma} σ", {'bold': 1, 'top': 0, 'align': 'left'}],
            [(6 + num_step, 6), f"Full external", {'bold': 1, 'top': 1, 'align': 'left'}],
            [(7 + num_step, 6), f"± {sigma} σ", {'bold': 1, 'top': 0, 'align': 'left'}],
            [(6 + num_step, 7, 7 + num_step, 7), f"MSWD", {'bold': 1, 'top': 1}],
            [(6 + num_step, 8, 7 + num_step, 8), f"39ArK", {'bold': 1, 'top': 1}],
            [(8 + num_step, 0), f"Total gas age", {'bold': 1, 'top': 6, 'italic': 1, 'align': 'left'}],
            [(8 + num_step, 1, 0), [''] * 8, {'top': 6}],
            [(9 + num_step, 0, 10 + num_step, 0), f"Total", {'bold': 1, 'align': 'center'}],
            [(12 + num_step, 0), f"40Ar/36Ar ratio ({self.sample.TotalParam[0][0]:.2f}) corrected plateau ages", {'bold': 1, 'italic': 1, 'align': 'left'}],
            [(18 + num_step, 0), f"{['Intercept of inverse isochron', 'Intercept of normal isochron', 'Inputted argon ratio'][int(self.sample.TotalParam[115][0])]} "
                                 f"(set 1 {set1_ratio} and set 2 {set2_ratio}) corrected plateau ages", {'bold': 1, 'italic': 1, 'align': 'left'}],
            [(24 + num_step, 0), f"Inverse isochron ages", {'bold': 1, 'italic': 1, 'align': 'left'}],
            [(30 + num_step, 0), f"Three-dimension ages", {'bold': 1, 'italic': 1, 'align': 'left'}],
        ]

        tga_res = self.sample.Info.results.age_spectra['TGA']
        content.extend([
            [(9 + num_step, 1, 10 + num_step, 1), tga_res['F'], {'num_format': '0.00000'}],
            [(9 + num_step, 2, 10 + num_step, 2), tga_res['sF'] * sigma, {'num_format': '0.00000'}],
            [(9 + num_step, 3, 10 + num_step, 3), tga_res['age'], {'num_format': '0.00'}],
            [(9 + num_step, 4), tga_res['s1'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
            [(9 + num_step, 5), tga_res['s2'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
            [(9 + num_step, 6), tga_res['s3'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
            [(10 + num_step, 4), tga_res['s1'] * sigma / abs(tga_res['age']), {'num_format': '± 0.00%', 'align': 'left'}],
            [(10 + num_step, 5), tga_res['s1'] * sigma / abs(tga_res['age']), {'num_format': '± 0.00%', 'align': 'left'}],
            [(10 + num_step, 6), tga_res['s1'] * sigma / abs(tga_res['age']), {'num_format': '± 0.00%', 'align': 'left'}],
            [(9 + num_step, 7, 10 + num_step, 7), tga_res['MSWD'], {'num_format': '0.00'}],
            [(9 + num_step, 8, 10 + num_step, 8), tga_res['Ar39'] / 100, {'num_format': '0.00%'}],
        ])

        row = 13
        ar39 = [0, 0]
        for res in [
            self.sample.Info.results.age_spectra, self.sample.Info.results.age_plateau,
            self.sample.Info.results.isochron['figure_3'], self.sample.Info.results.isochron['figure_7']
        ]:
            for index, _ in enumerate(['Set 1', 'Set 2']):
                ar39[index] = res[index].get('Ar39', ar39[index] * 100) / 100
                try:
                    content.extend([
                        [(row + num_step, 0, row + 1 + num_step, 0), _, {'bold': 1, 'align': 'center'}],
                        [(row + num_step, 1, row + 1 + num_step, 1), res[index]['F'], {'num_format': '0.00000'}],
                        [(row + num_step, 2, row + 1 + num_step, 2), res[index]['sF'], {'num_format': '0.00000'}],
                        [(row + num_step, 3, row + 1 + num_step, 3), res[index]['age'], {'num_format': '0.00'}],
                        [(row + num_step, 4), res[index]['s1'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
                        [(row + num_step, 5), res[index]['s2'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
                        [(row + num_step, 6), res[index]['s3'] * sigma, {'num_format': '± 0.00', 'align': 'left'}],
                        [(row + 1 + num_step, 4), res[index]['s1'] * sigma / abs(res[index]['age']), {'num_format': '± 0.00%', 'align': 'left'}],
                        [(row + 1 + num_step, 5), res[index]['s1'] * sigma / abs(res[index]['age']), {'num_format': '± 0.00%', 'align': 'left'}],
                        [(row + 1 + num_step, 6), res[index]['s1'] * sigma / abs(res[index]['age']), {'num_format': '± 0.00%', 'align': 'left'}],
                        [(row + num_step, 7, row + 1 + num_step, 7), res[index]['MSWD'], {'num_format': '0.00'}],
                        [(row + num_step, 8, row + 1 + num_step, 8), ar39[index], {'num_format': '0.00%'}],
                    ])
                except ZeroDivisionError:
                    pass
                row += 2
            row += 2
        content.append([(row - 2 + num_step, 0, 0), [''] * 9, {'top': 1}])

        for pos, value, _prop in content:
            prop = self.default_fmt_prop.copy()
            prop.update(_prop)
            fmt = Format(prop, xls.xf_format_indices, xls.dxf_format_indices)
            xls.formats.append(fmt)
            if isinstance(value, (list, np.ndarray)) and len(pos) == 3:
                [sht.write_row, sht.write_column][pos[2]](*pos[:2], value, fmt)
            elif len(pos) == 2:
                isnumeric = isinstance(value, (float, int)) and not np.isnan(value) and not np.isinf(value)
                [sht.write_string, sht.write_number][isnumeric](*pos, value if isnumeric else str(value), fmt)
            elif len(pos) == 4:
                isnumeric = isinstance(value, (float, int)) and not np.isnan(value) and not np.isinf(value)
                sht.merge_range(*pos, value if isnumeric else str(value), fmt)

        return sht


    def write_sht_table(self, sht_name, prop_name, sht_type, row, col, _, smp_attr_name, header_name, style, xls, sigma=1):
        sht = xls.add_worksheet(sht_name)
        num_step = len(self.sample.SequenceName)
        data = arr.transpose(getattr(self.sample, smp_attr_name, None).data)
        sht.hide_gridlines(2)  # 0 = show grids, 1 = hide print grid, else = hide print and screen grids
        sht.hide()  # default hidden table sheet
        sht.set_column(0, len(data), width=12)  # column width
        header = getattr(sample, header_name)
        header = list(map(lambda each: each if "σ" not in each else each.replace('1', str(sigma)) if str(sigma) not in each else each.replace('2', str(sigma)), header))

        content = [
            [(0, 0), f"{sht_name}", {'bold': 1, 'top': 1, 'align': 'left'}],
            *[[(1, col, 2, col), each, {'bold': 1, 'top': 1, 'bottom': 6}] for col, each in enumerate(header)],
            *[[(3, col, 1), each if "σ" not in header[col] else list(map(lambda _: _ * sigma, each)), {}] for col, each in enumerate(data)],
            [(3 + num_step, 0, 0), [''] * len(data), {'bold': 1, 'top': 1}],
        ]

        for pos, value, _prop in content:
            prop = self.default_fmt_prop.copy()
            prop.update(_prop)
            fmt = Format(prop, xls.xf_format_indices, xls.dxf_format_indices)
            xls.formats.append(fmt)
            if isinstance(value, (list, np.ndarray)) and len(pos) == 3:
                value = [None if isinstance(v, (float, int)) and np.isnan(v) else v for v in value]
                [sht.write_row, sht.write_column][pos[2]](*pos[:2], value, fmt)
            elif len(pos) == 2:
                isnumeric = isinstance(value, (float, int)) and not np.isnan(value) and not np.isinf(value)
                [sht.write_string, sht.write_number][isnumeric](*pos, value if isnumeric else str(value), fmt)
            elif len(pos) == 4:
                isnumeric = isinstance(value, (float, int)) and not np.isnan(value) and not np.isinf(value)
                sht.merge_range(*pos, value if isnumeric else str(value), fmt)


    def write_sht_chart(self, sht_name, prop_name, sht_type, row, col, _, smp_attr_name, header_name, style, xls, start_row, total_rows):
        sht = xls.add_chartsheet(sht_name)
        sht.set_paper(1)  # US letter = 1, A4 = 9, letter is more rectangular
        num_unselected = len(self.sample.UnselectedSequence)
        num_set1 = len(self.sample.SelectedSequence1)
        num_set2 = len(self.sample.SelectedSequence2)
        if "spectra" in prop_name.lower():
            figure = self.sample.AgeSpectraPlot
            data_area = [
                # Spectra lines
                f"A{start_row}:A{(total_rows + 1) * 2 + start_row - 1}",
                f"B{start_row}:B{(total_rows + 1) * 2 + start_row - 1}",
                f"C{start_row}:C{(total_rows + 1) * 2 + start_row - 1}",
                # set 1
                f"D{start_row}:D{(total_rows + 1) * 2 + start_row - 1}",
                f"E{start_row}:E{(total_rows + 1) * 2 + start_row - 1}",
                f"F{start_row}:F{(total_rows + 1) * 2 + start_row - 1}",
                # set 2
                f"G{start_row}:G{(total_rows + 1) * 2 + start_row - 1}",
                f"H{start_row}:H{(total_rows + 1) * 2 + start_row - 1}",
                f"I{start_row}:I{(total_rows + 1) * 2 + start_row - 1}",
            ]
            axis_range = [figure.xaxis.min, figure.xaxis.max, figure.yaxis.min, figure.yaxis.max]
            self.get_chart_age_spectra(xls, sht, data_area, axis_range, age_unit=self.sample.Info.preference['ageUnit'])
        elif "normal_isochron" in prop_name.lower():
            data_area = [
                f"O{start_row}:O{num_set1 + start_row - 1}", f"P{start_row}:P{num_set1 + start_row - 1}",
                f"Q{start_row}:Q{num_set2 + start_row - 1}", f"R{start_row}:R{num_set2 + start_row - 1}",
                f"S{start_row}:S{num_unselected + start_row - 1}",
                f"T{start_row}:T{num_unselected + start_row - 1}",
                f"U{start_row}:V{start_row}", f"U{start_row + 1}:V{start_row + 1}",
                f"W{start_row}:X{start_row}", f"W{start_row + 1}:X{start_row + 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_2').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_2').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_2').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_2').yaxis.max,
            ]
            self.get_chart_isochron(
                xls, sht, data_area, axis_range, title_name="Normal Isochron",
                x_axis_name=f"{consts.sup_39}Ar / {consts.sup_36}Ar",
                y_axis_name=f"{consts.sup_40}Ar / {consts.sup_36}Ar")
        elif "inverse_isochron" in prop_name.lower():
            data_area = [
                f"Y{start_row}:Y{num_set1 + start_row - 1}", f"Z{start_row}:Z{num_set1 + start_row - 1}",
                f"AA{start_row}:AA{num_set2 + start_row - 1}", f"AB{start_row}:AB{num_set2 + start_row - 1}",
                f"AC{start_row}:AC{num_unselected + start_row - 1}",
                f"AD{start_row}:AD{num_unselected + start_row - 1}",
                f"AE{start_row}:AF{start_row}", f"AE{start_row + 1}:AF{start_row + 1}",
                f"AG{start_row}:AH{start_row}", f"AG{start_row + 1}:AH{start_row + 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_3').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_3').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_3').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_3').yaxis.max,
            ]
            self.get_chart_isochron(
                xls, sht, data_area, axis_range, title_name="Inverse Isochron",
                x_axis_name=f"{consts.sup_39}Ar / {consts.sup_40}Ar",
                y_axis_name=f"{consts.sup_36}Ar / {consts.sup_40}Ar")
        elif "k-cl-ar_1_isochron" in prop_name.lower():
            data_area = [
                f"AI{start_row}:AI{num_set1 + start_row - 1}", f"AJ{start_row}:AJ{num_set1 + start_row - 1}",
                f"AK{start_row}:AK{num_set2 + start_row - 1}", f"AL{start_row}:AL{num_set2 + start_row - 1}",
                f"AM{start_row}:AM{num_unselected + start_row - 1}",
                f"AN{start_row}:AN{num_unselected + start_row - 1}",
                f"AO{start_row}:AP{start_row}", f"AO{start_row + 1}:AP{start_row + 1}",
                f"AQ{start_row}:AR{start_row}", f"AQ{start_row + 1}:AR{start_row + 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_4').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_4').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_4').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_4').yaxis.max,
            ]
            self.get_chart_isochron(
                xls, sht, data_area, axis_range, title_name="K-Cl-Ar 1 Isochron",
                x_axis_name=f"{consts.sup_39}Ar / {consts.sup_38}Ar",
                y_axis_name=f"{consts.sup_40}Ar / {consts.sup_38}Ar")
        elif "k-cl-ar_2_isochron" in prop_name.lower():
            data_area = [
                f"AS{start_row}:AS{num_set1 + start_row - 1}", f"AT{start_row}:AT{num_set1 + start_row - 1}",
                f"AU{start_row}:AU{num_set2 + start_row - 1}", f"AV{start_row}:AV{num_set2 + start_row - 1}",
                f"AW{start_row}:AW{num_unselected + start_row - 1}",
                f"AX{start_row}:AX{num_unselected + start_row - 1}",
                f"AY{start_row}:AZ{start_row}", f"AY{start_row + 1}:AZ{start_row + 1}",
                f"BA{start_row}:BB{start_row}", f"BA{start_row + 1}:BB{start_row + 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_5').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_5').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_5').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_5').yaxis.max,
            ]
            self.get_chart_isochron(
                xls, sht, data_area, axis_range, title_name="K-Cl-Ar 2 Isochron",
                x_axis_name=f"{consts.sup_39}Ar / {consts.sup_40}Ar",
                y_axis_name=f"{consts.sup_38}Ar / {consts.sup_40}Ar")
        elif "k-cl-ar_3_isochron" in prop_name.lower():
            data_area = [
                f"BC{start_row}:BC{num_set1 + start_row - 1}", f"BD{start_row}:BD{num_set1 + start_row - 1}",
                f"BE{start_row}:BE{num_set2 + start_row - 1}", f"BF{start_row}:BF{num_set2 + start_row - 1}",
                f"BG{start_row}:BG{num_unselected + start_row - 1}",
                f"BH{start_row}:BH{num_unselected + start_row - 1}",
                f"BI{start_row}:BJ{start_row}", f"BI{start_row + 1}:BJ{start_row + 1}",
                f"BK{start_row}:BL{start_row}", f"BK{start_row + 1}:BL{start_row + 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_6').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_6').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_6').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_6').yaxis.max,
            ]
            self.get_chart_isochron(
                xls, sht, data_area, axis_range, title_name="K-Cl-Ar 3 Isochron",
                x_axis_name=f"{consts.sup_38}Ar / {consts.sup_39}Ar",
                y_axis_name=f"{consts.sup_40}Ar / {consts.sup_39}Ar")
        elif "degas_pattern" in prop_name.lower():
            data_area = [
                f"BM{start_row}:BM{total_rows + start_row - 1}",
                f"BN{start_row}:BN{total_rows + start_row - 1}",
                f"BO{start_row}:BO{total_rows + start_row - 1}",
                f"BP{start_row}:BP{total_rows + start_row - 1}",
                f"BQ{start_row}:BQ{total_rows + start_row - 1}",
                f"BR{start_row}:BR{total_rows + start_row - 1}",
                f"BS{start_row}:BS{total_rows + start_row - 1}",
                f"BT{start_row}:BT{total_rows + start_row - 1}",
                f"BU{start_row}:BU{total_rows + start_row - 1}",
                f"BV{start_row}:BV{total_rows + start_row - 1}",
                f"BW{start_row}:BW{total_rows + start_row - 1}",
            ]
            axis_range = [
                basic.get_component_byid(self.sample, 'figure_8').xaxis.min,
                basic.get_component_byid(self.sample, 'figure_8').xaxis.max,
                basic.get_component_byid(self.sample, 'figure_8').yaxis.min,
                basic.get_component_byid(self.sample, 'figure_8').yaxis.max,
            ]
            self.get_chart_degas_pattern(
                xls, sht, data_area, axis_range,
                title_name="Degas Pattern", x_axis_name=f"Sequence", y_axis_name=f"Argon Isotopes (%)")

    def create_initial_chart(self, xls: Workbook, chart_type: str = 'scatter'):
        # chartarea
        chartarea_dict = {'border': {'none': True}, 'fill': {'color': self.chartarea_color}}
        # plotarea
        plotarea_dict = {
            'border': {'color': self.border_color, 'width': self.plot_border_width},
            'fill': {'color': self.plotarea_color}
        }
        # title, No title
        title_dict = {'none': True, 'name': '',
                      'name_font': {'name': self.font_name, 'size': self.title_font_size, 'color': self.font_color}}
        # axis
        axis_dict = {
            'name': 'Axis Name',  # axis name
            'name_font': {'name': self.font_name, 'size': self.axis_font_size, 'bold': self.axis_font_bold,
                          'color': self.font_color},
            # Setting number font
            'num_font': {'name': self.font_name, 'size': self.axis_num_font_size, 'color': self.font_color,
                         'italic': False},
            'major_gridlines': {'visible': False, 'line': {'width': 1.25, 'dash_type': 'dash'}},
            # Setting line (ticks) properties of chart axes
            'line': {'width': self.plot_border_width, 'color': self.border_color},
            'crossing': 'min',
        }
        # Not display legend
        legend_dict = {'none': True}

        chart = xls.add_chart({'type': chart_type})
        chart.set_chartarea(chartarea_dict)
        chart.set_plotarea(plotarea_dict)
        chart.set_title(title_dict)
        chart.set_x_axis(axis_dict)
        chart.set_y_axis(axis_dict)
        chart.set_legend(legend_dict)

        return chart

    def get_chart_age_spectra(self, xls: Workbook, sht: Chartsheet, data_area: list, axis_range: list, age_unit='Ma'):
        # ==============SpectraDiagram===============
        [xMin, xMax, yMin, yMax] = axis_range
        # Initializing a chart
        chart = self.create_initial_chart(xls, 'scatter')
        # Set data
        series = [
            {
                'name': 'Line 1-1',
                'categories': f'Reference!{data_area[0]}',
                'values': f'Reference!{data_area[1]}',
                'line': {'color': self.border_color, 'width': self.line_width},
                'marker': {'type': 'none'},
            },
            {
                'name': 'Line 1-2',
                'categories': f'Reference!{data_area[0]}',
                'values': f'Reference!{data_area[2]}',
                'line': {'color': self.border_color, 'width': self.line_width},
                'marker': {'type': 'none'},
            },
            {
                'name': 'Line 2-1',
                'categories': f'Reference!{data_area[3]}',
                'values': f'Reference!{data_area[4]}',
                'line': {'color': self.color_map[0], 'width': self.line_width},
                'marker': {'type': 'none'},
            },
            {
                'name': 'Line 2-2',
                'categories': f'Reference!{data_area[3]}',
                'values': f'Reference!{data_area[5]}',
                'line': {'color': self.color_map[0], 'width': self.line_width},
                'marker': {'type': 'none'},
            },
            {
                'name': 'Line 3-1',
                'categories': f'Reference!{data_area[6]}',
                'values': f'Reference!{data_area[7]}',
                'line': {'color': self.color_map[1], 'width': self.line_width},
                'marker': {'type': 'none'},
            },
            {
                'name': 'Line 3-2',
                'categories': f'Reference!{data_area[6]}',
                'values': f'Reference!{data_area[8]}',
                'line': {'color': self.color_map[1], 'width': self.line_width},
                'marker': {'type': 'none'},
            },
        ]
        for each in series:
            chart.add_series(each)
        # Title
        # chart.title_name = 'Age Spectra'
        # Axis title
        chart.x_axis.update({'name': f'Cumulative {consts.sup_39}Ar released (%)', 'min': xMin, 'max': xMax})
        chart.y_axis.update({'name': f'Apparent age ({age_unit})', 'min': yMin, 'max': yMax})
        sht.set_chart(chart)

    def get_chart_isochron(self, xls: Workbook, sht: Chartsheet, data_areas, axis_range,
                           title_name="", x_axis_name="", y_axis_name=""):
        # Initializing a chart
        isochron = self.create_initial_chart(xls, 'scatter')
        series = [
            {
                'name': 'Set 1 Selected Points',
                'categories': f'Reference!{data_areas[0]}',
                'values': f'Reference!{data_areas[1]}',
                'line': {'none': True},
                'marker': {
                    'type': 'square', 'size': 6,
                    'border': {'color': self.border_color},
                    'fill': {'color': self.color_map[0]}}
            },
            {
                'name': 'Set 2 Selected Points',
                'categories': f'Reference!{data_areas[2]}',
                'values': f'Reference!{data_areas[3]}',
                'line': {'none': True},
                'marker': {'type': 'square', 'size': 6,
                           'border': {'color': self.border_color},
                           'fill': {'color': self.color_map[1]}}
            },
            {
                'name': 'Unselected Points',
                'categories': f'Reference!{data_areas[4]}',
                'values': f'Reference!{data_areas[5]}',
                'line': {'none': True},
                'marker': {'type': 'square', 'size': 6,
                           'border': {'color': self.border_color},
                           'fill': {'color': self.color_map[2]}}
            },
            {
                'name': 'Line Set 1',
                'categories': f'Reference!{data_areas[6]}',
                'values': f'Reference!{data_areas[7]}',
                'line': {'color': self.color_map[0], 'width': self.line_width},
                'marker': {'type': 'none'}
            },
            {
                'name': 'Line Set 2',
                'categories': f'Reference!{data_areas[8]}',
                'values': f'Reference!{data_areas[9]}',
                'line': {'color': self.color_map[1], 'width': self.line_width},
                'marker': {'type': 'none'}
            }
        ]
        # isochron.title_name = title_name
        for each in series:
            isochron.add_series(each)
        isochron.x_axis.update({'name': x_axis_name, 'min': axis_range[0], 'max': axis_range[1]})
        isochron.y_axis.update({'name': y_axis_name, 'min': axis_range[2], 'max': axis_range[3]})
        sht.set_chart(isochron)

    def get_chart_degas_pattern(self, xls: Workbook, sht: Chartsheet, data_areas, axis_range,
                                title_name="", x_axis_name="", y_axis_name=""):
        # unicode for supscript numbers
        # series name
        series_name = [
            f'{consts.sup_36}Ara', f'{consts.sup_37}ArCa', f'{consts.sup_38}ArCl',
            f'{consts.sup_39}ArK', f'{consts.sup_40}Arr', f'{consts.sup_36}Ar',
            f'{consts.sup_37}Ar', f'{consts.sup_38}Ar', f'{consts.sup_39}Ar', f'{consts.sup_40}Ar',
        ]
        # Initializing a chart
        chart = self.create_initial_chart(xls, 'scatter')
        series = []
        for i in range(len(data_areas) - 1):
            series.append({
                'name': series_name[i],
                'categories': f'Reference!{data_areas[10]}',
                'values': f'Reference!{data_areas[i]}',
                'line': {'color': self.border_color, 'width': self.line_width},
                'marker': {
                    'type': 'square', 'size': 6,
                    'border': {'color': self.border_color},
                    # 'fill': {'color': self.color_map[0]},
                }
            })
        # chart.title_name = title_name
        for each in series:
            chart.add_series(each)
        chart.x_axis.update({'name': x_axis_name, 'min': axis_range[0], 'max': axis_range[1]})
        chart.y_axis.update({'name': y_axis_name, 'min': axis_range[2], 'max': axis_range[3]})

        chart.set_legend({'none': False, 'position': 'top'})

        sht.set_chart(chart)


class CreateOriginGraph:
    def __init__(self, **kwargs):
        self.name = "Origin"
        self.sample = Sample()
        self.export_filepath = ""
        self.spectra_data = [[]] * 3
        self.set1_spectra_data = [[]] * 3
        self.set2_spectra_data = [[]] * 3
        self.isochron_data = [[]] * 36
        self.isochron_lines_data = [[]] * 20
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_graphs(self):
        import originpro as op
        import OriginExt
        def origin_shutdown_exception_hook(exctype, value, traceback):
            """Ensures Origin gets shut down if an uncaught exception"""
            op.exit()
            sys.__excepthook__(exctype, value, traceback)

        if op and op.oext:
            sys.excepthook = origin_shutdown_exception_hook

        # Set Origin instance visibility.
        # Important for only external Python.
        # Should not be used with embedded Python.
        if op.oext:
            op.set_show(True)

        # Spectra lines
        linePoints = self.spectra_data if self.spectra_data != [] else [[]] * 3
        linePoints += self.set1_spectra_data if self.set1_spectra_data != [] else [[]] * 3
        linePoints += self.set2_spectra_data if self.set2_spectra_data != [] else [[]] * 3
        age_spectra_wks = op.new_sheet(lname='Age data')
        age_spectra_wks.from_list(0, linePoints[0], lname="X values")
        age_spectra_wks.from_list(1, linePoints[1], lname="Y1 values")
        age_spectra_wks.from_list(2, linePoints[2], lname="Y2 values")
        age_spectra_wks.from_list(3, linePoints[3], lname="Set 1 X values")
        age_spectra_wks.from_list(4, linePoints[4], lname="Set 1 Y1 values")
        age_spectra_wks.from_list(5, linePoints[5], lname="Set 1 Y2 values")
        age_spectra_wks.from_list(6, linePoints[6], lname="Set 2 X values")
        age_spectra_wks.from_list(7, linePoints[7], lname="Set 2 Y1 values")
        age_spectra_wks.from_list(8, linePoints[8], lname="Set 2 Y2 values")
        # Isochron scatter plots
        isochron_wb = op.new_book('w', lname='Isochron data')
        isochron_set1_ws = isochron_wb.add_sheet(name='Isochron Set 1', active=False)
        isochron_set2_ws = isochron_wb.add_sheet(name='Isochron Set 2', active=False)
        isochron_set3_ws = isochron_wb.add_sheet(name='Isochron Unselected', active=False)
        isochron_lines_ws = isochron_wb.add_sheet(name='Isochron Lines', active=False)

        for index, item in enumerate(self.isochron_lines_data):
            isochron_lines_ws.from_list(index, item, lname='')
        for index, each_col in enumerate(arr.transpose(
                [arr.transpose(self.isochron_data)[i] for i in self.sample.SelectedSequence1])):
            isochron_set1_ws.from_list(index, each_col)  # Normal, invers, K-Cl-Ar 1, K-Cl-Ar 2, K-Cl-Ar 3, 3D
        for index, each_col in enumerate(arr.transpose(
                [arr.transpose(self.isochron_data)[i] for i in self.sample.SelectedSequence2])):
            isochron_set2_ws.from_list(index, each_col)  # Normal, invers, K-Cl-Ar 1, K-Cl-Ar 2, K-Cl-Ar 3, 3D
        for index, each_col in enumerate(arr.transpose(
                [arr.transpose(self.isochron_data)[i] for i in self.sample.UnselectedSequence])):
            isochron_set3_ws.from_list(index, each_col)  # Normal, invers, K-Cl-Ar 1, K-Cl-Ar 2, K-Cl-Ar 3, 3D

        # Age spectra plot
        graph = self.sample.AgeSpectraPlot
        gr = op.new_graph(lname='Age Spectra',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(age_spectra_wks, coly='B', colx='A', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(age_spectra_wks, coly='C', colx='A', type='l')  # 'l'(Line Plot)
        pl_3 = gl_1.add_plot(age_spectra_wks, coly='E', colx='D', type='l')  # set 1
        pl_4 = gl_1.add_plot(age_spectra_wks, coly='F', colx='D', type='l')  # set 1
        pl_5 = gl_1.add_plot(age_spectra_wks, coly='H', colx='G', type='l')  # set 2
        pl_6 = gl_1.add_plot(age_spectra_wks, coly='I', colx='G', type='l')  # set 2
        pl_1.color = pl_2.color = graph.line1.color
        pl_3.color = pl_4.color = graph.line3.color
        pl_5.color = pl_6.color = graph.line5.color
        gl_1.axis('y').title = 'Apparent age (Ma)'
        gl_1.axis('x').title = 'Cumulative \+(39)Ar released (%)'
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))
        gl_1.axis('x').set_limits(0, 100, 20)
        # Normal Isochron plots
        graph = self.sample.NorIsochronPlot
        gr = op.new_graph(lname='Normal Isochron',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(isochron_set1_ws, colx='A', coly='C', type='s')  # 's'(Scatter Plot)
        pl_2 = gl_1.add_plot(isochron_set2_ws, colx='A', coly='C', type='s')  # 's'(Scatter Plot)
        pl_3 = gl_1.add_plot(isochron_set3_ws, colx='A', coly='C', type='s')  # 's'(Scatter Plot)
        for plt in gl_1.plot_list():
            plt.color = [graph.set1.color, graph.set2.color, '#333333'][plt.index()]
            plt.symbol_kind = 2
            plt.symbol_interior = 1
            plt.symbol_size = 3
        pl_1 = gl_1.add_plot(isochron_lines_ws, coly='B', colx='A', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(isochron_lines_ws, coly='D', colx='C', type='l')  # 'l'(Line Plot)
        pl_1.color = graph.line1.color
        pl_2.color = graph.line2.color
        gl_1.axis('x').title = '\+(39)Ar / \+(36)Ar'
        gl_1.axis('y').title = '\+(40)Ar / \+(36)Ar'
        gl_1.axis('x').set_limits(float(graph.xaxis.min), float(graph.xaxis.max))
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))
        # print(pl_1.layer.GetNumProp(f"{gl_1.axis('x')}.inc"))
        # pl_1.layer.SetNumProp(pl_1._format_property('symbol.size'), 10)
        # print(pl_1.layer.GetNumProp(pl_1._format_property('symbol.size')))
        # Inverse Isochron plots
        graph = self.sample.InvIsochronPlot
        gr = op.new_graph(lname='Inverse Isochron',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(isochron_set1_ws, colx='G', coly='I', type='s')  # 's'(Scatter Plot)
        pl_2 = gl_1.add_plot(isochron_set2_ws, colx='G', coly='I', type='s')  # 's'(Scatter Plot)
        pl_3 = gl_1.add_plot(isochron_set3_ws, colx='G', coly='I', type='s')  # 's'(Scatter Plot)
        for plt in gl_1.plot_list():
            plt.color = [graph.set1.color, graph.set2.color, '#333333'][plt.index()]
            plt.symbol_kind = 2
            plt.symbol_interior = 1
            plt.symbol_size = 3
        pl_1 = gl_1.add_plot(isochron_lines_ws, coly='F', colx='E', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(isochron_lines_ws, coly='H', colx='G', type='l')  # 'l'(Line Plot)
        pl_1.color = graph.line1.color
        pl_2.color = graph.line2.color
        gl_1.axis('x').title = '\+(39)Ar / \+(40)Ar'
        gl_1.axis('y').title = '\+(36)Ar / \+(40)Ar'
        gl_1.axis('x').set_limits(float(graph.xaxis.min), float(graph.xaxis.max))
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))
        # Cl correlation 1
        graph = self.sample.KClAr1IsochronPlot
        gr = op.new_graph(lname='Cl correlation 1',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(isochron_set1_ws, colx='M', coly='O', type='s')  # 's'(Scatter Plot)
        pl_2 = gl_1.add_plot(isochron_set2_ws, colx='M', coly='O', type='s')  # 's'(Scatter Plot)
        pl_3 = gl_1.add_plot(isochron_set3_ws, colx='M', coly='O', type='s')  # 's'(Scatter Plot)
        for plt in gl_1.plot_list():
            plt.color = [graph.set1.color, graph.set2.color, '#333333'][plt.index()]
            plt.symbol_kind = 2
            plt.symbol_interior = 1
            plt.symbol_size = 3
        pl_1 = gl_1.add_plot(isochron_lines_ws, coly='J', colx='I', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(isochron_lines_ws, coly='L', colx='K', type='l')  # 'l'(Line Plot)
        pl_1.color = graph.line1.color
        pl_2.color = graph.line2.color
        gl_1.axis('x').title = '\+(39)Ar / \+(38)Ar'
        gl_1.axis('y').title = '\+(40)Ar / \+(38)Ar'
        gl_1.axis('x').set_limits(float(graph.xaxis.min), float(graph.xaxis.max))
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))
        # Cl correlation 2
        graph = self.sample.KClAr2IsochronPlot
        gr = op.new_graph(lname='Cl correlation 2',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(isochron_set1_ws, colx='S', coly='U', type='s')  # 's'(Scatter Plot)
        pl_2 = gl_1.add_plot(isochron_set2_ws, colx='S', coly='U', type='s')  # 's'(Scatter Plot)
        pl_3 = gl_1.add_plot(isochron_set3_ws, colx='S', coly='U', type='s')  # 's'(Scatter Plot)
        for plt in gl_1.plot_list():
            plt.color = [graph.set1.color, graph.set2.color, '#333333'][plt.index()]
            plt.symbol_kind = 2
            plt.symbol_interior = 1
            plt.symbol_size = 3
        pl_1 = gl_1.add_plot(isochron_lines_ws, coly='N', colx='M', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(isochron_lines_ws, coly='P', colx='O', type='l')  # 'l'(Line Plot)
        pl_1.color = graph.line1.color
        pl_2.color = graph.line2.color
        gl_1.axis('x').title = '\+(39)Ar / \+(40)Ar'
        gl_1.axis('y').title = '\+(38)Ar / \+(40)Ar'
        gl_1.axis('x').set_limits(float(graph.xaxis.min), float(graph.xaxis.max))
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))
        # Cl correlation 3
        graph = self.sample.KClAr3IsochronPlot
        gr = op.new_graph(lname='Cl correlation 3',
                          template=os.path.join(SETTINGS_ROOT, 'OriginExportTemplate.otpu'))
        gl_1 = gr[0]
        pl_1 = gl_1.add_plot(isochron_set1_ws, colx='Y', coly='AA', type='s')  # 's'(Scatter Plot)
        pl_2 = gl_1.add_plot(isochron_set2_ws, colx='Y', coly='AA', type='s')  # 's'(Scatter Plot)
        pl_3 = gl_1.add_plot(isochron_set3_ws, colx='Y', coly='AA', type='s')  # 's'(Scatter Plot)
        for plt in gl_1.plot_list():
            plt.color = [graph.set1.color, graph.set2.color, '#333333'][plt.index()]
            plt.symbol_kind = 2
            plt.symbol_interior = 1
            plt.symbol_size = 3
        pl_1 = gl_1.add_plot(isochron_lines_ws, coly='R', colx='Q', type='l')  # 'l'(Line Plot)
        pl_2 = gl_1.add_plot(isochron_lines_ws, coly='T', colx='S', type='l')  # 'l'(Line Plot)
        pl_1.color = graph.line1.color
        pl_2.color = graph.line2.color
        gl_1.axis('x').title = '\+(38)Ar / \+(39)Ar'
        gl_1.axis('y').title = '\+(40)Ar / \+(39)Ar'
        gl_1.axis('x').set_limits(float(graph.xaxis.min), float(graph.xaxis.max))
        gl_1.axis('y').set_limits(float(graph.yaxis.min), float(graph.yaxis.max))

        # Save the opju to your UFF.
        op.save(self.export_filepath)

        # Exit running instance of Origin.
        # Required for external Python but don't use with embedded Python.
        if op.oext:
            op.exit()
        return 0


class CreatePDF:
    def __init__(self, **kwargs):
        self.filepath = ""
        self.sample = Sample()
        # self.name = "PDF"
        # self.figure = Plot()
        # self.page_size = [595, 842]
        # self.data_bytes = b""
        # self.component = []
        # self.text = []
        # self.frame = []
        # self.axis_area = [138, 400, 360, 270]  # x0, y0, w, h

        for key, value in kwargs.items():
            setattr(self, key, value)

    def color_hex_to_rgb(self, color: str):
        if color.startswith("#"):
            color = color[1:]
        r = int(color[:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return r, g, b

    def color_rgb_normalized(self, rgb):
        return [round(i / 255, 6) for i in rgb]

    def save(self, figure: str = "figure_3", use_split_number: bool = True):

        if figure in ['figure_2', 'figure_3', 'figure_4', 'figure_5', 'figure_6']:
            cv = self.plot_isochron(figure=figure)
        elif figure in ['figure_1']:
            cv = self.plot_spectra(figure=figure)
        elif figure in ['figure_8']:
            cv = self.plot_degas(figure=figure)
        elif figure in ['figure_9']:
            cv = self.plot_age_distribution(figure=figure)
        else:
            return

        file = pm.NewPDF(filepath=self.filepath)
        # rich text tags should follow this priority: color > script > break
        file.text(page=0, x=50, y=780, line_space=1.2, size=12, base=0, h_align="left",
                  text=f"The PDF can be edited with Adobe Acrobat, Illustrator and CorelDRAW.<r>"
                       f"<r> Sample Name: {self.sample.name()}"
                       f"<r> Figure Title: {basic.get_component_byid(self.sample, figure).name}",
                  )
        file.canvas(page=1, margin_top=5, canvas=cv, unit="cm", h_align="middle")

        # save pdf
        file.save()

    def plot_isochron(self, smp: Sample = None, figure: str = "figure_3"):
        if smp is None:
            smp = self.sample

        x_title = f""
        y_title = f""
        if figure == "figure_2":
            plot: Plot = smp.NorIsochronPlot
            x_title = f"<sup>40</sup>Ar/<sup>39</sup>Ar<sub>K</sub>"
            y_title = f"<sup>40</sup>Ar/<sup>36</sup>Ar<sub>a</sub>"
        if figure == "figure_3":
            plot: Plot = smp.InvIsochronPlot
            x_title = f"<sup>39</sup>Ar<sub>K</sub>/<sup>40</sup>Ar"
            y_title = f"<sup>36</sup>Ar<sub>a</sub>/<sup>40</sup>Ar"
        if figure == "figure_4":
            plot: Plot = smp.KClAr1IsochronPlot
            x_title = f"<sup>39</sup>Ar<sub>K</sub>/<sup>38</sup>Ar<sub>Cl</sub>"
            y_title = f"<sup>40</sup>Ar/<sup>38</sup>Ar<sub>Cl</sub>"
        if figure == "figure_5":
            plot: Plot = smp.KClAr2IsochronPlot
            x_title = f"<sup>39</sup>Ar<sub>K</sub>/<sup>40</sup>Ar"
            y_title = f"<sup>38</sup>Ar<sub>Cl</sub>/<sup>40</sup>Ar"
        if figure == "figure_6":
            plot: Plot = smp.KClAr3IsochronPlot
            x_title = f"<sup>38</sup>Ar<sub>Cl</sub>/<sup>39</sup>Ar<sub>K</sub>"
            y_title = f"<sup>40</sup>Ar/<sup>39</sup>Ar<sub>K</sub>"

        xaxis: Plot.Axis = plot.xaxis
        yaxis: Plot.Axis = plot.yaxis
        set1: Plot.Set = plot.set1
        set2: Plot.Set = plot.set2
        age_results = smp.Info.results.isochron[figure]
        xaxis_min = float(xaxis.min)
        xaxis_max = float(xaxis.max)
        yaxis_min = float(yaxis.min)
        yaxis_max = float(yaxis.max)

        plot_scale = (xaxis_min, xaxis_max, yaxis_min, yaxis_max)
        colors = [colors_map['red'], 'color']

        # create a canvas
        cv = pm.Canvas(width=17, height=12, unit="cm", show_frame=True, clip_outside_plot_areas=False)
        # change frame outline style
        cv.show_frame(color="grey", line_width=0.5)
        pt = cv.add_plot_area(name="Plot1", plot_area=(0.15, 0.15, 0.8, 0.8), plot_scale=plot_scale, show_frame=True)

        # isochron scatters
        data = arr.transpose(plot.data)
        colors = [
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set1.color)),
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set2.color)),
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set3.color)),
        ]
        stroke_colors = [
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set1.border_color)),
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set2.border_color)),
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.set3.border_color))
        ]
        for (x, sx, y, sy, r, i) in data:
            if (i - 1) in set1.data:
                pt.scatter(x, y, stroke_color=stroke_colors[0], fill_color=colors[0], line_width=int(float(plot.set1.border_width) / 2),
                           size=int(float(plot.set1.symbol_size) / 3), z_index=10)
            elif (i - 1) in set2.data:
                pt.scatter(x, y, stroke_color=stroke_colors[1], fill_color=colors[1], line_width=int(float(plot.set2.border_width) / 2),
                           size=int(float(plot.set2.symbol_size) / 3), z_index=10)
            else:
                pt.scatter(x, y, stroke_color=stroke_colors[2], fill_color=colors[2], line_width=int(float(plot.set3.border_width) / 2),
                           size=int(float(plot.set3.symbol_size) / 3), z_index=10)

        # split sticks
        # xaxis.interval = (xaxis_max - xaxis_min) / xaxis.split_number
        # yaxis.interval = (yaxis_max - yaxis_min) / yaxis.split_number
        for i in range(xaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = (end[0], start[1] - 5)
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=100)
                pt.text(x=start[0], y=end[1] - 15, clip=False, coordinate="pt", h_align="middle",
                        text=f"{Decimal(str(xaxis_min)) + Decimal(str(xaxis.interval)) * Decimal(str(i))}", z_index=150)
        for i in range(yaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = (start[0] - 5, end[1])
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=100)
                pt.text(x=end[0] - 5, y=end[1], clip=False, coordinate="pt", h_align="right", v_align="center",
                        text=f"{Decimal(str(yaxis_min)) + Decimal(str(yaxis.interval)) * Decimal(str(i))}", z_index=150)

        # axis titles
        p = pt.scale_to_points((xaxis_max + xaxis_min) / 2, yaxis_min)
        pt.text(x=p[0], y=p[1] - 30, text=x_title, clip=False, coordinate="pt",
                h_align="middle", v_align="top", z_index=150)
        p = pt.scale_to_points(xaxis_min, (yaxis_max + yaxis_min) / 2)
        pt.text(x=p[0] - 50, y=p[1], text=y_title, clip=False, coordinate="pt",
                h_align="middle", v_align="bottom", rotate=90, z_index=150)

        # inside text
        colors = [self.color_rgb_normalized(self.color_hex_to_rgb(plot.line1.color)),
                  self.color_rgb_normalized(self.color_hex_to_rgb(plot.line2.color))]
        widths = [int(float(plot.line1.line_width) / 2), int(float(plot.line2.line_width) / 2)]
        styles = [plot.line1.line_type, plot.line2.line_type]
        for index, data in enumerate([plot.line1.data, plot.line2.data]):
            # isochron line
            try:
                pt.line(start=data[0], end=data[1], clip=True, color=colors[index],
                        width=widths[index], line_style=styles[index], line_caps='square', z_index=50)
            except IndexError:
                pass
            if data != []:
                if index == 0:
                    pos = [round(i / 100, 2) for i in plot.text1.pos]
                    color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.text1.color))
                elif index == 1:
                    pos = [round(i / 100, 2) for i in plot.text2.pos]
                    color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.text2.color))
                else:
                    pos = (0.6, 0.7)
                    color = "black"
                age, sage = round(age_results[index]['age'], 2), round(age_results[index]['s2'], 2)
                F, sF = round(age_results[index]['F'], 2), round(age_results[index]['sF'], 2)
                R0, sR0 = round(age_results[index]['initial'], 2), round(age_results[index]['sinitial'], 2)
                MSWD, R2 = round(age_results[index]['MSWD'], 2), round(age_results[index]['R2'], 4)
                Chisq, p = round(age_results[index]['Chisq'], 2), round(age_results[index]['Pvalue'], 2)
                pt.text(x=(xaxis_max - xaxis_min) * pos[0] + xaxis_min,
                        y=(yaxis_max - yaxis_min) * pos[1] + yaxis_min,
                        text=f"Age ={age} {chr(0xb1)} {sage} Ma<r>F = {F} {chr(0xb1)} {sF}<r>"
                             f"R<sub>0</sub> = {R0} {chr(0xb1)} {sR0}<r>"
                             f"{MSWD = }, r<sup>2</sup> = {R2}<r>"
                             f"{Chisq = }, {p = }",
                        size=10, clip=True, coordinate="scale", h_align="left", v_align="bottom",
                        color=color, rotate=0, z_index=150)
        return cv

    def plot_spectra(self, smp: Sample = None, figure: str = "figure_1"):
        if smp is None:
            smp = self.sample

        x_title = f""
        y_title = f""
        if figure == "figure_1":
            plot: Plot = smp.AgeSpectraPlot
            x_title = f"Cumulative <sup>39</sup>Ar Released (%)"
            y_title = f"Apparent Age (Ma)"
        else:
            return

        xaxis: Plot.Axis = plot.xaxis
        yaxis: Plot.Axis = plot.yaxis
        set1: Plot.Set = plot.set1
        set2: Plot.Set = plot.set2
        # age_results = smp.Info.results.age_spectra
        age_results = smp.Info.results.age_plateau
        xaxis_min = float(xaxis.min)
        xaxis_max = float(xaxis.max)
        yaxis_min = float(yaxis.min)
        yaxis_max = float(yaxis.max)

        plot_scale = (xaxis_min, xaxis_max, yaxis_min, yaxis_max)

        # create a canvas
        cv = pm.Canvas(width=17, height=12, unit="cm", show_frame=True, clip_outside_plot_areas=False)
        # change frame outline style
        cv.show_frame(color="grey", line_width=0.5)
        pt = cv.add_plot_area(name="Plot1", plot_area=(0.15, 0.15, 0.8, 0.8), plot_scale=plot_scale, show_frame=True)

        # spectra lines
        data = plot.data
        colors = [
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.line1.color)),
            self.color_rgb_normalized(self.color_hex_to_rgb(plot.line2.color)),
        ]
        widths = [int(float(plot.line1.line_width) / 2), int(float(plot.line2.line_width) / 2)]
        styles = [plot.line1.line_type, plot.line2.line_type]
        for index in range(len(data) - 1):
            pt.line(start=(data[index][0], data[index][1]), end=(data[index + 1][0], data[index + 1][1]),
                    width=widths[0], line_style=styles[0], color=colors[0],
                    clip=True, line_caps="none", z_index=9)
            pt.line(start=(data[index][0], data[index][2]), end=(data[index + 1][0], data[index + 1][2]),
                    width=widths[1], line_style=styles[1], color=colors[1],
                    clip=True, line_caps="none", z_index=9)

        colors = [
            [self.color_rgb_normalized(self.color_hex_to_rgb(plot.line3.color)),
             self.color_rgb_normalized(self.color_hex_to_rgb(plot.line4.color))],
            [self.color_rgb_normalized(self.color_hex_to_rgb(plot.line5.color)),
             self.color_rgb_normalized(self.color_hex_to_rgb(plot.line6.color))]
        ]
        widths = [
            [int(float(plot.line3.line_width) / 2), int(float(plot.line4.line_width) / 2)],
            [int(float(plot.line5.line_width) / 2), int(float(plot.line6.line_width) / 2)]
        ]
        styles = [[plot.line3.line_type, plot.line4.line_type], [plot.line5.line_type, plot.line6.line_type]]
        for index, data in enumerate([plot.set1.data, plot.set2.data]):
            if not data:
                continue
            for i in range(len(data) - 1):
                pt.line(start=(data[i][0], data[i][1]), end=(data[i + 1][0], data[i + 1][1]),
                        width=widths[index][0], line_style=styles[index][0], color=colors[index][0],
                        clip=True, line_caps="square", z_index=99)
                pt.line(start=(data[i][0], data[i][2]), end=(data[i + 1][0], data[i + 1][2]),
                        width=widths[index][1], line_style=styles[index][1], color=colors[index][1],
                        clip=True, line_caps="square", z_index=99)
            if index == 0:
                pos = [round(i / 100, 2) for i in plot.text1.pos]
                color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.text1.color))
            elif index == 1:
                pos = [round(i / 100, 2) for i in plot.text2.pos]
                color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.text2.color))
            else:
                pos = (0.6, 0.7)
                color = "black"
            age, sage = round(age_results[index]['age'], 2), round(age_results[index]['s2'], 2)
            F, sF = round(age_results[index]['F'], 2), round(age_results[index]['sF'], 2)
            Num = int(age_results[index]['Num'])
            MSWD, Ar39 = round(age_results[index]['MSWD'], 2), round(age_results[index]['Ar39'], 2)
            Chisq, Pvalue = round(age_results[index]['Chisq'], 2), round(age_results[index]['Pvalue'], 2)
            pt.text(x=(xaxis_max - xaxis_min) * pos[0] + xaxis_min,
                    y=(yaxis_max - yaxis_min) * pos[1] + yaxis_min,
                    text=f"Age ={age} {chr(0xb1)} {sage} Ma<r>WMF = {F} {chr(0xb1)} {sF}, n = {Num}<r>"
                         f"MSWD = {MSWD}, <sup>39</sup>Ar = {Ar39}%<r>"
                         f"Chisq = {Chisq}, p = {Pvalue}",
                    size=10, clip=True, coordinate="scale", h_align="middle", v_align="center",
                    color=color, rotate=0, z_index=150)

        # split sticks
        for i in range(xaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = (end[0], start[1] - 5)
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=100)
                pt.text(x=start[0], y=end[1] - 15, text=f"{xaxis_min + xaxis.interval * i}", clip=False,
                        coordinate="pt", h_align="middle", z_index=150)
        for i in range(yaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = (start[0] - 5, end[1])
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=100)
                pt.text(x=end[0] - 5, y=end[1], text=f"{yaxis_min + yaxis.interval * i}", clip=False,
                        coordinate="pt", h_align="right", v_align="center", z_index=150)

        # axis titles
        p = pt.scale_to_points((xaxis_max + xaxis_min) / 2, yaxis_min)
        pt.text(x=p[0], y=p[1] - 30, text=x_title, clip=False, coordinate="pt",
                h_align="middle", v_align="top", z_index=150)
        p = pt.scale_to_points(xaxis_min, (yaxis_max + yaxis_min) / 2)
        pt.text(x=p[0] - 50, y=p[1], text=y_title, clip=False, coordinate="pt",
                h_align="middle", v_align="bottom", rotate=90, z_index=150)

        return cv

    def plot_degas(self, smp: Sample = None, figure: str = 'figure_8'):        # create a canvas
        if smp is None:
            smp = self.sample
        if figure != "figure_8":
            raise ValueError

        x_title = f""
        y_title = f""

        plot: Plot = smp.DegasPatternPlot
        title = plot.title.text
        xaxis: Plot.Axis = plot.xaxis
        yaxis: Plot.Axis = plot.yaxis
        x_title = xaxis.title.text
        y_title = yaxis.title.text
        xaxis_min = float(xaxis.min)
        xaxis_max = float(xaxis.max) + 2
        yaxis_min = float(yaxis.min)
        yaxis_max = float(yaxis.max)
        plot_scale = (xaxis_min, xaxis_max, yaxis_min, yaxis_max)

        # data
        data = plot.data  # 36a, 37ca, 38cl, 39k, 40r, 36, 37, 38, 39, 40

        # create a canvas
        cv = pm.Canvas(width=17, height=12, unit="cm", show_frame=True, clip_outside_plot_areas=False)
        # change frame outline style
        cv.show_frame(color="grey", line_width=0.5)
        pt = cv.add_plot_area(name="Plot1", plot_area=(0.15, 0.15, 0.8, 0.8), plot_scale=plot_scale, show_frame=True)

        COLOR_MAP_1: list = [
            # 3399FF, 33FF99, CCCC00, FF6666,
            [0.200, 0.600, 1.000], [0.200, 1.000, 0.600], [0.800, 0.800, 0.000], [1.000, 0.400, 0.400],
            # 00FFFF, 00994C, FF8000, 7F00FF
            [0.000, 1.000, 1.000], [0.000, 0.600, 0.298], [1.000, 0.502, 0.000], [0.498, 0.000, 1.000],
            # 3333FF, FF3399
            [1.000, 0.200, 0.600], [0.200, 0.200, 1.000],
        ]

        # spectra lines
        data = plot.data
        for i, isotope in enumerate(data):
            color = COLOR_MAP_1[i]
            for index, point in enumerate(isotope):
                # plot scatter pints
                pt.scatter(index + 1, point, fill_color="white", stroke_color=color, size=2)
                if index != 0:
                    pt.line(start=(index, isotope[index - 1]), end=(index + 1, point), clip=True, width=1, color=color)

        # split sticks
        for i in range(xaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = (end[0], start[1] - 5)
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt")
                pt.text(x=start[0], y=end[1] - 15, text=f"{int(xaxis_min + xaxis.interval * i)}", clip=False,
                        coordinate="pt", h_align="middle")
        for i in range(yaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = (start[0] - 5, end[1])
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt")
                pt.text(x=end[0] - 5, y=end[1], text=f"{yaxis_min + yaxis.interval * i}", clip=False,
                        coordinate="pt", h_align="right", v_align="center")

        # axis titles
        p = pt.scale_to_points((xaxis_max + xaxis_min) / 2, yaxis_min)
        pt.text(x=p[0], y=p[1] - 30, text=x_title, clip=False, coordinate="pt", h_align="middle", v_align="top")
        p = pt.scale_to_points(xaxis_min, (yaxis_max + yaxis_min) / 2)
        pt.text(x=p[0] - 50, y=p[1], text=y_title, clip=False, coordinate="pt",
                h_align="middle", v_align="bottom", rotate=90)

        return cv

    def plot_age_distribution(self, smp: Sample = None, figure: str = 'figure_9'):
        if smp is None:
            smp = self.sample
        if figure != "figure_9":
            raise ValueError

        plot: Plot = smp.AgeDistributionPlot
        title = plot.title.text
        xaxis: Plot.Axis = plot.xaxis
        yaxis: Plot.Axis = plot.yaxis
        x_title = f"<sup>40</sup>Ar/<sup>39</sup>Ar Age (Ma)"
        y_title = yaxis.title.text
        xaxis_min = float(xaxis.min)
        xaxis_max = float(xaxis.max)
        yaxis_min = float(yaxis.min)
        yaxis_max = float(yaxis.max)
        plot_scale = (xaxis_min, xaxis_max, yaxis_min, yaxis_max)

        cv = pm.Canvas(width=17, height=12, unit="cm", show_frame=True, clip_outside_plot_areas=False)
        # change frame outline style
        cv.show_frame(color="grey", line_width=0.5)
        pt = cv.add_plot_area(name="Plot1", plot_area=(0.15, 0.15, 0.8, 0.8), plot_scale=plot_scale, show_frame=True)

        # histogram
        color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.set1.border_color))
        fill_color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.set1.color))
        for i in range(plot.set1.bin_count):
            pt.rect(left_bottom=[plot.set1.data[2][i][0], 0], width=plot.set1.bin_width, height=plot.set1.data[1][i],
                    line_width=0, color=fill_color, fill_color=fill_color, fill=True, coordinate='scale', z_index=0)
            pt.line(start=[plot.set1.data[2][i][0], 0], end=[plot.set1.data[2][i][0], plot.set1.data[1][i]],
                    color=color, line_style=plot.set1.border_type, width=plot.set1.border_width,
                    coordinate='scale', z_index=1)
            pt.line(start=[plot.set1.data[2][i][0], plot.set1.data[1][i]],
                    end=[plot.set1.data[2][i][0] + plot.set1.bin_width, plot.set1.data[1][i]],
                    color=color, line_style=plot.set1.border_type, width=plot.set1.border_width,
                    coordinate='scale', z_index=1)
            pt.line(start=[plot.set1.data[2][i][0] + plot.set1.bin_width, plot.set1.data[1][i]],
                    end=[plot.set1.data[2][i][0] + plot.set1.bin_width, 0],
                    color=color, line_style=plot.set1.border_type, width=plot.set1.border_width,
                    coordinate='scale', z_index=1)

        # KDE
        scale = max(plot.set1.data[1]) / max(plot.set2.data[1])
        color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.set2.color))
        for i in range(plot.set2.band_points):
            pt.line(start=[plot.set2.data[0][i], plot.set2.data[1][i] * scale],
                    end=[plot.set2.data[0][i + 1], plot.set2.data[1][i + 1] * scale],
                    color=color, line_style=plot.set2.line_type, width=plot.set2.line_width,
                    coordinate='scale', z_index=5)

        # age bars
        ages = sorted(zip(*plot.set3.data), key=lambda x: x[0])
        color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.set3.color))
        fill_color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.set3.border_color))
        ppu_y = pt.ppu("y")
        height = float(plot.set3.bar_height) / ppu_y
        interval = float(plot.set3.bar_interval) / ppu_y if plot.set3.vertical_align == "bottom" else ((yaxis_max - yaxis_min) - height * len(ages)) / (len(ages) + 1)
        for index, age in enumerate(ages):
            pt.rect(left_bottom=[age[0] - age[1], interval + index * (interval + height)],
                    width=age[1] * 2, height=height, color=color, fill_color=fill_color, fill=True,
                    line_width=plot.set3.border_width, coordinate='scale', z_index=1)

        pos = [round(i / 100, 2) for i in plot.text1.pos]
        color = self.color_rgb_normalized(self.color_hex_to_rgb(plot.text1.color))
        text = plot.text1.text.replace('\n', '<r>')
        pt.text(x=(xaxis_max - xaxis_min) * pos[0] + xaxis_min,
                y=(yaxis_max - yaxis_min) * pos[1] + yaxis_min,
                text=text, size=10, clip=True, coordinate="scale", color=color,
                h_align="middle", v_align="center", rotate=0, z_index=100)

        # split sticks
        for i in range(xaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = pt.scale_to_points(xaxis_min + xaxis.interval * i, yaxis_min)
            end = (end[0], start[1] - 5)
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=50)
                pt.text(x=start[0], y=end[1] - 15, text=f"{int(xaxis_min + xaxis.interval * i)}", clip=False,
                        coordinate="pt", h_align="middle", z_index=100)
        for i in range(yaxis.split_number + 1):
            start = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = pt.scale_to_points(xaxis_min, yaxis_min + yaxis.interval * i)
            end = (start[0] - 5, end[1])
            if not pt.is_out_side(*start):
                pt.line(start=start, end=end, width=1, line_style="solid", clip=False, coordinate="pt", z_index=50)
                pt.text(x=end[0] - 5, y=end[1], text=f"{yaxis_min + yaxis.interval * i}", clip=False,
                        coordinate="pt", h_align="right", v_align="center", z_index=100)

        # axis titles
        p = pt.scale_to_points((xaxis_max + xaxis_min) / 2, yaxis_min)
        pt.text(x=p[0], y=p[1] - 30, text=x_title, clip=False, coordinate="pt",
                h_align="middle", v_align="top", z_index=150)
        p = pt.scale_to_points(xaxis_min, (yaxis_max + yaxis_min) / 2)
        pt.text(x=p[0] - 50, y=p[1], text=y_title, clip=False, coordinate="pt",
                h_align="middle", v_align="bottom", rotate=90, z_index=150)

        return cv


class CustomUnpickler(pickle.Unpickler):
    """https://blog.csdn.net/weixin_43236007/article/details/109506191"""

    def find_class(self, module, name):
        try:
            return super().find_class(__name__, name)
        except AttributeError:
            return super().find_class(module, name)