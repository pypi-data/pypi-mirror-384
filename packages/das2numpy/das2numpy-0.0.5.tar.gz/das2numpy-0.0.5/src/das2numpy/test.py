"""
    Deprecated
    
    Unittests for this dataloader-module
    by Erik Genthe
    05.01.2022
"""
from math import ceil, floor
import sys as SYS
from os import path as P
import datetime as DT
import h5py as H5PY
import numpy as NP

try:
    import dataloader as D
except ModuleNotFoundError as e:
    raise RuntimeError("TO RUN THIS TEST, MOVE IT INTO THE PARENT DIR FIRST!") from e
from dataloader.filefinder import to_posix_timestamp_ms



def test_silixa_filefinder():
    #file_path = '/wave/seismic-rawdata/desy_12km_1m_P7gauss/desy_UTC_20210522_155121.950.tdms'
    #ls /wave/seismic-rawdata/desy_12km_1m_P7gauss -l | grep -n --invert-match 504946688

    # Find one specific file...
    time = DT.datetime(2021, 5, 30, 14, 00, 00)
    filelist = D.silixa.FILE_FINDER.get_range(time, time)
    assert len(filelist) == 1
    assert filelist[0][1].endswith('/desy_UTC_20210530_135950.619.tdms')

    # Find all files...
    filelist = D.silixa.FILE_FINDER.get_range_posix(0, D.to_posix_timestamp_ms(DT.datetime.now()))
    assert len(filelist) > 9000


def test_optasense_filefinder():
    # Find one specific file...
    time = DT.datetime(2021, 5, 30, 14, 00, 00)
    filelist = D.optasense.FILE_FINDER.get_range(time, time)
    assert len(filelist) == 1
    assert filelist[0][1].endswith('2021-05-30T135924Z.h5')

    # Find all files...
    filelist = D.optasense.FILE_FINDER.get_range_posix(0, D.to_posix_timestamp_ms(DT.datetime.now()))
    assert len(filelist) > 9000


def test_fast_optasense_filefinder():
    # Find one specific file...
    time = DT.datetime(2021, 5, 30, 14, 00, 00)
    filelist = D.fast_optasense.FILE_FINDER.get_range(time, time)
    assert len(filelist) == 1
    assert filelist[0][1].endswith('2021-05-30T135924Z.h5.bin')

    # Find all files...
    filelist = D.optasense.FILE_FINDER.get_range_posix(0, D.to_posix_timestamp_ms(DT.datetime.now()))
    assert len(filelist) > 9000



def test_chunk(chunk, MAX_CHANNEL):
    import time as TIME
    #MAX_CHANNEL = 12608
    #chunk = D.silixa.create_chunk()
    t_start: int =          to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00, 00))
    t_end1: int = to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00,  1))
    t_end2: int = to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14,  1, 30))
    t_end3: int = to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 10, 00))
    t_end_one_hour: int =   to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 15, 00, 00))
    print()

    chunk.load(t_start, t_end1, 1, 0, MAX_CHANNEL, 1)
    assert chunk.data.shape == (1000, MAX_CHANNEL)
    print()

    chunk.load(t_start, t_end2, 3, 0, MAX_CHANNEL, 9)
    assert chunk.data.shape == (30000, ceil(MAX_CHANNEL / 9))
    print()

    # Now some benchmarks...
    #bench_start = TIME.time()
    #file_handle = open("/wave/seismic-rawdata/OPTA/Disk2/DESY-Rec-11-GL8m-Chan10000_2021-05-30T07_55_42+0100/DESY-Rec-11-GL8m-Chan10000_2021-05-30T135924Z.h5", 'rb')
    #file:H5PY.File = H5PY.File(file_handle, 'r')
    #data = file['Acquisition']['Raw[0]']['RawData'] # Data is not loaded into memory at this point! (Lazy evaluation)
    #data = NP.array(data)
    #print("TIME for loading one whole file using h5py:", TIME.time() - bench_start, "\n")

    bench_start = TIME.time()
    chunk.load(t_start, t_end3, 1, 0, 1000, 1)
    print("Time for loading the first 1000 sensors of one hour of data: %4f\n" % (TIME.time() - bench_start))
    assert chunk.data.shape == (600000, 1000)

    bench_start = TIME.time()
    chunk.load(t_start, t_end_one_hour, 1, 0, MAX_CHANNEL, 10)
    print("Time for loading one hour of data with with sensor_step=10: %4f\n" % (TIME.time() - bench_start))
    assert chunk.data.shape == (1000*60*60, ceil(MAX_CHANNEL/10))

    bench_start = TIME.time()
    chunk.load(t_start, t_end_one_hour, 1, 0, 100, 1)
    print("Time for loading 100 sensors with 1 hour of data: %4f\n" % (TIME.time() - bench_start))

    bench_start = TIME.time()
    chunk.load(t_start, t_end_one_hour, 1, 0, 1000, 1)
    print("Time for loading 1000 sensors with 1 hour of data: %4f\n" % (TIME.time() - bench_start))

    bench_start = TIME.time()
    chunk.load(t_start, t_end_one_hour, 1, 0, MAX_CHANNEL, 1)
    print("Time for loading 1 hour completely: %4f\n" % (TIME.time() - bench_start))



def test_equalness_of_fast_opta_simple():
    t_start: int =  to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00, 00))
    t_end: int =    to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00,  1))

    chunk_fast = D.fast_optasense.create_chunk()
    chunk_fast.load(t_start, t_end, 1, 0, 10, 1)

    chunk_normal = D.optasense.create_chunk()
    chunk_normal.load(t_start, t_end, 1, 0, 10, 1)

    assert chunk_fast.data.shape == chunk_normal.data.shape
    assert NP.array_equiv(chunk_fast.data, chunk_normal.data)


def test_equalness_of_fast_opta():
    t_start: int =  to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00, 00))
    t_end: int =    to_posix_timestamp_ms(DT.datetime(2021, 5, 30, 14, 00,  1))

    chunk_fast = D.fast_optasense.create_chunk()
    chunk_fast.load(t_start, t_end, 3, 2000, 7000, 9)

    chunk_normal = D.optasense.create_chunk()
    chunk_normal.load(t_start, t_end, 3, 2000, 7000, 9)

    assert chunk_fast.data.shape == chunk_normal.data.shape
    assert NP.array_equiv(chunk_fast.data, chunk_normal.data)


if __name__ == '__main__':
    #test_equalness_of_fast_opta_simple()
    #test_equalness_of_fast_opta()
    #test_fast_optasense_filefinder()
    #test_silixa_filefinder()
    #test_optasense_filefinder()



    print("\nSilixa benchmark:")
    test_chunk(D.silixa.create_chunk(), 12608)

    print("\nFast Optasense benchmark:")
    test_chunk(D.fast_optasense.create_chunk(), 10000)

    #print("\nOptasense benchmark:")
    #test_chunk(D.optasense.create_chunk(), 10000)
