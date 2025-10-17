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
import os


def test():
    example_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), r'examples')
    print(f"Running: ararpy.test()")
    print(f"============= Open an example .arr file =============")
    file_path = os.path.join(example_dir, r'22WHA0433.arr')
    sample = ap.from_arr(file_path=file_path)
    # file_path = os.path.join(example_dir, r'22WHA0433.age')
    # sample = ap.from_age(file_path=file_path)
    print(f"{file_path = }")
    print(f"sample = from_arr(file_path=file_path)")
    print(f"{sample.name() = }")
    sample.name("new name")
    print(f"{sample.name() = }")
    print(f"{sample.help() = }")
    print(f"{sample.parameters() = }")
    print(f"{sample.parameters().to_df() = }")
    print(sample.show_data())
    print(sample.sample())
    print(sample.blank().to_df().iloc[:, [1, 2, 3]])


def export_pdf_demo():
    import numpy as np
    import pdf_maker as pm

    example_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), r'examples')

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
            }
        ],
        "file_name": "WHA",
        "plot_names": ["all age plateaus"],
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


if __name__ == "__main__":
    test()
    # export_pdf_demo()
