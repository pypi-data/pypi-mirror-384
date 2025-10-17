# ArArPy

ArArPy is a module for the reduction of <sup>40</sup>Ar/<sup>39</sup>Ar 
geochronologic data. 

It packages the whole processing steps, including reading data from local files, 
blank correction, decay correction, interference reactions correction, age 
calculation, isochron regression, etc. 

The current version supports exported files in Thermo Scientific Qtegra (ISDS) 
platform software.

ArArPy is written in Python language combined with some open source packages, 
such as numpy, pandas, os, scipy, pickle, xlrd, xlsxwriter, and json. 

## Installing from PyPI
ArArPy can be installed via pip from PyPI.

    pip install ararpy
    
## API

### Class: Sample

#### new Sample(**kwargs)

    __init__(
        Doi = "",
        RawData = RawData(),
        Info = Info(),
        SequenceName = [],
        SequenceValue = [],
        SequenceUnit = [],
        NewIntercept = [],
        NewBlank = [],
        NewParam = [],
        SampleIntercept = [],
        BlankIntercept = [],
        AnalysisDateTime = [],
        BlankCorrected = [],
        MassDiscrCorrected = [],
        DecayCorrected = [],
        InterferenceCorrected = [],
        CorrectedValues = [],
        DegasValues = [],
        ApparentAgeValues = [],
        IsochronValues = [],
        TotalParam = [],
        PublishValues = [],
        SelectedSequence1 = [],
        SelectedSequence2 = [],
        UnselectedSequence = [],
        IsochronMark = [],
        UnknownTable = Table(),
        BlankTable = Table(),
        CorrectedTable = Table(),
        DegasPatternTable = Table(),
        PublishTable = Table(),
        AgeSpectraTable = Table(),
        IsochronsTable = Table(),
        TotalParamsTable = Table(),
        AgeSpectraPlot = Plot(),
        NorIsochronPlot = Plot(),
        InvIsochronPlot = Plot(),
        KClAr1IsochronPlot = Plot(),
        KClAr2IsochronPlot = Plot(),
        KClAr3IsochronPlot = Plot(),
        ThreeDIsochronPlot = Plot(),
        CorrelationPlot = Plot(),
        DegasPatternPlot = Plot(),
        AgeDistributionPlot = Plot(),
    )   
    
- ``` Doi``` ``` type: str ""``` ```default: ""```

    Instance id, created by uuid.uuid4().hex.

- ``` RawData ``` ``` type: RawData() ```

    RawData instance, contains information and data of the imported raw files.

- ``` Info ``` ``` type: Info() ```

    Info instance. it may contain:
    
    - ``` attr_name ``` ``` type: str ``` Info
    - ``` id ``` ``` type: str ``` 0
    - ``` name ``` ``` type: str ``` info
    - ``` type ``` ``` type: str ``` Info
    - ``` sample ``` Info instance.
        - ``` name ``` ``` type: str ``` Sample name.
        - ``` material ``` ``` type: str ``` Sample material.
        - ``` location ``` ``` type: str ``` Sample location.
    - ``` researcher ``` Info instance
        - ``` name ``` ``` type: str ``` Researcher name.
        - ``` email ``` ``` type: str ``` Researcher email.
    - ``` laboratory ``` Info instance
        - ``` name ``` ``` type: str ``` Laboratory name.
        - ``` email ``` ``` type: str ``` Laboratory email.
        - ``` addr ``` ``` type: str ``` Laboratory address.
        - ``` analyst ``` ``` type: str ``` Laboratory analyst.
        - ``` info ``` ``` type: str ``` Laboratory info.
    - ``` results ``` Info instance
        - ``` name ``` ``` type: str ``` RESULTS
        - ``` age_plateau ``` ``` type: List[float] ``` Age plateau.
        - ``` age_spectra ``` ``` type: List[float] ``` Age spectra.
        - ``` isochron ``` ``` type: List[float] ``` Isochron.
        - ``` isochron_F ``` ``` type: List[float] ``` Isochron F.
        - ``` isochron_age ``` ``` type: List[float] ``` Isochron age.
        - ``` J ``` ``` type: List[float] ``` J value, a list of value and error.
        - ``` plateau_F ``` ``` type: List[float] ``` Plateau F.
        - ``` plateau_age ``` ``` type: List[float] ``` Plateau age.
        - ``` total_F ``` ``` type: List[float] ``` total F.
        - ``` total_age ``` ``` type: List[float] ``` total age.
    - ``` reference ``` Info instance
        - ``` name ``` ``` type: str ``` REFERENCE.
        - ``` doi ``` ``` type: str ``` Paper doi.
        - ``` journal ``` ``` type: str ``` Journal name.

