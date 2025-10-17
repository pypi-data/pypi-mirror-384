#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2024 Yang 
# webarar - EXPORT_TO_PDF_DATA_PROPERTIES
# ==========================================
#
#
# 
"""

def plot_data(data: dict):
    """

    Parameters
    ----------
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
                - nameLocation: string
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
                - fillColor: string or list
                    color for filling markers, format is similar to that of color
                - data: 2-dimensional array
                    [[x1, y1], [x2, y2], ...]

                optional:
                - lineCaps: string
                    for lines only, 'square', 'none', 'butt'
                - text: string
                    for texts only
                - size: int
                    for scatters only


    Returns
    -------

    """
    pass


data = {
    "data": [
        {
            'name': 'spectra',
            'xAxis': [{'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100],
                       'title': 'Cumulative <sup>39</sup>Ar Released (%)', 'title_location': 'middle', }],
            'yAxis': [{'extent': [0, 25], 'interval': [0, 5, 10, 15, 20, 25],
                       'title': 'Apparent Age (Ma)', 'title_location': 'middle', }],
            'series': [
                {
                    'type': 'text', 'id': f'text_0', 'name': f'text_0', 'color': '#222222',
                    'text': f'xxx<r>xxxxxx', 'size': 10,
                    'data': [[5, 23]],
                },
                {
                    'type': 'series.line', 'id': f'line_0', 'name': f'line_0',
                    'color': '#333333',
                    'data': [[]], 'line_caps': 'square',
                },
                {
                    'type': 'series.line', 'id': f'line_2', 'name': f'line_2',
                    'color': '#555555',
                    'data': [[]], 'line_caps': 'square',
                }
            ]
        }
    ],
    "file_name": "WHA"
}