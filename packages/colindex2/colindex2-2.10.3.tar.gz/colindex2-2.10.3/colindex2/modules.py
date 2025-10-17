import os, sys
import numpy as np
import pandas as pd
import xarray as xr
import torch


def check_gpu(gpu):
    if gpu:
        if torch.backends.mps.is_available():  
            device = torch.device("mps")        # Apple GPU
        elif torch.cuda.is_available():        
            device = torch.device("cuda")       # NVIDIA GPU
        else:
            device = torch.device("cpu")        # CPU fallback
    else:
        device = torch.device("cpu")
    return device


def gcd(lon, lat, lons, lats, r=6371.):
    lon = np.deg2rad(lon)
    lat = np.deg2rad(lat)
    lons = np.deg2rad(lons)
    lats = np.deg2rad(lats)

    A = np.sin(lat) * np.sin(lats)
    B = np.cos(lat) * np.cos(lats) * np.cos(np.abs(lon-lons))
    C = np.arccos(A + B)
    return C * r


def invert_gcd2(lon, lat, theta, d, rr=6371.):

    # convert angles within +-360
    theta2 = np.remainder(theta, 360.)

    A = np.deg2rad(90.-theta2)
    c = d/rr  # center angle between pos. vectors of start and end [radian]
    b = np.deg2rad(90.-lat)  # zenith of start point

    # cosine formula of Spherical Trigonometry
    cos_a = np.cos(b)*np.cos(c) + np.sin(b)*np.sin(c)*np.cos(A)
    a = np.arccos(cos_a)  # zenith of end point [radian]
    lat_end = 90. - np.rad2deg(a)

    _N = np.cos(c) - cos_a*np.cos(b)
    _D = np.sin(a)*np.sin(b)

    cond = ((-90. < theta2) & (theta2 < 90.) | (270. < theta2))
    cond2 = (np.sin(b) != 0) & (np.sin(a) != 0)

    C = np.where(cond2,
                 np.arccos((_N/_D).clip(-1.,1.)),
                 0.)

    lon_end = np.where(cond2,
                        np.where(cond,
                                 lon+np.rad2deg(C),
                                 lon-np.rad2deg(C)),
                        np.where(np.sin(b)==0,
                                 theta2,
                                 0.))
    # convert angles within +-360
    lon_end = np.remainder(lon_end, 360.)

    return lon_end, lat_end



def _invert_gcd2_torch(lon,
                       lat,
                       theta,
                       d,
                       rr=6371.):  # earch radius km

    # convert angles within +-360
    theta2 = torch.remainder(theta, 360.)

    A = torch.deg2rad(90.-theta2)
    c = d/rr  # center angle between pos. vectors of start and end [radian]
    b = torch.deg2rad(90.-lat)  # zenith of start point

    # cosine formula of Spherical Trigonometry
    cos_a = torch.cos(b)*torch.cos(c) + torch.sin(b)*torch.sin(c)*torch.cos(A)
    a = torch.arccos(cos_a)  # zenith of end point [radian]
    lat_end = 90. - torch.rad2deg(a)

    _N = torch.cos(c) - cos_a*torch.cos(b)
    _D = torch.sin(a)*torch.sin(b)

    cond = ((-90. < theta2) & (theta2 < 90.) | (270. < theta2))
    cond2 = (torch.sin(b) != 0) & (torch.sin(a) != 0)

    C = torch.where(cond2,
                    torch.arccos((_N/_D).clamp(-1.,1.)),
                    0.)

    lon_end = torch.where(cond2,
                          torch.where(cond,
                                      lon+torch.rad2deg(C),
                                      lon-torch.rad2deg(C)),
                          torch.where(torch.sin(b)==0,
                                      theta2,
                                      0.))
    # convert angles within +-360
    lon_end = torch.remainder(lon_end, 360.)

    return lon_end, lat_end


