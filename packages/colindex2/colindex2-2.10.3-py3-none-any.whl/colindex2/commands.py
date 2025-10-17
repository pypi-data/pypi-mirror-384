import sys, os
import argparse
import importlib.util
import numpy as np
import pandas as pd
import xarray as xr
from .colindex2 import Detect
from .tracking_overlap2 import Track
from .get_IDfile import Finder
import shutil
from pathlib import Path
import importlib.resources

def gen_data_settings():
    with importlib.resources.path("colindex2", "data_settings.py") as file_path:
        dest = Path.cwd() / "data_settings.py"
        shutil.copy(file_path, dest)

def _load_local_module(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} has not generated yet. Use gen_data_settings command")
    spec = importlib.util.spec_from_file_location("data_settings", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_settings"] = module
    spec.loader.exec_module(module)
    return module


def detect():
    description = """
Run detection of colindex.
Before run, generate data_settings.py with 'gen_data_settings' command and edit it.

 $ gen_data_settings

Then execute below for netcdf input.

 $ detect path/to/file.nc

For binary input, specify start/end times (st,et) and frequency of timesteps (freq).

 $ detect path/to/file.grd -st "yyyy-mm-dd hh" -et "yyyy-mm-dd hh" -freq 6h

Option -track execute also tracking after detection.
In this case, 'tracking_times' in data_settings.py is ignored,
and the detection timesteps will be used.

 $ detect path/to/file.nc -track
 $ detect path/to/file.grd -st "yyyy-mm-dd hh" -et "yyyy-mm-dd hh" -freq 6h -track

Result data will be saved in output_dir/V output_dir/AS.
            """
#Option -n can set number of multiprocess (default 4)
#
# $ detect path/to/file.nc -n 20

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_data_path",
                        type=str,
                        help="input data path")
    #parser.add_argument("-n",
    #                    type=int,
    #                    help="number of multiprocessing, default is 4.",
    #                    default=4)
    parser.add_argument("-st",
                        type=str,
                        help="start timestep yyyy-mm-dd hh",
                        default="1700-01-01 00")
    parser.add_argument("-et",
                        type=str,
                        help="end timestep yyyy-mm-dd hh",
                        default="1700-01-01 00")
    parser.add_argument("-freq",
                        type=str,
                        help="frequency of timestep for pd.date_range (default: '6h')",
                        default="6h")
    parser.add_argument("-track",
                        action="store_true",
                        help="enable tracking",)
    args = parser.parse_args()
    input_data_path = args.input_data_path
    st = args.st
    et = args.et
    freq = args.freq
    _track = args.track

    data_settings_path = os.path.join(os.getcwd(), "data_settings.py")
    if not os.path.exists(data_settings_path):
        raise FileNotFoundError("No data_settings.py in the current dir. Run 'gen_data_settings' command.")
    D = _load_local_module(data_settings_path)

    if D.input_data_type == "nc":
        if not hasattr(D, "var_name"):
            da = xr.open_dataarray(input_data_path)
        else:
            ds = xr.open_dataset(input_data_path)
            da = ds[D.var_name]

        if hasattr(D, "lon_name"):
            da = da.rename({D.lon_name:"longitude"})
        if hasattr(D, "lat_name"):
            da = da.rename({D.lat_name:"latitude"})
        if hasattr(D, "lev_name"):
            da = da.rename({D.lev_name:"level"})
        if hasattr(D, "time_name"):
            da = da.rename({D.time_name:"time"})

        lons = da.longitude.values
        lats = da.latitude.values
        levs = da.level.values
        times = pd.to_datetime(da.time.values)
        da = da.values
        fmt = None

    else:
        lons = D.lons
        lats = D.lats
        levs = D.levs
        #times = D.times
        times = pd.date_range(st,et,freq=freq)
        shape = (len(times),len(levs),len(lats),len(lons))
        fmt = D.input_data_type
        with open(input_data_path, "r") as a:
            da = np.fromfile(a, dtype=fmt).reshape(shape)

    if D.output_data_type == "nc":
        nc = True
    else:
        nc = False
        fmt = D.output_data_type

    idx_levs = np.where(np.isin(levs, D.selected_levs))[0]

    for l in idx_levs:
        Detect(da[:,l,:,:],
               D.output_dir,
               D.detection_type,
               D.r,
               D.SR_thres,
               D.So_thres,
               D.Do_thres,
               D.xx_thres,
               D.rm_rmin,
               D.rm_rmax,
               D.factor,
               D.local_ex_req_num,
               D.gpu,
               nc,
               fmt,
               D.subs,
               levs[l],
               times,
               lons,
               lats,
               )

    if _track:
        track_cli(times)


