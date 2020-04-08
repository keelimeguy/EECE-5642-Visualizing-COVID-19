"""
by Keelin Becker-Wheeler, Apr 2020
"""

from matplotlib.collections import PatchCollection
from bisect import bisect

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime

from .world_shapes import create_world_map, get_location_to_shape_mapping, get_drawable_patches
# from .world_shapes import search_for_location_fix
# import sys


class CovidDataset:

    # Mapping of location names to corrected standard location names are provided for each granularity level
    # Necessary due to mismatch between location names in covid dataset and standard location names

    admin0_location_fixes = {
        'Bahamas': 'Bahamas, The',
        'Burma': 'Myanmar',
        'Congo (Brazzaville)': 'Congo, Rep.',
        'Congo (Kinshasa)': 'Congo, Dem. Rep.',
        'Cote d\'Ivoire': 'Côte d\'Ivoire',
        'Diamond Princess': None,
        'Egypt': 'Egypt, Arab Rep.',
        'Eswatini': 'eSwatini',
        'Gambia': 'Gambia, The',
        'Holy See': 'Vatican (Holy See)',
        'Iran': 'Iran, Islamic Rep.',
        'Korea, South': 'Korea, Rep.',
        'Kyrgyzstan': 'Kyrgyz Republic',
        'Laos': 'Lao PDR',
        'MS Zaandam': None,
        'North Macedonia': 'Macedonia, FYR',
        'Russia': 'Russian Federation',
        'Saint Kitts and Nevis': 'St. Kitts and Nevis',
        'Saint Lucia': 'St. Lucia',
        'Saint Vincent and the Grenadines': 'St. Vincent and the Grenadines',
        'Slovakia': 'Slovak Republic',
        'Syria': 'Syrian Arab Republic',
        'Taiwan*': 'Taiwan',
        'US': 'United States of America',
        'Venezuela': 'Venezuela, RB',
        'West Bank and Gaza': 'Palestine (West Bank and Gaza)',
    }

    admin1_location_fixes = {
    }

    def __init__(self, world_file, usa_file):
        """
        :param world_file: File path to world data (e.g. time-series-19-covid-combined.csv)
        :param usa_file: File path to USA data (e.g. us.csv)

        :type world_file: str, path object or file-like object
        :type usa_file: str, path object or file-like object
        """

        # Desired names of data columns
        col_names = ['Admin0', 'Admin1', 'Admin2', 'Latitude', 'Longitude', 'Date', 'Confirmed', 'Deaths']

        # Map the world data with the following column names to the desired order
        # -- Date,Country/Region,Province/State,Lat,Long,Confirmed,Recovered,Deaths,[Cities]
        col_order = [1, 2, 8, 3, 4, 0, 5, 7]
        world_data = pd.read_csv(world_file, header=0)
        world_data['Cities'] = np.NaN
        world_data = world_data[[world_data.columns[i] for i in col_order]]
        world_data.rename({world_data.columns[i]: n for i, n in enumerate(col_names)}, axis=1, inplace=True)

        # Map the US data with the following column names to the desired order
        # -- UID,iso2,iso3,code3,FIPS,Admin2,Province_State,Country_Region,
        #            Lat,Long_,Combined_Key,Population,Date,Confirmed,Deaths
        col_order = [7, 6, 5, 8, 9, 12, 13, 14]
        usa_data = pd.read_csv(usa_file, header=0)
        usa_data = usa_data[[usa_data.columns[i] for i in col_order]]
        usa_data.rename({usa_data.columns[i]: n for i, n in enumerate(col_names)}, axis=1, inplace=True)

        self.data = pd.concat([world_data, usa_data]).reset_index(drop=True)

        # Set missing location names to empty strings
        self.data['Admin1'].fillna('', inplace=True)
        self.data['Admin2'].fillna('', inplace=True)

        # Force timestamps to datetime format
        self.data['Date'] = pd.to_datetime(self.data['Date'])

        # Group data for convenient indexing
        self.data = self.data.groupby(['Date', 'Admin0', 'Admin1', 'Admin2']).mean()

        all_dates, _, _, _ = zip(*list(self.data.index))
        self.all_dates = sorted(list(set(all_dates)))

        self.world = None

    def get_closest_previous_date(self, date):
        """
        :type date: datetime.datetime

        :rtype: datetime.datetime
        """

        idx = bisect(self.all_dates, date)-1
        if idx < 0:
            idx = 0
        return self.all_dates[idx]

    def determine_world_mapping(self):
        """Draws a world map and adds a 'pos' field to data which encodes the (x,y) world position.

        :returns: Map figure on which geographical data can be drawn
        :rtype: matplotlib.figure.Figure
        """

        fig = plt.figure()
        ax = fig.gca()

        self.world = create_world_map(ax, fill_color=False, draw_borders=False)

        # Use map projection to convert long/lat into (x,y) positions
        self.data['pos'] = list(zip(*self.world(list(self.data.Longitude), list(self.data.Latitude))))

        return fig

    def plot_data_as_world_colors(self, date=None, shape_folder='.', level=0):
        """
        :param date: Timestamp at which to plot data. Will use current time if None, defaults to None
        :param shape_folder: Folder in which shape files exist, defaults to '.'
        :param level: Granularity of world data, higher is more detail. Either 0 or 1, defaults to 0

        :type date: datetime.datetime|None, optional
        :type shape_folder: str, optional
        :type level: int, optional

        :returns: Map figure on which geographical data was drawn
        :rtype: matplotlib.figure.Figure
        """

        if date is None:
            # Use current timestamp if not provided
            date = datetime.datetime.now()

        # Get a timestamp which is a valid date in the data
        date = self.get_closest_previous_date(date)

        if self.world is None:
            # Generate empty world if not already exists
            fig = self.determine_world_mapping()
        else:
            fig = plt.gcf()

        ax = fig.gca()
        ax.set_facecolor("#5D9BFF")

        locations, info_keys, location_fixes = self.load_shape_info_at_level(level, shape_folder=shape_folder)
        rev_location_fixes = {v: k for k, v in location_fixes.items() if v is not None}

        ##############################
        # If you need to manually check all location fix possibilities for a given location, uncomment the following:

        # debug_location = 'Greenland'
        # search_for_location_fix(self.world, debug_location, info_keys)
        # sys.exit(0)

        # You may also let the program search for and automatically print potential location fixes by setting the following
        debug_new_location_fixes = False
        ##############################

        shape_map, empty_patches = get_location_to_shape_mapping(self.world, locations, info_keys, rev_location_fixes)
        patches = get_drawable_patches(self.world, locations, shape_map, info_keys, location_fixes,
                                       debug_new_location_fixes=debug_new_location_fixes)

        # Store the polygons of locations which do not correspond with data
        patches[None] = empty_patches

        # Draw shapes with color according to associated location data
        colors = plt.cm.get_cmap('Reds')
        maximum = np.log(self.data.loc[date]['Confirmed'].max())
        for k, v in patches.items():
            if v:
                if k is None:
                    facecolor = 'k'
                    zorder = 2  # Make sure unknown locations are drawn behind known locations, in case of overlap

                else:
                    datapoint = self.data.loc[date].query(f'Admin{level} == "{k}"')['Confirmed'].sum()
                    value = np.log(datapoint) / maximum if datapoint != 0 else 0

                    # Change color based on data
                    facecolor = colors(value)
                    zorder = 3

                ax.add_collection(PatchCollection(v, facecolor=facecolor, edgecolor='k', linewidths=1., zorder=zorder))

        return fig

    def load_shape_info_at_level(self, level, shape_folder='.'):
        """
        :param level: Granularity of world data, higher is more detail. Either 0 or 1, defaults to 0
        :param shape_folder: Folder in which shape files exist, defaults to '.'

        :type level: int
        :type shape_folder: str, optional

        :returns: A list of locations at the given level, a list of keys used to get the location from the shape info data,
                  and a dictionary mapping location names to corrected names in the shape info data
        :rtype: ([str], [str], {str:str})

        :raises: NotImplementedError, ValueError
        """

        # Get unique names of locations
        Admin0, Admin1, _ = zip(*list(self.data.loc[self.all_dates[0]].index))

        if level == 0:
            locations = sorted(list(set(Admin0)))
            shape_file = 'ne_10m_admin_0_countries'
            info_keys = ['NAME_SORT', 'SOVEREIGNT']
            location_fixes = self.admin0_location_fixes

        elif level == 1:
            # TODO: Check shapes and location fixes for level 1 granularity
            raise NotImplementedError(f'level={level} implementation is incomplete')

            locations = sorted(list(set(Admin1)))
            shape_file = 'ne_10m_admin_1_states_provinces'
            info_keys = ['admin']
            location_fixes = self.admin1_location_fixes

        else:
            raise ValueError(f'unexpected level={level}')

        self.world.readshapefile(f'{shape_folder}/{shape_file}', 'shapes', drawbounds=False)

        return locations, info_keys, location_fixes

    def reset_world(self):
        """ Clears the world data associated with the dataset.
        """

        self.world = None
