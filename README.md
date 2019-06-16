![E.ON EBC RWTH Aachen University](./doc/_static/EBC_Logo.png)

[![Build Status](https://travis-ci.org/RWTH-EBC/pyCity_calc.svg?branch=master)](https://travis-ci.org/RWTH-EBC/pyCity_calc)
[![Coverage Status](https://coveralls.io/repos/github/RWTH-EBC/pyCity_calc/badge.svg)](https://coveralls.io/github/RWTH-EBC/pyCity_calc)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://doge.mit-license.org)

#  pyCity_calc

pyCity addon to perform energy balance and economic calculations for city 
districts.

## Contributing

1. Clone repository: `git clone git@github.com:RWTH-EBC/pyCity_calc.git` 
(for SSH usage) 
   otherwise, use https path: `git clone https://github.com/RWTH-EBC/pyCity_calc.git`
2. Create issue on  [https://github.com/RWTH-EBC/pyCity_calc/issues](https://github.com/RWTH-EBC/pyCity_calc/issues)
Create your feature branch: `git checkout -b issueXY_explanation`
3. Add and commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin issueXY_explanation`
5. Submit a pull request (for merging into development branch) to `@JSchiefelbein` [https://github.com/RWTH-EBC/pyCity_calc/pulls](https://github.com/RWTH-EBC/pyCity_calc/pulls)
6. Working version of development branch can later be merged into master

## Installation

pyCity_calc requires the following EBC Python packages:
- richardsonpy
- uesgraphs
- pyCity
- TEASER

richardsonpy is available via [https://github.com/RWTH-EBC/richardsonpy](https://github.com/RWTH-EBC/richardsonpy)

uesgraphs is available via [https://github.com/RWTH-EBC/uesgraphs](https://github.com/RWTH-EBC/uesgraphs)

TEASER is available  via[https://github.com/RWTH-EBC/TEASER](https://github.com/RWTH-EBC/TEASER)

pyCity is available via [https://github.com/RWTH-EBC/pyCity](https://github.com/RWTH-EBC/pyCity)

richardsonpy and uesgraphs can be installed into your system Python path via pip, e.g.:

`pip install uesgraphs`

If you want to use the most recent (non-published) version via git integration, you can download the 
most recent code version on Github via SSH or https access and install an egglink, e.g.:

`pip install -e 'your_path_to_richardsonpy_setup_folder'`

`pip install -e 'your_path_to_uesgraph_setup_folder'`

`pip install -e 'your_path_to_teaser_setup_folder'`

and

`pip install -e 'your_path_to_pycity_setup_folder'`

Annotation: The current usage of the VDI 6007 building TEASER model in pyCity_calc requires the pyCity_calc branch issue297_vdi_core_dev_jsc!
Thus, you should NOT install TEASER via pip but use the egglink integration instead.

In your current Python path does not point at your Python installation, you 
can directly call your Python interpreter and install the packages via pip, e.g.:

    "<path_to_your_python_distribution>\Python.exe" -m pip install -e <your_path_to_uesgraph_setup>

You can check if installation / adding packages to python has been successful
by adding new .py file and trying to import richardsonpy, uesgraphs and pycity.

`import richardsonpy`

`import uesgraphs`

`import teaser`

`import pycity_base`

Import should be possible without errors.

Further required packages are:

- numpy
- xlrd
- matplotlib
- networkx
- pytest
- shapely (for uesgraphs integration)
- pyproj (for uesgraphs integration)


### Shapely installation on Windows machine

On Windows systems, pip install of shapely (or pyproj etc.) will probably raise an error during installation. 
However, there is a workaround with precompiled Python packages.

-  Go to  [http://www.lfd.uci.edu/~gohlke/pythonlibs/](http://www.lfd.uci.edu/~gohlke/pythonlibs/)
-  Search for Python package, you could not install via pip (such as shapely)
-  Choose download file depending on your Python version and machine (e.g. cp34 stands for Python 3.4; win32 for 32 bit; amd64 for 64 bit)
-  Download wheel file and remember its path
-  Open a command prompt within your Python environment 
-  Type: ''pip install <path_to_your_whl_file>'
-  Python packages should be installed

Under Linux and Mac OS pip installation of shapely and pyproj should work without problems.

## Tutorial

pyCity_calc has a jupyter notebook tutorial script under pycity_calc/examples/tutorials/... 
To open the jupyter notebook, open a command/terminal window and change your directory to the directory, 
where tutorial_pycity_calc_1.ipynb is stored. Then type 'jupyter notebook' (without '' signs) and press Enter.
Jupyter notebook should open within your browser (such as Firefox). Click on one notebook to start.
If your Pyhton path does not point at your Python installation, you have to
open jupyter notebook directly, e.g. by looking for the jupyter.exe in your distribution.

## How to cite pyCity_calc

+ Schiefelbein, J., Rudnick, J., Scholl, A., Remmen, P., Fuchs, M., Müller, D. (2019),
Automated urban energy system modeling and thermal building simulation based on OpenStreetMap data sets,
Building and Environment,
Volume 149,
Pages 630-639,
ISSN 0360-1323
[pdf](https://doi.org/10.1016/j.buildenv.2018.12.025),
[bibtex](https://github.com/RWTH-EBC/pyCity_calc/tree/master/doc/S0360132318307686.bib)

If you require a citation in German language:
+ Schiefelbein, J. , Javadi, A. , Fuchs, M. , Müller, D. , Monti, A. and Diekerhof, M. (2017), Modellierung und Optimierung von Mischgebieten. Bauphysik, 39: 23-32. doi:10.1002/bapi.201710001
[pdf](https://doi.org/10.1002/bapi.201710001),
[bibtex](https://github.com/RWTH-EBC/pyCity_calc/tree/master/doc/pericles_1437098039.bib)

## License

pyCity_calc is released by RWTH Aachen University's E.ON Energy Research Center (E.ON ERC),
Institute for Energy Efficient Buildings and Indoor Climate (EBC) under the [MIT License](https://opensource.org/licenses/MIT)

## Acknowledgements

Grateful acknowledgement is made for financial support by Federal Ministry for Economic Affairs and Energy (BMWi), 
promotional references 03ET1138D and 03ET1381A.

<img src="http://www.innovation-beratung-foerderung.de/INNO/Redaktion/DE/Bilder/Titelbilder/titel_foerderlogo_bmwi.jpg;jsessionid=4BD60B6CD6337CDB6DE21DC1F3D6FEC5?__blob=poster&v=2)" width="200">
