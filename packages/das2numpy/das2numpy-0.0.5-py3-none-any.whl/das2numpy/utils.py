"""
Everything, that modifies the signal.
author: Erik Genthe
"""

import math as M
import numpy as NP
from numba import njit
import scipy.signal as SS
import scipy.stats

TIME_AXIS = 0

@DeprecationWarning
def remove_channel_offset(data:NP.ndarray):
    """Removes a constant value from each channel from the data.
        Expecting the time-axis to be the first axis! 
        The constant values are initially calculated and save to a file.
    """  

    print("Warning! Untested function!") #TODO
    #for i in range(data.shape[1]):
    #    data[:,i] -= data[:,i].mean(dtype=data.dtype)
    data -= data.mean(axis=0)

@njit
def differentiate(data: NP.ndarray, axis: int) -> NP.ndarray:
    """Differentiate the 2-dimensional signal over one axis
     A 2-d array is expected as input
     The return-value is None. The array is copied, modified and returned.
     :return: differentiated array
    """
    assert axis == 0 or axis == 1
    data = data.copy()
    if data.shape[axis] < 2:
        raise Exception("Integration with less then two samples makes no sense.")
    if axis == 0:
        for i in range(0, data.shape[0]-1):
            data[i] = data[i+1] - data[i]
    elif axis == 1:
        for i in range(0, data.shape[1]-1):
            data[:,i] = data[:,i+1] - data[:,i]
    return data


def integrate(data: NP.ndarray, axis: int, sample_rate_hz:float) -> NP.ndarray:
    """Integrate the 2-dimensional signal over one axis
       A 2-d array is expected as input
       The array is copied, modified and returned.
       :return: integrated array
    """
    integral = NP.cumsum(data, axis=axis) / sample_rate_hz
    return integral


def butterworth_filter(
            array : NP.ndarray,
            freq : float, 
            order : int, 
            btype, #: {‘lowpass’, ‘highpass’}
            fs : float) -> NP.ndarray:
    """
    Apply a butterwort high-pass-filter on time-axis.
    :array: The input data. Two dimensions expected. First dimension is expected to be the time dimension.
    return: The filtered array
    """
    sos = SS.iirfilter(order, freq, rp=None, rs=None, btype=btype, analog=False, ftype='butter', output='sos', fs=fs)
    array = SS.sosfiltfilt(sos, array, axis=TIME_AXIS, padtype='odd', padlen=None)
    return array



def mean_confidence_interval(data, confidence=0.95, min_samples=10):
    """
        Calculates the confidence interval for a student-t distribution.
        From https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
        Returns: [mean, lower-confidence-limit, upper-confidence-limit]
    """
    n = len(data)
    m = NP.mean(data)
    if n < min_samples:
        return m, None, None
    se = scipy.stats.sem(data)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return m, m-h, m+h


def spectrum_smoothing(frequencies:NP.ndarray, psd:NP.ndarray, n:int, mode="median", error_calculation=False):
    """
    Perform 1/n decade smoothing on the power spectral density (PSD) data.
    See also:  https://dsp.stackexchange.com/questions/9967/1-n-octave-smoothing

    Parameters:
    frequencies : numpy.ndarray
        Array containing the frequency values.
    psd : numpy.ndarray
        Array containing the power spectral density values corresponding to the frequencies.
    n : int
        The number of divisions per decade (e.g., n=10 for 1/10 decade smoothing).
    mode : "mean" or "median"
        How the data points of one bin should be reduced to one point.
    error_calculation : False, "std", or float.
        If false, the function returns only two arrays.
        If "std", the third array contains the standard deviation of the original data points per frequency bin.
        If "stderr", the third array contains the standard error or the original data points per frequency bin.
        If float [0.0 until 1.0], the third array contains the confidence intervall for each frequency bin (EXPERIMENTAL). 
    
    Returns:
    numpy.ndarray, numpy.ndarray, numpy:ndarray
        Smoothed frequencies, the PSD, and the Standard deviation for each bin.
    """
    frequencies = NP.array(frequencies)
    psd = NP.array(psd)
    if frequencies[0] == 0.0:
        frequencies = frequencies[1:]
        psd = psd[1:]


    # Generate new frequency points:
    min_freq = frequencies[0]
    max_freq = frequencies[-1]
    min_freq_new_log = NP.floor(NP.log10(min_freq))
    max_freq_new_log = NP.ceil(NP.log10(max_freq))
    n_decades = int(max_freq_new_log - min_freq_new_log)
    freq_new = NP.logspace(min_freq_new_log, max_freq_new_log, num=n_decades*n+1, base=10)
    freq_new_log = NP.log10(freq_new)
    step_log = freq_new_log[1] - freq_new_log[0]

    freq_new_actual = []
    psd_new = []
    error = []
    for i in range(len(freq_new)):
        f_log = freq_new_log[i]
        f_lower = 10**(f_log - step_log / 2)
        f_higher = 10**(f_log + step_log / 2)

        # Find the indices within this log decade interval
        mask = (frequencies >= f_lower) & (frequencies < f_higher)
        if NP.any(mask):
            freq_new_actual.append(NP.mean(frequencies[mask]))
            if mode == "mean":
                mean = NP.mean(psd[mask])
                psd_new.append(mean)
            elif mode == "median":
                psd_new.append(NP.median(psd[mask]))
            else:
                raise Exception("Mode should be 'mean' or 'median'!")
            if error_calculation == False:
                pass
            elif error_calculation == "std":
                if len(psd[mask]) <= 1:
                    error.append(float("NaN"))
                else:
                    error.append(NP.std(psd[mask]))
            elif error_calculation == "stderr":
                if len(psd[mask]) <= 1:
                    error.append(float("NaN"))
                else:
                    error.append(NP.std(psd[mask]) / NP.sqrt(len(psd[mask])))
            elif type(error_calculation) == float:
                confidence_level = error_calculation
                assert confidence_level >= 0.5
                #samples = psd[mask]                    
                #n = len(samples)
                ##h = scipy.stats.sem(psd[mask]) * scipy.stats.t.ppf((1 + confidence_level) / 2., n-1) # From https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
                #z_low  = scipy.stats.rayleigh.ppf((1 - confidence_level) / 2.0) # Rayleigh should be the correct distribution for ASD values
                #z_high = scipy.stats.rayleigh.ppf(confidence_level / 2.0) # Rayleigh should be the correct distribution for ASD values
                #mean_or_median = psd_new[-1]
                #standard_error = samples.std() / NP.sqrt(n)
                #confidence_interval = [ mean_or_median - standard_error * z_low, 
                #                        mean_or_median + standard_error * z_high]
                #print(f"-----------> m={mean_or_median}   stderr={standard_error}   z_low={z_low}   stderr*zlow={standard_error * z_low}   z+={z_high}")
                m, lower, upper = mean_confidence_interval(psd[mask], confidence_level)
                error.append([lower, upper])
            else:
                raise Exception(f"Error calculation type {error_calculation} is invalid.")

    if error_calculation:
        return NP.array(freq_new_actual), NP.array(psd_new), NP.array(error)
    else:
        return NP.array(freq_new_actual), NP.array(psd_new)


