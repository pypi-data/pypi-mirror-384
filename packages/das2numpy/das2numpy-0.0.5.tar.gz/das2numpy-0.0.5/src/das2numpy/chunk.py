"""
    See docstring of class Chunk.

    Benchmark Optasense (measurements in seconds):
    TIME for loading one whole file using h5py: 12.864407300949097 
    TIME for loading the first 1000 sensors from 10 files: 6.066787958145142 
    TIME for loading with sensor_step=10 from 10 files: 23.70387291908264 
    TIME for loading 100 sensors from 100 files 8.697869777679443
    TIME for loading 1000 sensors from 100 files 92.85049629211426 
    TIME for loading 40 files completely 278.97754430770874 
"""
from typing import Callable
from math import floor
from datetime import datetime
from random import shuffle
from multipledispatch import dispatch
import concurrent.futures as CF
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import numpy as NP
from .filefinder import FileFinder, to_posix_timestamp_ms


SHUFFLE_TASKS = False

def _predict_size(start: int, end: int, step: int) -> int:
    diff = end - start
    return int(((diff-1) - (diff-1)%step) / step + 1)




class Chunk():
    """ 
        Class for efficient loading and storing data 
        After the data is loaded, using one of the load...(...) methods,
        the data and the meta information can be accessed directly by accessing the following fields:
        data, timestamps, geo_positions, channel.
        TODO implement geo_positions, channel, timestamps
        author: ingrabarbosa, Erik genthe
    """


    def __init__(self, 
                file_finder:FileFinder,
                sample_rate,
                file_channel_amount:int, 
                multithreaded:bool, 
                workers:int,
                workerprocess:bool, 
                loading_function:Callable[[str, int, int, int, int, int, int], NP.ndarray]
                ):
        self.__file_finder = file_finder
        self.__sample_rate = sample_rate
        self.__file_channel_amount = file_channel_amount
        self.__multithreaded = multithreaded
        self.__workerprocess = workerprocess
        self.__loading_function = loading_function
        assert type(sample_rate) == int
        if multithreaded:
            self.__executor = ThreadPoolExecutor(workers)
        if not self.__multithreaded:
            print("Warning: Chunk is not in multiprocessing or multithreading mode!")



    def __load_from_file_into_data(self, 
                file_timestamp:int, # The timestamp retrieved from the filename
                file_path:str, 
                t_start:int, 
                t_end:int, 
                t_step:int, 
                channel_start:int, 
                channel_end:int, 
                channel_step:int
                ) -> None:
        #print("Args: ", file_timestamp, file_path, t_start, t_end, t_step, channel_start, channel_end, channel_step)
         # Check if the whole file shall be loaded. Especially the first and last file could be cut...
        print("das2numpy: Loading from", file_path)
        

        # Load h5-data using a different process... There is no other way to make h5py work parallel :(
        data = None
        if self.__workerprocess:
            pool = Pool(1)
            result = pool.apply_async(self.__loading_function, 
                    (file_path, file_timestamp, t_start, t_end, t_step, channel_start, channel_end, channel_step))
            pool.close()
            data = result.get() # Blocks!
        else:
            data = self.__loading_function(file_path, file_timestamp, t_start, t_end, t_step, channel_start, channel_end, channel_step)
        
        # Store loaded data part into all_data
        start_index = int((file_timestamp - t_start) * self.__sample_rate / 1000 / t_step)
        #print(start_index)
        if start_index < 0:
            start_index = 0
        #print("Shape: ", data.shape)

        # To make this a little bit tolerant to a changing amount of channels per file, also the number of channels is given!
        n_channels = min(data.shape[1], self.data.shape[1])
        if data.shape[1] != self.data.shape[1]:
            print(f"Warning: Incosistend amount of channels detected in file {file_path}. Expected={self.data.shape[1]}, file={data.shape[1]}. Cropping to fit.")
        self.data[start_index : start_index + data.shape[0], 0:n_channels] = data[:,:n_channels]
    
    @dispatch(int, int, int, int, int, int)
    def load_array_posix_ms(self, t_start: int, t_end: int, t_step: int, channel_start: int, channel_end: int, channel_step: int) -> NP.ndarray:
        """ Loading data
            Warning: using a different value then 1 for t_step or channel_step can result in a high cpu-usage.
                    Consider using multithreaded=True in the constructor and a high amount of workers if needed.
            Constraints: 
                t_start has to be less or equal t_end, 
                same for channel_start and channel_end.
                t_step and channel_step have to be greater then 0
            Args:
                t_start (int): A posix timestamp in ms which defines the start of the data to load.
                t_end (int): A posix timestamp in ms which defines the end of the data to load.
                t_step (int): If you, for example only want to load the data of every fourth timestep use t_end=4
                channel_start (int): The starting index of sensor in the data (inclusive).
                channel_end (int): The ending index of sensors in the data (exclusive).
                channel_step (int): Like t_step, but for the sensor position.
            Returns:
                Data as a numpy array
        """

        assert channel_start >= 0
        assert channel_start <= self.__file_channel_amount
        if channel_end == -1:
            channel_end = self.__file_channel_amount
        assert channel_end >= channel_start
        assert channel_end <= self.__file_channel_amount, "channel_end has to be less or equal than self.__file_channel_amount"
        assert t_step > 0
        assert channel_step > 0

        file_pathes = self.__file_finder.get_range_posix(t_start, t_end)
        print(f"Loading data from {len(file_pathes)} files.")
        #print("file_pathes", file_pathes)
        data_shape = (
                _predict_size(t_start * self.__sample_rate / 1000, t_end * self.__sample_rate / 1000, t_step),
                _predict_size(channel_start, channel_end, channel_step)
        )
        self.data = NP.zeros(shape=data_shape, dtype=NP.float32)
        if self.__multithreaded:
            futures = []
            if SHUFFLE_TASKS:
                shuffle(file_pathes)
            for file_timestamp, file_path in file_pathes:
                futures.append(
                    self.__executor.submit(
                        self.__load_from_file_into_data,
                        file_timestamp,
                        file_path,
                        t_start,
                        t_end,
                        t_step,
                        channel_start,
                        channel_end,
                        channel_step
                    )
                )

            for future in CF.as_completed(futures):
                future.result() # Raises possible exceptions

        else:
            for file_timestamp, file_path in file_pathes:
                self.__load_from_file_into_data(
                        file_timestamp,
                        file_path,
                        t_start,
                        t_end,
                        t_step,
                        channel_start,
                        channel_end,
                        channel_step)
        
        # The following is weird, but it solves issues with garbage collection. Otherwise this behaves like a memory leak.
        data = self.data
        del self.data
        return data





    @dispatch(datetime, datetime, int, int)
    def load_array(self, t_start:datetime, t_end:datetime, channel_start:int, channel_end:int) -> NP.ndarray:
        """ Loads data and returns it as a numpy array. 
            Constraints: 
                t_start has to be less or equal t_end, 
                same for channel_start and channel_end.
            Args:
                t_start (datetime): datetime object which defines the start of the data to load.
                t_end (datetime): datetime object which defines the end of the data to load.
                channel_start (int): The starting index of sensor in the data (inclusive).
                channel_end (int): The ending index of sensors in the data (exclusive).
            Returns:
                A 2d-numpy-array containing the data.
                The first axis corresponds to the time, the second to the channel
        """
        return self.load_array(t_start, t_end, 1, channel_start, channel_end, 1)


    @dispatch(datetime, datetime, int, int, int, int)
    def load_array(self, t_start:datetime, t_end:datetime, t_step:int, channel_start:int, channel_end:int, channel_step:int) -> NP.ndarray:
        """ Loading data into numpy array.
            Returns nothing, the data can be accessed by accessing the data field of this instance.
            Warning: using a different value then 1 for t_step or channel_step can result in a high cpu-usage.
                    Consider using multithreaded=True in the constructor and a high amount of workers if needed.
            Constraints: 
                t_start has to be less or equal t_end, 
                same for channel_start and channel_end.
                t_step and channel_step have to be greater then 0
            Args:
                t_start (datetime): datetime object which defines the start of the data to load.
                t_end (datetime): datetime object which defines the end of the data to load.
                t_step (int): If you, for example only want to load the data of every fourth timestep use t_end=4
                channel_start (int): The starting index of sensor in the data (inclusive).
                channel_end (int): The ending index of sensors in the data (exclusive).
                channel_step (int): Like t_step, but for the sensor position.
            Returns:
                A 2d-numpy-array containing the data.
                The first axis corresponds to the time, the second to the channel
        """
        return self.load_array_posix_ms(to_posix_timestamp_ms(t_start), to_posix_timestamp_ms(t_end), t_step, channel_start, channel_end, channel_step)


    @dispatch(int, int, int, int)
    def load_array_posix_ms(self, t_start:int, t_end:int, channel_start:int, channel_end:int) -> NP.ndarray:
        return self.load_array_posix_ms(t_start, t_end, 1, channel_start, channel_end, 1)


