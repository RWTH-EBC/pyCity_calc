## PyCity_Calculator

PyCity addon to perform energy balance and economic calculations for city districts.

## Contributing

1. Clone repository: `git clone git@git.rwth-aachen.de:jschiefelbein/PyCity_Calc.git` (for SSH usage) 
   otherwise, use https path: `git clone https://git.rwth-aachen.de/jschiefelbein/PyCity_Calc.git`
2. Create issue on  [https://git.rwth-aachen.de/jschiefelbein/PyCity_Calc/issues](https://git.rwth-aachen.de/jschiefelbein/PyCity_Calc/issues)
Create your feature branch: `git checkout -b issueXY_explanation`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin issueXY_explanation`
5. Submit a merge request (for merging into development branch) to `@jschiefelbein` [https://git.rwth-aachen.de/jschiefelbein/PyCity_Calc/merge_requests](https://git.rwth-aachen.de/jschiefelbein/PyCity_Calc/merge_requests)
6. Working version of development branch can later be merged into master

## Installation

PyCity requires the following EBC Python packages:
- uesgraph
- PyCity

uesgraph is available under [https://github.com/RWTH-EBC/uesgraphs](https://github.com/RWTH-EBC/uesgraphs)

PyCity is available under [https://github.com/RWTH-EBC/pyCity](https://github.com/RWTH-EBC/pyCity)

Both can be installed into your system Python path via pip:

`pip install -e 'your_path_to_uesgraph_setup'`

and

`pip install -e 'your_path_to_pycity_setup'`

In case you are using different Python distributions on your machine and your currently used distribution is not in the Python path, 
you can open a Python command window within your Python path (e.g. Winpython cmd window) and type

`python`

and press enter to open the python environment (the Python version number should be shown within cmd prompt).
Then type

`import pip`

enter, then type

`exit()`

and press enter to exit the Python environment. Then you should be able to install the missing Python packages locally to your specific Python distribution
via pip, e.g.

`pip install -e 'your_path_to_uesgraph_setup'`

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
- Optional: TEASER [https://github.com/RWTH-EBC/TEASER](https://github.com/RWTH-EBC/TEASER)

### Shapely installation on Windows machine

In many cases pip install of shapely (or pyproj etc.) will raise an error during installation. However, there is a workaround. 

-  Go to  [http://www.lfd.uci.edu/~gohlke/pythonlibs/](http://www.lfd.uci.edu/~gohlke/pythonlibs/)
-  Search for Python package, you could not install via pip (such as shapely)
-  Choose download file depending on your Python version and machine (e.g. cp34 stands for Python 3.4; win32 for 32 bit; amd64 for 64 bit)
-  Download wheel file and remember its path
-  Open a command prompt within your Python environment 
-  Type: ''pip install <path_to_your_whl_file>'
-  Python packages should be installed


## Tutorial

PyCity_Calc has a jupyter notebook tutorial script under pycity_calc/examples/tutorials/... 
To open the jupyter notebook, open a command/terminal window and change your directory to the directory, 
where tutorial_pycity_calc_1.ipynb is stored. Then type 'jupyter notebook' (without '' signs) and press Enter.
Jupyter notebook should open within your browser (such as Firefox). Click on one notebook to start.

## License

PyCity_Calc is released under the [MIT License](https://opensource.org/licenses/MIT)

## Acknowledgements

We gratefully acknowledge the financial support for parts of PyCity by BMWi (German Federal Ministry for Economic Affairs and Energy)
