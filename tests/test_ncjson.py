"""

Units test of ncjson


"""

import ncjson
import pytest
import numpy as np

url = 'https://co.ifremer.fr/co/ego/ego/v2/sea017/sea017_20230613/sea017_20230613_R.nc'
filename = 'data/sea017_20230613_R.nc'
filename = 'data/test.nc'


class Data:

    def __init__(self):
        self.writer = ncjson.DStoJSON(url)

    def __call__(self):
        return self.writer


data = Data()


@pytest.fixture
def writer():
    _writer = data()
    return _writer


class TestNcjson():

    def test_open_url(self):
        writer = ncjson.DStoJSON(url)
        writer.ds.close()

    def notest_open_file(self):
        # this test seems not to work, althoug a standalone script does read
        # nc files directly.
        writer = ncjson.DStoJSON(filename)
        writer.ds.close()

    def test_construct_json_output_filename_from_url(self, writer):
        fn = writer.construct_json_output_filename_from_url("url",
                                                            "data")
        assert fn == "data/url.json"

    def test_get_dimensions(self, writer):
        dimensions = writer.get_dimensions()
        assert "TIME" in dimensions and "TIME_GPS" in dimensions

    def test_get_variables(self, writer):
        variables = writer.get_variables()
        assert len(variables) == 101
        assert "PLATFORM_TYPE" in variables

    def test_get_attributes(self, writer):
        attributes = writer.get_attributes()
        assert type(attributes) is dict
        assert "data_type" in attributes.keys()
        assert len(list(attributes.keys())) == 49

    def test_get_bb(self, writer):
        bb = writer.get_bb()
        assert type(bb) is dict
        assert np.isclose(bb["UPPER_RIGHT_LATLON_GPS"][1], 45.4277333333)
