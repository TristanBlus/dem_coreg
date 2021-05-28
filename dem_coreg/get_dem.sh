#! /bin/bash
#################   This script was part of the   #################
################# <dem_coreg> processing workflow #################
#################     Lei Guo,  CSU 28/05/2021    #################

# proj='EPSG:4326'
# lyr=$(basename ${outfile%.*})
# ogr2ogr -t_srs $proj -overwrite -f '-f 'ESRI Shapefile' -nln $lyr $outfile $shp

dem_type=SRTMGL1_E
usage() {
	echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	echo " `basename $0`: multiple elevation source download. "
	echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	echo ""
	echo -e "Usage:\n`basename $0` <dem_type> <-s src_fn> [-e extent] [-o out_fn]\n"
	echo "-d dem_type    (input) dem datasets need to get"
	echo "                SRTMGL1_E(default)   SRTMGL1"
	echo "                NASADEM              SRTMGL3"
	echo "                AW3D30_E             AW3D30"
	echo "                COP30                COP90"
	echo "-s src_fn   (input) Source file to specify the extent(shp/raster)"
	echo "-e extent   (input) Specified extent: 'minlon, minlat, maxlon, maxlat'"
	echo "-o out_fn   (output) output name of downloaded DEM geotiff"
	echo ""
	exit 1
}

# predifined funciton
get_extent() {
    src_fn=$1
    ext="${src_fn##*.}"
    if [[ $ext == 'tif' ]]; then

        gdalinfo $src_fn > src_info
        limits_1=`awk '/Upper Left/{print}' src_info`
        limits_2=`awk '/Lower Right/{print}' src_info`
        minlon=`echo "$limits_1" |awk -F '[" ",()]'+ '{print $3}'`
        maxlat=`echo "$limits_1" |awk -F '[" ",()]'+ '{print $4}'`
        maxlon=`echo "$limits_2" |awk -F '[" ",()]'+ '{print $3}'`
        minlat=`echo "$limits_2" |awk -F '[" ",()]'+ '{print $4}'`
        rm -rf src_info
    
    elif [[ $ext == 'shp' ]]; then

        ogrinfo -al -so $src_fn > src_info
        minlon=`awk -F '[,)( ]' '/Extent:/{print $3}' src_info`
        minlat=`awk -F '[,)( ]' '/Extent:/{print $5}' src_info`
        maxlon=`awk -F '[,)( ]' '/Extent:/{print $9}' src_info`
        maxlat=`awk -F '[,)( ]' '/Extent:/{print $11}' src_info`
        rm -rf src_info

    else
        echo -e "ERROR: unsupported source file(shp/geotiff): $src_fn \n"
        exit 1
    fi

    extent="$minlon, $minlat, $maxlon, $maxlat"
    echo $extent
    return
}

get_dem_url() {
    extents=$2
    dem_type=$1
  
    minlon=`echo $extents | awk -F',' '{print $1*100/100-0.1}'`
    minlat=`echo $extents | awk -F',' '{print $2*100/100-0.1}'`
    maxlon=`echo $extents | awk -F',' '{print $3*100/100+0.1}'`
    maxlat=`echo $extents | awk -F',' '{print $4*100/100+0.1}'`
  
    url_pre='https://portal.opentopography.org/API/globaldem?'
  
    url=${url_pre}'demtype='${dem_type}'&south='${minlat}'&north='${maxlat}'&west='${minlon}'&east='${maxlon}'&outputFormat=GTiff'
  
    api_dem='NASADEM COP30 COP90'
    api_key='72dbcf229895ba05856406e6aed5c39f'
  
    if [[ $api_dem =~ $dem_type ]]; then
  	    url=${url}'&API_Key='${api_key}
    fi
  
    echo $url
    return
}

while getopts "d:s:e:o:" opt
do
	case $opt in
		d)
            dem_type=$OPTARG
		    echo "dem_type: $OPTARG";;
		s)
		    src_fn=$OPTARG
		    echo "src_fn: $OPTARG";;
	    e)
		    extent=$OPTARG
		    echo "extent: ${extent}";;
	    o)
		    out_fn=$OPTARG
		    echo "out_fn: ${out_fn}";;
	    ?)
		  echo "ERROR option: ${OPTARG}"
		  usage;;
	esac
done

# check parameters
dem_choice="SRTMGL1_E SRTMGL1 NASADEM SRTMGL3 AW3D30_E AW3D30 COP30 COP90"

if [[ -z $dem_type || ! $dem_choice =~ $dem_type ]]; then
	echo -e "Error Input: dem_type musted be input correctely!\n"
	exit 1
fi

if [[ -z $src_fn && -z $extent ]]; then
	echo -e "Extent error: src_fn/extent needed to specified at least one!\n"
	usage
	exit 1
fi

if [[ -n $src_fn ]]; then
	extent=$(get_extent $src_fn)
	echo -e "Extent from specified source file:\n$extent\n"
elif [[ -n $extent ]]; then
	echo -e "Extent from user defined:\n$extent\n"
fi

dem_url=$(get_dem_url $dem_type "$extent")
echo -e "URL for Specified DEM:\n$dem_url\n"

if [[ -z $out_fn ]];then
	out_fn=$(basename ${src_fn%%.*})'_'${dem_type}'.tif'
fi

echo "Start Downloading...."
# Downloading
if [[ -n $dem_url ]];then
	aria2c -c -s 5 $dem_url -o $out_fn
fi