def _gcd_torch(lon1, lat1, lon2, lat2, r=6371.):
    lon1 = torch.deg2rad(lon1)
    lat1 = torch.deg2rad(lat1)
    lon2 = torch.deg2rad(lon2)
    lat2 = torch.deg2rad(lat2)

    A = torch.sin(lat1) * torch.sin(lat2)
    B = torch.cos(lat1) * torch.cos(lat2) * torch.cos(torch.abs(lon1-lon2))
    C = torch.arccos(A + B)
    return C * r


def _interp_stencils_torch(step_x,step_y,
                           off_x,off_y,
                           x,y, # target location
                           ar, # base array
                           zloop): # 3d new_coords after 
    Ny,Nx = ar.shape
    device = x.device
    dtype = x.dtype

    px = (x - off_x) / step_x
    py = (y - off_y) / step_y

    j0 = torch.floor(px).to(torch.long)
    i0 = torch.floor(py).to(torch.long)

    wx = (px - j0).to(dtype)
    wy = (py - i0).to(dtype)

    j1 = j0 + 1
    i1 = i0 + 1

    if zloop:
        j0 = j0 % Nx
        j1 = j1 % Nx
        far_x = torch.zeros_like(x,
                                 dtype=torch.bool,
                                 device=device)
    else:
        j0 = j0.clamp(0, Nx-1)
        j1 = j1.clamp(0, Nx-1)
        xmax = off_x + (Nx - 1) * step_x
        far_x = (x < (off_x - step_x)) | (x > (xmax + step_x))

    i0 = i0.clamp(0, Ny - 1)
    i1 = i1.clamp(0, Ny - 1)

    ymax = off_y + (Ny - 1) * step_y
    far_y = (y < (off_y - step_y)) | (y > (ymax + step_y))

    z00 = ar[i0,j0]
    z01 = ar[i0,j1]
    z10 = ar[i1,j0]
    z11 = ar[i1,j1]

    # bilenear interpolation
    zz0 = (1-wx) * z00 + wx * z01
    zz1 = (1-wx) * z10 + wx * z11
    I = (1-wy) * zz0 + wy * zz1
    return torch.where(far_x | far_y, float("nan"), I)


def _local_ex_torch(ar,
                    minmax,
                    require,
                    zloop,
                    ar2=None,):

    if minmax == "min":
        ar = -ar

    Ny, Nx = ar.shape
    device = ar.device

    lmp = torch.zeros((Ny,Nx),dtype=bool, device=device)

    if not zloop:
        a = ar[1:-1,1:-1]
        aro = ar
        
    else:
        a = ar[1:-1,:]
        wide = torch.empty((Ny,Nx+2), device=device)
        wide[:,1:-1] = ar[:,:]
        wide[:,0] = ar[:,-1]
        wide[:,-1] = ar[:,0]
        aro = ar
        ar = wide

    a1 = torch.where(a - ar[1:-1,2:] > 0, 1, 0)
    a2 = torch.where(a - ar[1:-1,:-2] > 0, 1, 0)
    a3 = torch.where(a - ar[2:,1:-1] > 0, 1, 0)
    a4 = torch.where(a - ar[:-2,1:-1] > 0, 1, 0)

    a5 = torch.where(a - ar[:-2,2:] > 0, 1, 0)
    a6 = torch.where(a - ar[:-2,:-2] > 0, 1, 0)
    a7 = torch.where(a - ar[2:,:-2] > 0, 1, 0)
    a8 = torch.where(a - ar[2:,2:] > 0, 1, 0)
    mask = a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 >= require

    if not zloop:
        lmp[1:-1,1:-1] = torch.where(mask,True,False)
    else:
        lmp[1:-1,:] = torch.where(mask,True,False)

    if isinstance(ar2,torch.Tensor):
        lmp = torch.where(aro>ar2,lmp,False)

    return lmp


