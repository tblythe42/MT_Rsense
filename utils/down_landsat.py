"""
This module downloads landsat data.  Get the wrs (ascending)
from http://landsat.usgs.gov/worldwide_reference_system_WRS.php
select an area you want images for, save the selection and
pass shapefile to this program,
or just choose location coordinates
"""
import os
import requests.packages.urllib3
from osgeo import ogr
from datetime import datetime
from landsat import image, downloader, search

from vector_tools import lat_lon_to_ogr_point, get_path_row
from web_tools import lat_lon_to_path_row

requests.packages.urllib3.disable_warnings()


def download_landsat(start_end_tuple, satellite='L8', path_row_tuple=None, lat_lon_tuple=None,
                     shape=None, output_path=None,
                     dry_run=False, max_cloud=None, return_scenes=100):
    start_date, end_date = start_end_tuple[0], start_end_tuple[1]
    print 'Date range: {} to {}'.format(start_date, end_date)

    if shape:
        # assumes shapefile has a 'path' and a 'row' field
        ds = ogr.Open(shape)
        lyr = ds.GetLayer()
        image_index = get_path_row(lyr)
        assert type(image_index) == list
        print 'Downloading landsat by row/path shapefile: {}'.format(shape)

    elif lat_lon_tuple:
        point = lat_lon_to_ogr_point(lat, lon)
        image_index = [lat_lon_to_path_row(lat, lon)]
        print 'Downloading landsat by lat/lon: {}, {}'.format(lat, lon)

    elif path_row_tuple:
        path, row = path_row_tuple[0], path_row_tuple[1]
        image_index = [(path, row)]
        print 'Downloading landsat by path/row: {}, {}'.format(path, row)
        assert type(image_index) == list

    else:
        raise NotImplementedError('Must give path/row tuple, lat/lon tuple plus row/path \n'
                                  'shapefile, or a path/rows shapefile!')

    print 'Image Ind: {}'.format(image_index)

    for tile in image_index:
        path, row = tile[0], tile[1]
        searcher = search.Search()
        destination_path = os.path.join(output_path, 'd_{}_{}'.format(path, row))
        os.chdir(output_path)

        downer = downloader.Downloader(verbose=False, download_dir=destination_path)

        candidate_scenes = searcher.search(paths_rows='{},{},{},{}'.format(path, row, path, row),
                                           start_date=start_date,
                                           end_date=end_date,
                                           cloud_min=0,
                                           cloud_max=max_cloud,
                                           limit=return_scenes)

        print 'total images for tile {} is {}'.format(tile, candidate_scenes['total_returned'])

        x = 0

        if candidate_scenes['status'] == 'SUCCESS':
            for scene_image in candidate_scenes['results']:
                print 'Downloading:', (str(scene_image['sceneID']))
                if not dry_run:
                    try:
                        print 'Downloading tile {} of {}'.format(x, candidate_scenes['total_returned'])
                        downer.download([str(scene_image['sceneID'])])
                        image.Simple(
                            os.path.join(output_path, destination_path,
                                         '{}.tar.bz'.format(str(scene_image['sceneID']))))
                        x += 1
                    except downloader.RemoteFileDoesntExist:
                        print 'Skipping:', (str(scene_image['sceneID']))

        else:
            print 'nothing'

    print 'done'


if __name__ == '__main__':
    home = os.path.expanduser('~')
    print 'home: {}'.format(home)
    start = datetime(2013, 5, 1).strftime('%Y-%m-%d')
    end = datetime(2013, 9, 30).strftime('%Y-%m-%d')
    output = os.path.join(home, 'images', 'Landsat_8')
    poly = os.path.join(home, 'images', 'vector_data', 'wrs2_descending', 'path_rows_Z11.shp')
    lat, lon = 47.4, -109.5
    path_int, row_int = 36, 25
    download_landsat((start, end), shape=poly, dry_run=True,
                     output_path=output, max_cloud=70)

    # ===============================================================================
