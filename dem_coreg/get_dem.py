#! /usr/bin/env python
"""
Script to automatically download global dem from OpenTopography.

Lei Guo.
Central South University
05/07/2021
"""
# To do:

import sys
import os
import argparse
import subprocess
import math

from osgeo import gdal, ogr
from pygeotools.lib import geolib


def getparser():
    parser = argparse.ArgumentParser(description="Download DEM raster using specified spatial extent",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-src_fn', type=str, default=None, help='Source file to specify the extent(shp/raster/KML)')
    parser.add_argument('-src_fn_list', type=str, default=None, help='File list to specify the DEM required')
    parser.add_argument('-extent', type=float, nargs=4, default=None,
                        help='Specified extent in degree: (minlon, minlat, maxlon, maxlat)')
    parser.add_argument('-dem_type', type=str, default='SRTMGL1_E',
                        choices=["SRTMGL3", "SRTMGL1", "SRTMGL1_E", "AW3D30", "AW3D30_E", "NASADEM", "COP30", "COP90"],
                        help='DEM type you want to download')
    parser.add_argument('-outdir', type=str, default='.', help='Output directory')
    return parser


def main():
    parser = getparser()
    args = parser.parse_args()

    src_fn = args.src_fn
    src_fn_list = args.src_fn_list
    extent = args.extent

    dem_type = args.dem_type

    outdir = args.outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    if src_fn is None and extent is None and src_fn_list is None:
        sys.exit("Missing input. Either Source file or extent should be given!")

    if extent is not None:
        url = get_dem_url(extent=extent, dem_type=dem_type)

    elif src_fn is not None:
        extent = get_extent(src_fn)
        url = get_dem_url(extent=extent, dem_type=dem_type)
    else:
        f = open(src_fn_list)
        fn_list = [line.strip('\n') for line in f.readlines()]
        f.close()
        url = []
        for fn in fn_list:
            extent = get_extent(fn)
            url_tmp = get_dem_url(extent=extent, dem_type=dem_type)

            outprefix = os.path.splitext(os.path.split(fn)[-1])[0]
            outprefix = os.path.join(outdir, outprefix)
            out_fn = outprefix + '_' + dem_type + '.tif'
            url.append(url_tmp)
            url.append(' out='+out_fn)
        out_file = open('dem_url_list.txt', 'w')
        for line in url:
            out_file.write(str(line))
            out_file.write('\n')
        out_file.close()

    if isinstance(url, str) is True:
        outprefix = os.path.splitext(os.path.split(src_fn)[-1])[0]
        outprefix = os.path.join(outdir, outprefix)
        out_fn = outprefix + '_' + dem_type + '.tif'

        cmd = ['aria2c', '-c', '-s', '5', url, '-o', out_fn]
    else:
        cmd = ['aria2c', '-c', '-s', '5', '-j', '3', '-i', 'dem_url_list.txt', '--save-session=err_list']
    subprocess.call(cmd)


def get_extent(src_fn):
    """get extent from source file, using the pygeotools package
    """

    wgs_srs = geolib.wgs_srs

    suffix = os.path.splitext(src_fn)[-1]
    if suffix in ('.shp', '.kml'):
        ds = ogr.Open(src_fn)
        lyr = ds.GetLayer()
        shp_srs = lyr.GetSpatialRef()
        # fix bugs in kml srs comparasion due to segfault
        if suffix == '.shp' and not shp_srs.IsSame(wgs_srs):
            lyr = geolib.lyr_proj(lyr, t_srs=wgs_srs).GetLayer()
        extent = geolib.lyr_extent(lyr)
    elif suffix == '.tif':
        ds = gdal.Open(src_fn)
        extent = geolib.ds_extent(ds, t_srs=wgs_srs)
    else:
        sys.exit("Error input. Source file must be of shp/kml or Geotiff format!")
    return extent


def get_dem_url(extent=None, dem_type='SRTMGL1_E'):
    """ return opentopo api url to download dem
    """
    # enlarge the extent
    minlon = int(extent[0] * 100) / 100 - 0.1
    minlat = int(extent[1] * 100) / 100 - 0.1
    maxlon = math.ceil(extent[2] * 100) / 100 + 0.1
    maxlat = math.ceil(extent[3] * 100) / 100 + 0.1

    url_pre = 'https://portal.opentopography.org/API/globaldem?'

    url = url_pre + 'demtype=' + dem_type + '&south=' + str(minlat) + '&north=' + str(maxlat) + \
          '&west=' + str(minlon) + '&east=' + str(maxlon) + '&outputFormat=GTiff'

    api_dem = ['NASADEM', 'COP30', 'COP90']
    api_key = '72dbcf229895ba05856406e6aed5c39f'
    if dem_type in api_dem:
        url = url + '&API_Key=' + api_key

    return url


if __name__ == "__main__":
    main()
