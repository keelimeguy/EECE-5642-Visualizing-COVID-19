"""
by Keelin Becker-Wheeler, Apr 2020
"""

from mpl_toolkits.basemap import Basemap

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class CovidDataset:
    def __init__(self, world_file, usa_file):
        """
        :param world_file: File path to world data (e.g. time-series-19-covid-combined.csv)
        :param usa_file: File path to USA data (e.g. us.csv)

        :type world_file: str, path object or file-like object
        :type usa_file: str, path object or file-like object
        """

        col_names = ['Region', 'Subregion', 'Latitude', 'Longitude', 'Date', 'Confirmed', 'Deaths']

        # Date,Country/Region,Province/State,Lat,Long,Confirmed,Recovered,Deaths
        col_order = [1, 2, 3, 4, 0, 5, 7]
        world_data = pd.read_csv(world_file, header=0)
        world_data = world_data[[world_data.columns[i] for i in col_order]]
        world_data.rename({world_data.columns[i]: n for i, n in enumerate(col_names)}, axis=1, inplace=True)

        # UID,iso2,iso3,code3,FIPS,Admin2,Province_State,Country_Region,Lat,Long_,Combined_Key,Population,Date,Confirmed,Deaths
        col_order = [6, 5, 8, 9, 12, 13, 14]
        usa_data = pd.read_csv(usa_file, header=0)
        usa_data = usa_data[[usa_data.columns[i] for i in col_order]]
        usa_data.rename({usa_data.columns[i]: n for i, n in enumerate(col_names)}, axis=1, inplace=True)

        self.data = pd.concat([world_data, usa_data]).reset_index(drop=True)

    def determine_world_mapping(self, fill_color=True, draw_borders=True):
        """Draws a world map and adds a 'pos' field to data which encodes the (x,y) world position for plotting.

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

        m.drawmapboundary(fill_color="#5D9BFF" if fill_color else None, zorder=-1)
        if fill_color:
            m.fillcontinents(color="#0D9C29", lake_color="#5D9BFF", zorder=0)
        if draw_borders:
            m.drawcountries(color='#585858', linewidth=1)
            m.drawstates(linewidth=0.2)
        m.drawcoastlines(linewidth=1)

        # Use map projection to convert long/lat into (x,y) positions
        self.data['pos'] = list(zip(*m(list(self.data.Longitude), list(self.data.Latitude))))
        self.world = m

        return fig

    def plot_data_as_world_colors(self):

        if self.world is None:
            fig = self.determine_world_mapping(fill_color=False, draw_borders=False)
        else:
            fig = plt.gcf()

        ax = fig.gca()

        # TODO

        return fig

    def reset_world(self):
        """ Clears the world data associated with the dataset.
        """

        self.world = None
