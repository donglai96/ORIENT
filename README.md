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

### Usage – Command Line Interface (CCMC-style)

For automated pipeline execution and production use (e.g., at CCMC), use the command-line script:

```bash
# Basic usage: single energy
python examples/run_ORIENT.py \
  --start_time "2013-06-01 00:00" \
  --input_time "2013-06-01 03:00" \
  --end_time   "2013-06-02 00:00" \
  --energy_levels "235"

# Multiple energy levels with MLT plots
python examples/run_ORIENT.py \
  --start_time "2013-06-01 00:00" \
  --input_time "2013-06-01 12:00" \
  --end_time   "2013-06-05 00:00" \
  --energy_levels "50,235,597,909" \
  --get_mlt_flux true \
  --output_dir ./results

# Using different data sources
python examples/run_ORIENT.py \
  --start_time "2013-06-01 00:00" \
  --input_time "2013-06-01 06:00" \
  --end_time   "2013-06-02 00:00" \
  --energy_levels "235" \
  --dst_source kyoto \
  --al_source  al_CB \
  --sw_source  ace

#### Command Line Options

All times are interpreted as **UTC**.

* `--start_time`
  Model initialization start time, **including hour and minute**.
  Format: `YYYY-MM-DD HH:MM` (e.g., `"2013-06-01 00:00"`)

* `--input_time`
  “Prediction time” for flux and MLT distributions.
  The stacked plots draw a **red vertical line** at this time, and MLT polar plots are evaluated exactly at this instant.
  Format: `YYYY-MM-DD HH:MM`

* `--end_time`
  End time of the analysis window (last time shown in the stacked time–L plots).
  Format: `YYYY-MM-DD HH:MM`

* `--energy_levels`
  Comma-separated list of nominal energies (in keV):
  `50, 235, 597, 909`
  Example: `"50,235,597,909"`

* `--dst_source`
  SYMH/Dst data source

  * `omni` (default): OMNI SYM-H
  * `kyoto`: Kyoto WDC

* `--al_source`
  AL/AE data source

  * `omni` (default)
  * `al_CB`: AL forecast model (Xinlin Li, CU Boulder)

* `--sw_source`
  Solar wind data source

  * `omni` (default): gap-filled, processed
  * `ace`: ACE spacecraft (near-real-time, can have gaps)

* `--get_mlt_flux`
  Whether to compute and save MLT polar plots.

  * `true` or `false` (default: `false`)

* `--output_dir`
  Output directory where PNG plots are written.
  Default: `./orient_output`

> **Note:** This command-line interface is used by the Community Coordinated Modeling Center (CCMC) for automated execution of ORIENT model requests.

### Plot Outputs

The CLI wrapper produces two main kinds of plots:

#### 1. Stacked time–L plots

**Filename pattern:**

```text
ORIENT_stacked_<energy_list>keV.png
# e.g. ORIENT_stacked_50-235-597-909keV.png
```

**Structure (top → bottom):**

1. **SYMH** (from chosen Dst/SYM-H source)
2. **Solar wind speed** (V_SW) (km/s)
3. **Solar wind dynamic pressure** (P_SW) (nPa)
4. **IMF B_z** (nT)
5. **AL or AE** (depending on input availability)
6. **One time–L panel per energy channel** (50, 235, 597, 909 keV)

All panels share the same time axis. A **red dashed vertical line** marks the selected `--input_time` (prediction time).

**Color scaling:**

* Each energy panel shows **equatorial differential electron flux** vs. time and L-shell.
* The color map uses a **base-10 logarithmic scale** (`LogNorm`), with ticks at integer decades:

  * (10^0, 10^1, 10^2, …)
* By default:

  * **50 keV** uses a wider range (e.g. (10^2)–(10^7)) to capture large fluxes.
  * **235, 597, 909 keV** share a **single, common colorbar** and flux range (e.g. (10^0)–(10^{4.5})) so that these energies are **directly comparable**.
* Units:
  [
  \mathrm{cm^{-2},s^{-1},sr^{-1},keV^{-1}}
  ]

This design makes it easy to:

* See how inputs (SYMH, solar wind, AL/AE) evolve over the chosen interval.
* Compare how different energy channels respond to geomagnetic driving.
* Identify the state at the prediction time (via the red vertical line).

#### 2. MLT polar plots (optional)

If `--get_mlt_flux true` is set, ORIENT saves **one polar plot per energy**:

**Filename pattern:**

```text
ORIENT_<energy>keV_MLT.png
# e.g. ORIENT_235keV_MLT.png
```

Each plot shows:

* **Radius**: L-shell (typically 2.6–6.6)
* **Angle**: Magnetic local time (MLT), labelled in hours (0, 6, 12, 18)
* **Color**: Differential electron flux at the chosen `--input_time`

**Color scaling and units:**

* Flux is again plotted on a **base-10 logarithmic scale**.
* Tick marks appear only at decades ((10^n)) for clean scientific interpretation.
* The code uses percentile-based scaling to avoid single outliers dominating the color bar, but keeps values within physically reasonable global limits:

  * By default, **50 keV** polar plots emphasize roughly (10^2)–(10^7).
  * Higher energies (≥ 235 keV) emphasize roughly (10^0)–(10^5).
* Units:
  [
  \mathrm{cm^{-2},s^{-1},sr^{-1},keV^{-1}}
  ]

These MLT plots answer: *“Given the driving up to the prediction time, what does the radial and local-time distribution of flux look like right now?”*

You can override color limits programmatically via:

```python
fig, ax = eflux.makeMLTplot(
    energy_label="235 keV",
    normmin=1e0,
    normmax=1e5,
)
```

for fully reproducible comparisons across cases.

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
