# @Author : Donglai
# @Time   : 11/23/2020 11:38 PM
# @Email  : dma96@atmos.ucla.edu donglaima96@gmail.com

import os
from.config import CONFIG
from datetime import datetime, timedelta
import shutil
import urllib.request as request
from contextlib import closing
import pandas as pd
#from SWO2R.predict.utils import pdframe_to_real,frame_fillgap



def load(start_time, end_time, res = '1m', no_update = False):
    """
    Load the ace data

    The trick part of ACE data is that it latest file is in another file
    So I always download the newest day incase we need real time
    @param start_time: start_time in unix
    @param end_time: end_time in unix
    @return: pdframe of ace data
    """

    # Create data folder
    if not os.path.exists(CONFIG['local_data_dir']):
        os.makedirs(CONFIG['local_data_dir'])

    # Get the date str
    time_length = (end_time - start_time).days
    date_str_list = [(end_time - timedelta(days=x)).strftime("%Y%m%d")
                     for x in range(time_length)]
    date_str_list.sort()

    instruments = ['mag','swepam']
    for instrument in instruments:
        name_suffix = 'ace_' + instrument + '_' + res +'.txt'

        filenames = [CONFIG['local_data_dir'] + x + '_' + name_suffix for x in date_str_list]
        urls = [CONFIG['remote_data_dir'] + x + '_'+ name_suffix for x in date_str_list]
        filenames.append(CONFIG['local_data_dir'] + name_suffix )
        urls.append(CONFIG['remote_data_dir'] + name_suffix)

        no_update_list = filenames[:-2]
        for url,file in zip(urls,filenames):
            if os.path.exists(file) and file in no_update_list:
                print('File exist:',file)
                continue
            with closing(request.urlopen(url)) as r:
                with open(file, 'wb') as f:
                    shutil.copyfileobj(r, f)
                    print('Downloaded  %s'%file)

        if instrument is 'mag':
            mag_pdframe_list = []
            for f in filenames:
                daily = pd.read_csv(f, skiprows=20, header=None, sep='\s+', na_values='-999.9',
                                    parse_dates=[[0, 1, 2, 3]])
                daily_bz = daily.iloc[:, [0, 6]]
                daily_bz.columns = ['unix_time', 'bz_gsm']
                # Add 40 minutes to simulate the bow shock nose point
                #daily_bz.loc[:,'date'] +=timedelta(minutes=shift_min)

                daily_bz.set_index('unix_time', inplace=True, drop=True)
                mag_pdframe_list.append(daily_bz)

            mag_all_raw = pd.concat(mag_pdframe_list)
            # Remove the conflict values in real data and the value in the latest'YYYYHHMM' file
            mag_all = mag_all_raw.groupby(mag_all_raw.index).first()

        elif instrument is 'swepam':
            swepam_pdframe_list = []
            for f in filenames:
                daily = pd.read_csv(f, skiprows=18, header=None, sep='\s+', na_values='-9999.9',
                                    parse_dates=[[0, 1, 2, 3]])
                daily_SW = daily.iloc[:, [0, 4, 5]]
                daily_SW.columns = ['unix_time', 'proton_density', 'flowspeed']
                # Add timeshift to simulate the bow shock nose point
                #daily_SW.loc[:, 'date'] += timedelta(minutes=shift_min)
                daily_SW.set_index('unix_time', inplace=True, drop=True)
                swepam_pdframe_list.append(daily_SW)

            swepam_all_raw = pd.concat(swepam_pdframe_list)
            swepam_all = swepam_all_raw.groupby(swepam_all_raw.index).first()
            swepam_all['flow_pressure'] = 2e-6 * swepam_all['proton_density'] * (swepam_all['flowspeed']) ** 2


    ace_frame = pd.concat([swepam_all,mag_all],axis=1)
    ace_frame = ace_frame[start_time:end_time]
    ace_frame.columns = ['Density(#/cm^3)', 'Speed(km/s)', 'Pressure(nPa)','Bz(nT)']
    return ace_frame

