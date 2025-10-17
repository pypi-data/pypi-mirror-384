import os
import numpy as np
import pandas as pd
import xarray as xr
#import multiprocessing as mp
import warnings 
warnings.filterwarnings('ignore') 

from .modules import check_gpu
from .modules import _calc_as_torch

class Detect():
    """
    Depression detector by searching each optimal location, intensity, and size from 2D fields.
    See puplication for details (Kasuga et al. 2021; K21) and (Kasuga and Honda 2025; KH25).

    ----

    Parameters:
    -----------

    da : xarray.DataArray or numpy.ndarray
        The target 2D field with (or without) time axis.  
        The dimmension order must be time->latitude->longitude.

    odir : str, default './d01'
        Parent output directory path. By defaults, output data will be stored as follows
        Outputs will be produced in {odir}/AS (AS field) and {odir}/V (detected point values).

    ty : str, {'both', 'L', 'H'}, default 'both'
        Type of vortices to be detected.

    r : np.array, default np.arange(200, 2101, 100) (K21)
        Radial searching variable for average slop function (AS) [km].
        Set range to include scales of which phenomena you are interested in.

    SR_thres : float, default 3. (K21)
        Threshold to remove noises with respect to the slope ratio.

    So_thres : float, default 3. (KH25)
        Threshold to remove noises with respect to the intensity [m/100km].
        In K21, ``10`` and ``5`` was used for climatology for cutoff lows and preexisting troughs, respectively.

    Do_thres : float, default 0.
        Threshold to remove noises with respect to the depth [m].
        A large value (e.g., 10.) reduces small-size noise, which might be helpful for surface low/high detection.

    xx_thres : float, default 0.5
        Threshold to remove noises with respect to the zonal laplacan [m/(100 km)^2].
        This works for high detection
        by removeing large and weak ridges located south of the subtropical jet.

    rm_rmin : bool, default True
        Detected point will be removed if ro is minimum of r because this may be too small.
        True in K21 and KH25.

    rm_rmax : bool, default False
        Detected point will be removed if ro is maximum of r because this may be too large.
        True in K21 and False in KH25.

    factor : float, default 100.
        Factor to convert units of So and AS. Default convert m/km -> m/100 km for geopotential height input.

    local_ex_req_num : int, default 7.
        Number required in local extremum condition (N). 
        The conditions of minimum/maximum are defined in a 3x3 grid box as at least N points (out of 8 points)
        must greater/smaller than and equal to the center value.  

    gpu : bool, default False
        Note, this feature is experimental.
        If True, the processes wil be computed with gpu processing via CUDA or METAL.

    nc : bool, default True
        If True, netcdf file will be created for AS. If you want grads binary outputs, set False.

    fmt : str, default '<f4'
        Output binary format when nc=False. The format is correspond to dtype in numpy.

    subs : bool, default False
        If True, 2D fields of ro, m, and n are produced.

    t : pandas.DatetimeIndex, default [pd.Timestamp('1000-01-01 00:00')]
        Time of data. Option for numpy.ndarray input.

    lev : int, default 0
        Level of data. Option for numpy.ndarray input. This will be used in the name of output files.

    lons : list or numpy.ndarray, default [-999.]
        Longitude list. Option for numpy.ndarray input. Set like lon=np.arange(0, 360, 1.25).


    lats : list or numpy.ndarray, default [-999.]
        Option for numpy.ndarray input. Set like lon=np.arange(-90, 90, 1.25).

    """

    def __init__(self,
                 da,  # 2D DataArray or ndarray
                 odir='./d01',  # output parent dir
                 ty="both",
                 r=np.arange(200, 2101, 100),  # searching radius variable
                 SR_thres=3.,  # shape threshold
                 So_thres=3.,  # intensity threshold
                 Do_thres=0.,  # depth threshold
                 xx_thres=.5,  # zonal concavity thershold
                 rm_rmin=True,  # remove minimum size
                 rm_rmax=False,  # remove maximum size
                 factor=100.,  # factor of So m/km -> m/100km
                 local_ex_req_num=7, # out of 8 points
                 gpu=False, # gpu calculation
                 nc=True,  # netcdf outputs otherwise grads bin
                 fmt='<f4',  # binary format when nc=False
                 subs=False, # output intermediate fields
                 lev=0,  # for ndarray input below
                 t=[pd.Timestamp('1700-01-01 00:00')],
                 lons=[-999.],
                 lats=[-999.],
                 ):

        # constants
        self.rr = 6371.  # earth radius [km]
        self.g = 9.8  # gravity [m/ss]
        self.factor = factor

        self.ty = ty
        self.r = np.array(r)

        self.da = da
        self.odir = odir
        self.SR_thres = SR_thres
        self.So_thres = So_thres
        self.Do_thres = Do_thres
        self.xx_thres = xx_thres
        self.thres4 = [So_thres, Do_thres, SR_thres, xx_thres]
        self.rm_rmin = rm_rmin
        self.rm_rmax = rm_rmax
        self.local_ex_req_num = local_ex_req_num

        self.lons = lons
        self.lats = lats
        self.t = t
        self.lev = lev

        self.gpu = gpu
        self.nc = nc
        self.fmt = fmt
        self.subs = subs

        # main process
        self._main()

        # maxe a text about detection parameters
        self._save_param_text()

        print("done!")


    def _set_coords(self):

        da = self.da
        lons = self.lons
        lats = self.lats
        lev = self.lev
        t = self.t
        if isinstance(da, xr.DataArray):

            _dims = [k for k, v in da.coords.items()]  # this may include squeezed dims

            if 'valid_time' in _dims:
                tt = pd.to_datetime(da.valid_time.values)
            elif 'time' in _dims:
                tt = pd.to_datetime(da.time.values)

            if isinstance(tt, pd.Timestamp):
                self.t = [tt]  # must be iterable
                self.da = da.values[np.newaxis, ...]
            else:
                self.t = tt  # pd.DatetimeIndex or default list
                self.da = da.values

            if 'level' in _dims:
                self.lev = da.level.values
            elif 'lev' in _dims:
                self.lev = da.lev.values
            elif 'levs' in _dims:
                self.lev = da.levs.values
            elif 'isobaricInhPa' in _dims:
                self.lev = da.isobaricInhPa.values

            if 'longitude' in _dims:
                self.lon = da.longitude.values
            if 'lon' in _dims:
                self.lon = da.lon.values
            if 'lons' in _dims:
                self.lon = da.lons.values

            if 'latitude' in _dims:
                self.lat = da.latitude.values
            if 'lat' in _dims:
                self.lat = da.lat.values
            if 'lats' in _dims:
                self.lat = da.lats.values

        elif isinstance(da, np.ndarray):

            if len(lons) != da.shape[-1] or len(lats) != da.shape[-2]:
                raise ValueError('shape of lons or lats not fit input')
            else:
                self.t = t
                self.lev = lev
                self.lon = lons
                self.lat = lats
                self.da = da

            if len(self.t) == 1:
                self.da = [self.da]
                self.t = [self.t]

        else:
            raise ValueError('wrong input data type, must be xr.DataArray or np.ndarray')

        if isinstance(self.lev, np.ndarray):
            self.lev = self.lev.item()

        self.lev = int(self.lev)



    def check_zonal_loop(self):

        lon1 = self.lon[1]
        lon1n = self.lon[-1]
        lon0 = self.lon[0]
        dlon = lon1 - lon0

        if lon1n == lon0:
            raise ValueError("longitude is already looped. use non-looped data")

        l = lon1n + dlon

        if l == lon0 or l+360 == lon0 or l-360 == lon0: 
            self.zloop = True
        else:
            self.zloop = False

    def check_increasing_lat(self):
        
        dlat = self.lat[1] - self.lat[0]

        if dlat < 0.:
            self.da = self.da[...,::-1,:].copy()
            self.lat = self.lat[::-1].copy()


    def _main(self):

        # set coordinates of data
        self._set_coords()

        # check gpu is available
        self.device = check_gpu(self.gpu)

        # check whether data longitude is looped
        # and increasing latitude
        self.check_zonal_loop()
        self.check_increasing_lat()

        print("level:", self.lev)
        print("calculation:", self.device)
        print("-----------------------")

        # start main process
        args = [(
            self.odir,
            self.ty,
            self.da[i],
            self.lon,
            self.lat,
            self.lev,
            self.t[i],
            self.r,
            self.thres4,
            self.rm_rmin,
            self.rm_rmax,
            self.factor,
            self.zloop,
            self.device,
            self.nc,
            self.fmt,
            self.subs,
            self.local_ex_req_num,
            ) for i in range(len(self.t))]

        #with mp.Pool(self.nproc) as p:
        #    p.map(_calc_as_torch, args)
        for x in args:
            _calc_as_torch(x)

    def _save_param_text(self):
        from datetime import datetime
        import getpass
        import socket
        now = datetime.now()
        user = getpass.getuser()
        host = socket.gethostname()
        with open(f"{self.odir}/_detection_parms.txt", "w", encoding="utf-8") as f:
            print("r:", self.r, file=f)
            print("SR_thres:", self.SR_thres, file=f)
            print("So_thres:", self.So_thres, file=f)
            print("Do_thres:", self.Do_thres, file=f)
            print("xx_thres:", self.xx_thres, file=f)
            print("rm_rmin:", self.rm_rmin, file=f)
            print("rm_rmax:", self.rm_rmax, file=f)
            print("factor:", self.factor, file=f)
            print("local_ex_req_num:", self.local_ex_req_num, file=f)
            print("calculation device:", self.device, file=f)
            print("", file=f)
            print("executed in", now, "by", user, "@", host, file=f)
