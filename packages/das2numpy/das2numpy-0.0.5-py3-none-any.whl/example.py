import numpy as NP
import sys
from datetime import datetime
import matplotlib.pyplot as PP
from das2numpy import loader, utils


print("Load data to numpy-array")
t_start = datetime(2025,  3, 25, 1, 0, 0)
t_end   = datetime(2025,  3, 25, 1, 1, 0)
channel_start = 0
channel_end = -1
loader = loader("/pnfs/desy.de/m/project/iDAS/raw/2025-DESY/2025-03-25-desy", "SILIXA", 1)
data = loader.load_array(t_start, t_end, channel_start, channel_end)

print("Reduce data by binning (mean averaging)")
bin_factors = (100, 10)
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
PP.savefig("waterfall.png")
