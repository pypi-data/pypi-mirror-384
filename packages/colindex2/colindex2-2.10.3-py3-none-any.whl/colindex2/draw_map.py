#!/usr/bin/env python3
import os, sys
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import warnings
warnings.simplefilter('ignore')
import argparse
import importlib.util

def _load_local_module(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} has not generated yet. Use gen_data_settings command")
    spec = importlib.util.spec_from_file_location("data_settings", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_settings"] = module
    spec.loader.exec_module(module)
    return module

def _confine_region(df,ext,mproj):
    if mproj == "region":
        if not ext == [0,0,0,0]:
            v = df[(ext[0]<df.lon)&(df.lon<ext[1])&(ext[2]<df.lat)&(df.lat<ext[3])]
        else:
            v = df
    elif mproj == "nps":
        v = df[df.lat>0]
    elif mproj == "sps":
        v = df[df.lat<0]
    return v

def draw_ro(ax,v,alpha=1,lw=1.5):
    for i in v.index:

        if v.at[i, 'ex'] == 1 and v.at[i, 'ty'] == 0: c = "b"
        if v.at[i, 'ex'] == 0 and v.at[i, 'ty'] == 0: c = "g"
        if v.at[i, 'ex'] == 1 and v.at[i, 'ty'] == 1: c = "r"
        if v.at[i, 'ex'] == 0 and v.at[i, 'ty'] == 1: c = "orange"

        _x, _y = v.at[i, 'lon'], v.at[i, 'lat']
        ax.tissot(
            lons=_x, lats=_y,
            rad_km=v.at[i, 'ro'],
            facecolor='None', alpha=alpha,
            edgecolor=c, linewidth=lw, zorder=100)

        xa, ya = ax.projection.transform_point(_x, _y, src_crs=ccrs.PlateCarree())
        try:
            ant = f"{v.at[i, 'ID']}"
            ax.annotate(ant, c='k', alpha=alpha,
                xy=(xa, ya), color='k', size=7, zorder=101)
        except:
            pass
    return ax

#def _draw_map(z, odir, ext, type, mproj, zint=100.,vmin=0,vmax=40,dpi=200,csv="Vtc"):
def _draw_map(z, t, lev, type, ext,  mproj, odir="d01", zint=100.,vmin=0,vmax=40,dpi=200,csv="Vtc"):
    #          aslevs=np.arange(0,41,5)):
    #lev = int(z.level.values)
    #t = pd.to_datetime(z.time.values)
    ym = f'{t.year}{t.month:02}'
    tn = f'{ym}{t.day:02}{t.hour:02}00'
    #tn = f'{ym}{t.day:02}{t.hour:02}0000'
    print(tn)

    if type == "both":
        ASp = xr.open_dataarray(f'./{odir}/AS/{ym}/AS-L-{tn}-{lev:04}.nc').squeeze()
        ASn = xr.open_dataarray(f'./{odir}/AS/{ym}/AS-H-{tn}-{lev:04}.nc').squeeze()
        AS = xr.where(ASp**2 > ASn**2, ASp, ASn)
        Vp = pd.read_csv(f'./{odir}/{csv}/{ym}/V-L-{tn}-{lev:04}.csv', parse_dates=['time'])
        Vp = _confine_region(Vp,ext,mproj)
        Vn = pd.read_csv(f'./{odir}/{csv}/{ym}/V-H-{tn}-{lev:04}.csv', parse_dates=['time'])
        Vn = _confine_region(Vn,ext,mproj)
        TR = Vp[Vp.ex==0]
        CL = Vp[Vp.ex==1]
        RG = Vn[Vn.ex==0]
        CH = Vn[Vn.ex==1]
        Vs = [TR, CL, RG, CH]
        colors = ['tab:green', 'tab:blue', 'tab:orange', 'tab:red']
        cmap="bwr_r"
        vmin=-40
    else:
        AS = xr.open_dataarray(f'./{odir}/AS/{ym}/AS-{type}-{tn}-{lev:04}.nc').squeeze()
        V = pd.read_csv(f'./{odir}/{csv}/{ym}/V-{type}-{tn}-{lev:04}.csv', parse_dates=['time'])
        V = _confine_region(V,ext,mproj)
        if type == "L":
            TR = V[V.ex==0]
            CL = V[V.ex==1]
            Vs = [TR, CL]
            colors = ['tab:green', 'tab:blue']
            cmap = "Grays"
        elif type == "H":
            RG = V[V.ex==0]
            CH = V[V.ex==1]
            Vs = [RG, CH]
            colors = ['tab:orange', 'tab:red']
            cmap = "Grays_r"
    #'time', 'ty', 'lev', 'lat', 'lon', 'valV', 'valX', 'So',
    #'ro', 'Do', 'SBG', 'SBGang', 'm', 'n', 'SR', 'ex', 'ID', 'MERGE',
    #'SPLIT', 'DIST', 'SPEED', 'DIR', '_ID_c', '_SC', '_DC', '_LONs_B',
    #'_LATs_B', 'DU', 'XS', 'QS5', 'QS7', 'ALLDIST', 'MEDDIST', 'MAX',
    #'MAXSo', 'MAXXS', 'MAXQS5', 'MAXQS7'


    if mproj == "region":
        ax = plt.axes(projection=ccrs.PlateCarree())
        if not ext == [0,0,0,0]:
            ax.set_extent(ext)
    elif mproj == "nps":
        ax = plt.axes(projection=ccrs.Orthographic(central_latitude=90, central_longitude=180))
    elif mproj == "sps":
        ax = plt.axes(projection=ccrs.Orthographic(central_latitude=-90, central_longitude=0))
    else:
        raise ValueError("mproj must be nps or sps or region")

    ax.coastlines(lw=2., edgecolor='lightgray', alpha=.5)
    #ax.coastlines(fc='lightgray', ec='none', alpha=.5)
    ax.gridlines(xlocs=np.arange(-180,180,10),ylocs=np.arange(-85,90,10),
                  linewidth=.05, alpha=.5, zorder=5)

    #aslevs = np.arange(0, 41, 5)
    #shade = ax.contourf(AS.longitude, AS.latitude, np.abs(AS.values), aslevs,extend='both,
    shade = ax.pcolormesh(AS.longitude,AS.latitude,AS,vmax=vmax,vmin=vmin,
                        cmap=cmap, #alpha=.5,
                        transform=ccrs.PlateCarree())
    plt.colorbar(shade, shrink=.7,)# orientation='horizontal')

    zlevs = np.arange(z.min()//zint*zint, z.max()//zint*zint, zint)
    #zint2 = zint * 2
    #zlevs100 = np.delete(zlevs, zlevs%zint2==0)
    #zlevs200 = np.delete(zlevs, zlevs%zint2!=0)
    #contour = ax.contour(z.longitude, z.latitude, z.values, zlevs200, colors='k',
    #                     linewidths=1., transform=ccrs.PlateCarree(), zorder=6)
    contour = ax.contour(z.longitude, z.latitude, z.values, zlevs, colors='k',
                         linewidths=.7, transform=ccrs.PlateCarree(), zorder=6)
    plt.clabel(contour, fontsize=9)
    #ax.contour(z.longitude, z.latitude, z.values, zlevs100, colors='k', linewidths=.3,
    #           transform=ccrs.PlateCarree())

    for v, c in zip(Vs, colors):

        ax.scatter(v.lon, v.lat, c=c, lw=.3, zorder=10,
                   edgecolors='w', s=13,
                   transform=ccrs.PlateCarree())
        for i in v.index:
            _x, _y = v.at[i, 'lon'], v.at[i, 'lat']
            xa, ya = ax.projection.transform_point(_x, _y, src_crs=ccrs.PlateCarree())
            if csv == "Vt" or csv == "Vtc":
                ant = f"{v.at[i, 'ID']}"
                ax.annotate(ant, c='k', alpha=.8,
                    xy=(xa, ya), color='k', size=7, zorder=11)

    for v, c in zip(Vs, colors):
        ax.scatter(v.lon, v.lat, c=c, s=18, ec='w', lw=.4, zorder=10,
                   transform=ccrs.PlateCarree())
        for i in v.index:
            _x, _y = v.at[i, 'lon'], v.at[i, 'lat']
            ax.tissot(
                lons=_x, lats=_y,
                rad_km=v.at[i, 'ro'],
                facecolor='None', alpha=0.8,
                edgecolor=c, linewidth=1.6, zorder=10)

            xa, ya = ax.projection.transform_point(_x, _y, src_crs=ccrs.PlateCarree())
            if csv == "Vt" or csv == "Vtc":
                ant = f"{v.at[i, 'ID']}"
                ax.annotate(ant, c='k',
                    xy=(xa, ya), color='k', size=7, zorder=11)

    #ax.set_title(f'{tn} {lev} hPa')
    ax.set_title(f'{tn} {lev}')
    os.makedirs(f"{odir}/fig", exist_ok=True)
    plt.savefig(f"{odir}/fig/{mproj}-{type}-{lev:04}-{tn}.png")
    plt.close()

def draw_map():
    description = """
Draw maps using track data, AS, and geopotential height. data_settings.py is also referred. Figures will be stored in output_data_dir/fig.
 $ draw_map input_z_path output_data_dir type lev mproj
For example, You can set extent for regional map.
 $ draw_map ./z.nc ./d01 L 300 region -ext 120 150 20 50 
You can set specific timestep with/without range.
 $ draw_map ./z.nc ./d01 L 300 nps -t "2018-02-04 00"
 $ draw_map ./z.nc ./d01 L 300 nps -t "2018-02-04 00" "2018-02-04 18"
            """
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_z_path", type=str, help="input geopotential height data path")
    parser.add_argument("output_data_sir", type=str, help="top of output data dir")
    parser.add_argument("type", type=str, help="L or H")
    parser.add_argument("level", type=int, help="pressure level")
    parser.add_argument("mproj", type=str, help="region or nps or sps")
    parser.add_argument("-ext", nargs=4, type=str, help="map extent, west east south north", default=[0,0,0,0])
    parser.add_argument("-t", nargs="+", type=str, help="a time or start and end times to draw")
    parser.add_argument("-zint", type=float, help="Z contour interval (default 100 m)", default=100.)

    args = parser.parse_args()
    input_z_path = args.input_z_path
    odir = args.output_data_dir

    data_settings_path = os.path.join(os.getcwd(), "data_settings.py")
    D = _load_local_module(data_settings_path)

    if D.input_data_type == "nc":
        if not hasattr(D, "var_name"):
            da = xr.open_dataarray(input_z_path)
        else:
            ds = xr.open_dataset(input_z_path)
            da = ds[D.var_name]

        if hasattr(D, "lon_name"):
            da = da.rename({D.lon_name:"longitude"})
        if hasattr(D, "lat_name"):
            da = da.rename({D.lat_name:"latitude"})
        if hasattr(D, "lev_name"):
            da = da.rename({D.lev_name:"level"})
        if hasattr(D, "time_name"):
            da = da.rename({D.time_name:"time"})

        times = pd.to_datetime(da.time.values)

    else:
        lons = D.lons
        lats = D.lats
        levs = D.levs
        times = D.times
        shape = (len(times),len(levs),len(lats),len(lons))
        fmt = D.input_data_type
        with open(input_z_path, "r") as a:
            ar = np.fromfile(a, dtype=fmt).reshape(shape)
        dims = ["time","level","latitude","longitude"]
        coords = {"time": times,
                  "level": levs,
                  "latitude": lats,
                  "longitude": lons}
        da = xr.DataArray(ar, dims=dims, coords=coords)

    #idx_l = np.where(levs==float(args.lev))

    if type(args.t) == type(None):
        draw_times = times
    elif len(args.t) == 1:
        idx_t = np.where(times==args.t[0])[0][0]
        draw_times = [times[idx_t]]
    elif len(args.t) == 2:
        idx_ts = np.where(times==args.t[0])[0][0]
        idx_te = np.where(times==args.t[1])[0][0]
        draw_times = times[slice(idx_ts, idx_te+1)]

    for t in draw_times:
        z = da.sel(time=t, level=int(args.level))
        #_draw_map(z, odir, args.ext, args.type, args.mproj, args.zint)
        _draw_map(z, t, args.level, args.type, args.ext, args.mproj, odir=odir, zint=args.zint,vmin=0,vmax=40,dpi=200,csv="Vtc")

