# ORIENT

This is the final version of ORIENT.

## Installation
I suggest use conda to manage the environment,
```
conda create --name orient python=3.8 
```

Activate the env and then first install the build package for developing purpose.
```
pip install build
```
Download the code
```
 git clone https://github.com/donglai96/ORIENT.git
```
Build the code
```
cd ORIENT
python -m build
pip install dist/ORIENT-1.0-py3-none-any.whl # or any other name created by last command
```

## Model

The default model folder name is 'RB_Model', please contact dma96@atmos.ucla.edu for the latest model(including relativistic eflux > 1 MeV models). The model file can also be found at https://zenodo.org/record/6299967.
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

