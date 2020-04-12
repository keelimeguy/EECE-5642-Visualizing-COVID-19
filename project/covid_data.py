"""
by Keelin Becker-Wheeler, Apr 2020
"""

from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.collections import PatchCollection
from bisect import bisect

import matplotlib.colors as plt_colors
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import cv2
import os

from .world_shapes import create_world_map, get_location_to_shape_mapping, get_drawable_patches
from .utils.progress_tracker import ProgressTracker

##############################
# Uncomment if manually debugging location fixes

# from .world_shapes import search_for_location_fix
# import sys
##############################


class CovidDataset:

    # Mapping of location names to corrected standard location names are provided for each granularity level
    # Necessary due to mismatch between location names in covid dataset and standard location names

    location_fixes = {
        # Admin0
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

        # Admin1
        'Bonaire, Sint Eustatius and Saba': ['St. Eustatius', 'Bonaire', 'Saba'],
        'Channel Islands': None,
        'Curacao': 'Curaçao',
        'Falkland Islands (Islas Malvinas)': 'Falkland Islands',
        'French Guiana': 'Guyane française',
        'Grand Princess': None,
        'Hong Kong': 'Hong Kong S.A.R.',
        'Inner Mongolia': 'Inner Mongol',
        'Northwest Territories': ['Northwest Territories', 'Nunavut'],
        'Quebec': 'Québec',
        'Recovery aggregated': None,
        'Reunion': 'La Réunion',
        'St Martin': 'St. Martin',
        'Tibet': 'Xizang',
        'Virgin Islands': 'United States Virgin Islands',
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
        world_data = world_data[world_data.Admin0 != 'US']

        # Map the US data with the following column names to the desired order
        # -- UID,iso2,iso3,code3,FIPS,Admin2,Province_State,Country_Region,
        #            Lat,Long_,Combined_Key,Population,Date,Confirmed,Deaths
        col_order = [7, 6, 5, 8, 9, 12, 13, 14]
        usa_data = pd.read_csv(usa_file, header=0)
        usa_data = usa_data[[usa_data.columns[i] for i in col_order]]
        usa_data.rename({usa_data.columns[i]: n for i, n in enumerate(col_names)}, axis=1, inplace=True)

        self.data = pd.concat([world_data, usa_data]).reset_index(drop=True)

        for level in [1, 2]:
            # Set missing location names to empty string
            self.data[f'Admin{level}'].fillna('', inplace=True)

        # Force timestamps to datetime format
        self.data['Date'] = pd.to_datetime(self.data['Date'])

        # Group data for convenient indexing
        self.data = self.data.groupby(['Date', 'Admin0', 'Admin1', 'Admin2']).mean()

        all_dates, _, _, _ = zip(*list(self.data.index))
        self.all_dates = sorted(list(set(all_dates)))

        self.find_reversed_location_fixes()
        self.world = None

    def get_datapoints(self, locations=None, date=None, level=0, target='Confirmed'):
        """
        :param locations: A list of location names to get data for. Will use all locations if None, defaults to None
        :param date: Timestamp at which to get data. Will use current time if None, defaults to None
        :param level: Granularity of world data, higher is more detail. Either 0, 1 or 2, defaults to 0
        :param target: The target column to get data from, defaults to 'Confirmed'

        :type locations: [str]|None, optional
        :type date: datetime.datetime|None, optional
        :type level: int, optional
        :type target: str, optional

        :returns: The data corresponding to the given parameters
        :rtype: pd.DataFrame

        :raises: ValueError
        """

        if level not in [0, 1, 2]:
            raise ValueError(f'unexpected level={level}')

        if date is None:
            # Use current timestamp if not provided
            date = datetime.datetime.now()

        # Get a timestamp which is a valid date in the data
        date = self.get_closest_previous_date(date)

        if locations is None:
            Admin = tuple(zip(*list(self.data.loc[date].index)))
            locations = sorted(list(set(Admin[level])))

        data_dict = {}
        for location in locations:
            if location:
                datapoint = self.data.loc[date].query(f'Admin{level} == "{location}"')[target].sum()
                data_dict[location] = datapoint

        df = pd.DataFrame(data=data_dict, index=[0]).transpose()
        df.rename(columns={0: target}, inplace=True)
        return df

    def find_reversed_location_fixes(self):
        """ Create reversed location fix mapping
        """

        self.rev_location_fixes = {}
        for k, v in self.location_fixes.items():
            if v is not None:
                if isinstance(v, list):
                    for vv in v:
                        self.rev_location_fixes[vv] = k
                else:
                    self.rev_location_fixes[v] = k

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

    def plot_data_over_time(self, shape_folder='.', level=0, filename='covid_visualization.avi', overwrite=False):
        """
        :param shape_folder: Folder in which shape files exist, defaults to '.'
        :param level: Granularity of world data, higher is more detail. Either 0 or 1, defaults to 0
        :param filename: File to save video to, defaults to 'covid_visualization.avi'.
        :param overwrite: If True will overwrite existing file, defaults to False.

        :type shape_folder: str, optional
        :type level: int, optional
        :type filename: str, optional
        :type overwrite: bool, optional

        :returns: Filename of video file written.
        :rtype: str
        """

        if (not overwrite) and os.path.exists(filename):
            return filename

        video_writer = None
        admin = None
        w = 16
        h = 12
        dpi = 100

        with ProgressTracker('iterating dates') as progress:
            for date in self.all_dates:
                plotted_data, fig = self.plot_data_as_world_colors(date=date, shape_folder=shape_folder, level=level)
                fig.suptitle(f'Confirmed Cases - {date.date()}', y=0.73)
                fig.set_size_inches(w, h)

                if admin is None:
                    admin = plotted_data[level].index
                else:
                    # Sanity check that all countries are accounted for
                    assert((admin == plotted_data[level].index).all())

                # Create image from figure
                fig.canvas.draw()
                img = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
                img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                img = img[int(dpi*h*.25):int(dpi*h*.75), int(dpi*w*.05):int(dpi*w*.95)]

                plt.close(fig)
                self.reset_world()

                if video_writer is None:
                    height, width, _ = img.shape
                    size = (width, height)

                    video_writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'DIVX'), 5, size)

                video_writer.write(img)

                progress.add(1, maximum=len(self.all_dates))

        video_writer.release()
        return filename

    def plot_data_as_world_colors(self, date=None, shape_folder='.', level=0):
        """
        :param date: Timestamp at which to plot data. Will use current time if None, defaults to None
        :param shape_folder: Folder in which shape files exist, defaults to '.'
        :param level: Granularity of world data, higher is more detail. Either 0 or 1, defaults to 0

        :type date: datetime.datetime|None, optional
        :type shape_folder: str, optional
        :type level: int, optional

        :returns: A dictionary mapping levels to the plotted data at that level of granularity
                  and the map figure on which geographical data was drawn
        :rtype: ({int:pd.DataFrame}, matplotlib.figure.Figure)
        """

        if self.world is None:
            # Generate empty world if not already exists
            fig = self.determine_world_mapping()
        else:
            fig = plt.gcf()

        ax = fig.gca()
        ax.set_facecolor("#5D9BFF")

        ##############################
        # If you need to manually check all location fix possibilities for a given location, uncomment the following:

        # debug_location = 'Nunavut'
        # self.load_shape_info_at_level(level, shape_folder=shape_folder)
        # search_for_location_fix(self.world, debug_location, None)
        # sys.exit(0)

        # You may also let the program search for and automatically print potential location fixes by setting the following
        debug_new_location_fixes = False
        ##############################

        maximum = 0
        colors = None

        plotted_data_per_level = {}

        # Work up to highest granularity
        for lvl in range(level+1):
            locations, info_keys = self.load_shape_info_at_level(lvl, shape_folder=shape_folder)

            shape_map, empty_patches = get_location_to_shape_mapping(self.world, locations, info_keys, self.rev_location_fixes)
            patches = get_drawable_patches(self.world, locations, shape_map, info_keys, self.location_fixes,
                                           debug_new_location_fixes=debug_new_location_fixes)

            # Track what data is being plotted
            plotted_data_per_level[lvl] = self.get_datapoints(locations=patches.keys(), date=date, level=lvl)

            if lvl == 0:
                # Store the polygons of locations which do not correspond with data
                patches[None] = empty_patches

                maximum = plotted_data_per_level[lvl].max()

                # Set up a colormap with logarithmic scale
                colors = plt.cm.ScalarMappable(norm=plt_colors.LogNorm(vmin=1, vmax=maximum), cmap='Reds')
                colors.get_cmap().set_bad(colors.get_cmap()(0))

            # Draw shapes with color according to associated location data
            for k, v in patches.items():
                if v:
                    if k is None:
                        # Color unknown locations black
                        facecolor = 'k'
                        zorder = 2  # Make sure unknown locations are drawn behind known locations, in case of overlap

                    else:
                        # Change color based on data value
                        value = plotted_data_per_level[lvl].loc[k]
                        facecolor = colors.to_rgba(value)
                        zorder = 3 + lvl  # Make sure higher granularity is on top

                    ax.add_collection(PatchCollection(v, facecolor=facecolor, edgecolor='k', linewidths=0.2, zorder=zorder))

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.02)
        fig.colorbar(colors, cax=cax)

        return plotted_data_per_level, fig

    def load_shape_info_at_level(self, level, shape_folder='.'):
        """
        :param level: Granularity of world data, higher is more detail. Either 0 or 1, defaults to 0
        :param shape_folder: Folder in which shape files exist, defaults to '.'

        :type level: int
        :type shape_folder: str, optional

        :returns: A list of locations at the given level, a list of keys used to get the location from the shape info data
        :rtype: ([str], [str])

        :raises: ValueError
        """

        # Get unique names of locations
        Admin0, Admin1, _ = zip(*list(self.data.loc[self.all_dates[0]].index))

        if level == 0:
            locations = sorted(list(set(Admin0)))
            shape_file = 'ne_10m_admin_0_countries'
            info_keys = ['NAME_SORT', 'SOVEREIGNT']

        elif level == 1:
            locations = sorted(list(set(Admin1)))
            shape_file = 'ne_10m_admin_1_states_provinces'
            info_keys = ['name', 'admin']

        else:
            raise ValueError(f'unexpected level={level}')

        self.world.readshapefile(f'{shape_folder}/{shape_file}', 'shapes', drawbounds=False)

        return locations, info_keys

    def reset_world(self):
        """ Clears the world data associated with the dataset.
        """

        self.world = None
