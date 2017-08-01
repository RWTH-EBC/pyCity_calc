![E.ON EBC RWTH Aachen University](./doc/_static/EBC_Logo.png)

[![Build Status](https://travis-ci.com/RWTH-EBC/pyCity_calc.svg?token=ssfy4ps1Qm5kvs5yAxfm&branch=master)](https://travis-ci.com/RWTH-EBC/pyCity_calc.svg?token=ssfy4ps1Qm5kvs5yAxfm&branch=master)

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
- uesgraphs
- pyCity

uesgraph is available under [https://github.com/RWTH-EBC/uesgraphs](https://github.com/RWTH-EBC/uesgraphs)

pyCity is available under [https://github.com/RWTH-EBC/pyCity](https://github.com/RWTH-EBC/pyCity)

Both can be installed into your system Python path via pip:

`pip install -e 'your_path_to_uesgraph_setup'`

and

`pip install -e 'your_path_to_pycity_setup'`

In your current Python path does not point at your Python installation, you 
can directly call your Python interpreter and install the packages via pip, e.g.:

    "<path_to_your_python_distribution>\Python.exe" -m pip install -e <your_path_to_uesgraph_setup>

You can check if installation / adding packages to python has been successful
by adding new .py file and trying to import uesgraphs and pycity.

`import uesgraphs`

`import pycity`

Import should be possible without errors.

Further required packages are:

- numpy
- xlrd
- matplotlib
- networkx
- pytest
- shapely (for uesgraphs integration)
- pyproj (for uesgraphs integration)
- Optional (but strongly recommended): 
TEASER [https://github.com/RWTH-EBC/TEASER](https://github.com/RWTH-EBC/TEASER)

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

## License

pyCity_calc is released under the [MIT License](https://opensource.org/licenses/MIT)

## Acknowledgements

We gratefully acknowledge the financial support by BMWi 
(German Federal Ministry for Economic Affairs and Energy) 
under promotional references 03ET1138D and 03ET1381A.

<img src="http://www.innovation-beratung-foerderung.de/INNO/Redaktion/DE/Bilder/Titelbilder/titel_foerderlogo_bmwi.jpg;jsessionid=4BD60B6CD6337CDB6DE21DC1F3D6FEC5?__blob=poster&v=2)" width="200">
