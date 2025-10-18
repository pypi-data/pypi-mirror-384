""" Univsersal setup file for silixa, that detects sampling rate and number of channels by itself. 
The root directory shall be supplied by the user via an argument
"""

import sys as SYS
from os import path as P
import datetime as DT
import numpy as NP
from ..filefinder import FileFinder, to_posix_timestamp_ms
from ..chunk import Chunk
from .light_tdms_reader import TdmsReader
from ..utils import bin

CALIBRATE = True





def init(root_path, num_worker_threads):
    assert P.isdir(root_path)
    file_finder = FileFinder(root_path, ".tdms", filename_to_posix_timestamp)
    example_file_path = file_finder.get_elem(0)[1] #TODO is this still needed? I think the channel number can be adjusted on-the-fly
    tdms = TdmsReader(example_file_path)
    shape = tdms.get_mmap().shape
    file_time_sample_amount = shape[0]
    channel_amount = shape[1]
    assert num_worker_threads >= 1
    multithreaded = num_worker_threads > 1
    sample_rate = 1000
    return Chunk(
                file_finder,
                sample_rate,
                channel_amount, 
                multithreaded,
                num_worker_threads,
                False,
                load_file
            )

def filename_to_posix_timestamp(file_name:str) -> int:
    timestamp_str = file_name.split("_UTC_")[1][:19]
    timestamp_dt = DT.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S.%f")
    timestamp_ms = to_posix_timestamp_ms(timestamp_dt)
    return timestamp_ms


def load_file(file_path, file_timestamp, t_start, t_end, t_step, channel_start, channel_end, channel_step) -> NP.ndarray:
    """ Loads a single file, trims it. And returns the trimmed data as a numpy array. Downsampling (t_step, channel_step) is also possible!
    """
    
    with TdmsReader(file_path) as tdms:
        data = tdms.get_mmap()


        # Trim data
        rel_t_start = 0
        if t_start > file_timestamp: # Check if beginning should be trimmed.
            rel_t_start = t_start - file_timestamp
        rel_t_end = -1 
        if t_end < file_timestamp + data.shape[0]: # Check if end should be trimmed
            rel_t_end = t_end - file_timestamp
        if rel_t_start == rel_t_end:
            return NP.zeros(shape=[0, 0]) # No data should be loaded. Do nothing
        if file_timestamp + data.shape[0] <= t_start:
            print("Warning: File does not contain any parts of the requested data.",
                    "This can happen if there are leaks in the data. The corresponding output will be left filled with zeros.\n",
                    f"    Requested range (Posixtimestamps in ms): [{t_start}, {t_end}[\n",
                    f"    Filepath: {file_path}.")
            return NP.zeros(shape=[0, 0])
        assert rel_t_end == -1 or rel_t_end > rel_t_start, f"rel_t_start={rel_t_start}, rel_t_end={rel_t_end}."
        data = data[rel_t_start:rel_t_end, channel_start:channel_end]


        # Downsample data
        if t_step != 1 or channel_step != 1:
            data = bin(data, (t_step, channel_step))
        #if t_step != 1:
        #    data = data[::t_step]
        #if channel_step != 1:
        #    data = data[:, ::channel_step]
        assert len(data) > 0

        if CALIBRATE:
            data = calibrate(data)

    return data





def calibrate(data:NP.ndarray) -> NP.ndarray:
    """ Convert raw data to strain rate data. 
    As the resulting values are decimals, the datatype should be float. Otherwise an assertion fails. """
    #assert data.dtype in (NP.float, NP.float32, NP.float64), f"The data should be floating point. It is {data.dtype}"
    if data.dtype not in (float, NP.float32, NP.float64):
        NEW_TYPE = NP.float32
        #print("Warning: For calibration the data has to be of type float. Converting from {data.dtype} to {NEW_TYPE}")
        data = data.astype(NEW_TYPE)

    SAMPLE_FREQ = 1000.0
    EICHLAENGE = 10.0
    factor = 116.0 * 10.0**(-9.0) / 8192.0 * SAMPLE_FREQ / EICHLAENGE
    return data * factor # Result: 1 / s




