"""
Final Project
Data Visualization
EECE5642 - V30, Spring 2020

by Keelin Becker-Wheeler, Apr 2020
"""

import argparse
import time
import sys

import matplotlib.pyplot as plt

from .covid_data import CovidDataset
from .utils.benchmark import benchmark_timing


def main(args):
    dataset = benchmark_timing('Reading dataset', CovidDataset, args.world_data, args.usa_data)
    plotted_data, _ = benchmark_timing('Visualizing data', dataset.plot_data_as_world_colors,
                                       shape_folder=args.shapefiles, level=args.level)

    print(plotted_data, flush=True)
    plt.show()


if __name__ == '__main__':

    # Print system version at top of execution
    _border_str = '-' * len(sys.version)
    print(f"{_border_str}\n{sys.version}\n{_border_str}", end='\n\n', flush=True)

    # Specify command line arguments
    _parser = argparse.ArgumentParser(description='')
    _parser.add_argument('--world-data', default='covid-19-data/data/time-series-19-covid-combined.csv', help='')
    _parser.add_argument('--usa-data', default='covid-19-data/data/us.csv', help='')
    _parser.add_argument('--shapefiles', default='shapefiles', help='')
    _parser.add_argument('--level', default=0, type=int, help='')
    _args = _parser.parse_args()

    # Track runtime
    _main_start = time.time()
    main(_args)
    _main_end = time.time()

    print(f"\nmain() finished after {_main_end-_main_start:0.4f}s", flush=True)
