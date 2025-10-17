#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#  Copyright (C) 2023 Yang. - All Rights Reserved

import os
import ararpy as ap

example_dir = os.path.join(os.path.dirname(ap.__file__), r'examples')
# example_dir = os.path.join(os.getcwd(), r'examples')

ap.test.test()

# sample = ap.from_empty()  # create new sample instance
# print(sample.show_data())
# # Sample Name:
# #
# # Doi:
# #     9a43b5c1a99747ee8608676ac31814da
# # Corrected Values:
# #     Empty DataFrame
# # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
# # Index: []
# # Parameters:
# #     Empty DataFrame
# # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
# #           20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
# #           40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
# #           60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
# #           80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, ...]
# # Index: []
# #
# # [0 rows x 123 columns]
# # Isochron Values:
# #     Empty DataFrame
# # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
# #           20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
# #           40, 41, 42, 43, 44, 45, 46]
# # Index: []
# # Apparent Ages:
# #     Empty DataFrame
# # Columns: [0, 1, 2, 3, 4, 5, 6, 7]
# # Index: []
# # Publish Table:
# #     Empty DataFrame
# # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# # Index: []
#
# file_path = os.path.join(example_dir, r'22WHA0433.arr')
# sample = ap.from_arr(file_path)
# # normal isochron age
# print(f"{sample.results().isochron.inverse.set1.age = }")
# # sample.results().isochron.inverse.set1.age = 163.10336210925516
# # check current data point selection
# print(f"{sample.sequence().mark.value}")
# # [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
# #  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
# print(f"{sample.sequence().mark.set1.index}")
# # [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
#
# # change data point selection
# sample.set_selection(10, 1)
# # check new data point selection
# print(f"{sample.sequence().mark.value}")
# # ['', '', '', '', '', '', '', '', '', '', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
# print(f"{sample.sequence().mark.set1.index}")
# # [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
# # recalculate
# sample.recalculate(re_plot=True)
# # check new results
# print(f"{sample.results().isochron.inverse.set1.age = }")
# # sample.results().isochron.inverse.set1.age = 164.57644271385772


""" Open ArArCalc .age files """
# file_path = os.path.join(example_dir, r'22WHA0433.age')
# # file_path = os.path.join(example_dir, r'20WHA0103.age')
# sample: ap.Sample = ap.from_age(file_path=file_path)
# print(sample.name())
# print(ap.smp.basic.get_dict_from_obj(sample.Info))
# print(ap.smp.basic.get_dict_from_obj(sample.results()))
#
# ap.smp.corr.monte_carlo_f(sample)

# """ Open ArArCalc .full.xls files """
# file_path = os.path.join(example_dir, r'22WHA0433.full.xls')
# sample = ap.from_full(file_path=file_path)
# print(sample.name())
# print(ap.smp.basic.get_dict_from_obj(sample.Info))
#
# """ Open .arr files """
# file_path = os.path.join(example_dir, r'22WHA0433.arr')
# sample = ap.from_arr(file_path=file_path)
# print(sample.name())
# print(ap.smp.basic.get_dict_from_obj(sample.Info))
#
# # might not correct, because in this way the split numbers and the splits are not calculated correclty.
# # With WebArAr, due to the auto calculation by Echart this issue doesn't exist.
# sample.to_pdf(file_path="myFigure.pdf", figure="figure_3")

""" Open raw files """
# file_path = os.path.join(example_dir, r'22WHA0078.xls')
# input_filter_path = os.path.join(example_dir, r'Qtegra-exported-xls.input-filter')
# file_path = os.path.join(example_dir, r'24WHN0001-51-592.XLS')
# input_filter_path = os.path.join(example_dir, r'NGX-XLS.input-filter')

# sample = ap.from_raw(file_path, input_filter_path)
# print(sample.name())
# print(sample.parameters().to_df())
#
# # set info
# info = {
#     'sample': {'name': '22WHA0078', 'material': 'muscovite', 'location': 'China'},
#     'researcher': {'name': 'Yang'},
#     'laboratory': {'name': 'VU Ar lab', 'info': '', 'analyst': 'Yang'}
# }
# sample.set_info(info=info)
# # set calc parameters
# calc_params_file_path = os.path.join(example_dir, r'ArAr.calc')
# irra_params_file_path = os.path.join(example_dir, r'WH01.irra')
# # param = ap.files.basic.read(calc_params_file_path)
#
# sample.set_params(calc_params_file_path)
# sample.set_params(irra_params_file_path)
#
# print(sample.name())
# print(sample.parameters().to_df())


# """ progress """
# print(sample.sequence().mark.set1.index)
# print(sample.results().isochron.normal.set1.age)
# print(sample.results().age_plateau.set1.age)
# sample.set_selection(8, 1)
# print(sample.sequence().mark.set1.index)
# print(sample.results().isochron.normal.set1.age)
# print(sample.results().age_plateau.set1.age)
# sample.plot_normal()
# sample.plot_inverse()
# sample.plot_age_plateau()
# print(sample.sequence().mark.set1.index)
# print(sample.results().isochron.normal.set1.age)
# print(sample.results().age_plateau.set1.age)
# print(sample.help)
