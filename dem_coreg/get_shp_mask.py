#! /usr/bin/env python

import sys
import os

import argparse
from osgeo import gdal, ogr
from pygeotools.lib import warplib, geolib, iolib


def getparser():
    parser = argparse.ArgumentParser(description="Clip shpfile to match the extent of input Geotiff",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('src_fn', type=str, help='Source image to provide extent')
    parser.add_argument('-shp_fn', type=str, default=None, help='Source shp to be clipped')
    parser.add_argument('-out_fn', type=str, help='Output filename of clipped shp')
    parser.add_argument('-outdir', default='.', help='Output directory')
    return parser


def main():
    parser = getparser()
    args = parser.parse_args()

    if len(sys.argv[1:]) == 0:
        sys.exit("Usage: %s [src_fn] [-out_fn] [-outdir]" % os.path.basename(sys.argv[0]))

    src_fn = args.src_fn
    src_ds = gdal.Open(src_fn)
    print(src_fn)

    outprefix = os.path.splitext(os.path.split(src_fn)[-1])[0]

    out_fn = args.out_fn
    if out_fn is None:
	    out_fn=outprefix + '_glac.shp'

    outdir = args.outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)


    wgs_srs = geolib.wgs_srs
    ds_srs = geolib.get_ds_srs(src_ds)
    
    shp_fn = args.shp_fn
    if shp_fn is None:
    	datadir = iolib.get_datadir()
    	shp_fn = os.path.join(datadir, 'gamdam/gamdam_merge_refine_line.shp')
    shp_ds = ogr.Open(shp_fn)
    lyr = shp_ds.GetLayer()
    lyr_srs = lyr.GetSpatialRef()
    shp_extent = geolib.lyr_extent(lyr)
    ds_extent = geolib.ds_extent(src_ds, t_srs=lyr_srs)
    if geolib.extent_compare(shp_extent, ds_extent) is False:
        geolib.clip_shp(shp_fn, extent=ds_extent, out_fn=out_fn)

    print('Reprojection process is done.\n')
    print('Output file: %s' % os.path.join(outdir, out_fn))


if __name__ == "__main__":
    main()
