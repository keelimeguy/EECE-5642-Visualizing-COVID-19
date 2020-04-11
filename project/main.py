"""
Final Project
Data Visualization
EECE5642 - V30, Spring 2020

by Keelin Becker-Wheeler and Yiwen Ma, Apr 2020
"""

import argparse
import time
import sys

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from .covid_data import CovidDataset
from .utils.benchmark import benchmark_timing
from .prediction import test, plot_chart_and_table
from matplotlib import ticker


def main(args):
    dataset = benchmark_timing('Reading dataset', CovidDataset, args.world_data, args.usa_data)
    benchmark_timing('Visualizing data', dataset.plot_data_as_world_colors, shape_folder=args.shapefiles, level=args.level)

    # plot world graph
    plt.show()

    # plot top 10 countries confirmed with COVID-19 
    # confirmed VS deaths
    # predict confirmed cases after 5 days 
    plot_chart_and_table(dataset)

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