def _calc_elliplicity(xx, yy, xy):

    nan_mask = torch.isnan(xx) | torch.isnan(xy) | torch.isnan(yy)

    # hesse matrix H
    row1 = torch.stack([xx, xy], dim=-1)  # [..., 2]
    row2 = torch.stack([xy, yy], dim=-1)  # [..., 2]
    H = torch.stack([row1, row2], dim=-2)       # [..., 2, 2]

    eigs = torch.linalg.eigvalsh(H)

    # length of long and short axes
    axes = 1.0 / torch.sqrt(torch.abs(eigs))    # [..., 2]

    amin = torch.min(axes, dim=-1).values
    amax = torch.max(axes, dim=-1).values
    ee = amin / amax                         # [...,]
    return ee.masked_fill(nan_mask, float('nan'))


def _calc_as_torch(args):
    """
    main process for calculation of AS and point values on AS
    """

    odir,ty,ar,lons,lats,lev,t,r,thres4,rrmin,rrmax,fct,zloop,device,nc,fmt,subs,reqN = args

    # angles for 8-point stencils
    theta = np.arange(0., 360., 45.)

    # data info
    Nt = len(theta)
    Nr = len(r)
    Ny = len(lats)
    Nx = len(lons)
    org_shape = ar.shape

    step_x = lons[1] - lons[0]
    step_y = lats[1] - lats[0]
    off_x = lons[0]
    off_y = lats[0]

    # unpack thresholds
    So_thres, Do_thres, SR_thres, xx_thres = thres4
    rmin = r.min()
    rmax = r.max()

    # prepare output dir and meta data
    ym = f'{t.year}{t.month:02}'
    tn = f'{ym}{t.day:02}{t.hour:02}{t.minute:02}'
    DIR_V = f'{odir}/V/{ym}'
    os.makedirs(DIR_V, exist_ok=True)
    DIR_AS = f'{odir}/AS/{ym}'
    os.makedirs(DIR_AS, exist_ok=True)
    if nc:
        coords = {
               'time': [t],
               'level': ('level', [lev], {'units': 'millibars'}),
               'latitude': ('latitude', lats,
                            {'units': 'degrees_north'}),
               'longitude': ('longitude', lons,
                             {'units': 'degrees_east'})
               }
        dims = ["time","level","latitude","longitude"]


    ###### start main calculation! ######

    # use 32-bit arrays (torch default)
    f4 = torch.float
    i4 = torch.int

    # convert numpy to torch.Tensor
    lons = torch.from_numpy(lons).to(device=device, dtype=f4)
    lats = torch.from_numpy(lats).to(device=device, dtype=f4)
    r = torch.from_numpy(r).to(device=device, dtype=f4)
    theta = torch.from_numpy(theta).to(device=device, dtype=f4)
    ar = torch.from_numpy(ar).to(device=device, dtype=f4)

    # broadcasting
    lons = lons.view(1,1,1,Nx)
    lats = lats.view(1,1,Ny,1)
    r = r.view(1,Nr,1,1)
    theta = theta.view(Nt,1,1,1)

    # get stencil coordinates
    lons_stencils, lats_stencils = _invert_gcd2_torch(lons, lats, theta, r)

    # interpolate values on the stencils
    ar_stencils = _interp_stencils_torch(step_x, step_y,
                                         off_x, off_y,
                                         lons_stencils,
                                         lats_stencils,
                                         ar, zloop)

    # calc AS
    ar = ar.view(1,1,Ny,Nx)
    AS = torch.mean((ar_stencils - ar) / r, dim=0)

    # unpack stencil values and calc slope related values
    e,ne,n,nw,w,sw,s,se = ar_stencils
    # reduce dims for stencils
    ar = ar.squeeze().view(1,Ny,Nx)
    zero = torch.zeros((Nr,Ny,Nx),dtype=f4,device=device)
    r = r.view(Nr,1,1) + zero
    # backgound slopes (for 8-point stencils)
    cos45 = torch.cos(torch.Tensor((np.pi/4,))).to(device)
    m = (e-w)/4/r + (ne+se-nw-sw)/8/r/cos45
    n = (n-s)/3/r + (ne+nw-se-sw)/8/r/cos45
    # second order derivatives
    xx = (e+w-2*ar)/r/r
    yy = (n+s-2*ar)/r/r
    xy = (ne-nw-se+sw)/4/r/cos45

    # get index for r that maximize AS (ro)
    idx_r_p = AS.max(dim=0, keepdim=True).indices.squeeze()
    idx_r_n = AS.min(dim=0, keepdim=True).indices.squeeze()
    idx_rs = [idx_r_p, idx_r_n]

    idx_y, idx_x = torch.meshgrid(torch.arange(Ny, device=device),
                                  torch.arange(Nx, device=device),
                                  indexing="ij")

    # get AS,ro,m,n positive/negative fields
    AS_p = AS[idx_r_p,idx_y,idx_x] * fct
    AS_n = -AS[idx_r_n,idx_y,idx_x] * fct
    ro_p = r[idx_r_p,idx_y,idx_x]
    ro_n = r[idx_r_n,idx_y,idx_x]
    m_p = m[idx_r_p,idx_y,idx_x]
    m_n = m[idx_r_n,idx_y,idx_x]
    n_p = n[idx_r_p,idx_y,idx_x]
    n_n = n[idx_r_n,idx_y,idx_x]

    # collect arrays for return
    ASs = [AS_p, AS_n]
    ros = [ro_p, ro_n]
    ms = [m_p, m_n]
    ns = [n_p, n_n]
    _ASs = [v.cpu().numpy() for v in ASs]
    _ros = [v.cpu().numpy() for v in ros]
    _ms = [v.cpu().numpy() for v in ms]
    _ns = [v.cpu().numpy() for v in ns]

    # squeeze r and theta dims
    lons, lats = lons.squeeze(), lats.squeeze()
    lats_mesh, lons_mesh = torch.meshgrid(lats, lons, indexing="ij")
    ar = ar.squeeze()
    r = r.squeeze()

    # loop list for L/H detection(s)
    if ty == "both":
        loop_list = [0,1]
    elif ty == "L":
        loop_list = [0]
    elif ty == "H":
        loop_list = [1]
    else:
        raise ValueError("ty must be both, L, or H")

    # making point data at center of vortices
    arrs = []
    is_detected = True
    for i in loop_list:  # type loop for lows and highs

        type = "L" if i == 0 else "H"

        # read ro index and get corresponding values
        idx = idx_rs[i]
        _xx = xx[idx,idx_y,idx_x]
        _yy = yy[idx,idx_y,idx_x]
        _xy = xy[idx,idx_y,idx_x]

        # search local maxima(minima) of AS_p(AS_n)
        # checking its value must be lager than AS_n(AS_p) on the same ponits
        # lmp: bool array whether indexing is local max/min of AS_p/AS_n
        j = (i + 1) % 2
        lmp = _local_ex_torch(ASs[i],"max",reqN,zloop,ar2=ASs[j])

        # get vortices characteristics where AS_p/AS_n local max/min
        ls_So = ASs[i][lmp]
        ls_ro = ros[i][lmp]
        ls_m = ms[i][lmp]
        ls_n = ns[i][lmp]

        # number of initially detected points
        N = len(ls_So)

        ls_lon = lons_mesh[lmp]
        ls_lat = lats_mesh[lmp]
        ls_valV = ar[lmp]

        # calc other parameters
        ls_Do = ls_So * ls_ro / fct  #[gpm]
        ls_SBG = (ls_m**2.+ls_n**2.)**.5 #[gpm/100km]
        ls_SBGang = torch.arctan2(ls_n, ls_m)  #[rad]
        ls_SR = ls_SBG / ls_So

        ls_xx, ls_yy, ls_xy = _xx[lmp], _yy[lmp], _xy[lmp]
        
        # making elliplicity
        ls_ee = _calc_elliplicity(ls_xx,ls_yy,ls_xy)

        # abs and fct for zonal flattness test
        ls_xx = torch.abs(ls_xx) * fct * fct

        # threshold mask
        mask1 = ((ls_So > So_thres) &
                 (ls_SR < SR_thres) &
                 (ls_Do > Do_thres) &
                 (ls_xx > xx_thres))
        if rrmin:
            mask1 = mask1 & (ls_ro != rmin)
        if rrmax:
            mask1 = mask1 & (ls_ro != rmax)

        # mask to remove extremely near but weaker pair (yamane scheme)
        dd = _gcd_torch(ls_lon.view(1,N),ls_lat.view(1,N),ls_lon.view(N,1),ls_lat.view(N,1))
        ls_ro_y = ls_ro.view(N,1)
        ls_ro_x = ls_ro.view(1,N)
        ls_ro_y, ls_ro_x = torch.meshgrid(ls_ro,ls_ro,indexing="ij")
        ls_So_y, ls_So_x = torch.meshgrid(ls_So,ls_So,indexing="ij")
        mask2 = (dd < ls_ro_y) & (dd < ls_ro_x) & (ls_So_y < ls_So_x)
        mask2 = ~torch.any(mask2, dim=1)

        mask = mask1 & mask2
        if torch.any(mask):  # if there is at least one detection...

            # get simple local extrema of input
            if i == 0:
                lmp = _local_ex_torch(ar,"min",reqN,zloop)
            else:
                lmp = _local_ex_torch(ar,"max",reqN,zloop)

            # determine local extrema of input (ex), not local extrema of ASs
            ls_lon_x, ls_lat_x = lons_mesh[lmp], lats_mesh[lmp]
            ls_ar_x = ar[lmp]
            M = len(ls_ar_x)

            # prepare ex (closed contour) condition
            ls_ex = torch.zeros((N,), dtype=i4, device=device)

            if M == 0:  # there is no local extremum

                ls_lonX = np.full((N,), 999.9, dtype=np.float32)
                ls_latX = np.full((N,), 999.9, dtype=np.float32)
                ls_valX = np.full((N,), 0, dtype=np.int32)

            else:

                # co-location matrix for ASs extrema and input extrema
                lon_v, lon_x = torch.meshgrid(ls_lon, ls_lon_x, indexing="ij")
                lat_v, lat_x = torch.meshgrid(ls_lat, ls_lat_x, indexing="ij")
                dd = _gcd_torch(lon_v, lat_v, lon_x, lat_x)
                ro_v, ar_x = torch.meshgrid(ls_ro * 0.63, ls_ar_x, indexing="ij")

                # update ex
                #idx_ex = ~torch.any(dd < ro_v, dim=1)
                idx_ex = torch.any(dd < ro_v, dim=1)
                ls_ex[idx_ex] = 1

                # get values on the extrema
                min_d, min_idx = torch.min(dd, dim=1)
                idx_v = torch.arange(N, device=device)
                nearest_lon = lon_x[idx_v, min_idx]
                nearest_lat = lat_x[idx_v, min_idx]
                nearest_val = ar_x[idx_v, min_idx]
                ls_lonX = torch.where(idx_ex, nearest_lon, 999.9).cpu().numpy()
                ls_latX = torch.where(idx_ex, nearest_lat, 999.9).cpu().numpy()
                ls_valX = torch.where(idx_ex, nearest_val, 0.).cpu().numpy()

            ls_t = np.full((N,), t)
            ls_ty = np.full((N,), i)
            ls_lev = np.full((N,), lev)

            # make csv for detected point data
            dir = {
                    "time": ls_t,
                    "ty": ls_ty,
                    "lev": ls_lev,
                    "lat": ls_lat.cpu().numpy(),
                    "lon": ls_lon.cpu().numpy(),
                    "valV": ls_valV.cpu().numpy(),
                    "So": ls_So.cpu().numpy(),
                    "ro": ls_ro.cpu().numpy(),
                    "Do": ls_Do.cpu().numpy(),
                    "SBG": ls_SBG.cpu().numpy(),
                    "SBGang": ls_SBGang.cpu().numpy(),
                    "SR": ls_SR.cpu().numpy(),
                    "m": ls_m.cpu().numpy(),
                    "n": ls_n.cpu().numpy(),
                    "EE": ls_ee.cpu().numpy(),
                    "XX": ls_xx.cpu().numpy(),
                    "ex": ls_ex.cpu().numpy(),
                    "valX": ls_valX,
                    "lonX": ls_lonX,
                    "latX": ls_latX,
                    }
            df = pd.DataFrame(dir)
            df = df[mask.cpu().numpy()].reset_index(drop=True)

            # save V
            PATH = f'{DIR_V}/V-{type}-{tn}-{lev:04}.csv'
            df.to_csv(PATH, index=False)

        # save AS
        data_name = ["AS","ro","m","n"]  # all saved in DIR_AS
        data_arrs = [_ASs[i],_ros[i],_ms[i],_ns[i]]

        for dname, darr in zip(data_name, data_arrs):
            darr = darr[np.newaxis, np.newaxis, :, :]

            if nc:
                da = xr.DataArray(darr, dims=dims, coords=coords)
                ds = xr.Dataset({dname: da})
                name = f'{DIR_AS}/{dname}-{type}-{tn}-{lev:04}.nc'
                ds.to_netcdf(name)
            else:
                name = f'{DIR_AS}/{dname}-{type}-{tn}-{lev:04}.grd'
                darr.astype(fmt).tofile(name)

            if not subs: break

    print("done", lev, tn)


