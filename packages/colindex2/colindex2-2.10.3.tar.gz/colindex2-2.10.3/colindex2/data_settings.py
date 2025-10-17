import numpy as np
import pandas as pd

# DATA SETTINGS ----------
output_dir = "./d01"
output_data_type = "nc"  # nc or <f4 or >f4
input_data_type = "nc"  # nc or <f4 or >f4
# nc: netcdf
# <f4: little endian, 4-byte float binary
# >f4: big endian, 4-byte float binary

if input_data_type == "nc":
    pass
    #var_name = "z"  # when input has multiple variables
    #lon_name = ""  # use if each differs from "longitude"
    #lat_name = ""  # "latitude""
    #lev_name = ""  # "level"
    #time_name = ""  # "time"
else:  # for binary input
    lons = np.arange(-180, 180, 1.25)  # degrees east
    lats = np.arange(90, -90, -1.25)  # degrees north
    levs = [1000,975,925,900,875,850,800,775,750,700,650,600,500,450,400,350,300,250,225,200,175,150,125,100,85,70,60,50,40,30,20,10,7,5,3,2,1,0.7,0.3,0.1,0.03,0.01]  # hPa
    times = pd.date_range("1700-01-01 00", "1700-01-01 00", freq="6h")
    # document of pandas.date_range() is below
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.date_range.html

selected_levs = [300]  # hPa, must be list

# DETECTION SETTINGS ----------
detection_type = "both"  # L or H or both
r = np.arange(200, 2100, 100)  # km
SR_thres = 3.  # slope ratio to remove noises (Kasuga et al. 2021; K21)
So_thres = 3.  # m/(100km), intensity (Kasuga and Honda 2025; KH25)
Do_thres = 0.  # m, depth
xx_thres = .5   # m/(100km)^2, zonal concavity (to remove low-lat. highs)
rm_rmin = True  # remove small noises (K21, KH25)
rm_rmax = False  # remove too big vortices (True in K21, False in KH25)
factor = 100.  # covert unit of AS from m/mk to m/100 km
local_ex_req_num = 7 # least points for local min/max condition out of 8 points in 3x3 box
gpu = False # gpu calculation, make sure gpu availavility for python
subs = False  # save intermediate fields (ro,m,n)

# TRACKING SETTINGS ----------
tracking_types = "L"  # L or H or both
tracking_times = pu.date_range("1700-01-01 00", "1700-01-01 00", freq="6h")
tlimit = 150  # kmuh, maximum tracking speed (KH 25)
DU_thres = 36.  # h, duration threshold (Munoz et al. 2020 and KH25)
penalty = 0  # 0: use distance/intensity/size/backgrounnd for traking (KH25; modified L23), 1: use only intensity
QS_min_intensity = 10.0  # m/100, km for significant blocking
QS_min_radius = 0  # km, for significant blocking
QS_min_overlap_ratio = 0.7  # for significant blocking (stationarity)

long_term = False  # if True, ID will be reset as 1 when every 00UTC 1st Jan 
operational = False  # if True, tracking process starts from already tracked data which stored in Vt directory (experimental)
only_count = False  # if True, first tracking process will be skipped

