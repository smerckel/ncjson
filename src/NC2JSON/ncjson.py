#!/usr/bin/env python3

import argparse
import json
import sys
import os

import fsspec
import xarray as xr
import numpy as np

# fs = fsspec.filesystem('https')
# url = 'https://co.ifremer.fr/co/ego/ego/v2/sea017/sea017_20230613/sea017_20230613_R.nc'
# fs.size(url)/1e6
# ds = xr.open_dataset(fs.open(url))
# ds


class DStoJSON():
    '''
    Xarray Dataset to JSON converter

    A class to convert most fields in a netCDF file to a JSON format. Arrays with (many) floats are omitted, and
    represented by an empty list.
    
    Parameters
    ----------
    url : str
        url to nc file
    json_output_filename : str
        name of json file for output. If not given, the filename is constructed from the url.
    json_output_directory : str
        name of the directory to write the json files in. Only applies if json_output_filename is not given.
    write_to_stdout : bool {False}
        if set to True, the information is also output to stdout.


    Ideally this class should be used in a context, taking care of closing the netCDF file.

    >>> with DStoJSON(url) as writer:
    >>>     writer.write_json()
    
    '''
    MAXARRAYSIZE = 15 # we will process arrays with text, possibly contaminated with floats/nans, just to a depth of this value.
    
    def __init__(self, url, json_output_filename='', json_output_directory='.'):
        self.json_output_filename = json_output_filename or self.construct_json_output_filename_from_url(url, json_output_directory)
        self.config=dict(indent=4, ensure_ascii=False, allow_nan=True)
        try: # see if there is a local file
            self.ds = xr.open_dataset(url, decode_times=False)
        except OSError:
            # if no local file can be opened, try a webservice
            fs = fsspec.filesystem('https')
            self.ds = xr.open_dataset(fs.open(url), decode_times=False)

            
    def __enter__(self, *p, **kwd):
        return self

    
    def __exit__(self, *p, **kwd):
        self.ds.close() # I think I don't understand this xarray,
                        # because this does not seem to close the
                        # file.
                        

    def construct_json_output_filename_from_url(self, url, json_output_directory):
        # given the url and the output directory, an output filename
        # is constructed. Any non-existing direcotries are made on the
        # fly.
        os.makedirs(json_output_directory, exist_ok=True) # Creates dir if not exising.
        json_output_filename = os.path.join(json_output_directory, os.path.basename(url)+'.json')
        return json_output_filename

            
    def write_json(self, write_to_stdout=False):
        ''' Writes JSON file. '''
        json_dict = {"dimensions":self.get_dimensions(),
                     "dimensions_without_coords":self.get_dimensions_without_coords(),
                     "variables":self.get_variables(),
                     "attributes":self.get_attributes(),
                     "bounding_box":self.get_bb()
                     }
        s = json.dumps(json_dict, **self.config)
        with open(self.json_output_filename, 'w') as fp:
            fp.write(s)
        if write_to_stdout:
            print(s)


    def get_dimensions(self):
        dimensions = self._get_dimensions(True)
        return dimensions

    
    def get_dimensions_without_coords(self):
        dimensions = self._get_dimensions(False)
        return dimensions

    
    def get_variables(self):
        variables = {}
        # instead of self.ds.data_vars, there is also
        # self.ds.variables, which includes data_vars, + {'LATITUDE',
        # 'LONGITUDE', 'PRES', 'TIME', 'TIME_GPS'}
        for k, v in self.ds.data_vars.items():
            if v.shape == (): # zero-sized array
                _v = v.item()
                dtype = type(_v) # float/bytes it seems?
                if dtype == bytes:
                    variables[k] = self._bytes_decoder(_v)
                else:
                    variables[k] = _v # this could be nan, need to make json.dump aware of this.
            else:
                vp = []
                for i in range(min(v.size, DStoJSON.MAXARRAYSIZE)): 
                    _v = v.item(i)
                    if type(_v) == bytes:
                        # we can decode this one. Possibly.
                        s = self._bytes_decoder(v.item(i))
                        if s:
                            vp.append(s)
                    else:
                        vp.append(_v)
                variables[k] = vp
        return variables

    
    def _get_latlon(self, coordinate):
        values = self.ds.data_vars[f"{coordinate.upper()}_GPS"].values
        qc = self.ds.data_vars['POSITION_GPS_QC'].values
        values = values.compress(qc)
        return np.min(values), np.max(values)

    
    def get_bb(self):
        values = self.ds.coords["TIME_GPS"].values
        qc = self.ds.data_vars['TIME_GPS_QC'].values
        values = values.compress(qc)
        tm_min, tm_max = np.min(values), np.max(values)
        lat_min, lat_max = self._get_latlon('latitude')
        lon_min, lon_max = self._get_latlon('longitude')
        d = dict(TIME_GPS_MIN = tm_min,
                 TIME_GPS_MAX = tm_max,
                 LOWER_LEFT_LATLON_GPS = (lat_min, lon_min),
                 UPPER_RIGHT_LATLON_GPS = (lat_max, lon_max),
                 )
        return d
                 
        
    def get_attributes(self):
        attributes = dict([(k,v) for k,v in self.ds.attrs.items()])
        return attributes

    
    def _bytes_decoder(self, bs):
        # method to decode a byte string. It can be that some strings
        # cannot be decoded, because of invalid characters. This
        # method replaces these characters by "?"
        try:
            s = bs.decode('utf-8')
        except UnicodeError as e:
            if e.reason=='invalid start byte' or e.reason=='invalid continuation byte':
                # So we have at least one byte that causes the
                # decoding to fail. Fix this, and call the decoding
                # funtion again, in case there is another byte that
                # will break the decoding. This uses a recursive
                # algorithm.
                b = [i for i in bs] # make a list of bytes, that we can manipulate.
                for i in range(e.start, e.end):
                    b[i] = 63 # 'corresponds to "?"
                s = self._bytes_decoder(bytes(b)) # create a bytestring again using bytes.
            else:
                # we got an unexpected decode error. Reraise the exception so we know what happened.
                raise e
        return s.strip() # remove any trailing white spaces.
    
    
    def _get_dimensions(self, s):
        dimensions = [k for k in self.ds.dims if bool(self.ds.get(k).coords)==s]
        return dimensions


