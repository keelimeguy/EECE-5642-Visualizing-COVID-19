"""
by Keelin Becker-Wheeler, Apr 2020
"""

from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon

import numpy as np

import sys


def create_world_map(ax, fill_color=True, draw_borders=True):
    """
    :param ax: Axes on which to draw map
    :param fill_color: Whether to fill the graph with color, defaults to True
    :param draw_borders: Whether to draw state/country borders, defaults to True

    :type ax: matplotlib.axes.Axes
    :type fill_color: bool, optional
    :type draw_borders: bool, optional

    :rtype: Basemap
    """

    # Create a map projection space in order to display nodes at geographical positions
    m = Basemap(projection='gall', resolution='c', llcrnrlat=-60, urcrnrlat=90,
                llcrnrlon=-180, urcrnrlon=180, ax=ax)

    m.drawparallels(np.arange(-90, 90, 30), labels=[1, 0, 0, 0])
    m.drawmeridians(np.arange(m.lonmin, m.lonmax+30, 60), labels=[0, 0, 0, 1])

    if fill_color:
        m.fillcontinents(color="#0D9C29", lake_color="#5D9BFF", zorder=0)
    if draw_borders:
        m.drawmapboundary(fill_color="#5D9BFF" if fill_color else None, zorder=-1)
        m.drawcountries(color='#585858', linewidth=1)
        m.drawstates(linewidth=0.2)
        m.drawcoastlines(linewidth=1)

    return m


def get_drawable_patches(m, locations, shape_map, info_keys, location_fixes, debug_new_location_fixes=False):
    """
    :param m: The world basemap
    :param locations: A list of location names associated with data of interest
    :param shape_map: A dictionary mapping all locations from the shape info to lists of shape data
    :param info_keys: List of keys used to get location names from the shape info data
    :param location_fixes: A mapping of names in the list of locations to corrected shape info location names
    :param debug_new_location_fixes: If True will search for and print fixes for name inconsistencies, defaults to False

    :type m: Basemap
    :type locations: [str]
    :type shape_map: {str:[Basemap.shape]}
    :type info_keys: [str]
    :type location_fixes: {str:str}
    :type debug_new_location_fixes: bool, optional

    :returns: A dictionary mapping names of locations from the list given to drawable polygons
    :rtype: {str:[Polygon]}
    """

    patches = {}

    # Find drawable polygons for each location with data
    for location in sorted(locations):
        shapes = None
        try:
            shapes = shape_map[location]

        except KeyError as e:
            # The location name in the given list is not found in the available shape locations

            # Check if a fix exists for location name inconsistencies
            if location in location_fixes:
                fixed_location = location_fixes[location]
                shapes = shape_map[fixed_location]

            else:
                if debug_new_location_fixes:
                    # Search for and print potential fixes for the location name inconsistencies (not guaranteed fixes)
                    search_for_location_fix(m, location, info_keys, automated_mode=True)

                else:
                    raise e

        finally:
            if shapes is not None:
                # Add shapes to be drawn
                patches[location] = []
                for shape in shapes:
                    patches[location].append(Polygon(np.array(shape), True))

    return patches


def get_location_to_shape_mapping(m, known_locations, info_keys, rev_location_fixes):
    """
    :param m: The world basemap
    :param known_locations: A list of location names associated with data of interest
    :param info_keys: List of keys used to get location names from the shape info data
    :param rev_location_fixes: A mapping of corrected shape info location names to names in the known locations

    :type m: Basemap
    :type known_locations: [str]
    :type info_keys: [str]
    :type rev_location_fixes: {str:str}

    :returns: A dictionary mapping all locations from the shape info to lists of shape data,
              and a list of drawable Polygons corresponding to locations from the shape info that are not known locations
    :rtype: ({str:[Basemap.shape]}, [Polygon])
    """

    empty_patches = []
    shape_map = {None: None}

    for info, shape in zip(m.shapes_info, m.shapes):
        # Add shape to map
        seen = set()
        for info_key in info_keys:
            if info[info_key] in seen:
                continue
            seen.add(info[info_key])

            if info[info_key] not in shape_map:
                shape_map[info[info_key]] = []
            shape_map[info[info_key]].append(shape)

            # Add shape to empty_patches if not associated with data
            if info[info_key] not in known_locations:
                empty_patches.append(Polygon(np.array(shape), True))
            elif info[info_key] in rev_location_fixes:
                if rev_location_fixes[info[info_key]] not in known_locations:
                    empty_patches.append(Polygon(np.array(shape), True))

    return shape_map, empty_patches


def search_for_location_fix(m, location, info_keys, automated_mode=False):
    """
    :param m: The world basemap
    :param location: A location name to inspect
    :param info_keys: List of keys used to get location names from the shape info data
    :param automated_mode: If True will print the first found mapping, else will print all shape info, defaults to False

    :type m: Basemap
    :type location: str
    :type info_keys: [str]
    :type automated_mode: bool, optional
    """

    # The strategy here is to find any shape info data point which references the location at any key
    for i, info in enumerate(m.shapes_info):
        good = False
        for k, v in info.items():
            if isinstance(v, str) and location in v:
                good = True
                break

        if automated_mode:
            # Print the found mapping then exit
            if good:
                print(f"\'{location}\': \'{info[info_keys[0]]}\',")
                break
            elif i == len(m.shapes_info)-1:
                print(f"\'{location}\': None,")
                break

        elif good:
            # Print all the found shape info for manual inspection then continue looking for potential shape info points
            for k, v in info.items():
                sys.stdout.buffer.write(f'{k}: {v}\n'.encode('utf-8'))
            print('------------------------------------------', flush=True)
