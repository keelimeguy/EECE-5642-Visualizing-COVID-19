"""
by Keelin Becker-Wheeler, Apr 2020
"""

from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from bisect import bisect

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime

import sys

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


class CovidDataset:
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
        # -- UID,iso2,iso3,code3,FIPS,Admin2,Province_State,Country_Region,Lat,Long_,Combined_Key,Population,Date,Confirmed,Deaths
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

    def determine_world_mapping(self, fill_color=True, draw_borders=True):
        """Draws a world map and adds a 'pos' field to data which encodes the (x,y) world position.

        :param fill_color: Whether to fill the graph with color, defaults to True.
        :param draw_borders: Whether to draw state/country borders, defaults to True.

        :type fill_color: bool, optional
        :type draw_borders: bool, optional

        :returns: Map figure on which geographical data can be drawn
        :rtype: matplotlib.figure.Figure
        """

        fig = plt.figure()
        ax = fig.gca()
        ax.set_aspect('equal')

        # Create a map projection space in order to display nodes at geographical positions.
        m = Basemap(projection='gall', resolution='c', ax=ax)

        m.drawparallels(np.arange(-90, 90, 30), labels=[1, 0, 0, 0])
        m.drawmeridians(np.arange(m.lonmin, m.lonmax+30, 60), labels=[0, 0, 0, 1])

        if fill_color:
            m.fillcontinents(color="#0D9C29", lake_color="#5D9BFF", zorder=0)
        if draw_borders:
            m.drawmapboundary(fill_color="#5D9BFF" if fill_color else None, zorder=-1)
            m.drawcountries(color='#585858', linewidth=1)
            m.drawstates(linewidth=0.2)
            m.drawcoastlines(linewidth=1)

        # Use map projection to convert long/lat into (x,y) positions
        self.data['pos'] = list(zip(*m(list(self.data.Longitude), list(self.data.Latitude))))
        self.world = m

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

        :raises: NotImplementedError, ValueError
        """

        if date is None:
            # Use current timestamp if not provided
            date = datetime.datetime.now()

        # Get a timestamp which is a valid date in the data
        date = self.get_closest_previous_date(date)

        if self.world is None:
            # Generate empty world if not already exists
            fig = self.determine_world_mapping(fill_color=False, draw_borders=False)
        else:
            fig = plt.gcf()

        ax = fig.gca()
        ax.set_facecolor("#5D9BFF")

        # Get unique names of locations at specified level

        Admin0, Admin1, _ = zip(*list(self.data.loc[date].index))

        if level == 0:
            locations = set(Admin0)
            shape_file = 'ne_10m_admin_0_countries'
            info_key = 'NAME_SORT'
            location_fixes = admin0_location_fixes

        elif level == 1:
            # TODO: Check shapes and location fixes for level 1 granularity
            raise NotImplementedError(f'level={level} implementation is incomplete')

            locations = set(Admin1)
            shape_file = 'ne_10m_admin_1_states_provinces'
            info_key = 'admin'
            location_fixes = admin1_location_fixes

        else:
            raise ValueError(f'unexpected level={level}')

        rev_location_fixes = {v: k for k, v in location_fixes.items() if v is not None}

        self.world.readshapefile(f'{shape_folder}/{shape_file}', 'shapes', drawbounds=False)

        ##############################
        # If you need to manually check all location fix possibilities for a given location, uncomment the following:
        # shapefile_debug(self.world, 'Congo') # This will also end the program here
        ##############################

        # Create map of locations to shapes
        patches = {None: []}
        shape_map = {None: None}

        for info, shape in zip(self.world.shapes_info, self.world.shapes):
            # Add shape to map
            if info[info_key] not in shape_map:
                shape_map[info[info_key]] = []
            shape_map[info[info_key]].append(shape)

            # Add shape to empty patches if not associated with data
            if info[info_key] not in locations:
                patches[None].append(Polygon(np.array(shape), True))
            elif info[info_key] in rev_location_fixes:
                if rev_location_fixes[info[info_key]] not in locations:
                    patches[None].append(Polygon(np.array(shape), True))

        # Find shapes for each location with data
        for location in sorted(locations):
            try:
                shapes = shape_map[location]

            except KeyError:
                # Check if a fix exists for location name inconsistencies
                if location in location_fixes:
                    location = location_fixes[location]
                    shapes = shape_map[location]

                # Search for and print potential fixes for the location name inconsistencies
                # (this can be manually accomplished using the commented out shapefile_debug() line above)
                else:
                    for i, info in enumerate(self.world.shapes_info):
                        good = False
                        for k, v in info.items():
                            if isinstance(v, str) and location in v:
                                good = True
                                break

                        if good:
                            print(f"\'{location}\': \'{info[info_key]}\',")
                            break
                        elif i == len(self.world.shapes_info)-1:
                            print(f"\'{location}\': None,")
                            break

                    shapes = None

            finally:
                if shapes is not None:
                    # Add shapes to be drawn
                    patches[location] = []
                    for shape in shapes:
                        patches[location].append(Polygon(np.array(shape), True))

        # Draw shapes with color according to associated location data
        for k, v in patches.items():
            if k is None:
                facecolor = 'k'
            else:
                # TODO: change color based on data
                facecolor = '#0D9C29'

            ax.add_collection(PatchCollection(v, facecolor=facecolor, edgecolor='k', linewidths=1., zorder=2))

        return fig

    def reset_world(self):
        """ Clears the world data associated with the dataset.
        """

        self.world = None


def shapefile_debug(world, location):
    for i, info in enumerate(world.shapes_info):
        good = False
        for k, v in info.items():
            if isinstance(v, str) and location in v:
                good = True
                break

        if good:
            for k, v in info.items():
                sys.stdout.buffer.write(f'{k}: {v}\n'.encode('utf-8'))
            print('------------------------------------------', flush=True)

    sys.exit(0)
