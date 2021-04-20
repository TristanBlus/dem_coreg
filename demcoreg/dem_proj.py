#! /usr/bin/env python

import sys
import os

import argparse
from osgeo import gdal, osr
from pygeotools.lib import warplib, geolib


def getparser():
    parser = argparse.ArgumentParser(description="Perform image reprojection: WGS ——> UTM or Other ——> WGS",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('src_fn', type=str, help='Source image to be reprojected')
    parser.add_argument('-outdir', default='.', help='Output directory')
    parser.add_argument('-dst_ndv', type=int, default=0, help='NoData value of output image')
    return parser


def main():
    parser = getparser()
    args = parser.parse_args()

    if len(sys.argv[1:]) == 0:
        sys.exit("Usage: %s [src_fn] [-outdir] [-dst_ndv]" % os.path.basename(sys.argv[0]))

    src_fn = args.src_fn
    src_ds = gdal.Open(src_fn)
    print(src_fn)

    outdir = args.outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    dst_ndv = args.dst_ndv

    outprefix = os.path.splitext(os.path.split(src_fn)[-1])[0]

    wgs_srs = geolib.wgs_srs
    ds_srs = geolib.get_ds_srs(src_ds)

    if ds_srs.IsSame(wgs_srs):
        geom = geolib.ds_geom(src_ds)
        t_srs = geolib.get_proj(geom)
        t_srs_str = t_srs.ExportToProj4().strip()
        # try to fix bugs in geolib.get_proj due to datum missing
        if 'ellps' in t_srs_str:
            t_srs_str = t_srs_str.replace('ellps', 'datum')
            t_srs = osr.SpatialReference()
            t_srs.ImportFromProj4(t_srs_str)
        dst_fn = outprefix + '_utm.tif'
    else:
        t_srs = wgs_srs
        dst_fn = outprefix + '_wgs.tif'

    print('\nOriginal Coordinate System:\n %s\n' % ds_srs.ExportToProj4().strip())
    print('Destination Coordinate System:\n %s\n' % t_srs.ExportToProj4().strip())

    src_src_ds_align = warplib.diskwarp(src_ds, t_srs=t_srs, outdir=outdir, dst_fn=dst_fn, dst_ndv=dst_ndv)

    print('Reprojection process is done.\n')
    print('Output file: %s' % os.path.join(outdir, dst_fn))


if __name__ == "__main__":
    main()
