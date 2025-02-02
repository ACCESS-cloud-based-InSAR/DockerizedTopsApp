from pathlib import Path

import numpy as np
import rasterio
from isce.components.isceobj.Alos2Proc.runDownloadDem import download_wbd
from shapely.geometry import box
from tile_mate import get_raster_from_tiles

from .localize_dem import fix_image_xml


def download_water_mask(
    extent: list, water_mask_name: str = "pekel_water_occurrence_2021", buffer: float = 0.1
) -> dict:
    output_dir = Path(".").absolute()

    extent_geo = box(*extent)
    extent_buffered = list(extent_geo.buffer(buffer).bounds)
    extent_buffered = [
        np.floor(extent_buffered[0]),
        np.floor(extent_buffered[1]),
        np.ceil(extent_buffered[2]),
        np.ceil(extent_buffered[3]),
    ]

    if water_mask_name == 'esa_world_cover_2021_10m':
        X, p = get_raster_from_tiles(extent_buffered, tile_shortname='esa_world_cover_2021')
        mask = (X == 80).astype(np.uint8)
        mask[mask.astype(bool)] = 255
        mask_filename = 'water_mask_derived_from_esa_world_cover_2021_10m.geo'

        # Remove esa nodata, change gdal driver to ISCE, and generate VRT as in localize DEM
        p_isce = p.copy()
        p_isce['nodata'] = None
        p_isce['driver'] = 'ISCE'

        with rasterio.open(mask_filename, 'w', **p_isce) as ds:
            ds.write(mask)

        mask_filename = fix_image_xml(mask_filename)

    elif water_mask_name == 'pekel_water_occurrence_2021':
        X, p = get_raster_from_tiles(extent_buffered, tile_shortname='pekel_water_occ_2021')
        mask = (X >= 95).astype(np.uint8)
        mask[mask.astype(bool)] = 255
        mask_filename = 'water_mask_derived_from_pekel_water_occurrence_2021_with_at_least_95_perc_water.geo'

        # Remove esa nodata, change gdal driver to ISCE, and generate VRT as in localize DEM
        p_isce = p.copy()
        p_isce['nodata'] = None
        p_isce['driver'] = 'ISCE'

        with rasterio.open(mask_filename, 'w', **p_isce) as ds:
            ds.write(mask)

        mask_filename = fix_image_xml(mask_filename)

    elif water_mask_name == "SWBD":
        # Download SRTM-SWDB water mask
        # Water mask dataset extent
        # Latitude S55 - N60

        lats = [extent_buffered[1], extent_buffered[3]]
        if (np.abs(lats) < 59.9).all():
            mask_filename = download_wbd(
                extent_buffered[1],
                extent_buffered[3],
                extent_buffered[0],
                extent_buffered[2],
            )
            mask_filename = str(output_dir / mask_filename)
        else:
            print('Request out of SWBD coverage ',
                  'Skip downloading water mask!!')
            mask_filename = ''

    else:
        raise NotImplementedError("Water mask not available")

    return {"water_mask": mask_filename}
