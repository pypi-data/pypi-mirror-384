import numpy as NP
import sys
from datetime import datetime
import matplotlib.pyplot as PP
from das2numpy import loader, utils

USE_DOWNSAMPLED = False

print("Load data to numpy-array")
t_start = datetime(2025, 10, 14, 2, 58, 59)
t_end   = datetime(2025, 10, 14, 2, 59, 1)
channel_start = 1000
channel_end = 3000

if USE_DOWNSAMPLED:
    loader = loader("/pnfs/desy.de/m/project/iDAS/work/derived-data/DOWNSAMPLED_200HZ/2025-10/", "SILIXA_200HZ", 1)
else:
    loader = loader("/pnfs/desy.de/m/project/iDAS/raw/2025-DESY/2025-10-14-desy", "SILIXA", 1)
data = loader.load_array(t_start, t_end, channel_start, channel_end)

print("Reduce data by binning (mean averaging)")
if USE_DOWNSAMPLED:
    bin_factors = (1, 1)
    data = utils.bin(data, bin_factors) # Reduce time sampling and spatial sampling by averaging.
    sampling_hz = 200.0 / bin_factors[0]
else:
    bin_factors = (5, 1)
    data = utils.bin(data, bin_factors) # Reduce time sampling and spatial sampling by averaging.
    sampling_hz = 1000.0 / bin_factors[0]
channel_spacing = 1.0 * bin_factors[1]

NP.save("data.npy", data)

print("Create plot with pyplot")
PP.title(f"{t_start.isoformat()}")
PP.imshow(
    data,
    cmap = "seismic",
    aspect = "auto",
    interpolation = "nearest",
    vmin = -1e-7,
    vmax = +1e-7,
    extent = (
        channel_start, channel_start + (data.shape[1] * channel_spacing), 
        data.shape[0] / sampling_hz, 0
    )
)
PP.xlabel("Position [m]")
PP.ylabel("Time [s]")
PP.colorbar(label="Strain-rate [$\\frac{m}{m \\cdot s}$]")
if USE_DOWNSAMPLED:
    PP.savefig("waterfall_downsampled.png")
else:
    PP.savefig("waterfall.png")