- ``` SequenceName = [] ``` ``` type: List[str] ``` 
    
    Sequence name list.

- ``` SequenceValue = [] ``` ``` type: List[str] ``` 

    Sequence label list.

- ``` SequenceUnit = [] ``` ``` type: List[str] ``` 

    Sequence unit list.

- ``` NewIntercept = [] ``` ``` type: List[str] ``` 

    New intercept list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` NewBlank = [] ``` ``` type: List[str] ``` 

    New Blank list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` NewParam = [] ``` ``` type: List[str] ``` 

    New Param list, 2d list, shape = (123, n), n is the number of sample sequences.

- ``` SampleIntercept = [] ``` ``` type: List[str] ``` 

    Unknown intercept list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` BlankIntercept = [] ``` ``` type: List[str] ``` 

    Blank intercept list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` AnalysisDateTime = [] ``` ``` type: List[str] ``` 

    Analysis DateTime list, 1d list, length equals the number of sample sequences.

- ``` BlankCorrected = [] ``` ``` type: List[str] ``` 

    Blank-corrected list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` MassDiscrCorrected = [] ``` ``` type: List[str] ``` 

    Mass discrimination corrected list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` DecayCorrected = [] ``` ``` type: List[str] ``` 

    Decay corrected list, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` InterferenceCorrected = [] ``` ``` type: List[str] ``` 

    Interference corrected values, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` CorrectedValues = [] ``` ``` type: List[str] ``` 

    Corrected values, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` DegasValues = [] ``` ``` type: List[str] ``` 

    Degas values, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` ApparentAgeValues = [] ``` ``` type: List[str] ``` 

    Degas values, 2d list, shape = (10, n), n is the number of sample sequences.

- ``` IsochronValues = [] ``` ``` type: List[str] ``` 

    Isochron ratio values, 2d list, shape = (39, 0)

- ``` TotalParam = [] ``` ``` type: List[str] ``` 

    Parameters values, 2d list, shape = (123, 0)
    
- ``` PublishValues = [] ``` ``` type: List[str] ``` 

    Publish values, 2d list, shape = (11, 0)

- ``` SelectedSequence1 = [] ``` ``` type: List[str] ``` 

    Selected sequence values of set 1, 1d list, shape = (n, ), n is the number of set 1 selected sequences

- ``` SelectedSequence2 = [] ``` ``` type: List[str] ``` 

    Selected sequence values of set 2, 1d list, shape = (n, ), n is the number of set 2 selected sequences

- ``` UnselectedSequence = [] ``` ``` type: List[str] ``` 

    Unselected sequence values, 1d list, shape = (n, ), n is the number of unselected sequences

- ``` IsochronMark = [] ``` ``` type: List[str] ``` 

    Isochron mark values, 1d list, shape = (n, ), n is the number of whole sequences

- ``` UnknownTable = Table() ``` ``` type: Table ``` 

    Unknown intercept Table.

- ``` BlankTable = Table() ``` ``` type: Table ``` 

    Blank intercept Table.

- ``` CorrectedTable = Table() ``` ``` type: Table ``` 

    Corrected values Table.

- ``` DegasPatternTable = Table() ``` ``` type: Table ``` 

    Degas values Table.

- ``` PublishTable = Table() ``` ``` type: Table ``` 

    Publish values Table.

