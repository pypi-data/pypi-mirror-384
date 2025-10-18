""" Deprecated
"""

from math import ceil, floor
import mmap
from os import path as P
import numpy as NP
import h5py as H5PY
import datetime as DT
from time import time
from filefinder import FileFinder, to_posix_timestamp_ms
from chunk import Chunk

#/wave/seismic-work/markhoff/pilot/data/cache/7wave7seismic-rawdata7OPTA7Disk27DESY-Rec-9-GL8m-Chan10000_2021-05-28T06_01_36+01007DESY-Rec-9-GL8m-Chan10000_2021-05-28T194319Z.h5.bin
FILE_TIME_SAMPLE_AMOUNT = 60000
CHANNEL_AMOUNT = 10000
DATA_ROOT = "/wave/seismic-work/markhoff/pilot/data/cache"
assert P.isdir(DATA_ROOT)

def _filename_to_posix_timestamp(file_name:str) -> int:
    return to_posix_timestamp_ms(DT.datetime.strptime(file_name[-25:], "%Y-%m-%dT%H%M%SZ.h5.bin"))



def _load_from_h5(file_path, rel_t_start, rel_t_end, t_step, channel_start, channel_end, channel_step) -> NP.ndarray:
    """ Internal helper function """
    #file_handle = open(file_path, 'rb')
    #file:H5PY.File = H5PY.File(file_handle, 'r')
    #data = file['Acquisition']['Raw[0]']['RawData'] # Data is not loaded into memory at this point! (Lazy evaluation)
#
    ## At this point the data gets loaded into memory.
    #data = data[
    #        channel_start : channel_end : channel_step, 
    #        rel_t_start : rel_t_end : t_step
    #]

    DTYPE_SIZE = 4
    data = None
    #if channel_step == 1:
    #    data = NP.fromfile(
    #        file_path,
    #        dtype = NP.int32,
    #        offset = channel_start * FILE_TIME_SAMPLE_AMOUNT * DTYPE_SIZE,
    #        count = (channel_end-channel_start) * FILE_TIME_SAMPLE_AMOUNT
    #    )
    #    data.shape = (channel_end-channel_start, FILE_TIME_SAMPLE_AMOUNT)
    #    data = data[:, rel_t_start:rel_t_end:t_step]
    #else:
    #    data = NP.ndarray(
    #        shape=(
    #            ceil((channel_end - channel_start) / channel_step),
    #            FILE_TIME_SAMPLE_AMOUNT
    #        ),
    #        dtype=NP.int32
    #    )
    #    file_handle = open(file_path, 'rb')
    #    data_index = 0
    #    for channel_index in range(channel_start, channel_end, channel_step):
    #        file_handle.seek(channel_index * FILE_TIME_SAMPLE_AMOUNT)
    #        channel_data = NP.frombuffer(file_handle.read(FILE_TIME_SAMPLE_AMOUNT))
    #        data[data_index] = channel_data
    #        data_index += 1
    #    file_handle.close()
    #    data = data[:, rel_t_start:rel_t_end:t_step]

    data = NP.fromfile(
        file_path,
        dtype = NP.int32,
        offset = channel_start * FILE_TIME_SAMPLE_AMOUNT * DTYPE_SIZE,
        count = (channel_end-channel_start) * FILE_TIME_SAMPLE_AMOUNT
    )
    data.shape = (channel_end-channel_start, FILE_TIME_SAMPLE_AMOUNT)
    data = data[::channel_step, rel_t_start:rel_t_end:t_step]

    print("Args (channel):", channel_start, channel_end, channel_step)
    print("Args (time):", rel_t_start, rel_t_end, rel_t_end)
    print("Fresh after loading: ", data.shape)
    data = data.transpose() # Extremely efficient :)
    return data

def _load_from_h5_X(file_path, rel_t_start, rel_t_end, t_step, channel_start, channel_end, channel_step) -> NP.ndarray:
    DTYPE_SIZE = 4
    t1 = time()
    mm = NP.memmap(file_path, dtype=NP.int32, mode='readonly')
    mm.shape = (CHANNEL_AMOUNT, FILE_TIME_SAMPLE_AMOUNT)
    t2 = time()
    data = mm[channel_start:channel_end:channel_step, rel_t_start:rel_t_end:t_step]
    t3 = time()
    data = NP.array(data)
    t4 = time()
    data = data.transpose() # Extremely efficient :)
    t5 = time()
    print("DELTAS", t2-t1, t3-t2, t4-t3, t5-t4)
    #print("Args (channel):", channel_start, channel_end, channel_step)
    #print("Args (time):", rel_t_start, rel_t_end, rel_t_end)
    #print("Fresh after loading: ", data.shape)
    return data

FILE_FINDER = FileFinder(DATA_ROOT, ".h5.bin", _filename_to_posix_timestamp)


def create_chunk():
    return Chunk( 
                FILE_FINDER, 
                CHANNEL_AMOUNT, 
                FILE_TIME_SAMPLE_AMOUNT, 
                True, 
                8,
                False,
                _load_from_h5
            )
