# ORIENT

This is the final version of ORIENT.

## Installation

python setup.py -develop

Notice the pyspedas might have some problems, whatever the missing repo just use pip to install them should be fine.

## Example code
```
import ORIENT as orient


from datetime import datetime


start_time = datetime(2018,8,15)
end_time = datetime(2018,9,15)
input_time =  datetime(2018,9,1,3)

eflux_1 =  orient.eflux.model.ElectronFlux(start_time, end_time,instrument = 'mageis',channel = 16)
final_frame, X_input_total = eflux_1.get_flux(dst_source='omni',
                 al_source='omni',
                 sw_source='omni',use_omni = True,use_traj = False,get_input_time = input_time)
```

