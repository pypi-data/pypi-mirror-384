#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - smp - initial
# ==========================================
#
#
#
"""
import os
import pickle
import uuid
import pandas as pd
import numpy as np
import copy
from typing import List, Union, Optional
from ..calc import arr, err
from ..files import calc_file
from . import (sample as samples, basic, table, raw as smp_raw)

Sample = samples.Sample
Table = samples.Table
Plot = samples.Plot
RawData = samples.RawData
Sequence = samples.Sequence
ArArBasic = samples.ArArBasic

plateau_res_keys = [
    'F', 'sF', 'Num', 'MSWD', 'Chisq', 'Pvalue', 'age', 's1', 's2', 's3', 'Ar39',
    'rs',  # 'rs' means relative error of the total sum
]
PLATEAU_RES = dict(zip(plateau_res_keys, [np.nan for i in plateau_res_keys]))
iso_res_keys = [
    'k', 'sk', 'm1', 'sm1',
    'MSWD', 'abs_conv', 'iter', 'mag', 'R2', 'Chisq', 'Pvalue',
    'rs',  # 'rs' means relative error of the total sum
    'age', 's1', 's2', 's3',
    'conv', 'initial', 'sinitial', 'F', 'sF',
]
ISO_RES = dict(zip(
    iso_res_keys, [np.nan for i in iso_res_keys])
)
spectra_res_keys = [
    'F', 'sF', 'Num', 'MSWD', 'Chisq', 'Pvalue', 'age', 's1', 's2', 's3', 'Ar39',
    'rs',  # 'rs' means relative error of the total sum
]
SPECTRA_RES = dict(zip(
    spectra_res_keys, [np.nan for i in spectra_res_keys])
)
preference_keys = [
    'decimalPlaces', 'toPrecision', 'confidenceLevel', 'ageUnit'
]
PREFERENCE_RES = dict(zip(
    preference_keys, [6, 'fixed', 1, 'Ma'])
)


# create sample instance
def create_sample_from_df(content: pd.DataFrame, smp_info: dict):
    """

    Parameters
    ----------
    content : [
            sample_values, blank_values, corrected_values, degas_values, publish_values,
            apparent_age_values, isochron_values, total_param, sample_info, isochron_mark,
            sequence_name, sequence_value
        ]
    smp_info : dict

    Returns
    -------
    Sample instance
    """
    content_dict = content.to_dict('list')
    res = dict(zip([key[0] for key in content_dict.keys()], arr.create_arr((len(content_dict), 0))))
    for key, val in content_dict.items():
        res[key[0]] = res[key[0]] + [val]

    return create_sample_from_dict(content=res, smp_info=smp_info)


def create_sample_from_dict(content: dict, smp_info: dict):
    """
    content:
        {
            'smp': [], 'blk': [], 'cor': [], 'deg': [], 'pub': [],
            'age': [], 'iso': [], 'pam': [], 'mak': [], 'seq': [],
            'seq': []
        }
    return sample instance
    """
    # Create sample file
    smp = Sample()
    # Initializing
    initial(smp)
    smp.SampleIntercept = content['smp']
    smp.BlankIntercept = content['blk']
    smp.CorrectedValues = content['cor']
    smp.DegasValues = content['deg']
    smp.PublishValues = content['pub']
    smp.ApparentAgeValues = content['age']
    smp.IsochronValues = content['iso']
    smp.TotalParam = content['pam']
    smp.IsochronMark = content['mak'][0]
    smp.SequenceName = content['seq'][0]
    smp.SequenceValue = content['seq'][1]

    smp.Info = basic.update_plot_from_dict(smp.Info, smp_info)

    smp.SelectedSequence1 = [index for index, item in enumerate(smp.IsochronMark) if item == 1 or item == '1']
    smp.SelectedSequence2 = [index for index, item in enumerate(smp.IsochronMark) if item == 2 or item == '2']
    smp.UnselectedSequence = [index for index, item in enumerate(smp.IsochronMark) if item not in [1, 2, '1', '2']]
    #
    smp.Info.results.selection[0]['data'] = smp.SelectedSequence1
    smp.Info.results.selection[1]['data'] = smp.SelectedSequence2
    smp.Info.results.selection[2]['data'] = smp.UnselectedSequence

    return smp


def initial(smp: Sample):
    # 已更新 2023/7/4
    smp.TotalParam = arr.create_arr((len(samples.TOTAL_PARAMS_HEADERS) - 3, 0))
    smp.BlankIntercept = arr.create_arr((len(samples.BLANK_INTERCEPT_HEADERS) - 3, 0))
    smp.SampleIntercept = arr.create_arr((len(samples.SAMPLE_INTERCEPT_HEADERS) - 3, 0))
    smp.PublishValues = arr.create_arr((len(samples.PUBLISH_TABLE_HEADERS) - 3, 0))
    smp.DecayCorrected = arr.create_arr((10, 0))
    smp.CorrectedValues = arr.create_arr((len(samples.CORRECTED_HEADERS) - 3, 0))
    smp.DegasValues = arr.create_arr((len(samples.DEGAS_HEADERS) - 3, 0))
    smp.ApparentAgeValues = arr.create_arr((len(samples.SPECTRUM_TABLE_HEADERS) - 3, 0))
    smp.IsochronValues = arr.create_arr((len(samples.ISOCHRON_TABLE_HEADERS) - 3, 0))

    # Doi
    if not hasattr(smp, 'Doi') or getattr(smp, 'Doi') in (None, ""):
        setattr(smp, 'Doi', str(uuid.uuid4().hex))

    # Info
    setattr(smp, 'Info', ArArBasic(
        id='0', name='info', attr_name='Info', arr_version=samples.VERSION,
        sample=ArArBasic(
            name='SAMPLE NAME', material='MATERIAL', location='LOCATION', type='Unknown', method='',
            sequence_unit='', weight=''
        ),
        researcher=ArArBasic(
            name='RESEARCHER', addr='ADDRESS', email='EMAIL'
        ),
        laboratory=ArArBasic(
            name='LABORATORY', addr='ADDRESS', email='EMAIL', info='INFORMATION', analyst='ANALYST'
        ),
        results=ArArBasic(
            name='RESULTS', plateau_F=[], plateau_age=[], total_F=[], total_age=[],
            isochron_F=[], isochron_age=[], J=[],
            # set1=result_set_1, set2=result_set_2,
            isochron={
                'figure_2': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
                'figure_3': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
                'figure_4': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
                'figure_5': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
                'figure_6': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
                'figure_7': {
                    0: copy.deepcopy(ISO_RES), 1: copy.deepcopy(ISO_RES), 2: copy.deepcopy(ISO_RES)},
            },
            age_plateau={
                0: copy.deepcopy(PLATEAU_RES), 1: copy.deepcopy(PLATEAU_RES), 2: copy.deepcopy(PLATEAU_RES)},
            age_spectra={
                'TGA': copy.deepcopy(SPECTRA_RES),
                0: copy.deepcopy(SPECTRA_RES), 1: copy.deepcopy(SPECTRA_RES), 2: copy.deepcopy(SPECTRA_RES),
            },
            selection={
                0: {'data': [], 'name': 'set1'},
                1: {'data': [], 'name': 'set2'},
                2: {'data': [], 'name': 'set3'}
            }
        ),
        reference=ArArBasic(
            name='REFERENCE', journal='JOURNAL', doi='DOI'
        ),
        preference=copy.deepcopy(PREFERENCE_RES),
        experiment=ArArBasic(
            name='', mass_spec='', collectors='', step_num=0
        ),
    ))

    decimal_places = PREFERENCE_RES['decimalPlaces']
    # Plots and Tables
    setattr(smp, 'UnknownTable', Table(
        id='1', name='Unknown', header=samples.SAMPLE_INTERCEPT_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 20))
    ))
    setattr(smp, 'BlankTable', Table(
        id='2', name='Blank', header=samples.BLANK_INTERCEPT_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 20))
    ))
    setattr(smp, 'CorrectedTable', Table(
        id='3', name='Corrected', header=samples.CORRECTED_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 35))
    ))
    setattr(smp, 'DegasPatternTable', Table(
        id='4', name='Degas Pattern', header=samples.DEGAS_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 35))
    ))
    setattr(smp, 'PublishTable', Table(
        id='5', name='Publish', header=samples.PUBLISH_TABLE_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 20))
    ))
    setattr(smp, 'AgeSpectraTable', Table(
        id='6', name='Age Spectra', header=samples.SPECTRUM_TABLE_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2],
        # numeric_indexes=list(range(1, 26))
    ))
    setattr(smp, 'IsochronsTable', Table(
        id='7', name='Isochrons', header=samples.ISOCHRON_TABLE_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2, 8, 14, 20, 26, 32],
        # numeric_indexes=[1, *list(range(3, 42))]
    ))
    setattr(smp, 'TotalParamsTable', Table(
        id='8', name='Total Params', header=samples.TOTAL_PARAMS_HEADERS, decimal_places=decimal_places,
        text_indexes=[0, 1, 2, 29, 30, 32, 33, 60, 99, *list(range(100, 115))],
        # numeric_indexes=list(range(1, 120)),
    ))

    initial_plot_styles(smp)

    return smp


def initial_plot_styles(smp: Sample, except_attrs=None):
    """
    Initialize plot components styles based on Default Styles. Except attrs is a list containing attrs
    that are not expected to be initialized.
    Judgment order:
        1. The attr name is in except attrs and the sample has this attr: skip
        2. The value is not a dict instance: setattr()
        3. The sample has attr and it is a Set/Label/Text/Axis instance: iteration
    """

    if except_attrs is None:
        except_attrs = []

    def set_attr(obj, name, value):
        if name in except_attrs and hasattr(obj, name):
            pass
        elif not isinstance(value, dict):
            setattr(obj, name, value)
        else:
            if not (hasattr(obj, name) and isinstance(getattr(obj, name), Plot.BasicAttr)):
                setattr(obj, name, getattr(Plot, value['type'].capitalize())())
            for k, v in value.items():
                set_attr(getattr(obj, name), k, v)

    default_styles = get_default_plot_style(smp)
    for figure_index, figure_attr in default_styles.items():
        plot = getattr(smp, figure_attr['attr_name'], Plot())
        for key, attr in figure_attr.items():
            set_attr(plot, key, attr)


def get_default_plot_style(smp: Sample):
    sample_type = smp.Info.sample.type
    try:
        age_unit = str(smp.Info.preference['ageUnit']).capitalize()
    except:
        age_unit = "Undefined"
    return copy.deepcopy(samples.DEFAULT_PLOT_STYLES(sample_type, age_unit))


def re_set_smp(smp: Sample):
    std = initial(Sample())
    basic.get_merged_smp(smp, std)
    return check_version(smp)


def check_version(smp: Sample):
    """

    Parameters
    ----------
    smp

    Returns
    -------

    """
    if smp.version != samples.VERSION:
        std = initial(Sample())
        basic.get_merged_smp(smp, std)

    try:
        version = int(smp.version)
    except ValueError:
        return smp

    # 20250328:  # Experiment info
    smp.Info.experiment.name = smp.name()
    smp.Info.experiment.step_num = smp.sequence().size

    # old version: add masses and gain factors
    if version < 20240730:
        gains = np.ones([10, smp.Info.experiment.step_num])
        gains[[1, 3, 5, 7, 9], :] = 0
        smp.TotalParam[126:136] = gains.tolist()
        gains[0] = 35.96754628
        gains[2] = 36.9667759
        gains[4] = 37.9627322
        gains[6] = 38.964313
        gains[8] = 39.962383123
        smp.TotalParam[71:81] = gains.tolist()
        smp.version = "20240730"

    # 20250404:  # Normalization for steps with different J values
    doNormalize = True
    v, sv = [], []
    try:
        if smp.Info.sample.type.lower() == "unknown":
            v, sv = smp.TotalParam[67:69]
            sv = np.multiply(v, sv) / 100
        elif smp.Info.sample.type.lower() == "air":
            v, sv = smp.TotalParam[93:95]
            sv = np.multiply(v, sv) / 100
        elif smp.Info.sample.type.lower() == "standard":
            v, sv = smp.TotalParam[59:61]
    except:
        doNormalize = False
    smp.TotalParam[136:138] = [
        [1 if v[0] == each or not doNormalize else v[0] / each for each in v],
        [0 if v[0] == v[i] or not doNormalize else err.div((v[0], sv[0]), (v[i], sv[i])) for i in range(len(v))]
    ]

    # 20251001:  # add marks for every table
    smp = smp.recalculate(re_set_table=True, re_table_style=True)
    return smp


# create
def from_empty(file_path: str = '', sample_name: str = None):
    """
    Parameters
    ----------
    file_path
    sample_name

    Returns
    -------

    """
    sample = Sample()
    # initial settings
    initial(sample)
    if sample_name is not None:
        sample.Info.sample.name = sample_name
    return sample


# create
def from_arr_files(file_path, sample_name: str = ""):
    """
    file_path: full path of input file
    name： samplename
    return sample instance
    """

    class RenameUnpickler(pickle.Unpickler):
        def find_class(self, module: str, name: str):
            SAMPLE_MODULE = Sample().__module__
            renamed_module = module
            if '.sample' in module and module != SAMPLE_MODULE:
                renamed_module = SAMPLE_MODULE
            try:
                return super(RenameUnpickler, self).find_class(renamed_module, name)
            except AttributeError:
                return super(RenameUnpickler, self).find_class(renamed_module, 'ArArBasic')

    def renamed_load(file_obj):
        return RenameUnpickler(file_obj).load()

    with open(file_path, 'rb') as f:
        sample = renamed_load(f)
    # Check arr version
    # recalculation will not be applied automatically
    return check_version(sample)


# create
def from_calc_files(file_path: str, **kwargs):
    """

    Parameters
    ----------
    file_path

    Returns
    -------

    """
    file = calc_file.ArArCalcFile(file_path=file_path, **kwargs).open()
    sample = create_sample_from_df(file.get_content(), file.get_smp_info())
    return check_version(sample)


# create
def from_full_files(file_path: str, sample_name: str = None):
    """
    Parameters
    ----------
    file_path
    sample_name

    Returns
    -------

    """
    if sample_name is None:
        sample_name = str(os.path.split(file_path)[-1]).split('.')[0]
    content, sample_info = calc_file.open_full_xls(file_path, sample_name)
    sample = create_sample_from_dict(content=content, smp_info=sample_info)
    return check_version(sample)


# create
def from_raw_files(file_path: Union[str, List[str]], input_filter_path: Union[str, List[str]],
                   mapping: Optional[List[dict]] = None) -> Sample:
    raw = smp_raw.to_raw(file_path, input_filter_path)
    raw.do_regression()
    return from_raw_data(raw, mapping)


def from_raw_data(raw: RawData, mapping: Optional[List[dict]] = None) -> Sample:
    """
    Parameters
    ----------
    raw
    mapping :
        mapping is a list of dictionaries with two keys of blank and unknown,
        for example, mapping = [
            {'blank': blank_name, 'unknown': unknown_name_1},
            ...,
            {'blank': blank_name, 'unknown': unknown_name_1}
        ]

    Returns
    -------

    """
    if mapping is None:
        mapping = []
        _b: Sequence = raw.get_sequence(index=True, flag='is_blank', unique=True)
        for _index, _seq in enumerate(raw.sequence):
            if _seq.is_blank():
                _b = _seq
                continue
            else:
                mapping.append({'unknown': _seq.name, 'blank': _b.name})

    # 创建sample
    sample = Sample()
    sample.RawData = raw
    initial(sample)
    unknown_intercept, blank_intercept = [], []
    for row in mapping:
        row_unknown_intercept = []
        row_blank_intercept = []

        unknown: Sequence = raw.get_sequence(row['unknown'], flag='name')
        if row['blank'].lower() == "Interpolated Blank".lower():
            blank: Sequence = arr.filter(
                raw.interpolated_blank, func=lambda seq: seq.datetime == unknown.datetime,
                get=None, unique=True)
        else:
            blank: Sequence = raw.get_sequence(row['blank'], flag='name')
        for i in range(5):
            row_unknown_intercept = arr.multi_append(row_unknown_intercept, *unknown.results[i][int(unknown.fitting_method[i])][:2])
            row_blank_intercept = arr.multi_append(row_blank_intercept, *blank.results[i][int(blank.fitting_method[i])][:2])

        unknown_intercept.append(row_unknown_intercept)
        blank_intercept.append(row_blank_intercept)
        sample.SequenceName.append(unknown.name)
        sample.SequenceValue.append('')
        sample.TotalParam[31].append(unknown.datetime)

    sample.SampleIntercept = arr.transpose(unknown_intercept)
    sample.BlankIntercept = arr.transpose(blank_intercept)
    sample.UnselectedSequence = list(range(len(sample.SequenceName)))
    sample.SelectedSequence1 = []
    sample.SelectedSequence2 = []
    #
    sample.Info.results.selection[0]['data'] = sample.SelectedSequence1
    sample.Info.results.selection[1]['data'] = sample.SelectedSequence2
    sample.Info.results.selection[2]['data'] = sample.UnselectedSequence

    table.update_table_data(sample)  # Update table after submission row data and calculation

    # sample.TotalParam[31] = [raw.get_sequence(row['unknown'], flag='name').datetime for row in mapping]

    return check_version(sample)