- ``` AgeSpectraTable = Table() ``` ``` type: Table ``` 

    Age spectra values Table.

- ``` IsochronsTable = Table() ``` ``` type: Table ``` 

    Isochron values Table.

- ``` TotalParamsTable = Table() ``` ``` type: Table ``` 

    Total parameters Table.

- ``` AgeSpectraPlot = Plot() ``` ``` type: Plot ``` 

    Age spectra Plot.

- ``` NorIsochronPlot = Plot() ``` ``` type: Plot ``` 

    Normal Isochron Plot.

- ``` InvIsochronPlot = Plot() ``` ``` type: Plot ``` 

    Inverse Isochron Plot.

- ``` KClAr1IsochronPlot = Plot() ``` ``` type: Plot ``` 

    K-Cl-Ar 1 Isochron Plot.

- ``` KClAr2IsochronPlot = Plot() ``` ``` type: Plot ``` 

    K-Cl-Ar 2 Isochron Plot.

- ``` KClAr3IsochronPlot = Plot() ``` ``` type: Plot ``` 

    K-Cl-Ar 3 Isochron Plot.

- ``` ThreeDIsochronPlot = Plot() ``` ``` type: Plot ``` 

    Three dimensional isochron Plot.

- ``` CorrelationPlot = Plot() ``` ``` type: Plot ``` 

    Correlation Plot.

- ``` DegasPatternPlot = Plot() ``` ``` type: Plot ``` 

    Degas pattern Plot.

- ``` AgeDistributionPlot = Plot() ``` ``` type: Plot ``` 

    Age distribution Plot.

#### name()

Get sample name.

#### doi()

Get sample doi.

#### sample()

Get sample info.

#### researcher()

Get researcher info.

#### laboratory()

Get laboratory info.

#### results()

Get results, a ArArBasic class.

For example:
 
    {
        'isochron': {
            'normal': {
                'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, 
                        'abs_conv': nan, 'iter': nan, 'mag': nan, 'R2': nan, 
                        'Chisq': nan, 'Pvalue': nan, 'rs': nan, 'age': nan, 
                        's1': nan, 's2': nan, 's3': nan, 'conv': nan, 'initial': nan, 
                        'sinitial': nan, 'F': nan, 'sF': nan}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}
            }, 
            'inverse': {
                'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}
            }, 
            'cl_1': {
                'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}
            }, 
            'cl_2': {
                'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}
            }, 
            'cl_3': {
                'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}
            }, 
            'three_d': {'set1': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'set2': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}, 
                'unselected': {'k': nan, 'sk': nan, 'm1': nan, 'sm1': nan, 'MSWD': nan, ...}}
        }, 
        'age_plateau': {
            'set1': {'F': nan, 'sF': nan, 'Num': nan, 'MSWD': nan, 'Chisq': nan, 'Pvalue': nan, 
                    'age': nan, 's1': nan, 's2': nan, 's3': nan, 'Ar39': nan, 'rs': nan}, 
            'set2': {'F': nan, 'sF': nan, 'Num': nan, 'MSWD': nan, 'Chisq': nan, 'Pvalue': nan, ...}, 
            'unselected': {'F': nan, 'sF': nan, 'Num': nan, 'MSWD': nan, 'Chisq': nan, 'Pvalue': nan, ...}
        }
    }


#### sequence()

Get sequence, a ArArBasic class.

    sample.sequence() = ArArBasic(
        size=len(_smp.SequenceName), name=_smp.SequenceName,
        value=_smp.SequenceValue, unit=_smp.SequenceUnit,
        mark=ArArBasic(
            size=len(_smp.IsochronMark),
            set1=ArArBasic(
                size=sum([1 if i == 1 else 0 for i in _smp.IsochronMark]),
                index=[index for index, _ in enumerate(_smp.IsochronMark) if _ == 1],
            ),
            set2=ArArBasic(
                size=sum([1 if i == 2 else 0 for i in _smp.IsochronMark]),
                index=[index for index, _ in enumerate(_smp.IsochronMark) if _ == 2],
            ),
            unselected=ArArBasic(
                size=sum([0 if i == 2 or i == 1 else 1 for i in _smp.IsochronMark]),
                index=[index for index, _ in enumerate(_smp.IsochronMark) if _ != 1 and _ != 2],
            ),
            value=_smp.IsochronMark,
        )
    )
    
