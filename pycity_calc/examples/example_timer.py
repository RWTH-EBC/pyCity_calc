# coding=utf-8
"""
Example script for extended timer class
"""

import pycity_calc.environments.timer as time


def run_example():
    year = 2010
    timestep = 900  # timestep in seconds

    #  Create timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    print('Timestep of timer:')
    print(timer.timeDiscretization)
    print('Number of timesteps:')
    print(int(timer.timestepsHorizon))
    print('Final timestep in hours:')
    print(int(timer.timestepsHorizon * timer.timeDiscretization / 3600))
    print('Reference year:')
    print(timer.year)

if __name__ == '__main__':
    run_example()