def conv_second(dt):
    # 'H' and 'T' are deprecated since pandas-2.2.0
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases

    if 'H' in dt or 'h' in dt:
        if 'H' == dt:
            _h = 1
        else:
            _h = int(dt[:-1])
        return 60*60*_h

    elif 'D' in dt:
        if 'D' == dt:
            _d = 1
        else:
            _d = int(dt[:-1])
        return 60*60*24*_d

    elif 'T' in dt or 'min' in dt:
        if 'T' == dt:
            _T = 1
        else:
            _T = int(dt[:-1])
        return 60*_T


def moving_direction(lon_B, lat_B, lon_F, lat_F):
    
    b = gcd(lon_B, lat_B, lon_F, lat_F)
    a = gcd(lon_F, lat_B, lon_F, lat_F)

    alpha = np.arcsin(a/b)  # returns 0 ~ pi/2 since 0 < a/b < 1
    # shogen (temae/oku -> east/west x north/south)
    d_lon_abs = np.abs(lon_B - lon_F)
    d_lon = lon_F - lon_B
    d_lat1 = lat_F - lat_B
    d_lat2 = lat_F + lat_B
    
    temae = d_lon_abs < 90. or 270. <= d_lon_abs < 360.
    oku = not temae
    east = 0. < d_lon < 180. or -360 < d_lon < -180.
    west = not east 
    
    shogen = 0
    
    if temae and east:
        if d_lat1 > 0: shogen = 1
        else: shogen = 4
    if temae and west:
        if d_lat1 > 0: shogen = 2
        else: shogen = 3
    if oku and east:
        if d_lat2 > 0: shogen = 1
        else: shogen = 4
    if oku and west:
        if d_lat2 > 0: shogen = 2
        else: shogen = 3                    

    if shogen == 0:
        raise ValueError('shogen error!')
        
    if shogen == 1:
        azimuth = alpha
    elif shogen == 2:
        azimuth = np.pi - alpha
    elif shogen == 3:
        azimuth = np.pi + alpha
    elif shogen == 4:
        azimuth = 2*np.pi - alpha

    return azimuth


