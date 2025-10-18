#! /usr/bin/env python

""" Create a HDF5 file with all the supported attribute types. """
import sys
import h5py
import numpy as np
from pathlib import Path


def create_file(path):

    with h5py.File(path, 'w') as f:
        attrs = f.attrs

        # integers
        attrs.create('int08_little', -123, dtype='<i1')
        attrs.create('int16_little', -123, dtype='<i2')
        attrs.create('int32_little', -123, dtype='<i4')
        attrs.create('int64_little', -123, dtype='<i8')

        attrs.create('uint08_little', 130, dtype='<u1')
        attrs.create('uint16_little', 32770, dtype='<u2')
        attrs.create('uint32_little', 2147483650, dtype='<u4')
        attrs.create('uint64_little', 9223372036854775810, dtype='<u8')

        attrs.create('int08_big', -123, dtype='>i1')
        attrs.create('int16_big', -123, dtype='>i2')
        attrs.create('int32_big', -123, dtype='>i4')
        attrs.create('int64_big', -123, dtype='>i8')

        attrs.create('uint08_big', 130, dtype='>u1')
        attrs.create('uint16_big', 32770, dtype='>u2')
        attrs.create('uint32_big', 2147483650, dtype='>u4')
        attrs.create('uint64_big', 9223372036854775810, dtype='>u8')

        # floating point
        attrs.create('float32_little', 123, dtype='<f4')
        attrs.create('float64_little', 123, dtype='<f8')

        attrs.create('float32_big', 123, dtype='>f4')
        attrs.create('float64_big', 123, dtype='>f8')

        # fixed-length strings
        attrs.create('string_one', b'H', dtype='|S1')
        attrs.create('string_two', b'Hi', dtype='|S2')

        # variable length strings
        attrs['vlen_string'] = b'Hello'

        # variable length unicode
        attrs['vlen_unicode'] = u'Hello' + chr(0x00A7)

        # arrayed numeric types
        attrs.create('int32_array', [-123, 45], dtype='<i4')
        attrs.create('uint64_array', [12, 34], dtype='>u8')
        attrs.create('float32_array', [123, 456], dtype='<f4')

        # arrayed variable length strings and bytes
        # see https://github.com/NCAS-CMS/pyfive/pull/102#discussion_r2393563713
        attrs['vlen_str_array'] = np.array([b'Hello', b'World!'], dtype="|S")
        attrs['vlen_str_array1'] = [b'Hello', b'World!']

        # variables length sequences
        val = np.empty((2, ), dtype=object)
        val[0] = np.array([-1, 2], dtype='<i4')
        val[1] = np.array([3, 4, 5], dtype='<i4')
        dt = h5py.special_dtype(vlen=np.dtype('<i4'))
        attrs.create('vlen_int32', val, dtype=dt)

        val = np.empty((3, ), dtype=object)
        val[0] = np.array([1, 2], dtype='>u8')
        val[1] = np.array([3, 4, 5], dtype='>u8')
        val[2] = np.array([42], dtype='>u8')
        dt = h5py.special_dtype(vlen=np.dtype('>u8'))
        attrs.create('vlen_uint64', val, dtype=dt)

        val = np.empty((3, ), dtype=object)
        val[0] = np.array([0, ], dtype='<f4')
        val[1] = np.array([1, 2, 3], dtype='<f4')
        val[2] = np.array([4, 5], dtype='<f4')
        dt = h5py.special_dtype(vlen=np.dtype('<f4'))
        attrs.create('vlen_float32', val, dtype=dt)

        # TODO more complex datatypes
        # complex H5T_COMPOUND
        attrs.create('complex64_little', 123+456.j, dtype='<c8')
        attrs.create('complex128_little', 123+456.j, dtype='<c16')

        attrs.create('complex64_big', 123+456.j, dtype='<c8')
        attrs.create('complex128_big', 123+456.j, dtype='<c16')

        # booleans  HT5_ENUM
        #attrs.create('bool', True, dtype=np.bool_)

        # H5T_ENUM
        # Define an enum dtype
        enum_dtype = h5py.special_dtype(
            enum=(np.int32, {'one': 1, 'two': 2, 'three': 3})
        )
        # Create an attribute with that enum dtype
        attrs.create('enum', 2, dtype=enum_dtype)

        # empty string with NULL dataspace
        # see https://github.com/NCAS-CMS/pyfive/issues/100
        attrs.create('empty_string', h5py.Empty(dtype=np.dtype('|S1')))


if __name__ == "__main__":
    default_path = Path(__file__).parent / "attr_datatypes.hdf5"
    filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    create_file(filepath)
