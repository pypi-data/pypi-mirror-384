import sys, os, calendar
from glob import glob
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd


class Finder:
    """
    Generate specific tracking data as one csv

    ----

    Parameters:
    -----------

    **odir** : ``str``, default ``'./d01'``
        Analysis directory of the detection/tracking (the same as ``odir`` in Detector and Tracker).

        Output files will be stored in $odir/ID if ``IDdir`` option is missing.

    **timestep** : ``int``, default ``6``
        Timestep of tracking data in hour.
    """

    def __init__(self,
                 odir='./d01',
                 timestep=6):

        self.idir = odir
        self.odir = odir+"/ID"
        self.timestep = timestep


    def find_one(self,
                 ty,
                 lev,
                 ym,
                 ID,
                 after_merge=False,
                 before_split=False,
                 _df2=None,
                 IDorg=None):
        """Get a specific track by specifing year, month, and ID.

        Parameters:
        -----------

        **ty** : "L" or "H"

        **lev** : int or float
            Level for the target depression.

        **ym** : int
            yyyymm for year and month when the target depression is being active.

        **ID** : int
            ID for the target depression.

        **after_merge** : bool
            If True, track will be gathered after merging to other track, till the track stops with 'solitary lysis' flag.

        **before_split** : bool
            If True, track will be gathered before splitting from other track, till the track stops with 'solitary genesis' flag.
        """
        os.makedirs(f'{self.odir}', exist_ok=True)

        ym = str(ym)
        y = int(ym[:4])
        m = int(ym[4:6])

        pick_ym = ym

        this_month = datetime(y, m, 1)
        prev_month = datetime(y, m, 1) - relativedelta(months=1)
        next_month = datetime(y, m, 1) + relativedelta(months=1)

        # check prev_month
        _y = prev_month.year
        _m = prev_month.month
        if not os.path.exists(f'{self.idir}/Vtc/{_y}{_m:02}'):
            prev_month = this_month

        # check next_month
        _y = next_month.year
        _m = next_month.month
        if not os.path.exists(f'{self.idir}/Vtc/{_y}{_m:02}'):
            next_month = this_month

        _py = prev_month.year
        _pm = prev_month.month    
        _ny = next_month.year
        _nm = next_month.month

        ld = calendar.monthrange(_ny, _nm)[1]
        tt = pd.date_range(f'{_py}-{_pm}-1 00',
                           f'{_ny}-{_nm}-{ld} {24-self.timestep:02}',
                           freq=f'{self.timestep}H')

        #tt_pre = pd.date_range(f'{y}-{m}-1 00', freq='-6H', periods=2)
        #print(tt_pre)

        # concatination of DataFrame
        first = True
        for t in tt:

            yy, mm = t.year, t.month
            dd, hh = t.day, t.hour

            tn = f'{yy}{mm:02}{dd:02}{hh:02}00'
            _ym = f'{yy}{mm:02}'

            name = f'V-{ty}-{tn}-{lev:04}'
            #name = f'V-{ty}-{tn}-'+str(lev).zfill(4)

            if not os.path.exists(f'{self.idir}/Vtc/{_ym}/{name}.csv'):
                continue

            if first:
                df = pd.read_csv(f'{self.idir}/Vtc/{_ym}/{name}.csv',
                                 parse_dates=[0])
                first = False

            if not first:
                _df = pd.read_csv(f'{self.idir}/Vtc/{_ym}/{name}.csv',
                                  parse_dates=[0])
                df = pd.concat([df,_df], ignore_index=True)
        if first:
            raise FileNotFoundError(f"there is no data in {self.idir}/Vtc/{_ym}")

        # search ID
        df_id = df[df.ID==ID].reset_index(drop=True)

        if len(df_id) == 0:
            raise ValueError(f"ID={ID} is not found.")

        # trim non sequential (~jumping time) data
        first = True
        seq_flag = False
        for i in df_id.index:

            ttt = df_id['time'].iloc[i]
            Y = ttt.year
            M = ttt.month
            D = ttt.day
            H = ttt.hour

            if first:
                ptime = datetime(Y, M, D, H)
                cint = [i]
                first = False
                init_ym = f'{Y}{M:02}'
                continue  # !! no need time here
            else:
                time = datetime(Y, M, D, H)

            if time == ptime + timedelta(hours=self.timestep):
                cint.append(i)

                if Y == y and M == m:
                    seq_flag = True

            elif seq_flag:
                break

            else:
                cint = [i]

            ptime = time

        #if not seq_flag:
        #    print(f'no match, {ym}')

        # select continuous data
        df_id = df_id.iloc[cint].reset_index(drop=True).astype({"ID":int})

        if type(IDorg) == type(None):
            IDorg=ID

        if after_merge:

            if type(_df2) == pd.DataFrame:
                last_time = _df2.time[len(_df2)-1]
                df0=df_id[df_id.time>last_time]
                df2=pd.concat([_df2,df0],ignore_index=True)
                print(f"concat {ID} after {IDorg}")
            else:
                df2=df_id

            merge_id = df2.MERGE.values[-1]
            split_id = df2.SPLIT.values[0]

            if merge_id > 0:  # there is at least an upstream vortex
                t2=df_id.time[len(df_id)-1]
                ym2=f"{t2.year}{t2.month:02}"

                self.find_one(ty,lev,ym2,merge_id,
                              after_merge=after_merge,before_split=before_split,
                              _df2=df2,IDorg=IDorg)

            elif merge_id in [-1,-3]:  # no more upstream vortex
                if before_split and split_id > 0:
                    t2=df2.time[0]
                    ym2=f"{t2.year}{t2.month:02}"
                    self.find_one(ty,lev,ym2,split_id,
                                  after_merge=False,before_split=before_split,
                                  _df2=df2,IDorg=IDorg)
                else:
                    # save file
                    output_file_path = f'{self.odir}/{ty}-{lev}-{pick_ym}-{IDorg}.csv'
                    df2.to_csv(output_file_path, index=False)
                    print(f"done {IDorg}!")

        elif before_split:

            if type(_df2) == pd.DataFrame:
                last_time = _df2.time[0]
                df0=df_id[df_id.time<last_time]
                df2=pd.concat([df0,_df2],ignore_index=True)
                print(f"concat {ID} before {IDorg}")
            else:
                df2=df_id

            merge_id = df2.MERGE.values[-1]
            split_id = df2.SPLIT.values[0]

            if split_id > 0:  # there is at least an downstream vortex
                t2=df_id.time[0]
                ym2=f"{t2.year}{t2.month:02}"
                self.find_one(ty,lev,ym2,split_id,
                              after_merge=False,before_split=before_split,
                              _df2=df2,IDorg=IDorg)

            elif split_id in [-1,-3]:  # no more downstream vortex
                # save file
                output_file_path = f'{self.odir}/{ty}-{lev}-{pick_ym}-{IDorg}.csv'
                df2.to_csv(output_file_path, index=False)
                print(f"done {IDorg}!")

        else:
            # save file
            output_file_path = f'{self.odir}/{ty}-{lev}-{pick_ym}-{ID}.csv'
            df_id.to_csv(output_file_path, index=False)
            print(f"done {ID}!")


    def find_all(self, ty, lev, all_in_one=False):
        """Search all tracks on the specific level in a whole time range and save them as csvs.
        Recommended for case studies.
        NOT recommended for long term analyses because ALL csv will be
        loaded and ALL tracks will be produced as separated csvs.
         
        If all_in_one is True, tracks will be gathered in one file as odir/all_{ty}_{lev}.csv
        Original daily track data (Vtc/*.csv) will not be deleted
        """
        os.makedirs(f'{self.odir}', exist_ok=True)

        ll = glob(f'{self.idir}/Vtc/*/V-{ty}-*-{lev:04}.csv')
        first = True

        if len(ll) == 0:
            raise FileNotFoundError(f"there is no match {self.idir}/Vtc/*/V-{ty}-*-{lev:04}.csv")

        for i,l in enumerate(ll):
            print("\r","reading",i+1,"/",len(ll),end="")
            if first:
                df = pd.read_csv(l, parse_dates=[0])
                first = False
            else:
                _df = pd.read_csv(l, parse_dates=[0])
                df = pd.concat([_df, df], ignore_index=True)

        df["ymID"] = [f"{df.time[i].year}{df.time[i].month:02}_{df.ID[i]}" for i in df.index]

        ids = sorted(df['ymID'].unique().tolist())
        #ids = [int(i) for i in ids if not np.isnan(i)]
        #keta = len(str(ids[-1]))
        
        #print('all IDs')
        #print(ids)

        for i,ID in enumerate(ids):
            print("\r",f"writing {ID}",i+1,"/",len(ids),end="")
            df_id = df[df.ymID==ID].sort_values('time', ascending=True)
            df_id["seqID"] = i
            df_id = df_id.reset_index(drop=True)
            if not all_in_one:
                df_id.to_csv(f'{self.odir}/{ty}-{lev}-{ID}.csv', index=False)
            else:
                if i==0:
                    df_id.to_csv(f'{self.idir}/all-{ty}-{lev}.csv', index=False,header=True)
                else:
                    df_id.to_csv(f'{self.idir}/all-{ty}-{lev}.csv', index=False, header=False,mode="a")
        print("done!")

    def count_all(self, ty, lev):
        """
        Print out count of all tracks on the specific level in the output directory.
        Yearly conts are also printed. 
        """
        
        ll = glob(f'{self.idir}/Vtc/*/V-{ty}-*-{lev:04}.csv')
        first = True

        ids_y = {}
        ids_pre = []
        for l in ll:
            y = int(l.split('/')[-2][:4])  # year
            m = int(l.split('/')[-2][4:]) # month

            df = pd.read_csv(l)
            if 'ID' not in df.columns:
                continue

            _ids = df['ID'].unique().tolist()
            # get new id in this time
            # to prevent double count when year changes
            ids_new = [i for i in _ids if i not in ids_pre]

            if y in ids_y.keys():
                ids_y[y] = ids_y[y] + ids_new
            else:
                ids_y[y] = ids_new

            # update pre with original
            ids_pre = _ids

        cnt_y = {k: len(np.unique(ids_y[k])) for k in ids_y.keys()}
        cnt_all = sum(cnt_y.values())

        for k in cnt_y.keys():
            print(f'{k}, {cnt_y[k]}')
        print(f'ALL, {cnt_all}')

