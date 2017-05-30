#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze shapefiles (shp)
"""

import os
from osgeo import ogr
import shapefile


def load_shp_data(path, drivername='ESRI Shapefile'):
    """
    Returns shp file dataset

    Parameters
    ----------
    path : str
        Path to shp file
    drivername : str, optional
        ogr driver name (default: 'ESRI Shapefile')

    Returns
    -------
    shp : object
        shp data object
    """

    driver = ogr.GetDriverByName(drivername)
    return driver.Open(path)


def shp_analyze(shp):
    """
    Perform shp file analysis. Print spatial reference as well as
    names, types, width and precision of attributes.

    Parameters
    ----------
    shp : object
        Shapefile object
    """

    # Get Projection from layer
    layer = shp.GetLayer()
    spatialRef = layer.GetSpatialRef()
    print(spatialRef)

    # Get Shapefile Fields and Types
    layerDefinition = layer.GetLayerDefn()

    print("Name  -  Type  Width  Precision")
    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(
            fieldTypeCode)
        fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
        GetPrecision = layerDefinition.GetFieldDefn(i).GetPrecision()
        print(
            fieldName + " - " + fieldType + " " + str(fieldWidth) + " " + str(
                GetPrecision))


if __name__ == '__main__':

    #  shp filename
    filename = u'Gebäudetypologie.shp'

    this_path = os.path.dirname(os.path.abspath(__file__))
    path_input = os.path.join(this_path, 'input', filename)

    #  Load shapefile data
    shp_data = load_shp_data(path_input)

    #  Perform analysis
    shp_analyze(shp_data)

    #  Load data via shapefile
    sf = shapefile.Reader(path_input)  # Reading the Shapefile
    fields = sf.fields  # Reading the attribute fields
    records = sf.records()  # Reading the records of the features
    shapRecs = sf.shapeRecords()  # Read Geometry and Records simultaneously

    print('Records:')
    print('######################################################')
    for rec in shapRecs:
        print(rec.record)
    print()

    print('Geometry')
    print('######################################################')
    for rec in sf.iterShapes():
        x, y = rec.points[0]
        print(x, y)
