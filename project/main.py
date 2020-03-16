"""
Final Project
Data Visualization
EECE5642 - V30, Spring 2020
"""

import argparse
import time
import sys


def main(args):
    pass


if __name__ == '__main__':

    # Print system version at top of execution
    _border_str = '-' * len(sys.version)
    print(f"{_border_str}\n{sys.version}\n{_border_str}", end='\n\n', flush=True)

    # Specify command line arguments
    _parser = argparse.ArgumentParser(description='')
    _args = _parser.parse_args()

    # Track runtime
    _main_start = time.time()
    main(_args)
    _main_end = time.time()

    print(f"\nmain() finished after {_main_end-_main_start:0.4f}s", flush=True)
