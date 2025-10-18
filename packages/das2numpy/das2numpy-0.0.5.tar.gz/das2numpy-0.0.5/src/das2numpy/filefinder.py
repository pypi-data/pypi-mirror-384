""" See class docstring FileFinder """


import pickle as PICKLE
import os as OS
import datetime as DT
from typing import Callable
from time import time # For debug

USE_CACHE_FILE = False

def to_posix_timestamp_ms(timestamp:DT.datetime) -> int:
    """
        Takes a datetime-object and returns the posix timestamp in milliseconds.
    """
    return int(timestamp.timestamp()*1000)

instance_counter = 0    # Caution: This is a CLASS-Variable.

class FileFinder():
    """
        Class for finding the required files for given time-ranges.
        @author: Erik Genthe
        @since: 04.01.2022
    """

    # Time complexities.
    # Source: https://wiki.python.org/moin/TimeComplexity
    # list append() -> O(1)
    # list len() -> O(1)
    # list get() -> O(1)

    def __init__(self, root_path:str, file_suffix:str, filename_to_posixtimestamp:Callable[[str], int]):
        global instance_counter
        self.instance_number = instance_counter
        instance_counter += 1
        self.__root_path = root_path
        self.__file_pathes = []
        self.__cache_path = OS.path.dirname(__file__) + "/pathes_cache" + str(self.instance_number)

        if USE_CACHE_FILE and OS.path.exists(self.__cache_path):
            f = open(self.__cache_path, 'rb')
            self.__file_pathes = PICKLE.load(f)
            f.close()
        else:
            time_start = time()
            for pathlist in OS.walk(root_path):
                for file_name in pathlist[2]:
                    if file_name.endswith(file_suffix):
                        posix_timestamp_ms = filename_to_posixtimestamp(file_name)
                        path = OS.path.join(pathlist[0], file_name)
                        self.__file_pathes.append((posix_timestamp_ms, path))
            self.__file_pathes.sort()
            time_end = time()
            print(f"Filefinder: Time used for creating file list: {time_end-time_start} seconds for {len(self.__file_pathes)} files.")
            if USE_CACHE_FILE:
                f = open(self.__cache_path, 'wb')
                PICKLE.dump(self.__file_pathes, f)
                f.close()

        if self.__file_pathes == []:
            raise RuntimeError(f"Error: No {file_suffix} files found in {root_path} and its subdirectories.")


    def __find_nearest_before(self, posix_timestamp_ms: int) -> tuple:
        """Method __find_neares_before(self, posix_timestamp_ms)
        Time complexity: O(n)  (n := number of files)
        TODO reduce to O(log(n)). This can be easily done.

        Args:
            posix_timestamp_ms (int): The posix timestamp in milliseconds to base the search on.
        Returns:
            tuple: A triple (internal_index, posix timestamp in millis of the file start, file path)
            None: If the given time was before any recording was done.
        """
        for i in range(len(self.__file_pathes)-1, 0, -1): # Iterate reverse
            key, value = self.__file_pathes[i]
            if key < posix_timestamp_ms:
                return (i, key, value)
        return None


    def get_range(self, t_start:DT.datetime, t_end:DT.datetime) -> list:
        """
            See method get_range_posix.
        """
        return self.get_range_posix(to_posix_timestamp_ms(t_start), to_posix_timestamp_ms(t_end))


    def get_range_posix(self, t_start:int, t_end:int) -> list:
        """Gets the files that contain the data for a given time-range.
        Args:
            t_start (int): Starting time of the requested range
            t_end (int): Ending time of the requested range
        Returns:
            tuple:  A list containing tuples. 
                    First element of each tuple is the posix timestamp in ms of the start of the file, 
                    Second element of each tuple is the path of the file.
        """
        assert isinstance(t_start, int)
        assert isinstance(t_end, int)
        assert t_start <= t_end, f"t_start={t_start} is supposed to be less or equal t_end={t_end}"
        first = self.__find_nearest_before(t_start)
        last = self.__find_nearest_before(t_end)
        if first is None:
            first = (0,)
        if last is None:
            return []
        return self.__file_pathes[ first[0] : last[0] + 1 ]


    def get_elem(self, index) -> tuple:
        if len(self.__file_pathes) == 0:
            raise Exception(f"No data files found in root directory: {self.__root_path}")
        return self.__file_pathes[index]