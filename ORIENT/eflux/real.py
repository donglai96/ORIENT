"""
@author Donglai Ma
@email donglaima96@gmail.com
@create date 2022-05-17 21:01:43
@modify date 2022-05-17 21:01:43
@desc real flux
"""
import numpy as np
import pandas as pd
import os
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm

class TrajFlux(object):
    def __init__(self,
                 selfmade_dir = '~/Research/data/selfmade/',
                 data_res = 5,
                 #model_folder =CONFIG['model_dir'],
                 instrument = 'mageis',
                 #satellites = ['a','b'],
                 channel = 11

                 #L_range = np.arange(2.6,6.6,0.1),
                 
                 #gap_max = 180

                 ):
        self.channel = channel
        self.selfmade_dir = selfmade_dir
        self.data_res = data_res
        #self.model_folder = model_folder
        self.instrument = instrument
        

        print('ORIENT initialized, Getting eflux from:',self.instrument,'channel:',self.channel)

    def get_flux(self,start_time, end_time):
        self.start_time = start_time # datetime of start
        self.end_time = end_time # datetime of end, in prediction mode, it's the end of nowcast
        tdate = [self.start_time,self.end_time]
        #self.aflux,self.bflux, self.atraj,self.btraj,self.atime,self.btime = None
        time_unix_traj = pd.read_pickle(self.selfmade_dir + 'unix_time_5min')
        time_traj = pd.to_datetime(time_unix_traj,unit='s')
        a_flux_name ='rbspa' + '_' + 'eflux_' + 'ch' + str(self.channel) + '_' + self.instrument + '_' + str(self.data_res) + 'min'
        b_flux_name ='rbspb' + '_' + 'eflux_' + 'ch' + str(self.channel) + '_' + self.instrument + '_' + str(self.data_res) + 'min'

            # get the traj information(make a matrix) and cut the time
        data_a = pd.DataFrame(data = {'time':time_traj})
        data_b = pd.DataFrame(data = {'time':time_traj})
        position_name = ['Lm_eq', 'ED_MLT', 'ED_MLAT', 'ED_R']
        for name in position_name:
            file_name_a = 'rbspa' + '_' + name + '_OP77Q_intxt_5min'
            file_name_b = 'rbspb' + '_' + name + '_OP77Q_intxt_5min'
            data_a[name] = pd.read_pickle(self.selfmade_dir + file_name_a)
            data_b[name] = pd.read_pickle(self.selfmade_dir + file_name_b)
        data_a['flux'] = pd.read_pickle(self.selfmade_dir + a_flux_name)
        data_b['flux'] = pd.read_pickle(self.selfmade_dir + b_flux_name)
        data_a_frame = (data_a[(data_a['time']<=tdate[-1]) & ( data_a['time']>=tdate[0]) ]).copy()
        data_b_frame = (data_b[(data_b['time']<=tdate[-1]) & ( data_b['time']>=tdate[0]) ]).copy()
        return data_a_frame,data_b_frame
        

def plot_real_flux(ax,frame,flux_min,flux_max,cmap = 'jet',linewidth = 4,use_L = 'ED_R',frame_name = 'flux'):
    L_probe = frame[use_L]
    flux_real = frame[frame_name].values + 1
    inxval_real = mdates.date2num(frame['time'])
    points_real = np.array([inxval_real, L_probe]).T.reshape(-1,1,2)
    segments_real = np.concatenate([points_real[:-1],points_real[1:]], axis=1)
    
    lc_real = LineCollection(segments_real, cmap=cmap, linewidth=linewidth,norm=LogNorm(vmin = 10**flux_min,vmax=10**flux_max))

    lc_real.set_array(flux_real)
    line_real = ax.add_collection(lc_real)
    return line_real