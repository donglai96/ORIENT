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
eflux_1.make_plot(normmax = 10**4)

```

### Usage - Command Line Interface Recommended for Community Coordinated Modeling Center (CCMC)

For automated pipeline execution and production use, use the command-line script:

```bash
# Basic usage
python examples/run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 3 --end_time 2013-06-02 --energy_levels "50,235"

# Multiple energy levels with MLT plots
python examples/run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 12 --end_time 2013-06-05 --energy_levels "50,235,597,909" --get_mlt_flux true --output_dir ./results

# Using different data sources
python examples/run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 3 --end_time 2013-06-02 --energy_levels "235" --dst_source kyoto --al_source al_CB --sw_source ace
```

#### Command Line Options:
- `--start_time`: Model initialization start time (YYYY-MM-DD)
- `--input_time`: Input time for flux prediction (YYYY-MM-DD)  
- `--input_hour`: Hour for prediction (0-23)
- `--end_time`: End time for analysis (YYYY-MM-DD)
- `--energy_levels`: Comma-separated energy levels: "50,235,597,909" (keV)
- `--dst_source`: DST data source (`omni` or `kyoto`)
- `--al_source`: AL data source (`omni` or `al_CB`)
- `--sw_source`: Solar wind data source (`omni` or `ace`)
- `--get_mlt_flux`: Generate MLT plots (`true` or `false`)
- `--output_dir`: Output directory for plots and data

**Note**: This command-line interface is used by the Community Coordinated Modeling Center (CCMC) for automated execution of ORIENT model requests.

## Examples
The examples are in the example/ folder as jupyter notebook.
### Model name
instrument : mageis, 
channel: 3, 11, 14, 16 , corresponding energy: 50 keV, 235 keV, 597 keV, 909 keV

instrument : rbsp
channel:1 .1.8 MeV
Put the *RB_model* folder under the same dir
### CCMC_test_storm
This example show a one month with multi storms. It also include MLT visulization
### CCMC_test_recent_storm
When not using OMNI data (i.e. The data period we want to check is too close to the current time), we can change the source of the input parameter
#### DST source
support 'kyoto' and 'omni'
#### AL source
support 'omni' and 'al_CB', the AL_CB is the AL index model from CU Boulder, an example can also be found in another [repo](https://github.com/donglai96/ORIENT-M)
#### solarwind source
support 'omni' and 'ace'

## To do
Add orbit and can compare with e.g. Arase mission and Van Allen Probe on orbit. The Van Allen Probe part has finished, but it requires original orbit data which is not included.