#### initial()

Initialize sample instance.

#### set_selection(index, mark)

``` args: index, mark ``` 

``` index: int, index of the selected data point```

``` mark: 1 or 2 for set 1 or set 2```

#### update_table(data, table_id)

Update table data.

#### unknown()

Get sample intercept data.

#### blank()

Get blank intercept data.
   
#### parameters()

Get parameters data.

#### corrected()

Get corrected data.

#### degas()

Get degas data.

#### isochron()

Get isochron data.

#### apparent_ages()

Get apparent ages data.

#### publish()

Get publish data.

#### corr_blank()

Do correction for blank.

#### corr_massdiscr()

Do correction for mass discrimination.

#### corr_decay()

Do correction for decay.

#### corr_ca()

Do correction for ca.

#### corr_k()

Do correction for k.

#### corr_cl()

Do correction for cl.

#### corr_atm()

Do correction for atm.

#### corr_r()

Do calculation of radiogenic 40Ar.

#### corr_ratio()

Do calculation of ratios.

#### set_params()

Set parameters

#### set_info()

Set sample info

#### recalculate()

Re-calculate

#### plot_init()

Re-calculate initialize

#### plot_isochron()

Re-calculate plot isochron

#### plot_age_plateau()

Re-calculate plot age plateau

#### plot_normal()

Re-calculate plot normal isochron

#### plot_inverse()

Re-calculate plot inverse isochron

#### plot_cl_1()

Re-calculate plot K-Cl-Ar correlation 1

#### plot_cl_2()

Re-calculate plot K-Cl-Ar correlation 2

#### plot_cl_3()

Re-calculate plot K-Cl-Ar correlation 3

#### plot_3D()

Re-calculate plot 3D diagram

#### show_data()

Show all data


## Testing
#### 1. **Running the test function from a Python terminal**

    >>> import ararpy as ap
    >>> ap.test()
    Running: ararpy.test()
    ============= Open an example .arr file =============
    file_path = 'your_dir\\examples\\22WHA0433.arr'
    sample = from_arr(file_path=file_path)
    sample.name() = '22WHA0433 -PFI'
    sample.help = 'builtin methods:\n __class__\t__delattr__\t__dir__\t__eq__\t__format__\t__ge__\t__getattribute__\t__gt__\t__hash__\t__init__\t__init_subclass__\t__le__\t__lt__\t__ne__\t__new__\t__reduce__\t__reduce_ex__\t__repr__\t__setattr__\t__sizeof__\t__str__\t__subclasshook__\ndunder-excluded methods:\n apparent_ages\tblank\tcalc_ratio\tcorr_atm\tcorr_blank\tcorr_ca\tcorr_cl\tcorr_decay\tcorr_k\tcorr_massdiscr\tcorr_r\tdoi\tinitial\tisochron\tlaboratory\tname\tparameters\tpublish\trecalculation\tresearcher\tresults\tsample\tsequence\tset_selection\tunknown\tupdate_table\n'
    sample.parameters() = <ararpy.ArArData object at 0x0000027F7FBEC9D0>
    sample.parameters().to_df() = 
             0    1      2       3       4    5  ...   117     118   119 120 121 122
    0   298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    1   298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    2   298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    3   298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    4   298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    ... ...     ...  ...    ...     ...     ...  ...  ...   ...     ...    ... ... ...
    22  298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    23  298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    24  298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    25  298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1
    26  298.56  0.0  0.018  0.0063  0.1885  0.0  ...  0.31  298.56  0.31   1   1   1

