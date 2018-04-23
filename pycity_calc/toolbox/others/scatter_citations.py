#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import warnings
import matplotlib.pyplot as plt

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)

N = 12
province = ['',
            'Monte Carlo method',
            'Stochastic optimization',
            'Robust optimization',
            'Multi-criteria decision making',
            'Interval analysis',
            'Point estimation',
            'Fuzzy optimization',
            'Scenario based modeling',
            'z-numbers',
            'Information gap decision theory',
            '']
pos1 = [0, 2000, 1000, 2500, 4000, 5000, 6000, 7000, 7500, 7000, 6500, 10000]
pos2 = [0, 7000, 1000, 2500, 4000, 5000, 6000, 7000, 7500, 8000, 8500, 10000]
numbers = [0, 10259, 2270, 1547, 817, 642, 462, 394, 144, 113, 55, 0]
plt.scatter(pos1, pos2, s=numbers, color='#EC635C')
for i in range(N):
    plt.annotate(province[i], xy=(pos1[i], pos2[i]))

plt.axis('off')

this_path = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(this_path, 'output')
output_filename = 'literature_ref_bubbles'
dpi = 100
save_pgf = False
save_tikz = True

# Save plot
if (output_path is not None and output_filename is not None):
    #  Generate path if not existent
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tiff = output_filename + '.tiff'
    file_tikz = output_filename + '.tikz'
    file_svg = output_filename + '.svg'
    file_pgf = output_filename + '.pgf'

    #  Generate saving pathes
    path_pdf = os.path.join(output_path, file_pdf)
    path_eps = os.path.join(output_path, file_eps)
    path_png = os.path.join(output_path, file_png)
    path_tiff = os.path.join(output_path, file_tiff)
    path_tikz = os.path.join(output_path, file_tikz)
    path_svg = os.path.join(output_path, file_svg)
    path_pgf = os.path.join(output_path, file_pgf)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf', dpi=dpi)
    plt.savefig(path_eps, format='eps', dpi=dpi)
    plt.savefig(path_png, format='png', dpi=dpi)
    # plt.savefig(path_tiff, format='tiff', dpi=dpi)
    plt.savefig(path_svg, format='svg', dpi=dpi)

    if save_pgf:
        plt.savefig(path_pgf, format='pgf', dpi=dpi)

    if save_tikz:
        tikz_save(path_tikz, figureheight='\\figureheight',
                  figurewidth='\\figurewidth')

plt.show()
