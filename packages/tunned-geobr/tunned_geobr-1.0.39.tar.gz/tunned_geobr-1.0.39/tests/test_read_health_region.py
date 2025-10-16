import geopandas as gpd
import pytest
from geobr import read_health_region


def test_read_health_region():

    assert isinstance(read_health_region(), gpd.geodataframe.GeoDataFrame)

    with pytest.raises(Exception):
        read_health_region(year=9999999)


def test_read_health_region_macro():

    assert isinstance(read_health_region(macro=True), gpd.geodataframe.GeoDataFrame)

    with pytest.raises(Exception):
        read_health_region(year=9999999)