url = 'https://co.ifremer.fr/co/ego/ego/v2/sea017/sea017_20230613/sea017_20230613_R.nc'
json_output_filename = 'test.json'

#url = sys.argv[1]
#json_output_filename = 'JSON/NC/'+os.path.basename(url)+'.json'

# json_output_filename = sys.argv[2]

with DStoJSON(url) as writer:
    writer.write_json(write_to_stdout=True)

Q    
# url = 'https://co.ifremer.fr/co/ego/ego/v2/sea017/sea017_20230613/sea017_20230613_R.nc'
# json_output_filename = 'test.json'

#url = sys.argv[1]
#json_output_filename = 'JSON/NC/'+os.path.basename(url)+'.json'

# json_output_filename = sys.argv[2]

# with DStoJSON(url) as writer:
#     writer.write_json(json_output_filename)
#     writer.write_json(sys.stdout)


parser = argparse.ArgumentParser(prog='ProgramName',
                                 description='What the program does',
                                 epilog='Text at the bottom of help')

parser.add_argument('url', help='help text')                               # positional argument
parser.add_argument('-o', '--json_output_filename', help="help")      # option that takes a value
parser.add_argument('-d', '--json_output_directory', help="make note only applies when outputfile is constructed from url. if -o option is given, this is ignored.")      # option that takes a value
parser.add_argument('-s', '--write_to_stdout', help="help", action='store_true')
# or if you want to write by default, but have the option to suppress
# parser.add_argument('-s', '--write_to_stdout', action='store_false') # you may want to rename write_to_stdout, here and below, though.
args = parser.parse_args()

if 0: # does not close the file  
    writer = DStoJSON(args.url,
                      args.json_output_filename,
                      args.json_output_directory,
                      args.write_to_stdout)
    writer.write_json()
else: # does close the file: better.
    with DStoJSON(args.url,
                  args.json_output_filename,
                  args.json_output_directory,
                  args.write_to_stdout) as writer:
        writer.write_json()



