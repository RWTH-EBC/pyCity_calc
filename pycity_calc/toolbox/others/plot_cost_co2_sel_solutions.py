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


def main():

    list_cost = [68369,
                     71194,
                     75005,
                     78085,
                     80534,
                     88221
                     ]

    list_co2 = [129979,
                126105,
                116708,
                107570,
                101366,
                91737
                ]

    # list_sol = [1,
    #            9,
    #            63,
    #            111,
    #            163,
    #            225]

    list_sol = ['1 (BOI+PV)',
                '9 (1x CHP)',
                '63 (2x CHP)',
                '111 (1x LHN (3 nodes))',
                '163 (1x LHN (6 nodes))',
                '225 (2x LHN (3 nodes))']

    for i in range(len(list_cost)):
        cost = list_cost[i] / 1000
        co2 = list_co2[i] / 1000
        if i == 0:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o',
                     # markersize=3,
                     c='#E53027',
                     label='Selected solutions')
        else:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o',
                     # markersize=3,
                     c='#E53027')

    ax = plt.gca()

    for i in range(len(list_sol)):
        nb_sol = list_sol[i]
        cost = list_cost[i] / 1000
        co2 = list_co2[i] / 1000

        #  Add annotations with arrows
        ax.annotate(str(nb_sol),
                    xy=(cost, co2),
                    xytext=(cost - 1, co2 + 2)#,
                    # arrowprops=dict(  # facecolor='black',
                    #     arrowstyle='->'
                    #     # ,shrink=0.01
                    # )
        )

    #  Reference MILP scenario (boilers only)
    plt.plot([69.23],
             [156.6], linestyle='',
             marker='o',
             # markersize=5,
             c='#1058B0',
             label='Reference (BOI only)')

    ax.set_xlim([65, 100])
    ax.set_ylim([90, 160])

    plt.xlabel('Total annualized cost in thousand-Euro/a')
    plt.ylabel('CO2 emissions in t/a')
    plt.legend()
    plt.tight_layout()

    this_path = os.path.dirname(os.path.abspath(__file__))
    path_save = os.path.join(this_path, 'output', 'cost_co2_sel_sol')

    output_filename = 'cost_co2_sel_sol'

    dpi = 100

    if not os.path.exists(path_save):
        os.makedirs(path_save)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tikz = output_filename + '.tikz'
    file_svg = output_filename + '.svg'

    #  Generate saving pathes
    path_pdf = os.path.join(path_save, file_pdf)
    path_eps = os.path.join(path_save, file_eps)
    path_png = os.path.join(path_save, file_png)
    path_tikz = os.path.join(path_save, file_tikz)
    path_svg = os.path.join(path_save, file_svg)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf', dpi=dpi)
    plt.savefig(path_eps, format='eps', dpi=dpi)
    plt.savefig(path_png, format='png', dpi=dpi)
    plt.savefig(path_svg, format='svg', dpi=dpi)

    try:
        tikz_save(path_tikz, figureheight='\\figureheight',
                  figurewidth='\\figurewidth')
    except:
        msg = 'tikz_save command failed. Could not save figure to tikz.'
        warnings.warn(msg)

    plt.show()
    plt.close()

if __name__ == '__main__':
    main()