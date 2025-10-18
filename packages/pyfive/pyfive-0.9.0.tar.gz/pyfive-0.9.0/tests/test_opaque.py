import os

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import pyfive
import h5py


def test_opaque_dataset1_hdf5(name, data):

    # Verify that h5py can read this file before we do
    # our own test. If this fails, pyfive cannot be 
    # expected to get it right.

    (ordinary_data, string_data, opdata) = data

    with h5py.File(name, "r") as f:
        dset = f["opaque_datetimes"]
        assert_array_equal(dset[...], opdata.astype(h5py.opaque_dtype(opdata.dtype)))

    # Now see if pyfive can do the right thing
    with pyfive.File(name) as hfile:
        # check data
        dset = hfile["opaque_datetimes"]
        # pyfive should return the same raw bytes that h5py wrote
        # but in the instance that it is tagged with NUMPY, 
        # pyfive automatically fixes it, which it should be for this example.
        assert_array_equal(dset[...], opdata)

        # make sure the other things are fine
        assert_array_equal(hfile['string_data'][...],string_data)
        assert_array_equal(hfile['ordinary_data'][...],ordinary_data)

        # check the dtype interrogation functions

        assert pyfive.check_opaque_dtype(dset.dtype) is True
        assert pyfive.check_enum_dtype(dset.dtype) is None
        assert pyfive.check_opaque_dtype(hfile['ordinary_data'].dtype) is False
        assert pyfive.check_dtype(opaque=hfile['ordinary_data'].dtype) is False
        assert pyfive.check_dtype(opaque=hfile['opaque_datetimes'].dtype) is True
        assert pyfive.check_dtype(opaque=hfile['opaque_datetimes'].dtype) is True
        assert pyfive.check_dtype(opaque=hfile['opaque_datetimes'].dtype) is True
        assert pyfive.check_dtype(enum=hfile['string_data'].dtype) is None
        assert pyfive.check_dtype(vlen=hfile['string_data'].dtype) is not None       
        assert pyfive.check_dtype(vlen=hfile['ordinary_data'].dtype) is None

        dt = hfile['ordinary_data'].dtype
        with pytest.raises(NotImplementedError):
            pyfive.check_dtype(ref=dt)

        with pytest.raises(TypeError):
            pyfive.check_dtype(fred=1,jane=2)

def test_opaque_dataset2_fixed(really_opaque):

    name, original_data = really_opaque


    with h5py.File(name, "r") as f:
        dset = f["opaque_data"]
        assert dset.shape == (3,)
        assert dset.dtype == np.dtype('V64')

        for i, blob in enumerate(original_data):
            assert dset[i].tobytes().startswith(blob)
        

    with pyfive.File(name) as hfile:
        dset = hfile['opaque_data']
        assert dset.shape == (3,)
        assert dset.dtype == np.dtype('V64')

        for i, blob in enumerate(original_data):
            assert dset[i].tobytes().startswith(blob)

        assert pyfive.check_opaque_dtype(dset.dtype) is True
        assert pyfive.check_dtype(opaque=dset.dtype) is True
        assert pyfive.check_enum_dtype(dset.dtype) is None


@pytest.fixture(scope='module')
def really_opaque(modular_tmp_path):
    """ Create an HDF5 file with a fixed size opaque dataset. """
    name = modular_tmp_path / "opaque_fixed.hdf5"

    with h5py.File(name, "w") as f:
        # Define a fixed-size opaque dtype as NumPy void
        max_len = 64  # bytes per element
        dt = np.dtype(f"V{max_len}")  # 'V' = void type

        # Create dataset
        dset = f.create_dataset("opaque_data", shape=(3,), dtype=dt)

        data = [
            b"hello world",
            b"\x01\x02\x03\x04custombinarydata",
            bytes(range(10))
        ]

        for i, blob in enumerate(data):
            buf = blob[:max_len].ljust(max_len, b'\x00')
            dset[i] = np.void(buf)
    
    return name , data  


@pytest.fixture(scope='module')
def data():
    """Provide datetime64 array data."""
    ordinary_data = np.array([1, 2, 3], dtype='i4')
    #string_data = np.array([b'one', b'two', b'three'], dtype='S5')
    dt = h5py.special_dtype(vlen=str)
    string_data = np.array(['one', 'two', 'three'], dtype=dt)
    opaque_data =  np.array([
            np.datetime64("2019-09-22T17:38:30"),
            np.datetime64("2020-01-01T00:00:00"),
            np.datetime64("2025-10-04T12:00:00"),
        ])

    data = (ordinary_data, string_data, opaque_data)
    
    return data


@pytest.fixture(scope='module')
def name(data, modular_tmp_path):
    """Create an HDF5 file with datetime64 data stored as opaque."""
    name = modular_tmp_path / "opaque_datetime.hdf5"

    (ordinary_data, string_data, opdata) = data

    # Convert dtype to an opaque version (as per h5py docs)
    # AFIK this just adds {'h5py_opaque': True} to the dtype metadata
    # without which h5py cannot write the data.

    opaque_data = opdata.astype(h5py.opaque_dtype(opdata.dtype))
   
    # Want to put some other things in the file too, so we can exercise
    # some of the other code paths.
   
    with h5py.File(name, "w") as f:
        f["opaque_datetimes"] = opaque_data
        f['string_data'] = string_data
        f['ordinary_data'] = ordinary_data

    return name


