import pyspedas
from pytplot import get_data
import numpy as np
import pandas as pd


class InitialFlux(object):
    def __init__(self,
                 event_time,
                 look_back_window = 120):
        
        self.event_time = event_time
        self.look_back_window = look_back_window

def get_initial_flux_data(trange, given_time, probe = 'b'):
    """
    Get the initial flux data, from mageis and rbsp
    """
    mageis_vars = pyspedas.rbsp.mageis(trange=trange, probe=probe, level='l3', rel='rel04')
    flux_mageis = get_data('FEDU')
    L = get_data('L')
    MLT = get_data('MLT')
    MLAT = get_data('MLAT')
    data_datetime_mageis = pd.to_datetime(flux_mageis.times,unit = 's')
