# Visualizing COVID-19

A final project for EECE 5642 - Data Visualization

## Setup
1. Clone this repo
2. `git submodule update --init`

## Usage

### Requirements
Tested on:
- Python 3.8.1 

`pip install -r requirements.txt`

#### Potential Issues
You may be unable to find the Basemap library automatically through the `pip` command.

If this is the case, the following steps may help to solve the issue:

1. `sudo apt-get install -y libgeos-dev`
2. `pip install https://github.com/matplotlib/basemap/archive/v1.2.1rel.tar.gz`
3. `pip install -r requirements.txt`

### Command line
`python -m project.main -h`