def track_cli(times=0):

    data_settings_path = os.path.join(os.getcwd(), "data_settings.py")
    if not os.path.exists(data_settings_path):
        raise FileNotFoundError("No data_settings.pn in the current dir. Run 'gen_data_settings' command.")
    D = _load_local_module(data_settings_path)

    if isinstance(times, pd.DatetimeIndex):
        tracking_times = times
    else:
        tracking_times = D.tracking_times

    argss=[(
        D.output_dir,
        D.tracking_types,
        lev,
        tracking_times,
        D.tlimit,
        D.penalty,
        D.long_term,
        D.operational,
        D.DU_thres,
        D.QS_min_intensity,
        D.QS_min_radius,
        D.QS_min_overlap_ratio,
        D.only_count
        ) for lev in D.selected_levs]

    for _args in argss:
        Track(*_args)


def track():
    description = """
Run tracking of colindex. Before run, edit TRACKING SETTINGS section in data_settings.py

 $ track

Result data will be saved in output_dir/Vtc.
"""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.parse_args()
    track_cli()


def find_track():
    description = """
Search tracking for specific IDs and save. Four arguments are required.
 $ find_track output_dir type lev freqH type2

The fourth argument 'type2' can be set 3 types:

c: only count number of all tracks
 $ find_track ./d01 L 300 6 c

A: find all tracks and save them as an all-included csv output_dir/all_{type}_{lev}.csv.
 $ find_track ./d01 L 300 6 A

a: find all tracks and save them separately in output_dir/ID/.
 $ find_track ./d01 L 300 6 a

(digit of ID): find one track labeled by ID. Add fifth argument of 'yyyymm' (year month) when the track observed, as following
 $ find_track ./d01 L 300 6 2222 202302

 This will produce a track obtained from 6-hour intarval data for 300-hPa level whose ID is 2222, appears in Feb 2023. 
 If add -a (-b) option at its tail, the tracks after merging (before splitting) are connected.
 $ find_track ./d01 L 300 6 2222 202302 -a
 $ find_track ./d01 L 300 6 2222 202302 -b
 $ find_track ./d01 L 300 6 2222 202302 -a -b

 """
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("odir", type=str, help="output data directory")
    parser.add_argument("ty", type=str, help="L or H")
    parser.add_argument("lev", type=str, help="level")
    parser.add_argument("freqH", type=int, help="frequency of timestep in hour")
    parser.add_argument("type2", nargs="+", type=str, help="A or a or c or 'ID yyyymm'")
    parser.add_argument('-a', '--option_a', action='store_true', default=False, help='follow track after merge')
    parser.add_argument('-b', '--option_b', action='store_true', default=False, help='follow track before split')
    args = parser.parse_args()
    odir = args.odir
    ty = args.ty
    #lev = int(args.lev)
    lev = args.lev
    type2 = args.type2

    #data_settings_path = os.path.join(os.getcwd(), "data_settings.py")
    #D = _load_local_module(data_settings_path)
    #freqH = int(D.tracking_times.inferred_freq[:-1])
    freqH = args.freqH

    f = Finder(odir, timestep=freqH)

    if type2[0] == "a":
        f.find_all(ty,lev)
    elif type2[0] == "c":
        f.count_all(ty,lev)
    elif type2[0] == "A":
        f.find_all(ty,lev,all_in_one=True)
    elif args.option_a and args.option_b:
        f.find_one(ty,lev,int(type2[1]), int(type2[0]),after_merge=True,before_split=True)
    elif args.option_a:
        f.find_one(ty,lev,int(type2[1]), int(type2[0]),after_merge=True)
    elif args.option_b:
        f.find_one(ty,lev,int(type2[1]), int(type2[0]),before_split=True)
    else:
        f.find_one(ty,lev,int(type2[1]), int(type2[0]))
