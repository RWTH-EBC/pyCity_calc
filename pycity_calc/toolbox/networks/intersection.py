# coding=utf-8
"""
Script calculates intersection point between point and linestring
"""

import warnings

import shapely.geometry.point as pnt
import shapely.geometry.linestring as lstr


def calc_dist_point_to_linestr(point, linestr):
    """
    Calculate distance between shapely point and linestring.

    Parameters
    ----------
    point : object
        Shapely point object
    linestr : object
        Shapely LineString object

    Returns
    -------
    dist : float
        Distance between point and linestring
    """

    dist = point.distance(linestr)

    return dist


def calc_closest_point_w_linestr(point, linestr):
    """
    Calculate closest point between shapely LineString and Point.

    Parameters
    ----------
    point : object
        Shapely point object
    linestr : object
        Shapely LineString object

    Returns
    -------
    closest_point : object
        Shapely point object, which is on LineString and closest to target
        point
    """

    closest_point = linestr.interpolate(linestr.project(point))

    return closest_point


def calc_closest_point_w_list_linestr(point, list_lstr):
    """
    Calculate closest point between list of shapely LineStrings and point

    Parameters
    ----------
    point : object
        Shapely point object
    list_lstr : list (of LineString object)
        List of shapely LineString objects

    Returns
    -------
    closest_point : object
        Shapely point object, which is on LineString and closest to target
        point
    """

    #  Dummy distance value
    min_dist = calc_dist_point_to_linestr(point, list_lstr[0]) + 100000
    closest_point = None

    for i in range(len(list_lstr)):

        #  Current LineString
        curr_lstr = list_lstr[i]

        #  Current distance between point and current LineString
        curr_dist = calc_dist_point_to_linestr(point, curr_lstr)

        #  If distance is smaller than current min. distance, replace it
        if curr_dist < min_dist:
            min_dist = curr_dist

            closest_point = calc_closest_point_w_linestr(point, curr_lstr)

    return closest_point


def get_lstr_points(point, linestr):
    """
    Returns start and stop points of LineString for point on LineString.
    This point results out of perpendicular connection between input parameter
    point and input parameter linestr.
    If no perpendicular connection exists, returns None.

    Parameters
    ----------
    point : object
        Shapely point object
    linestr : object
        Shapely LineString object

    Returns
    -------
    tup_coord : tuple (of tuples)
        Tuple of coordinates (start and stop point of LineString segment)
    """

    tup_coord = None

    inter = linestr.intersection(point)

    #  Check if point is on linestring
    if inter.is_empty:

        wrnmsg = 'No point-linestring perpendicular connection found. Going' \
                 'to return None (get_lstr_points in intersection.py).'
        warnings.warn(wrnmsg)

        return tup_coord

    for i in range(len(linestr.coords[:])):

        tup_1 = linestr.coords[i]
        tup_2 = linestr.coords[i + 1]

        #  Check if point is on linestring of
        curr_lstr = lstr.LineString([tup_1, tup_2])

        #  if point is on segment, break for loop
        if curr_lstr.intersection(point).is_empty is False:
            tup_coord = (tup_1, tup_2)
            break

    return tup_coord


def get_lstr_points_list(point, list_linestr):
    """
    Returns start and stop points of LineString for perpendicular connection
    point on LineString

    Parameters
    ----------
    point : object
        Shapely point object
    linestr : list (of LineString object)
        List of shapely LineString objects

    Returns
    -------
    tup_coord : tuple (of tuples)
        Tuple of coordinates (start and stop point of LineString segment)
    """

    #  Dummy value
    min_dist = calc_dist_point_to_linestr(point, list_linestr[0]) + 1000000000

    for i in range(len(list_linestr)):

        curr_lstr = list_linestr[i]

        curr_dist = calc_dist_point_to_linestr(point, curr_lstr)

        if curr_dist < min_dist:
            min_dist = curr_dist

            tup_coord = get_lstr_points(point, curr_lstr)

    return tup_coord


if __name__ == '__main__':
    #  #------------------------------------------------------------------

    #  Define points
    P1 = pnt.Point(10, 0)
    P2 = pnt.Point(10, 10)
    P3 = pnt.Point(20, 5)
    P4 = pnt.Point(20, 15)
    P5 = pnt.Point(0, 25)
    P6 = pnt.Point(20, 25)

    # Define segments
    S1 = lstr.LineString([(P1.x, P1.y), (P2.x, P2.y)])
    S2 = lstr.LineString([(P3.x, P3.y), (P4.x, P4.y)])
    S3 = lstr.LineString([(P5.x, P5.y), (P6.x, P6.y)])

    list_seg = [S1, S2, S3]  # Test case 1

    target_point = pnt.Point(10, 20)

    complex_lstr = lstr.LineString([(P1.x, P1.y), (P2.x, P2.y),
                                    (P3.x, P3.y), (P4.x, P4.y),
                                    (P5.x, P5.y), (P6.x, P6.y)])

    target_point2 = pnt.Point(20, 25)

    #  #------------------------------------------------------------------

    print('Find closest point between point ' + str(target_point)
          + ' and linestring ' + str(S1))
    closest_point = calc_closest_point_w_linestr(target_point, S1)
    print('Closest point: ', closest_point)
    print()

    print('Find distance between point ' + str(target_point)
          + ' and linestring ' + str(S1))
    dist = calc_dist_point_to_linestr(target_point, S1)
    print('Distance: ', dist)
    print()

    print('Find closest point between point ' + str(target_point)
          + ' and list of linestrings ' + str(list_seg))
    closest_point = calc_closest_point_w_list_linestr(target_point, list_seg)
    print('Closest point: ', closest_point)
    print()

    print('Find start and stop coordinates of linestring segment, where'
          ' target point is placed on (complex_lstr):')
    tup_coord = get_lstr_points(target_point, complex_lstr)
    print('Coordinates: ', tup_coord)
    print()

    print('Find start and stop coordinates of linestring segment, where'
          ' target point 2 is placed on (list_seg):')
    tup_coord = get_lstr_points_list(target_point2, list_seg)
    print('Coordinates: ', tup_coord)
    print()
