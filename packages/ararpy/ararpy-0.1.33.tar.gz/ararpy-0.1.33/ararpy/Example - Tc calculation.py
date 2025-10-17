#  Copyright (C) 2024 Yang. - All Rights Reserved
"""
# ==========================================
# Copyright 2024 Yang
# ararpy - test.py
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

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def export_pdf(each_line, X, Y, x, y, Tc_list, sample_name):

    example_dir = r"C:\Users\Young\OneDrive\00-Projects\【2】个人项目\2022-05论文课题\初稿\封闭温度计算"

    # ------ 将以下五个样品的年龄谱图组合到一起 -------
    arr_files = [
        os.path.join(example_dir, r'22WHA0433.arr'),
        os.path.join(example_dir, r'20WHA0103.age'),
    ]
    colors = ['#1f3c40', '#e35000', '#e1ae0f', '#3d8ebf']
    series = []

    # ------ 构建数据 -------
    for index, file in enumerate(arr_files):
        smp = ap.from_arr(file_path=file) if file.endswith('.arr') else ap.from_age(file_path=file)
        age = smp.ApparentAgeValues[2:4]
        ar = smp.DegasValues[20]
        data = ap.calc.spectra.get_data(*age, ar, cumulative=False)
        series.append({
            'type': 'series.line', 'id': f'line{index * 2 + 0}', 'name': f'line{index * 2 + 0}', 'color': colors[index],
            'data': np.transpose([data[0], data[1]]).tolist(), 'line_caps': 'square',
        })
        series.append({
            'type': 'series.line', 'id': f'line{index * 2 + 1}', 'name': f'line{index * 2 + 1}', 'color': colors[index],
            'data': np.transpose([data[0], data[2]]).tolist(), 'line_caps': 'square',
        })
        series.append({
            'type': 'text', 'id': f'text{index * 2 + 0}', 'name': f'text{index * 2 + 0}', 'color': colors[index],
            'text': f'{smp.name()}<r>{round(smp.Info.results.age_plateau[0]["age"], 2)}',
            'size': 10, 'data': [[index * 15 + 5, 23]],
        })
    data = {
        "data": [
            {
                'xAxis': [{'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100],
                           'title': 'Cumulative <sup>39</sup>Ar Released (%)', 'nameLocation': 'middle', }],
                'yAxis': [{'extent': [0, 250], 'interval': [0, 50, 100, 150, 200, 250],
                           'title': 'Apparent Age (Ma)', 'nameLocation': 'middle', }],
                'series': series
            },
            {
                'xAxis': [{'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100],
                           'title': 'Cumulative <sup>39</sup>Ar Released (%)', 'nameLocation': 'middle', }],
                'yAxis': [{'extent': [0, 250], 'interval': [0, 50, 100, 150, 200, 250],
                           'title': 'Apparent Age (Ma)', 'nameLocation': 'middle', }],
                'series': series
            }
        ],
        "file_name": f"{sample_name}",
        "plot_names": [f"{sample_name}"],
    }

    # write pdf
    file = pm.NewPDF(filepath=os.path.join(example_dir, f"{data['file_name']}.pdf"))
    for index, each in enumerate(data['data']):
        # rich text tags should follow this priority: color > script > break
        file.text(page=index, x=50, y=780, line_space=1.2, size=12, base=0, h_align="left",
                  text=f"The PDF can be edited with Adobe Acrobat, Illustrator and CorelDRAW")
        cv = ap.smp.export.export_chart_to_pdf(each)
        file.canvas(page=index, base=0, margin_top=5, canvas=cv, unit="cm", h_align="middle")
        if index + 1 < len(data['data']):
            file.add_page()

    # save pdf
    file.save()


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


def calculate_dr2(f, ti, ar, sar, use_ln=True, logdr2_method="plane"):
    try:
        if str(logdr2_method).lower().startswith('plane'.lower()):
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_plane(f, ti, ar=ar, sar=sar, ln=use_ln)
        elif str(logdr2_method).lower() == 'yang':
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_yang(f, ti, ar=ar, sar=sar, ln=use_ln)
        elif str(logdr2_method).lower().startswith('sphere'.lower()):
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_sphere(f, ti, ar=ar, sar=sar, ln=use_ln)
        elif str(logdr2_method).lower().startswith('Thern'.lower()):
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_thern(f, ti, ar=ar, sar=sar, ln=use_ln)
        elif str(logdr2_method).lower().startswith('cylinder'.lower()):
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_cylinder(f, ti, ar=ar, sar=sar, ln=use_ln)
        elif str(logdr2_method).lower().startswith('cube'.lower()):
            dr2, ln_dr2, wt = ap.smp.diffusion_funcs.dr2_cube(f, ti, ar=ar, sar=sar, ln=use_ln)
        else:
            raise KeyError(f"Geometric model not found: {str(logdr2_method).lower()}")
    except (Exception, BaseException) as e:
        raise ValueError

    return dr2, ln_dr2, wt


def calculate_tc(arr_file_path, logdr2_method='plane', A=55, cooling_rate=10, radius=100, use_ln=True, index=None):
    base = np.e if use_ln else 10
    # [A, cooling_rate, radius] = [55, 10, 100]  # 55, 10°C/Ma, 100µm

    # 读取样品信息
    [_, _, seq_value, te, ti, age, sage, ar, sar, f, dr2, ln_dr2, wt], name = read_sample(arr_file_path=arr_file_path)
    dr2, ln_dr2, wt = calculate_dr2(f, ti, ar, sar, use_ln=use_ln, logdr2_method=logdr2_method)
    te = [i + 273.15 for i in te]

    @np.vectorize
    def get_da2_e_Tc(b, m):
        k1 = base ** b * ap.thermo.basic.SEC2YEAR  # k1: da2
        k2 = -10 * m * ap.thermo.basic.GAS_CONSTANT * np.log(base)  # activation energy, kJ
        try:
            # Closure temperature
            k3, _ = ap.thermo.basic.get_tc(da2=k1, sda2=0, E=k2 * 1000, sE=0, pho=0,
                                           cooling_rate=cooling_rate, A=A)
        except ValueError as e:
            # print(e.args)
            k3 = 999
        return k1, k2, k3  # da2, E, Tc

    index = np.s_[index if index is not None else list(range(len(te)))]
    each_line = [np.nan for i in range(17)]  # [b, sb, a, sa, ..., energy, se, tc, stc]
    temp_err = 5
    X, Y, wtX, wtY = 10000 / np.array(te), np.array(ln_dr2), 10000 * temp_err / np.array(te) ** 2, np.array(wt)
    x, y, wtx, wty = X[index,], Y[index,], wtX[index,], wtY[index]
    Tc_list = []

    if len(x) > 0:

        for cooling_rate in np.linspace(start=0, stop=100, num=100):
            # Arrhenius line regression
            # each_line[0:6] = ap.thermo.basic.fit(x, y, wtx, wty)  # intercept, slop, sa, sb, chi2, q
            # b (intercept), sb, a (slope), sa, mswd, dF, Di, k, r2, chi_square, p_value, avg_err_s, cov
            each_line[0:13] = ap.calc.regression.york2(x, wtx, y, wty, ri=np.zeros(len(x)))
            each_line[1] = each_line[1] * 1  # 1 sigma
            each_line[3] = each_line[3] * 1  # 1 sigma

            # monte carlo simulation with 4000 trials
            cov_matrix = np.array([[each_line[1] ** 2, each_line[12]], [each_line[12], each_line[3] ** 2]])
            mean_vector = np.array([each_line[0], each_line[2]])
            random_numbers = np.random.multivariate_normal(mean_vector, cov_matrix, 4000)
            res, cov = ap.calc.basic.monte_carlo(get_da2_e_Tc, random_numbers, confidence_level=0.95)
            da2, E, Tc = res[0:3, 0]
            # sda2, sE, sTc = np.diff(res[0:3, [1, 2]], axis=1).flatten() / 2
            sda2, sE, sTc = 2 * cov[0, 0] ** .5, 2 * cov[1, 1] ** .5, 2 * cov[2, 2] ** .5  # 95%

            each_line[13:15] = [E, sE]
            each_line[15:17] = [Tc, sTc]

            Tc_list.append([cooling_rate, Tc, sTc])

    Tc_list = np.transpose(Tc_list)

    return each_line, X, Y, x, y, Tc_list, name


def plot_Tc(file_path, index=None, radius=100, use_ln=True):
    if index is None:
        index = [1, 2, 3, 4, 5]
    logdr2_methods = ['plane', 'cylinder', 'sphere']
    As = [8.7, 27, 55]

    x1_extent = [10, 0]
    y1_extent = [-5, -10]

    x2_extent = [0, 100]
    y2_extent = [0, 450]

    fig, axs = plt.subplots(len(logdr2_methods), 2, figsize=(12, 12))
    for i in range(len(logdr2_methods)):
        logdr2_method = logdr2_methods[i]
        A = As[i]
        each_line, X, Y, x, y, Tc_list, name = calculate_tc(file_path, logdr2_method=logdr2_method, A=A, radius=radius,
                                                      use_ln=use_ln, index=index, cooling_rate=10)
        print(each_line)
        [E, sE] = each_line[13:15]
        axs[i, 0].scatter(X, Y, c='white', edgecolors='black')
        axs[i, 0].scatter(x, y, c='red')
        axs[i, 0].plot([min(x), max(x)], [i * each_line[2] + each_line[0] for i in [min(x), max(x)]], c='blue')
        axs[i, 0].set_title(f'{name} - Arrhenius Plot - {logdr2_method}')
        axs[i, 0].set_xlabel(f'10000 / T')
        axs[i, 0].set_ylabel(f'ln(D/r2)' if use_ln else f'log(D/r2)')
        axs[i, 0].text(axs[0, 0].get_xlim()[0], np.average(axs[0, 0].get_ylim()),
                       f'intercept = {each_line[0]:.6f} ± {each_line[1]:.6f}\n'
                       f'slope = {each_line[2]:.6f} ± {each_line[3]:.6f}\n'
                       f'E = {E / 4.184:.6f} ± {2 * sE / 4.184:.6f} kcal/mol (2sigma)\n'
                       f'log(D0/r2) = {each_line[0]:.6f} ± {2 * each_line[1]:.6f} /s (2sigma)\n'
                       f'A = {A}\n'
                       f'radius = {radius} µm')

        for s in Tc_list[2]:
            axs[i, 1].plot([Tc_list[0], Tc_list[0]], [Tc_list[1]-2*s, Tc_list[1]+2*s], c="#f0f0f0")
            axs[i, 1].plot([Tc_list[0], Tc_list[0]], [Tc_list[1]-s, Tc_list[1]+s], c="#8e8e8e")

        axs[i, 1].plot(Tc_list[0], Tc_list[1], c="black")
        axs[i, 1].set_ylim(*[y2_extent])
        axs[i, 1].set_xlim(*[x2_extent])
        axs[i, 1].set_xlabel(f'Cooling Rate')
        axs[i, 1].set_ylabel(f'Closure Temperature')

        x1_extent = [min(axs[i, 0].get_xlim()[0], x1_extent[0]), max(axs[i, 0].get_xlim()[1], x1_extent[1])]
        y1_extent = [min(axs[i, 0].get_ylim()[0], y1_extent[0]), max(axs[i, 0].get_ylim()[1], y1_extent[1])]


    for i in range(len(logdr2_methods)):
        axs[i, 0].set_xlim(*[x1_extent])
        axs[i, 0].set_ylim(*[y1_extent])


    print(Tc_list[0])
    fig.tight_layout()
    plt.show()


def export_ar_relase_curve():

    plot_data = {
        "data": [],
        "file_name": f"-Tc",
        "plot_names": [f"-Tc"],
    }

    plot_data['data'].append({
        'xAxis': [{
            'extent': [400, 1500], 'interval': [400, 600, 800, 1000, 1200, 1400, 1600],
            'title': f'Temperature [°C]', 'nameLocation': 'middle',
            'show_frame': True, 'label_size': 10, 'title_size': 10,
        }],
        'yAxis': [{
            'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100],
            # 'extent': [-25, 0], 'interval': [-30, -25, -20, -15, -10, -5, 0],
            'title': f'Cumulative argon released [%]', 'nameLocation': 'middle',
            'show_frame': True, 'label_size': 10, 'title_size': 10,
        }],
        'series': [
        ]
    })

    plot_data['data'].append({
        'xAxis': [{
            'extent': [0, 100], 'interval': [0, 20, 40, 60, 80, 100],
            'title': 'Cooling Rate [°C/Ma]', 'nameLocation': 'middle', 'show_frame': True,
            'label_size': 10, 'title_size': 10,
        }],
        'yAxis': [{
            'extent': [0, 850], 'interval': [0, 100, 200, 300, 400, 500, 600, 700, 800],
            'title': 'Closure Temperature [°C]', 'nameLocation': 'middle', 'show_frame': True,
            'label_size': 10, 'title_size': 10,
        }],
        'series': []
    })

    colors = {"bt": 'black', 'ms': 'red', 'tour': 'grey', 'amp': 'blue', 'pl': '#a4df82', 'kfs': '#a43c82'}
    sample_types = [
        r"bt",
        r"ms",
        r"bt",
        r"bt",
        r"ms",
        r"ms",
        r"bt",
        r"ms",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"kfs",
        r"tour",
        r"tour",
        r"tour",
        r"tour",
        r"tour",
        r"tour",
        r"amp",
        r"amp",
        r"amp",
        r"amp",
        r"amp",
    ]
    files = [
        r"D:\DjangoProjects\webarar\static\download\20241121_24FY01a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241123_24FY02a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241125_24FY03a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241129_24FY06a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241130_24FY07a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20241201_24FY08a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241202_24FY09a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241203_24FY10a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240630_24FY49a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240705_24FY50a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240710_24FY51a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240714_24FY52.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240728_24FY55a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240801_24FY61.arr",
        r"D:\DjangoProjects\webarar\private\upload\20241016_24FY66a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240821_24FY67a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240924_24FY70a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20240823_24FY71a.arr",
        r"D:\DjangoProjects\webarar\private\upload\20241212_24FY80a.arr",
        r"C:\Users\Young\OneDrive\00-Projects\【2】个人项目\2022-05论文课题\初稿\[01]ArAr\Gaowu\20241115_24FY81a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241210_24FY82a.arr",
        r"D:\DjangoProjects\webarar\static\download\20241019_24FY83a.arr",
        r"D:\DjangoProjects\webarar\private\upload\Table_M - BH04 diffusion experiment.arr",
        r"D:\DjangoProjects\webarar\private\mdd\MA08-1\Table_K - MA08 diffusion experiment.arr",
        r"D:\DjangoProjects\webarar\private\mdd\126KD57\126KD57-Dinh2023.arr",
        r"D:\DjangoProjects\webarar\private\mdd\Growdon2013\CT0714-Growdon2013.arr",
        r"D:\DjangoProjects\webarar\private\mdd\Growdon2013\CT0705A-Growdon2013.arr",
        r"D:\DjangoProjects\webarar\private\mdd\Growdon2013\CT0712-Growdon2013.arr",
        r"D:\DjangoProjects\webarar\private\mdd\Growdon2013\CT0726-Growdon2013.arr",
    ]
    for arr_file, sample_type in zip(files, sample_types):
        print(f"{sample_type = }, {arr_file = }")
        sample = ap.from_arr(file_path=arr_file)
        te = np.array(sample.TotalParam[124], dtype=np.float64)
        ar = np.array(sample.DegasValues[20], dtype=np.float64)  # 20-21 Argon 39
        f = np.cumsum(ar) / ar.sum() * 100

        plot_data['data'][-2]['series'].append(
            {
                'type': 'series.line', 'id': f'scatter_line', 'name': f'scatters_line',
                'color': colors[sample_type], 'line_width': 1,
                'data': np.transpose([te, f]).tolist(), 'line_caps': 'none',
            },
        )

    params_list = {
        "page_size": 'a4', "ppi": 72, "width": 9.5, "height": 7,
        "pt_width": 0.8, "pt_height": 0.8, "pt_left": 0.16, "pt_bottom": 0.18,
        "offset_top": 0, "offset_right": 0, "offset_bottom": 25, "offset_left": 35,
        "plot_together": False, "show_frame": True,
    }

    filename = f"释放曲线"
    filepath = os.path.join(r"C:\Users\Young\Downloads", f"{filename}.pdf")
    cvs = [[ap.smp.export.get_cv_from_dict(plot, **params_list) for plot in plot_data['data']]]
    filepath = ap.smp.export.export_chart_to_pdf(cvs, filename, filepath)



if __name__ == "__main__":
    file_path = r"D:\DjangoProjects\webarar\private\mdd\Y01\20241121_24FY01a-removeHT.arr"
    index = [1, 2, 3, 4, 5, 6, 7, 8]

    # file_path = r"D:\DjangoProjects\webarar\private\mdd\MA08-2\Table_L - MA08 diffusion experiment.arr"
    # index = [0, 1, 2, 3, 4, 5]
    # # plot_Tc(file_path, index=index)
    #
    # file_path = r"D:\DjangoProjects\webarar\private\mdd\MA08-1\Table_K - MA08 diffusion experiment.arr"
    # index = [4, 5, 6, 7, 8]
    #
    # file_path = r"D:\DjangoProjects\webarar\private\mdd\CR99NW\CR99NW Shi 2020.arr"
    # index = list(range(10))


    # file_path = r"D:\DjangoProjects\webarar\private\mdd\Y07"
    # index = list(range(1, 9))
    #
    # plot_Tc(file_path, index=index, use_ln=True, radius=100)


    # for cr in [1, 10, 20, 40, 60, 80, 100]:
    #     tc, _ = ap.thermo.basic.get_tc(da2=0.077 / (0.0140 ** 2) * 3600 * 24 * 365.24, sda2=0, E=47*1000 * 4.184, sE=0, pho=0,
    #                                    cooling_rate=cr, A=55)
    #     print(f"cooling rate = {cr}, tc = {tc}")
    #
    # for cr in [1, 10, 20, 40, 60, 80, 100]:
    #     tc, _ = ap.thermo.basic.get_tc(da2=18 * 3600 * 24 * 365.24, sda2=0, E=87*1000 * 4.184, sE=0, pho=0,
    #                                    cooling_rate=cr, A=6)
    #     print(f"cooling rate = {cr}, tc = {tc}")
    #
    # for cr in [1, 10, 20, 40, 60, 80, 100]:
    #     tc, _ = ap.thermo.basic.get_tc(da2=10**9.05 * 3600 * 24 * 365.24, sda2=0, E=83.79*1000 * 4.184, sE=0, pho=0,
    #                                    cooling_rate=cr, A=55)
    #     print(f"cooling rate = {cr}, tc = {tc}")

    export_ar_relase_curve()

