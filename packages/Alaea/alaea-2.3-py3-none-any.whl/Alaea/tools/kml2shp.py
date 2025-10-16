#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2024/11/6 16:32
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

https://mp.weixin.qq.com/s/UDBQYQgErxUxNJvWc2E1LA
"""

import warnings
from osgeo import ogr

warnings.warn('This module has not been checked yet', UserWarning)


def convert_kml_to_shp(in_file, out_file):
    """
    Converts a KML file to a shapefile using GDAL/OGR.

    Args:
        in_file (str): Path to the input KML file.
        out_file (str): Path to the output SHP file.
    """
    # Open the KML file using OGR
    ds_in = ogr.Open(in_file)
    if ds_in is None:
        print(f"Failed to open {in_file}")
        return

    layer = ds_in.GetLayer(0)

    # Get the spatial reference of the source layer
    srs = layer.GetSpatialRef()

    # Create the output shapefile
    ds_out = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(out_file)
    if ds_out is None:
        print(f"Failed to create {out_file}")
        return

    # Copy the layer definition
    layer_defn = layer.GetLayerDefn()
    layer_out = ds_out.CreateLayer('output', srs=srs, geom_type=layer_defn.GetGeomType())

    # Copy the fields
    for i in range(layer_defn.GetFieldCount()):
        field_defn = layer_defn.GetFieldDefn(i)
        layer_out.CreateField(field_defn)

    # Get the Feature Definition for the output layer
    feat_defn = layer_out.GetLayerDefn()

    # Process each feature in the input layer
    for feat_in in layer:
        # Create a new feature
        feat_out = ogr.Feature(feat_defn)

        # Set the geometry
        feat_out.SetGeometry(feat_in.GetGeometryRef())

        # Set the attributes
        for i in range(feat_defn.GetFieldCount()):
            feat_out.SetField(feat_defn.GetFieldDefn(i).GetNameRef(), feat_in.GetField(i))

        # Create the feature in the output layer
        layer_out.CreateFeature(feat_out)

        # Clean up
        feat_out = None

    # Clean up
    ds_out = None
    ds_in = None

    print(f"{in_file} converted to {out_file}")


if __name__ == '__main__':
    shapefile = r'D:\temp\create_shp_by_fiona1.shp'
    kml_file = r'D:\temp\create_shp_by_fiona.kml'
    convert_kml_to_shp(kml_file, shapefile)