#### 2. **Example 1： create an empty sample**

    >>> import ararpy as ap    
    >>> sample = ap.from_empty()  # create new sample instance
    >>> print(sample.show_data())
    # Sample Name:
    #
    # Doi:
    #    9a43b5c1a99747ee8608676ac31814da  # uuid
    # Corrected Values:
    #     Empty DataFrame
    # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # Index: []
    # Parameters:
    #     Empty DataFrame
    # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
    #           30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
    #           57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83,
    #           84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, ...]
    # Index: []
    #
    # [0 rows x 123 columns]
    # Isochron Values:
    #     Empty DataFrame
    # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
    #           30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]
    # Index: []
    # Apparent Ages:
    #     Empty DataFrame
    # Columns: [0, 1, 2, 3, 4, 5, 6, 7]
    # Index: []
    # Publish Table:
    #     Empty DataFrame
    # Columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # Index: []
    
#### 3. **Example 2： change data point selection and recalculate**

    >>> import ararpy as ap 
    >>> import os
    >>> example_dir = os.path.join(os.path.dirname(os.path.abspath(ap.__file__)), r'examples')
    >>> file_path = os.path.join(example_dir, r'22WHA0433.arr')
    >>> sample = ap.from_arr(file_path)
    # normal isochron age
    >>> print(f"{sample.results().isochron.inverse.set1.age = }")
    # sample.results().isochron.inverse.set1.age = 163.10336210925516
    # check current data point selection
    >>> print(f"{sample.sequence().mark.value}")
    # [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    >>> print(f"{sample.sequence().mark.set1.index}")
    # [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    
    # change data point selection
    >>> sample.set_selection(10, 1)
    # check new data point selection
    >>> print(f"{sample.sequence().mark.set1.index}")
    # [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    
    # recalculate
    >>> sample.recalculate(re_plot=True)
    # check new results
    >>> print(f"{sample.results().isochron.inverse.set1.age = }")
    # sample.results().isochron.inverse.set1.age = 164.57644271385772

## Classes

    Info
    Plot
    Sample
    Table
    
    class Info(builtins.object)
     |  Info(id='', name='', type='Info', **kwargs)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, id='', name='', type='Info', **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Plot(builtins.object)
     |  Plot(id='', type='', name='', data=None, info=None, **kwargs)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, id='', type='', name='', data=None, info=None, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  Axis = <class 'sample.Plot.Axis'>
     |  
     |  BasicAttr = <class 'sample.Plot.BasicAttr'>
     |  
     |  Label = <class 'sample.Plot.Label'>
     |  
     |  Set = <class 'sample.Plot.Set'>
     |  
     |  Text = <class 'sample.Plot.Text'>
    
    class Sample(builtins.object)
     |  Sample(**kwargs)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  apparent_ages(self)
     |  
     |  blank(self)
     |  
     |  calc_ratio(self)
     |  
     |  corr_atm(self)
     |  
     |  corr_blank(self)
     |  
     |  corr_ca(self)
     |  
     |  corr_cl(self)
     |  
     |  corr_decay(self)
     |  
     |  corr_k(self)
     |  
     |  corr_massdiscr(self)
     |  
     |  corr_r(self)
     |  
     |  corrected(self)
     |  
     |  doi(self)
     |
     |  degas(self)
     |  
     |  initial(self)
     |  
     |  isochron(self)
     |  
     |  laboratory(self)
     |  
     |  name(self)
     |  
     |  parameters(self)
     |  
     |  publish(self)
     |  
     |  recalculation(self)
     |  
     |  researcher(self)
     |  
     |  results(self)
     |  
     |  sample(self)
     |  
     |  sequence(self)
     |  
     |  set_selection(self)
     |  
     |  show_data(self)
     |  
     |  unknown(self)
     |  
     |  update_table(self)
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties defined here:
     |  
     |  version
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Table(builtins.object)
     |  Table(id='', name='Table', colcount=None, rowcount=None, header=None, data=None, coltypes=None, textindexs=None, numericindexs=None, **kwargs)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, id='', name='Table', colcount=None, rowcount=None, header=None, data=None, coltypes=None, textindexs=None, numericindexs=None, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