def bin(arr: NP.ndarray, bin_factors:tuple):
    """ Returns a binned version of arr. If factors were 1, the original array is returned."""
    assert len(bin_factors) == len(arr.shape)
    #assert arr.dtype == NP.float32 or arr.dtype == NP.float64
    assert len(arr.shape) == 2
    for factor in bin_factors:
        assert factor > 0

    if bin_factors[0] == 1 and bin_factors[1] == 1:
        return arr

    #newshape = NP.array(arr.shape) // NP.array(bin_factors)
    newshape = NP.array(arr.shape).astype(NP.float32) / NP.array(bin_factors)
    newshape = NP.ceil(newshape).astype(NP.int32)
    newarr = NP.empty(newshape, dtype=arr.dtype)
    _bin_helper(arr, newarr, bin_factors)
    return newarr

@njit
def _bin_helper(arr, newarr, bin_factors):
    for x in range(newarr.shape[0]):
        for y in range(newarr.shape[1]):
            x_ = x * bin_factors[0]
            y_ = y * bin_factors[1]
            newarr[x][y] = NP.mean(arr[x_ : x_ + bin_factors[0], y_ : y_ + bin_factors[1]])


def log_scale_symmetric(arr:NP.ndarray) -> NP.ndarray:
    """ Symmetric logarithmic scaling. For negative values it is applied as if they were positive"""

    zeros = NP.zeros(arr.shape)
    positives = NP.maximum(zeros, arr)
    negatives = NP.minimum(zeros, arr)

    positives += 1
    positives = NP.log2(positives, dtype=NP.float32)

    negatives *= -1
    negatives += 1
    negatives = NP.log2(negatives, dtype=NP.float32)
    negatives *= -1

    result = zeros
    result = negatives + positives
    return result


def rms(arr: NP.ndarray, bin_factors:tuple):
    """ Returns a binned (rms) version of arr. If factors were 1, the original array is returned."""
    assert len(bin_factors) == len(arr.shape)
    #assert arr.dtype == NP.float32 or arr.dtype == NP.float64
    assert len(arr.shape) == 2
    for factor in bin_factors:
        assert factor > 0

    if bin_factors[0] == 1 and bin_factors[1] == 1:
        return arr

    #newshape = NP.array(arr.shape) // NP.array(bin_factors)
    newshape = NP.array(arr.shape).astype(NP.float32) / NP.array(bin_factors)
    newshape = NP.ceil(newshape).astype(NP.int32)
    newarr = NP.empty(newshape, dtype=arr.dtype)
    _rms_helper(arr, newarr, bin_factors)
    return newarr

@njit
def _rms_helper(arr, newarr, bin_factors):
    for x in range(newarr.shape[0]):
        for y in range(newarr.shape[1]):
            x_ = x * bin_factors[0]
            y_ = y * bin_factors[1]
            subarr = arr[x_ : x_ + bin_factors[0], y_ : y_ + bin_factors[1]]
            rms_value = NP.sqrt(NP.mean(subarr*subarr))
            newarr[x][y] = rms_value


