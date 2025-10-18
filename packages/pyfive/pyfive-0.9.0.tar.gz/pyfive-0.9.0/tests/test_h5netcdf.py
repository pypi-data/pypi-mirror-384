# tests the variables found in the file h5netcdf_test.hdf5,
# which is produced by the write_h5netcdf test routine in the h5netcdf package
#
import os

import pyfive
import h5py
import warnings
from pathlib import Path

DIRNAME = Path(__file__).parent

def test_file_contents():
    fpath = os.path.join(DIRNAME, 'data', 'h5netcdf_test.hdf5')
    p5file = pyfive.File(fpath) 
    h5file = h5py.File(fpath)

    expected_variables = [
        "foo",
        "z",
        "intscalar",
        "scalar",
        "mismatched_dim",
        "foo_unlimited",
         "var_len_str",
        "enum_var",
    ]

    cannot_handle = ['var_len_str', 'enum_var']

    p5contents = set([a for a in p5file])
    h5contents = set([a for a in h5file])

    assert p5contents == h5contents

    for x in list(set(expected_variables) - set(cannot_handle)):
        try:
            # check we can get the variable
            p5x, h5x = p5file[x], h5file[x]
            if p5x is None:
                warnings.warn(f'Had to skip {x}')
          
            if isinstance(h5x,h5py.Dataset):
                # check the dtype
                assert p5x.dtype == h5x.dtype
                # check the shape
                assert p5x.shape == h5x.shape
                # now look into the details
                if h5x.shape != ():
                    # do the values match
                    sh5x = str(h5x[:])
                    sp5x = str(p5x[:])
                    assert sh5x == sp5x
                # what about the dimensions?
                dh5x = h5x.dims
                dp5x = p5x.dims
                assert len(dh5x) == len(dp5x)
                print(p5x)
        except:
            print('Attempting to compare ',x)
            print(h5file[x])
            print(p5file[x])
            raise

    # check dereferencing
    ref1 = p5file["foo"].attrs["DIMENSION_LIST"][0][-1]
    assert p5file["x"].id == p5file[ref1].id
    assert str(p5file["x"][:]) == str(p5file[ref1][:])

    ref2 = p5file["subgroup/subvar"].attrs["DIMENSION_LIST"][0][-1]
    assert p5file["x"].id == p5file[ref2].id
    assert str(p5file["x"][:]) == str(p5file[ref2][:])

    assert p5file[ref1].id == p5file[ref2].id
    assert str(p5file[ref1][:]) == str(p5file[ref2][:])

    ref3 = p5file["subgroup/y_var"].attrs["DIMENSION_LIST"][0][-1]
    assert p5file["subgroup/y"].id == p5file[ref3].id
    assert str(p5file["subgroup/y"][:]) == str(p5file[ref3][:])
    assert p5file["y"].id != p5file[ref3].id
