# @Author : Donglai
# @Time   : 1/4/2021 7:47 PM
# @Email  : dma96@atmos.ucla.edu donglaima96@gmail.com


from datetime import datetime, timedelta
import mechanize
import os
from .config import CONFIG
import pandas as pd
#from ..predict.realtime_read import pdframe_to_mat

def load(start_time = None,
         end_time = None):
    """
    Real time downloader of Kyoto data set
    @param start_time:
    @param end_time:
    @return: frame of dst
    """
    if not os.path.exists(CONFIG['local_data_dir']):
        os.makedirs(CONFIG['local_data_dir'])

    # if time_now is None:
    #     date_now = datetime.utcnow()
    # else:
    #     date_now = time_now
    #
    # start_time = date_now - timedelta(days = date_history)
    # end_time = date_now


    sCent = int(start_time.year / 100)
    sTens = int((start_time.year - sCent * 100) / 10)
    sYear = int(start_time.year - sCent * 100 - sTens * 10)
    sMonth = start_time.strftime("%m")
    eCent = int(end_time.year / 100)
    eTens = int((end_time.year - eCent * 100) / 10)
    eYear = end_time.year - eCent * 100 - eTens * 10
    eMonth = end_time.strftime("%m")

    dst_br = mechanize.Browser()
    dst_br.set_handle_robots(False)  # no robots
    dst_br.set_handle_refresh(False)  # can sometimes hang without this
    dst_br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    dst_br.open(CONFIG['remote_data_dir'])

    dst_br.form = list(dst_br.forms())[0]

    # fill out the page fields
    dst_br.form.find_control('SCent').value = [str(sCent)]
    dst_br.form.find_control('STens').value = [str(sTens)]
    dst_br.form.find_control('SYear').value = [str(sYear)]
    dst_br.form.find_control('SMonth').value = [sMonth]
    dst_br.form.find_control('ECent').value = [str(eCent)]
    dst_br.form.find_control('ETens').value = [str(eTens)]
    dst_br.form.find_control('EYear').value = [str(eYear)]
    dst_br.form.find_control('EMonth').value = [eMonth]

    dst_br.form.find_control('Output').value = ['DST']
    dst_br.form.find_control('Out format').value = ['IAGA2002']
    #dst_br.form.find_control('Email').value = "donglaima96@gmail.com"

    response = dst_br.submit()
    lines = response.readlines()
    dst_time = []
    dst_name = 'DST_realtime.txt'
    dst_txt_name = os.path.join(CONFIG['local_data_dir'], dst_name)
    dst_file = open(dst_txt_name,'w')
    for l in lines:

        clean_line = l.strip().decode("utf-8")

        if clean_line[-1] is not '|':
            dst_time.append(clean_line.split("\s+")[0])
            dst_file.write(clean_line)
            dst_file.write('\n')
    dst_file.close()
    dst_all = pd.read_csv(dst_txt_name, header=None, sep='\s+',
                          parse_dates=[[0, 1]], na_values=99999.99)
    dst_pdframe = dst_all.iloc[:, [0, 2]]
    dst_pdframe.columns = ['unix_time', 'dst_kyoto']
    dst_pdframe.set_index('unix_time', inplace=True, drop=True)
    dst_pdframe = dst_pdframe[start_time:end_time]
    #pdframe_to_mat(dst_pdframe,CONFIG['real_data_dir'],res = '60m')



    return dst_pdframe