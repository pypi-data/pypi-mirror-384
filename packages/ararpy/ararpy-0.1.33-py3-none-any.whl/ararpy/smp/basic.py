#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - smp - basic
# ==========================================
#
#
#
"""
# === Internal imports ===
import os
import re
import traceback
import pandas as pd
import numpy as np
import copy
from typing import Optional, Union, List
from .. import calc
from ..files.basic import (read as read_params)
from .sample import Sample, Table, Plot, ArArData, ArArBasic, Sequence, RawData
from .initial import preference_keys

Set = Plot.Set
Label = Plot.Label
Axis = Plot.Axis
Text = Plot.Text

pd.options.mode.chained_assignment = None  # default='warn'


# =======================
# Calculate ages
# =======================
def calc_apparent_ages(smp: Sample):
    """

    Parameters
    ----------
    smp

    Returns
    -------

    """
    if str(smp.Info.sample.type).lower() == "unknown":
        v = calc_age(smp=smp)
    elif str(smp.Info.sample.type).lower() == "standard":
        v = calc_j(smp=smp)
    elif str(smp.Info.sample.type).lower() == "air":
        v = calc_mdf(smp=smp)
    else:
        raise TypeError(f"Sample type is not supported: {smp.Info.sample.type}")
    try:
        smp.ApparentAgeValues[2:6] = v[0:4]
        smp.PublishValues[5:7] = copy.deepcopy(v[0:2])
    except (Exception, BaseException):
        raise


def calc_j(ar40ar39=None, params: dict = None, smp: Sample = None, index: list = None):
    params_index_dict = {
        34: 'L', 35: 'rsL', 59: 'Age', 60: 'sAge'
    }
    if ar40ar39 is None and smp is not None:
        ar40ar39 = smp.ApparentAgeValues[0:2]  # ar40ar39 air, error
    if len(np.shape(ar40ar39)) == 1:
        ar40ar39 = np.reshape(ar40ar39, (2, 1))
    if index is None:
        index = list(range(np.shape(ar40ar39)[-1]))
    if smp is None and params is None:
        raise ValueError(f"Parameters are required for calculating mdf, or it is empty.")
    if params is not None:
        for key, val in params.items():
            if not isinstance(val, list):
                params[key] = list(val)
    if smp is not None:
        try:
            params_from_smp = dict(zip(
                list(params_index_dict.values()),
                [[smp.TotalParam[i][j] for j in index] for i in params_index_dict.keys()]
            ))
        except Exception:
            print(traceback.format_exc())
            raise ValueError(f"Parameters cannot be found in the given sample object")
        if params is not None:
            params_from_smp.update(params)
        params = params_from_smp

    j = calc.jvalue.j_value(params['Age'], params['sAge'], *ar40ar39, params['L'], params['rsL'])

    if len(index) == 1:
        return np.array(j).squeeze().tolist()
    else:
        return np.array(j).tolist()


def calc_mdf(ar40ar36=None, params: dict = None, smp: Sample = None, index: list = None):
    params_index_dict = {
        71: 'M36', 72: 'sM36', 79: 'M40', 80: 'sM40', 93: 'Air', 94: 'rsAir', 100: 'Discr'
    }
    if ar40ar36 is None and smp is not None:
        ar40ar36 = smp.ApparentAgeValues[0:2]  # ar40ar36 air, error
    if len(np.shape(ar40ar36)) == 1:
        ar40ar36 = np.reshape(ar40ar36, (2, 1))
    if index is None:
        index = list(range(np.shape(ar40ar36)[-1]))
    if smp is None and params is None:
        raise ValueError(f"Parameters are required for calculating mdf, or it is empty.")
    if params is not None:
        for key, val in params.items():
            if not isinstance(val, list):
                params[key] = list(val)
    if smp is not None:
        try:
            params_from_smp = dict(zip(
                list(params_index_dict.values()),
                [[smp.TotalParam[i][j] for j in index] for i in params_index_dict.keys()]
            ))
        except Exception:
            print(traceback.format_exc())
            raise ValueError(f"Parameters cannot be found in the given sample object")
        if params is not None:
            params_from_smp.update(params)
        params = params_from_smp

    mdf = []
    for i in range(len(index)):
        k = calc.corr.mdf(ar40ar36[0][i], ar40ar36[1][i], params['M36'][i], params['M40'][i],
                          params['Air'][i], params['rsAir'][i])  # linear, exp, pow
        mdf.append({"linear": k[0:4], "exp": k[4:8], "pow": k[8:12]}[params['Discr'][i].lower()])

    if len(index) == 1:
        return np.transpose(mdf).squeeze().tolist()
    else:
        return np.transpose(mdf).tolist()


def calc_age(ar40ar39=None, params: dict = None, smp: Sample = None, index: list = None):
    """
    40Ar/39Ar age calculation, two methods are supported: Min et al. (2000) or general equation.
    Parameters
    ----------
    ar40ar39 : 2D DataFrame, Series, list
    params : dict
    smp : Sample instance
    index:

    Returns
    -------

    """
    params_index_dict = {
        34: 'L', 35: 'sL', 36: 'Le', 37: 'sLe', 38: 'Lb', 39: 'sLb', 48: 'A', 49: 'sA',
        50: 'Ae', 51: 'sAe', 52: 'Ab', 53: 'sAb', 54: 'Abp', 55: 'sAbp', 59: 't', 60: 'st',
        61: 'Ap', 62: 'sAp', 63: 'Kp', 64: 'sKp', 67: 'J', 68: 'sJ',
        81: 'W', 82: 'sW', 83: 'No', 84: 'sNo', 85: 'Y', 86: 'sY', 87: 'f', 88: 'sf', 110: 'Min'
    }

    if isinstance(ar40ar39, pd.Series):
        ar40ar39 = [ar40ar39.tolist(), [0] * ar40ar39.size]
    if isinstance(ar40ar39, pd.DataFrame):
        ar40ar39 = ar40ar39.transpose().values.tolist()
    if ar40ar39 is None and smp is not None:
        ar40ar39 = smp.ApparentAgeValues[0:2]
    if len(np.shape(ar40ar39)) == 1:
        ar40ar39 = np.reshape(ar40ar39, (2, 1))
    if index is None:
        index = list(range(np.shape(ar40ar39)[-1]))

    if smp is None and params is None:
        raise ValueError(f"Parameters are required for calculating ages, or it is empty.")
    if params is not None:
        for key, val in params.items():
            if not isinstance(val, list):
                params[key] = list(val)
    if smp is not None:
        try:
            params_from_smp = dict(zip(
                list(params_index_dict.values()),
                [[smp.TotalParam[i][j] for j in index] for i in params_index_dict.keys()]
            ))
        except Exception:
            print(traceback.format_exc())
            raise ValueError(f"Parameters cannot be found in the given sample object")
        if params is not None:
            params_from_smp.update(params)
        params = params_from_smp

    u = 'Ma'
    try:
        u = smp.Info.preference['ageUnit']
    except:
        print(traceback.format_exc())
        pass
    finally:
        if u.lower() == 'ga':
            age_unit_factor = 1000000000
        elif u.lower() == 'ma':
            age_unit_factor = 1000000
        elif u.lower() == 'ka':
            age_unit_factor = 1000
        else:
            age_unit_factor = 1

    # check if using Min equation
    params['Min'] = [i if isinstance(i, bool) else False for i in params['Min']]

    idx1 = np.flatnonzero(np.where(params['Min'], True, False))  # True, using Min equation
    idx2 = np.flatnonzero(np.where(params['Min'], False, True))  # False
    k1, k2 = [], []
    if np.size(idx1) > 0:
        k1 = calc.age.calc_age_min(
            F=[ar40ar39[0][i] for i in idx1], sF=[ar40ar39[1][i] for i in idx1],
            **dict(zip(params.keys(), [[val[i] for i in idx1] for val in params.values()])))
        k1 = [i / age_unit_factor for i in k1]
    if np.size(idx2) > 0:
        k2 = calc.age.calc_age_general(
            F=[ar40ar39[0][i] for i in idx2], sF=[ar40ar39[1][i] for i in idx2],
            **dict(zip(params.keys(), [[val[i] for i in idx2] for val in params.values()])))
        k2 = [i / age_unit_factor for i in k2]

    # idx1 = params[params['Min'].astype(bool)].index
    # idx2 = params[~params['Min'].astype(bool)].index  # The operators are: | for or, & for and, and ~ for not
    # k1, k2 = [], []
    # if idx1.size > 0:
    #     k1 = calc.age.calc_age_min(
    #         F=ar40ar39.take(idx1)[0], sF=ar40ar39.take(idx1)[1], **params.take(idx1).to_dict('list'))
    # if idx2.size > 0:
    #     k2 = calc.age.calc_age_general(
    #         F=ar40ar39.take(idx2)[0], sF=ar40ar39.take(idx2)[1], **params.take(idx2).to_dict('list'))

    columns = ['age', 's1', 's2', 's3']
    ages = pd.concat([
        pd.DataFrame([*k1], columns=idx1, index=columns),
        pd.DataFrame([*k2], columns=idx2, index=columns)
    ], axis=1).transpose().reset_index(drop=True)

    if len(index) == 1:
        return ages.transpose().squeeze().tolist()
    else:
        return ages.transpose().values.tolist()


# =======================
# Search components
# =======================
def get_content_dict(smp: Sample):
    """

    Parameters
    ----------
    smp

    Returns
    -------

    """
    return dict(zip(
        ['smp', 'blk', 'cor', 'deg', 'pub', 'age', 'iso', 'pam', 'mak', 'seq'],
        [smp.SampleIntercept, smp.BlankIntercept, smp.CorrectedValues, smp.DegasValues,
         smp.PublishValues, smp.ApparentAgeValues, smp.IsochronValues, smp.TotalParam,
         [smp.IsochronMark], [smp.SequenceName, smp.SequenceValue]]
    ))


def get_dict_from_obj(obj: (Sample, Plot, Table, Set, Label, Axis, Text,
                            ArArBasic, ArArData, Sequence, RawData)):
    """

    Parameters
    ----------
    obj

    Returns
    -------

    """
    res = {}
    for key, attr in obj.__dict__.items():
        if not isinstance(attr, (Sample, Plot, Table, Set, Label, Axis, Text,
                                 ArArBasic, ArArData, Sequence, RawData)):
            res.update({key: attr})
        else:
            res.update({key: get_dict_from_obj(attr)})
    return res


def get_components(smp: Sample):
    """
    Get updated sample.Components dict
    Parameters
    ----------
    smp

    Returns
    -------

    """
    components_name = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8',
        'figure_1', 'figure_2', 'figure_3', 'figure_4', 'figure_5', 'figure_6', 'figure_7', 'figure_8', 'figure_9',
    ]
    components = {}
    for key in components_name:
        comp = get_component_byid(smp, key)
        components.update({key: comp})
    return components


def get_component_byid(smp: Sample, comp_id: str):
    """
    Get a component (Table or Plot) based on input id
    Parameters
    ----------
    smp
    comp_id

    Returns
    -------

    """
    for key, val in smp.__dict__.items():
        if isinstance(val, (Plot, Table, ArArBasic)) and getattr(val, 'id') == comp_id:
            return val


def get_plot_set(plot: Plot, comp_id):
    """
    Get a Set, Text, Axis, Label of a sample instance based on given id
    """
    for v in [getattr(plot, k) for k in dir(plot)]:
        if isinstance(v, Plot.BasicAttr) and v.id.lower() == comp_id.lower():
            return v
    return None


# =======================
# Update
# =======================
def update_plot_from_dict(plot, attrs: dict):
    """ Set instance based on the given attrs dictionary
    Parameters
    ----------
    plot
    attrs : dict
        for example: update_plot_from_dict(sample.Info, info: dict), where info = {
            'sample': {'name': 'name', 'material': 'material', 'location': 'location'},
            'researcher': {'name': 'researcher'},
            'laboratory': {'name': 'laboratory'}
        }

    Returns
    -------

    """

    def _do(_plot, _attrs: dict):
        for k1, v1 in _attrs.items():
            if isinstance(v1, dict):
                if hasattr(_plot, k1):
                    if isinstance(getattr(_plot, k1), dict):
                        setattr(_plot, k1, calc.basic.update_dicts(getattr(_plot, k1), v1))
                        # setattr(_plot, k1, v1)
                    else:
                        _do(getattr(_plot, k1), v1)
            else:
                setattr(_plot, k1, v1)

    _do(_plot=plot, _attrs=attrs)
    return plot


def update_object_from_dict(obj, attrs: dict):
    """
    update object
    Parameters
    ----------
    obj
    attrs

    Returns
    -------

    """
    def _do(_obj, _attrs: dict):

        for k1, v1 in _attrs.items():
            if hasattr(_obj, k1):
                if getattr(_obj, k1) == v1:
                    continue
                elif isinstance(v1, dict):
                    if isinstance(getattr(_obj, k1), dict):
                        setattr(_obj, k1, calc.basic.update_dicts(getattr(_obj, k1), v1))
                        # setattr(_plot, k1, v1)
                    else:
                        _do(getattr(_obj, k1), v1)
                else:
                    setattr(_obj, k1, v1)
            else:
                setattr(_obj, k1, v1)

    _do(_obj=obj, _attrs=attrs)
    return obj


# =======================
# Merge sample instances
# =======================
def get_merged_smp(a: Sample, b: (Sample, dict)):
    """ Comparing two sample instances a and b
        This function is used to update sample instance to make sure JS can read properties it required.
    Parameters
    ----------
    a : sample instance that has old attributes,
    b : new sample instance that has some new attributes or a has similar but different name for this attribute

    Returns
    -------
    None
        return none, but a will be updated after calling this function

            for example:
                A = Sample(id = 'a', set1 = Set(id = 'set1', data = [], symbolSize = 10)),
                B = Sample(id = 'b', set1 = Set(id = 'set1', data = [2023], symbol_size = 5, line_type = 'solid')),
                after get_merged_smp(A, B), A will be Sample(id = 'a', 'set1' = Set(id = 'set1', data = [],
                                                        symbol_size = 10, line_type = 'solid'))
    """

    def get_similar_name(_name: str):
        res = []
        for i in range(len(_name) + 1):
            str_list = [i for i in _name]
            str_list.insert(i, '_')
            res.append(''.join(str_list))
        for i in range(len(_name)):
            str_list = [i for i in _name]
            str_list[i] = str_list[i].capitalize()
            res.append(''.join(str_list))
        for i in range(len(_name)):
            str_list = [i for i in _name]
            if _name[i] in '-_':
                str_list.pop(i)
                res.append(''.join(str_list))
        return res

    if not isinstance(b, dict):
        b = b.__dict__

    for name, attr in b.items():
        if hasattr(a, name):
            if isinstance(attr, (Plot, Table, ArArBasic, Plot.BasicAttr)):
                if not type(getattr(a, name)) == type(attr):
                    if isinstance(getattr(a, name), dict):
                        setattr(a, name, type(attr)(**getattr(a, name)))
                    else:
                        setattr(a, name, type(attr)())
                get_merged_smp(getattr(a, name), attr)
            if isinstance(attr, dict) and isinstance(getattr(a, name), dict):
                setattr(a, name, calc.basic.merge_dicts(getattr(a, name), attr))
            if isinstance(attr, list) and isinstance(getattr(a, name), list):
                if len(attr) > len(getattr(a, name)):
                    setattr(a, name, getattr(a, name) + attr[len(getattr(a, name)):])
            continue
        else:
            for xxx in get_similar_name(name):
                for xx in get_similar_name(xxx):
                    for x in get_similar_name(xx):
                        if hasattr(a, x):
                            # print(f'Has similar {name} = {x}: {getattr(a, x)}')
                            setattr(a, name, getattr(a, x))
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
            if not hasattr(a, name):
                setattr(a, name, attr)


# =======================
# Difference between two sample instances
# =======================
def get_diff_smp(backup: (dict, Sample), smp: (dict, Sample)):
    """ Comparing two sample component dicts or sample instances, and return difference between them.
    Parameters
    ----------
    backup : backup of sample.Components or sample before changed.
    smp : sample.Components or sample after changed

    Returns
    -------
    dict
        dict of keys and values that have difference, iterate to a sepcial difference,

            for example:
                A = Sample(id = 'a', set1 = Set(id = 'set1', data = [])),
                B = Sample(id = 'b', set1 = Set(id = 'set1', data = [2023])),
                res = get_diff_smp(A, B) will be {'id': 'b', 'set1': {'data': [2023]}}

    """
    res = {}
    if isinstance(backup, Sample) and isinstance(smp, Sample):
        return get_diff_smp(backup.__dict__, smp.__dict__)
    for name, attr in smp.items():
        if name not in backup.keys() or not isinstance(backup[name], type(attr)):
            res.update({name: attr})
            continue
        if isinstance(attr, dict):
            # if name not in backup.keys():
            #     res.update({name: attr})
            #     continue
            _res = get_diff_smp(backup[name], attr)
            if _res != {}:
                res.update({name: _res})
            continue
        if isinstance(attr, np.ndarray):
            if not np.array_equal(attr, backup[name]):
                res.update({name: attr})
            continue
        if isinstance(attr, (Plot, Table, Plot.Text, Plot.Axis, Plot.Set,
                             Plot.Label, Plot.BasicAttr, ArArBasic, ArArData)):
            _res = get_diff_smp(backup[name].__dict__, attr.__dict__)
            if _res != {}:
                res.update({name: _res})
            continue
        if str(backup[name]) == str(attr) or backup[name] == attr:
            continue
        res.update({name: attr})
    return res


# =======================
# Set parameters
# =======================
def set_params(smp: Sample, params: Union[List, str], flag: Optional[str] = None, rows: Optional[List] =None):
    """
    Parameters
    ----------
    smp
    params
    flag : optional, should be one of 'calc', 'irra', and 'smp'. If it is not given,
        the text of the extension without a dot will be used
    rows

    Returns
    -------

    """
    if rows is None:
        rows = []
    rows = list(set(rows))

    if isinstance(params, str) and os.path.isfile(params):
        if flag is None:
            flag = params.split(".")[-1]
        return set_params(smp, read_params(params), flag=flag)

    def isValid(item):
        valid = True
        if isinstance(item, (float, int)):
            valid = not np.isnan(item)
        return valid and item is not None and item != ""

    def remove_none(old_params, new_params, row_list, length):
        res = [[old_params[i][j] if j < len(old_params[i]) else None for j in range(max(len(old_params[i]), length))] for i in range(len(old_params))]
        for index, item in enumerate(new_params):
            if isValid(item):
                for row in row_list:
                    res[index][row] = item
        return res

    n = len(smp.SequenceName)
    if n == 0:
        raise ValueError(f"The number of sample sequences is zero")

    if flag == 'calc':
        smp.TotalParam[34:56] = remove_none(smp.TotalParam[34:56], params[0:22], rows, n)
        smp.TotalParam[71:97] = remove_none(smp.TotalParam[71:97], params[22:48], rows, n)
    elif flag == 'irra':
        smp.TotalParam[0:20] = remove_none(smp.TotalParam[0:20], params[0:20], rows, n)
        smp.TotalParam[56:58] = remove_none(smp.TotalParam[56:58], params[20:22], rows, n)  # Cl36/38 productivity
        smp.TotalParam[20:27] = remove_none(smp.TotalParam[20:27], params[22:29], rows, n)
        irradiation_time = []
        duration = []
        if None not in params[29:-3] and '' not in params[29:-3]:
            for i in range(len(params[29:-3])):
                if i % 2 == 0:
                    irradiation_time.append(params[29:-3][i] + 'D' + str(params[29:-3][i + 1]))
                    duration.append(float(params[29:-3][i + 1]))
            smp.TotalParam[27:30] = remove_none(smp.TotalParam[27:30], ['S'.join(irradiation_time), params[-3], sum(duration)], rows, n)
        if params[-5] != '':
            smp.TotalParam[30:32] = remove_none(smp.TotalParam[30:32], [params[-5], None], rows, n)
        try:
            stand_time_second = [
                calc.basic.get_datetime(*re.findall(r"\d+", smp.TotalParam[31][i])) - calc.basic.get_datetime(
                    *re.findall(r"\d+", smp.TotalParam[30][i])) for i in range(len(smp.TotalParam[30]))]
        except (BaseException, Exception):
            print(f'Error in calculate standing duration: {traceback.format_exc()}')
            smp.TotalParam[32] = [None for index in range(n)]
        else:
            smp.TotalParam[32] = [item / (3600 * 24 * 365.242) if index in rows else smp.TotalParam[32][index] for index, item in enumerate(stand_time_second)]  # stand year

    elif flag == 'smp':
        smp.TotalParam[67:71] = remove_none(smp.TotalParam[67:71], params[0:4], rows, n)
        smp.TotalParam[58:67] = remove_none(smp.TotalParam[58:67], params[4:13], rows, n)
        smp.TotalParam[97:100] = remove_none(smp.TotalParam[97:100], params[13:16], rows, n)
        smp.TotalParam[115:120] = remove_none(smp.TotalParam[115:120], params[16:21], rows, n)
        smp.TotalParam[126:136] = remove_none(smp.TotalParam[126:136], params[21:31], rows, n)
        # smp.TotalParam[120:123] = remove_none(smp.TotalParam[120:123], params[31:34], rows, n)
        smp.TotalParam[100:114] = remove_none(
            smp.TotalParam[100:114],
            [['Linear', 'Exponential', 'Power'][params[35:38].index(True)] if True in params[35:38] else '', *params[38:]], rows, n)
        pref = dict(zip(preference_keys, params[31:35]))
        smp.Info.preference.update(pref)
        for key, comp in get_components(smp).items():
            if isinstance(comp, Table):
                comp.decimal_places = pref['decimalPlaces']
                comp.set_coltypes()
        smp.AgeSpectraPlot.yaxis.title.text = f"Apparent Age ({str(pref['ageUnit']).capitalize()})"

    else:
        raise KeyError(f"{flag = } is not supported. It must be 'calc' for Calc Params, "
                       f"'irra' for Irradiation Params, or 'smp' for Sample Params.")
    return smp


def get_sequence(smp: Sample):
    set1_index = [index for index, _ in enumerate(smp.IsochronMark) if _ in [1, '1']]
    set2_index = [index for index, _ in enumerate(smp.IsochronMark) if _ in [2, '2']]
    set3_index = list(set(range(0, len(smp.IsochronMark))) - set(set1_index) - set(set2_index))
    smp.SelectedSequence1 = set1_index
    smp.SelectedSequence2 = set2_index
    smp.UnselectedSequence = set3_index
    smp.Info.results.selection[0]['data'] = smp.SelectedSequence1
    smp.Info.results.selection[1]['data'] = smp.SelectedSequence2
    smp.Info.results.selection[2]['data'] = smp.UnselectedSequence
    return ArArBasic(
        size=len(smp.SequenceName), name=smp.SequenceName, value=smp.SequenceValue, unit=smp.SequenceUnit,
        mark=ArArBasic(
            size=len(smp.IsochronMark), value=smp.IsochronMark,
            set1=ArArBasic(size=len(set1_index), index=set1_index),
            set2=ArArBasic(size=len(set2_index), index=set2_index),
            unselected=ArArBasic(size=len(set3_index), index=set3_index),
        )
    )


def get_results(smp: Sample):
    return ArArBasic(
        isochron=ArArBasic(**dict(
            ({'figure_2': 'normal', 'figure_3': 'inverse', 'figure_4': 'cl_1',
              'figure_5': 'cl_2', 'figure_6': 'cl_3', 'figure_7': 'three_d'}[key],
             ArArBasic(**dict(({2: 'unselected', 0: 'set1', 1: 'set2'}[_key],
                               ArArBasic(**_value)) for (_key, _value) in value.items())))
            for (key, value) in smp.Info.results.isochron.items())),
        age_plateau=ArArBasic(**dict(
            ({2: 'unselected', 0: 'set1', 1: 'set2'}[key], ArArBasic(**value))
            for (key, value) in smp.Info.results.age_plateau.items()))
    )

