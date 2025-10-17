#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# webarar - raw_file
# ==========================================
#
#
#
"""

from typing import List, Union
import traceback
import os
import re
import pickle
import chardet
from xlrd import open_workbook
from datetime import datetime
from parse import parse as string_parser
import dateutil.parser as datetime_parser
from ..calc.arr import get_item
from ..calc.basic import utc_dt
from ..smp.sample import RawData

""" Open raw data file """

DEFAULT_SAMPLE_INFO = {
    "ExpName": "en",        # "Experiment Name"
    "StepName": "sn",       # "Step Name"
    "StepType": "st",       # "Step Type"
    "StepLabel": "sl",      # "Step Label"
    "ZeroYear": "date",     # "Zero Date Year"
    "ZeroHour": "time",     # "Zero Time Hour"
    "ZeroMon": "mon",       # "Zero Date Month"
    "ZeroMin": "min",       # "Zero Time Minute"
    "ZeroDay": "day",       # "Zero Date Day"
    "ZeroSec": "sec",       # "Zero Time Second"
    "SmpName": "smpn",      # "Sample Name"
    "SmpLoc": "smpl",       # "Sample location"
    "SmpMatr": "smpm",      # "Sample Material"
    "ExpType": "et",        # "Experiment Type"
    "SmpWeight": "smpw",    # "Sample Weight"
    "Stepunit": "su",       # "Step unit"
    "HeatingTime": "ht",    # "Heating time"
    "InstrName": "inn",     # "Instrument name"
    "Researcher": "re",     # "Researcher"
    "Analyst": "an",        # "Analyst"
    "Lab": "la",            # "Laboratory"
    "Jv": "jv",             # "J value"
    "Jsig": "je",           # "J value error"
    "MDF": "mdf",           # "MDF"
    "MDFSig": "mdfe",       # "MDF error"
    "CalcName": "cp",       # "Calc params"
    "IrraName": "in",       # "Irra name"
    "IrraLabel": "il",      # "Irra label"
    "IrraPosH": "ih",       # "Irra position H"
    "IrraPosX": "ix",       # "Irra position X"
    "IrraPosY": "iy",       # "Irra position Y"
    "StdName": "stdn",      # "Standard name"
    "StdAge": "stda",       # "Standard age"
    "StdAgeSig": "stde",    # "Standard age error"
}



def open_file(file_path: str, input_filter: List[Union[str, int, bool]]):
    """
    Parameters
    ----------
    file_path:
    input_filter

    Returns
    -------
    step_list -> [[[header of step one], [cycle one in the step], [cycle two in the step]],[[],[]]]
        example:
            [
                [
                    [1, '6/8/2019  8:20:51 PM', 'BLK', 'B'],  # step header
                    # [sequence index, date time, label, value]
                    ['1', 12.30, 87.73, 12.30, 1.30, 12.30, 0.40, 12.30, 0.40, 12.30, 0.44],  # step/sequence 1
                    # [cycle index, time, Ar40 signal, time, Ar39 signal, ..., time, Ar36 signal]
                    ['2', 24.66, 87.70, 24.66, 1.14, 24.66, 0.36, 24.66, 0.35, 24.66, 0.43],  # step/sequence 2
                    ...
                    ['10', 123.06, 22262.68, 123.06, 6.54, 123.06, 8.29, 123.06, 0.28, 123.06, 29.22],
                ],
                [
                    ...
                ]
            ]

    """
    extension = str(os.path.split(file_path)[-1]).split('.')[-1]
    try:
        handler = {'txt': open_raw_txt, 'excel': open_raw_xls,
                   'Qtegra Exported XLS': open_qtegra_exported_xls, 'Seq': open_raw_seq}[
            ['txt', 'excel', 'Qtegra Exported XLS', 'Seq'][int(input_filter[1])]]
    except KeyError:
        raise FileNotFoundError("Wrong File.")
    return handler(file_path, input_filter)


def open_qtegra_exported_xls(filepath, input_filter=None):
    if input_filter is None:
        input_filter = []
    try:
        wb = open_workbook(filepath)
        sheets = wb.sheet_names()
        sheet = wb.sheet_by_name(sheets[0])
        value, step_header, step_list = [], [], []
        for row in range(sheet.nrows):
            row_set = []
            for col in range(sheet.ncols):
                if sheet.cell(row, col).value == '':
                    pass
                else:
                    row_set.append(sheet.cell(row, col).value)
            if row_set != [] and len(row_set) > 1:
                value.append(row_set)
        for each_row in value:
            # if the first item of each row is float (1.0, 2.0, ...) this row is the header of a step.
            if isinstance(each_row[0], float):
                each_row[0] = int(each_row[0])
                if "M" in each_row[1].upper():
                    each_row[1] = datetime.strptime(each_row[1], '%m/%d/%Y  %I:%M:%S %p').isoformat(timespec='seconds')
                else:
                    each_row[1] = datetime.strptime(each_row[1], '%m/%d/%Y  %H:%M:%S').isoformat(timespec='seconds')
                step_header.append(each_row)
        for step_index, each_step_header in enumerate(step_header):
            row_start_number = value.index(each_step_header)
            try:
                row_stop_number = value.index(step_header[step_index + 1])
            except IndexError:
                row_stop_number = len(value) + 1
            step_values = [
                each_step_header[0:4],
                *list(map(
                    # lambda x: [x[0], x[1], x[2], x[1], x[3], x[1], x[4], x[1], x[5], x[1], x[6]],
                    # x[1] = time, x[2] = H2:40, x[3] = H1: 39, x[4] = AX: 38, x[5] = L1: 37, x[6] = L2: 36
                    lambda x: [x[0], x[1], x[6], x[1], x[5], x[1], x[4], x[1], x[3], x[1], x[2]],
                    # in sequence: Ar36, Ar37, Ar38, Ar39, Ar40
                    [value[i] for i in range(row_start_number + 2, row_stop_number - 7, 1)]))
            ]
            step_list.append(step_values)
    except Exception as e:
        raise ValueError('Error in opening the original file: %s' % str(e))
    else:
        return {'data': step_list}


def open_raw_txt(file_path, input_filter: List[Union[str, int]]):
    """
    Parameters
    ----------
    input_filter
    file_path

    Returns
    -------

    """
    if not input_filter:
        raise ValueError("Input filter is empty array.")

    if os.path.splitext(file_path)[1][1:].lower() != input_filter[0].strip().lower():
        raise ValueError("The file does not comply with the extension in the given filter.")

    with open(file_path, 'rb') as f:
        contents = f.read()
        encoding = chardet.detect(contents)
        lines = [line.strip().split(['\t', ';', " ", ",", input_filter[3]][int(input_filter[2])])
                 for line in contents.decode(encoding=encoding["encoding"]).split('\r\n')]

    file_name = os.path.basename(file_path).rstrip(os.path.splitext(file_path)[-1])
    step_list = get_raw_data([lines], input_filter, file_name=file_name)
    return {'data': step_list}


def open_raw_xls(file_path, input_filter: List[Union[str, int]]):
    """
    Parameters
    ----------
    file_path
    input_filter

    Returns
    -------

    """
    if not input_filter:
        raise ValueError("Input filter is empty array.")

    if os.path.splitext(file_path)[1][1:].lower() != input_filter[0].strip().lower():
        raise ValueError("The file does not comply with the extension in the given filter.")

    def _get_content_from_sheet(_index) -> List[List[Union[str, bool, int, float]]]:
        try:
            _sheet = wb.sheet_by_index(_index)
        except IndexError:
            return []
        else:
            return [[_sheet.cell(_row, _col).value for _col in range(_sheet.ncols)] for _row in range(_sheet.nrows)]

    wb = open_workbook(file_path)
    contents = [_get_content_from_sheet(i) for i in range(100)]
    file_name = os.path.basename(file_path).rstrip(os.path.splitext(file_path)[-1])
    step_list = get_raw_data(contents, input_filter, file_name=file_name)

    return {'data': step_list}


def open_raw_seq(file_path, input_filter=None):

    class RenameUnpickler(pickle.Unpickler):
        def find_class(self, module: str, name: str):
            MODULE = RawData().__module__
            renamed_module = module
            if '.sample' in module and module != MODULE:
                renamed_module = MODULE
            try:
                return super(RenameUnpickler, self).find_class(renamed_module, name)
            except AttributeError:
                return super(RenameUnpickler, self).find_class(renamed_module, 'ArArBasic')

    def renamed_load(file_obj):
        return RenameUnpickler(file_obj).load()

    with open(file_path, 'rb') as f:
        sequences = renamed_load(f)

    # with open(file_path, 'rb') as f:
    #     sequences = pickle.load(f)
    #     print(sequences[0].__module__)

    name_list = []
    for seq in sequences:
        while seq.name in name_list:
            seq.name = f"{seq.name}-{seq.index}"
        name_list.append(seq.name)

    return {'sequences': sequences}


def get_raw_data(file_contents: List[List[Union[int, float, str, bool, list]]], input_filter: list,
                 file_name: str = "") -> list:
    """
    Parameters
    ----------
    file_name
    file_contents
    input_filter

    Returns
    -------

    """

    def datetime_parse(string, f):
        try:
            return datetime.strptime(string, f)
        except ValueError as v:
            if f.strip() == "":
                return datetime_parser.parse(string)
            elif len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
                string = string[:-(len(v.args[0]) - 26)]
                return datetime.strptime(string, f)
            else:
                raise

    step_list = []
    idx = step_index = 0

    header = input_filter[5]
    isotope_index = input_filter[8:28]
    data_index = input_filter[4:33]
    strings_index = input_filter[33:41]         # strings: filename, parsing information, datetime, timezone
    optional_info_index = input_filter[41:-7]       # from Exp Name to Std Age Error
    check_box_index = input_filter[-7:]

    while True:  # measurment steps sloop

        # ============ all text information ============
        options = get_sample_info(file_contents, optional_info_index, default="", base=[1, 1 - idx, 1])

        # ============ Step name ============
        try:
            step_name = options.get('StepName')
            experiment_name = options.get('ExpName')
            if check_box_index[1] and strings_index[0].strip() != "":
                res = string_parser(strings_index[0], file_name)
                if res is not None and "en" in res.named.keys():
                    experiment_name = res.named.get("en")
                if res is not None and "sn" in res.named.keys():
                    step_index = res.named.get("sn")
                    if step_index.isnumeric():
                        step_name = f"{experiment_name}-{int(step_index):02d}"
                    else:
                        step_name = f"{experiment_name}-{step_index}"
            if step_name == "":
                raise ValueError(f"Step name not found")
        except (TypeError, ValueError, IndexError):
            # When parsing the step name fails, the end of the file has been reached
            # raise
            print(traceback.format_exc())
            break
        else:
            options.update({'StepName': step_name})
            options.update({'ExpName': experiment_name})

        # ============ Step information ============
        try:
            if check_box_index[2]:
                string = get_item(file_contents, strings_index[1:4], default="", base=[1, 1 - idx, 1])
                res = string_parser(strings_index[4], string)
                if res is not None:
                    options.update(dict(zip(DEFAULT_SAMPLE_INFO.keys(), [res.named.get(value, options.get(key)) for key, value in DEFAULT_SAMPLE_INFO.items()])))
        except (TypeError, ValueError, IndexError):
            print(traceback.format_exc())
            break
        else:
            pass

        # ============ Zero datetime ============
        timezone = strings_index[7] if strings_index[7] != "" else "utc"
        options.update({'TimeZone': timezone})
        try:
            if check_box_index[3]:  # date in one string
                zero_date = datetime_parse(options.get('ZeroYear'), strings_index[5])
            else:
                zero_date = datetime(year=options.get('ZeroYear'), month=options.get('ZeroMon'),
                                     day=options.get('ZeroDay'))

            if check_box_index[4]:  # time in one string
                zero_time = datetime_parse(options.get('ZeroHour'), strings_index[6])
            else:
                zero_time = datetime(year=2020, month=12, day=31, hour=options.get('ZeroHour'),
                                     minute=options.get('ZeroMin'), second=options.get('ZeroSec'))

            zero_datetime = datetime(
                zero_date.year, zero_date.month, zero_date.day, zero_time.hour, zero_time.minute, zero_time.second)
            # adjust to UTC
            zero_datetime = utc_dt(zero_datetime, tz=timezone).isoformat(timespec='seconds')
            options.update({'ZeroDT': zero_datetime})
        except (TypeError, ValueError, IndexError) as e:
            print(traceback.format_exc())
            raise ValueError(f"Failed to parse zero datetime: {e}")
            # zero_datetime = datetime(1970, 1, 1, 0, 0, 0).isoformat(timespec='seconds')
        current_step = [[step_name, zero_datetime, options]]

        # ============ isotope data ============
        break_num = 0
        cycle_num = 0
        f = float(data_index[27])  # Intensity Scale Factor
        data_content = file_contents[data_index[0] - 1 if data_index[0] != 0 else 0]
        base = 1
        for i in range(2000):  # measurement cycle sloop
            if break_num < data_index[25]:
                break_num += 1
                continue
            break_num = 0
            if int(data_index[2]) == 0:  # == 0, vertical
                start_row = data_index[24] * cycle_num + data_index[25] * cycle_num + header + idx
                try:
                    current_step.append([
                        str(cycle_num + 1),
                        # in sequence: Ar36, Ar37, Ar38, Ar39, Ar40
                        float(data_content[start_row + isotope_index[18] - base][isotope_index[19] - base]),
                        float(data_content[start_row + isotope_index[16] - base][isotope_index[17] - base]) * f,
                        float(data_content[start_row + isotope_index[14] - base][isotope_index[15] - base]),
                        float(data_content[start_row + isotope_index[12] - base][isotope_index[13] - base]) * f,
                        float(data_content[start_row + isotope_index[10] - base][isotope_index[11] - base]),
                        float(data_content[start_row + isotope_index[ 8] - base][isotope_index[ 9] - base]) * f,
                        float(data_content[start_row + isotope_index[ 6] - base][isotope_index[ 7] - base]),
                        float(data_content[start_row + isotope_index[ 4] - base][isotope_index[ 5] - base]) * f,
                        float(data_content[start_row + isotope_index[ 2] - base][isotope_index[ 3] - base]),
                        float(data_content[start_row + isotope_index[ 0] - base][isotope_index[ 1] - base]) * f,
                    ])
                except (ValueError, IndexError):
                    print(f"Cannot parse isotope data")
                    print(traceback.format_exc())
                    current_step.append([
                        str(cycle_num + 1), None, None, None, None, None, None, None, None, None, None,
                    ])
            elif int(data_index[2]) == 1:  # == 1, horizontal
                start_row = data_index[1] + idx
                col_inc = data_index[24] * cycle_num + data_index[25] * cycle_num - base
                try:
                    current_step.append([
                        str(cycle_num + 1),
                        # Ar36, Ar37, Ar38, Ar39, Ar40
                        float(data_content[start_row][isotope_index[19] + col_inc]),
                        float(data_content[start_row][isotope_index[17] + col_inc]) * f,
                        float(data_content[start_row][isotope_index[15] + col_inc]),
                        float(data_content[start_row][isotope_index[13] + col_inc]) * f,
                        float(data_content[start_row][isotope_index[11] + col_inc]),
                        float(data_content[start_row][isotope_index[ 9] + col_inc]) * f,
                        float(data_content[start_row][isotope_index[ 7] + col_inc]),
                        float(data_content[start_row][isotope_index[ 5] + col_inc]) * f,
                        float(data_content[start_row][isotope_index[ 3] + col_inc]),
                        float(data_content[start_row][isotope_index[ 1] + col_inc]) * f,
                    ])
                except (ValueError, IndexError):
                    print(f"Cannot parse isotope data")
                    print(traceback.format_exc())
                    current_step.append([
                        str(cycle_num + 1), None, None, None, None, None, None, None, None, None, None,
                    ])
            else:
                raise ValueError(f"{data_index[2]} not in [0, 1]")

            cycle_num += 1
            if cycle_num >= data_index[3]:
                break

        step_list.append(current_step)
        idx = data_index[28] * len(step_list)
        if not check_box_index[0] or len(step_list) >= 500:  # check_box_index[0]: multiple sequences
            print(f"Multiple Sequence = {check_box_index[0]}, Step number = {len(step_list)}")
            break

    if not step_list:
        raise ValueError("Failed to read the original file. It might be because the names of the experiments or steps were not recognized.")

    return step_list


def get_sample_info(file_contents: list, index_list: list, default="", base: Union[int, tuple, list] = 1) -> dict:
    """
    Parameters
    ----------
    file_contents
    index_list
    default
    base

    Returns
    -------

    """
    sample_info = DEFAULT_SAMPLE_INFO.copy()
    sample_info.update({
        "ExpName": get_item(file_contents, index_list[0:3], default=default, base=base),
        "StepName": get_item(file_contents, index_list[3:6], default=default, base=base),
        "StepType": get_item(file_contents, index_list[6:9], default=default, base=base),
        "StepLabel": get_item(file_contents, index_list[9:12], default=default, base=base),
        "ZeroYear": get_item(file_contents, index_list[12:15], default=default, base=base),
        "ZeroHour": get_item(file_contents, index_list[15:18], default=default, base=base),
        "ZeroMon": get_item(file_contents, index_list[18:21], default=default, base=base),
        "ZeroMin": get_item(file_contents, index_list[21:24], default=default, base=base),
        "ZeroDay": get_item(file_contents, index_list[24:27], default=default, base=base),
        "ZeroSec": get_item(file_contents, index_list[27:30], default=default, base=base),
        "SmpName": get_item(file_contents, index_list[30:33], default=default, base=base),
        "SmpLoc": get_item(file_contents, index_list[33:36], default=default, base=base),
        "SmpMatr": get_item(file_contents, index_list[36:39], default=default, base=base),
        "ExpType": get_item(file_contents, index_list[39:42], default=default, base=base),
        "SmpWeight": get_item(file_contents, index_list[42:45], default=default, base=base),
        "Stepunit": get_item(file_contents, index_list[45:48], default=default, base=base),
        "HeatingTime": get_item(file_contents, index_list[48:51], default=default, base=base),
        "InstrName": get_item(file_contents, index_list[51:54], default=default, base=base),
        "Researcher": get_item(file_contents, index_list[54:57], default=default, base=base),
        "Analyst": get_item(file_contents, index_list[57:60], default=default, base=base),
        "Lab": get_item(file_contents, index_list[60:63], default=default, base=base),
        "Jv": get_item(file_contents, index_list[63:66], default=default, base=base),
        "Jsig": get_item(file_contents, index_list[66:69], default=default, base=base),
        "MDF": get_item(file_contents, index_list[69:72], default=default, base=base),
        "MDFSig": get_item(file_contents, index_list[72:75], default=default, base=base),
        "CalcName": get_item(file_contents, index_list[75:78], default=default, base=base),
        "IrraName": get_item(file_contents, index_list[78:81], default=default, base=base),
        "IrraLabel": get_item(file_contents, index_list[81:84], default=default, base=base),
        "IrraPosH": get_item(file_contents, index_list[84:87], default=default, base=base),
        "IrraPosX": get_item(file_contents, index_list[87:90], default=default, base=base),
        "IrraPosY": get_item(file_contents, index_list[90:93], default=default, base=base),
        "StdName": get_item(file_contents, index_list[93:96], default=default, base=base),
        "StdAge": get_item(file_contents, index_list[96:99], default=default, base=base),
        "StdAgeSig": get_item(file_contents, index_list[99:102], default=default, base=base),
    })
    return sample_info
