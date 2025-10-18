"""
Deprecated
"""

from os import path as P
import numpy as NP
import h5py as H5PY
import datetime as DT
from ..filefinder import FileFinder, to_posix_timestamp_ms
from ..chunk import Chunk


FILE_TIME_SAMPLE_AMOUNT = 60000
CHANNEL_AMOUNT = 10000
DATA_ROOT = "/wave/seismic-rawdata/OPTA"
NUM_WORKER_THREADS = 16
CALIBRATE = True
assert P.isdir(DATA_ROOT)

def _filename_to_posix_timestamp(file_name:str) -> int:
    return to_posix_timestamp_ms(DT.datetime.strptime(file_name[-21:], "%Y-%m-%dT%H%M%SZ.h5"))



def _load_from_h5(file_path, rel_t_start, rel_t_end, t_step, channel_start, channel_end, channel_step) -> NP.ndarray:
    """ Internal helper function """
    file_handle = open(file_path, 'rb')
    file:H5PY.File = H5PY.File(file_handle, 'r')
    data = file['Acquisition']['Raw[0]']['RawData'] # Data is not loaded into memory at this point! (Lazy evaluation)

    # At this point the data gets loaded into memory.
    data = data[
            channel_start : channel_end : channel_step, 
            rel_t_start : rel_t_end : t_step
    ]

    # To numpy and transpose...
    data = NP.array(data)
    data = data.transpose() # Extremely efficient :)
    file.close()
    file_handle.close()

    # Calibrate
    data = _calibrate(data)
    return data



def _calibrate(data:NP.ndarray) -> NP.ndarray:
    """ Convert raw data to strain data. 
    As the resulting values are decimals, the datatype should be float. Otherwise an assertion fails. """
    assert data.dtype in (NP.float, NP.float32, NP.float64), "The data should be floating point."

    # The parameters and the formula are aquired from the Optasense user manual.
    # If samples are stored as integer values the sample value’s unit is “rad*10430.378850470453”.
    # To obtain phase shift values in “rad” divide each sample value by 10430.378850470453
    # data /= 10430.378850470453
    #
    # delta_phase_shift_in_rad = 4 * pi * groupindex * gaugelength * scaling_factor * strain / wavelength
    # wavelength = 1550 / 1000 / 1000 / 1000 # Meters. "OptaSenses ODH DAS systems operate at a wavelength of 1550 nm"
    # groupindex = 1.468 #TODO inprecise # "The fiber’s refractive index can vary with fiber type, it is typically in the vicinity of 1.468"
    # gaugelength = 10 # Meters
    # scaling_factor = 0.78
    # delta_phase_shift_in_rad = data
    # strain = delta_phase_shift_in_rad * wavelength / 4 / 3.141 / groupindex / gaugelength / scaling_factor
    # print("Factor: ", wavelength / 4 / 3.141 / groupindex / gaugelength / scaling_factor, 1 / (wavelength / 4 / 3.141 / groupindex / gaugelength / scaling_factor))
    # data *= wavelength / 4 / 3.141 / groupindex / gaugelength / scaling_factor
    # Result: Strain [Dimensionless, m/m]

    GAUGELENGTH = 10
    OMN_2       = 10430.378350470453
    OMN_WAVELENGTH   = 1550e-9
    OMN_N       = 1.4682
    OMN_X       = 0.78

    OPTASENSE_CAL = OMN_WAVELENGTH / 4 / pi / OMN_N / GAUGELENGTH / OMN_X / OMN_2
    return data * OPTASENSE_CAL


FILE_FINDER = FileFinder(DATA_ROOT, ".h5", _filename_to_posix_timestamp)

def create_chunk():
    return Chunk( 
                FILE_FINDER, 
                CHANNEL_AMOUNT, 
                FILE_TIME_SAMPLE_AMOUNT, 
                True,
                16,
                True,
                _load_from_h5
            )
