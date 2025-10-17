
# colindex2

<!--
<div align="left">
<img src="map.png" width="40%">
</div>
-->

A python package for atmospheric depression detection and tracking. The main target is to capture upper tropospheric disturbances such as cutoff lows and blockng highs from their earlier stages of troughs and ridges, respectively, with their seamless transitions of basic variables such as intensity, size, duration, etc..


[![PyPI version](https://badge.fury.io/py/colindex2.svg)](https://pypi.org/project/colindex2/)

### Reference

- Kasuga, S., M. Honda, J. Ukita, S. Yaname, H. Kawase, and A. Yamazaki, 2021: Seamless detection of cutoff lows and preexisting troughs. *Monthly Weather Review*, **149**, 3119–3134, [https://doi.org/10.1175/MWR-D-20-0255.1](https://doi.org/10.1175/MWR-D-20-0255.1) (K21)  

- Kasuga, S., and M. Honda, 2025: Climatology of Cutoff Lows Approaching Japan. *SOLA*, **21**, 329-333, [https://doi.org/10.2151/sola.2025-049](https://doi.org/10.2151/sola.2025-049) (KH25)  


<!--
Site above references when you publish papers using this package.
:warning: The tracking scheme is underconstruction and its definition may be changed unnoticed. The relatively stabe versions are v2.7.6, and v2.8.1 See Tags and CHANGELOG. (edit: 2025.4.30)
-->

# Install

```
pip install colindex2
```
Dependecies are...

```
numpy pandas pytorch scipy xarray netCDF4 h5netcdf matplotlib cartopy  
```

If you use anaconda environment, prepare the dependencies using `conda` in advance and then install `colindex2` using conda's `pip`, as recommended by [anaconda.com](https://www.anaconda.com/blog/using-pip-in-a-conda-environment). Maybe more stable by using conda-forge.  


# Tutorial
Try [quick tutorial](colindex2_tutorial.ipynb) and see [python template](template_for_python_user.py).

# Table of contents
[[_TOC_]]

# How to execute
## Python functions

Below examples excecute the detection and tracking with default settings.

```python
# importing
import xarray as xr
from colindex2 import Detect, Track

# load xr.DataArray of a latitude-longitude 2D field
z = xr.open_dataarray("z.nc").sel(level=300)

# execute detection with default options
Detect(z)

# execute tracking with default options
track_times = pd.date_range("yyyy-mm-dd hh", "yyyy-mm-dd hh", freq="6h")
Track(times=track_times, level=300)
```

<details>

<summary> Important default arguments (KH25) </summary>

- `Detect()` (For more details, see [source code](colindex2/colindex2.py#L12))

| args| default values | description |
| ---- | ----------- | ----- |
| odir | "./d01" | Parent output directory path. |
| r | np.arange(200,2101,100) | Searching radius variable r [km]. Set it considering depression size range of your interest. |
| SR_thres | 3.0 | SR threshold to remove tiny trough |
| So_thres | 3.0 | So threshold to remove weak vortices [m/100km]|
| gpu | False | Calculate using GPU if CUDA or MPS (METAL) is available. This mode is experimental and not fully tested. For MPS, you must set `PYTORCH_ENABLE_MPS_FALLBACK=1` in your environment. |


- `Track()` (For more details, see [source code](colindex2/tracking_overlap2.py#L14))

| args| default values | description |
| ---- | ----------- | ----- |
| odir | "./d01" | parent output directory name |
| tlimit | 150.0 | Traveling speed limit to prevent wrong connections by large depressions [km/h]. Default 150 km/h is 900 km in 6 hour. |
| long_term | False | If False, tracking ID will be continuously counted up during the analysis period, and massive memory usage may occur. If True, tracking ID will be labeled from 1 in every 00UTC 1st Jan. |
| DU_thres | 36 | Threshold for noise removal with respect to duration (life time) [hour]. |

<!--
| QS_min_intensity | 10.0 | Minimum So for significant blocking [m/100 km]. A in Schwierz et al. (2004, GRL). |
| QS_min_radius | 800 | Minimum ro for significant blocking [km]. S in Schwierz et al. (2004, GRL). 1200 km is correspond to a 2,000,000 km^2 feature area when it is defined as a circle with radius of `ro` /* 2/3 (i.e., 800 km). |
| QS_min_overlap_ratio | 0.7 | Temporal overlapping ratio of ro circles for the quasi-stational conditions. O in Schwierz et al. (2004, GRL). |
-->


</details>

## Shell commands
Note that python3 and requirements must be installed.  

Add `-h` to see their documets.

- 1. Generate data_settings.py

```bash
gen_data_settings
```

- 2. Edit [data_settings.py](data_settings.py)

- 3. Run detection

```bash
detect z.nc
```

- 4. Run tracking

```bash
track
```

or, you can do doth as follows:

```bash
detect z.nc -track
```

<!--
- Draw maps to check tracking data and AS (netcdf output only)

```bash
$ draw_map z.nc ./d01 L 300 nps
```
-->

- Find and make each tracking data

```
find_track ./d01 L 300 a
```

## Directory structure of outputs

```
current_dir/
|
└── d01/  # default name
    |
    ├── AS/  # 2D averaged slope function
    |   └── AS-{ty}-{yyyymmddhhTT}-{llll}.nc (or .grd)
    |
    ├── V/   # point values after detection, will be used for tracking
    |   └── V-{ty}-{yyyymmddhhTT}-{llll}.csv
    |
    ├── Vt/  # intermediate data (you can remove after all processes are finished)
    |   └── V-{ty}-{yyyymmddhhTT}-{llll}.csv
    |
    ├── Vtc/ # final point values after tracking
    |    └── V-{ty}-{yyyymmddhhTT}-{llll}.csv
    |
    └── ID/  # continuous csv for a specific track whose id is `ID`
         └── {ty}-{l}-{yyyymm}-{ID}.csv
```
where, `ty` is `L` or `H`, `yyyymmddhhTT` is timestep, `llll` is level in 4 digits, and `l` is level.  


# How to use outputs
## How to load outputs in programs

- python3

 point data (`V` and `Vtc`, csv) 
```python3
import pandas as pd
df = pd.read_csv(path_to_V, parse_dates=["time"])

# drawing ro circle
from colindex2 import draw_ro
ax = plt.axes(projection=ccrs.PlateCarree())
ax = draw_ro(ax, df)
```
 mesh data (`AS`, netcdf)
```python3
import xarray
da = xr.open_dataarray(path_to_AS).squeeze()

# drawing shading of AS
ax = plt.axes(projection=ccrs.PlateCarree())
s = ax.contourf(da.longitude,
                da.latitude,
                da,)
plt.colorbar(s)
```

<!--
- julia

 point data (`V` and `Vtc`, csv) 
```julia
using CSV, DataFrames, Dates
df = CSV.read(path_to_V, DataFrame)
df.time = DateTime.(df.time, "yyyy-mm-dd HH:MM:SS")
```
 mesh data (`AS`, netcdf)
```julia
using Datasets
ds = Dataset(path_to_AS)
ar = ds["AS"][:,:]
```
-->

## How to get csv for a specific track

<details>
<summary> Click here </summary>

Please obtain the ID for a specific depressin and its appeared year and month in advance.

Use `find_one` function by importing `Finder`.

```python
from colindex2 import Finder

# set output dir (default:"`./d01`") and timestep of output csv in `Vtc`
F = Finder(odir="./d01", timestep=6)

# set type (`"L"` or `"H"` for low or high detection, respectively), level (e.g., 300 hPa here), and year/month with 6 digits (e.g., 201504) when the feature appeared, and ID for the specific feature (e.g., 333)
# here, the result will be produced at "`./d01/ID/L-300-201504-333.csv`"
F.find_one("L", 300, 201504, 333)

# try below to concatenate the specific track with before splitting from and after merging to other features
F.find_one("L", 300, 201504, 333, before_split=True, after_merge=True)
```

You can use following functions (experimental, welcome bug reports!)

- `count_all(ty, lev)`: Print out count of all tracks on the specific level in the output directory.

- `find_all(ty, lev, all_in_one=False)`: Search all tracks on the specific level in a whole time range and save them as csvs. Recommended only for case studies.

</details>

## Parameter list for `Vct` data

| Names| Description |
| ---- | ----------- |
| time | Time. |
| ty | `0` for lows and troughs, <br> `1` for highs and ridges. |
| lev | Level of the input field. |
| lat, lon | Central coorditates in latitude and longitude. |
| valV | Value of input field on the center |
| valX | Value of the nearest local minimum (maximum) of input field for a low (high). |
| lonX,latX | Latitude and longitude of the nearest local extremum if any, otherwise this value will be `999.9` |
| So | Optimal slope [m/100 km]. Intensity of depresion (circular geostrophic wind speed). |
| ro | Optimal radius [r km]. Size of depression (as a radius of its surrounding circulation). |
| Do | Optimal depth [m]. Vertical depth of depression. |
| SBG | Background slope [m/100 km]. |
| SBGang | Angle of Background slope vector [radian]. `0` for east. |
| m, n | Zonal, meridional components of SBG, respectivelly [m/100 km]. |
| SR | Slope ratio. Less (more) than 1.34 tends to correspond to a closed-contour (open-contour) system. See K21 for detail discussions. |
| ex | Distinction between closed and open systems. <br>`1` (there is a extremum within `ro`\*0.65) for lows/highs <br> `0` for troughs/ridges. |
| EE | Eccentricity (1 for pure isotropic, smaller values for oval shape. |
| XX | Zonal discrete laplacian with a step of `ro` [m/(100 km)**2]. Small value means the feature has weak zonal concavity. `0.5` might be a good value to exclude sub-tropical large ridges. |
| ID | Identification number. This can be larger than number of resultant detections since it includes noises. |
| MERGE | Merge lysis flag. <br>`-1` for soritary lysis, <br>`-2` for being merged from someone, <br>`-3` for lysis at the end of analysis, <br>`-4` for being involved in the secondary process (see Fig. S2 in KH25), <br>`other integers` for the object ID of its merge lysis. |
| SPLIT | Split genesis flag. <br>`-1` for soritary genesis, <br>`-2` for being splitting and producing someone, <br>`-3` for genesis at the start of analysis, <br>`-4` for being involved in the secondary process (see Fig. S2 in KH25), <br>`other integers` for the object ID of its split genesis. |
| DIST | Moving distance in a timestep [km]. Central difference. When merge/split/genesis/lysis, value will be missing. |
| SPEED | Moving speed [m/s]. DIST/timestep. |
| DIR | Moving direction [radian]. 0 for east. |
| \_ DC | Accumulated duration [timestep] including before split. |
| DU | Duration [hour]. |
| XS | Sequential duration being `ex`=1 (lows/highs). |
| QS | Quasi-stational (QS) duration [hour]. The conditions for QS are controlled by the options in `Track()` as follows: <br> - `QS_min_intensity` <br> - `QS_min_radius` <br> - `QS_min_overlap_ratio` |
| MAX | `1` for the maximum development timestep (maximum `So`). |
| MAXSo | `So` when MAX. |
| exGEN | Closed system genesys (`ex` changed from `0` to `1` in this timestep). |
| exLYS | Closed system lysis (`ex` changed from `1` to `0` in the next timestep). |

<!--
| ALLDIST | Accumulated moving distance [km]. |
| MEDDIST | Median moving distance in a track [km]. |
| MAXXS | Maximum duration of XS in a track (XS can be scored in multiple sequences). |
| MAXQS5 | Maximum duration of QS5 in a track. |
| MAXQS7 | Maximum duration of QS7 in a track. |
-->

