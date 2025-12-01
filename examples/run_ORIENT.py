#!/usr/bin/env python3
"""
ORIENT quick wrapper: parse CLI → run per-energy model(s) → save plots.
Created: 06/13/2025
Author: Jack Topper

This script runs the ORIENT outer-radiation-belt model for one or more
electron energies and produces two standard science figures:

1. A **stacked time–L plot**:
   - Top 5 panels: geomagnetic and solar wind drivers used by the model  
     (SYMH, \(V_{SW}\), \(P_{SW}\), \(B_z\), AL/AE).
   - Lower panels: equatorial electron flux vs. time and L-shell for each
     requested energy (50, 235, 597, 909 keV).
   - A vertical red line marks the chosen **snapshot time**.

2. A set of **MLT–L polar plots** (one per energy):
   - Flux in the magnetic equatorial plane as a function of magnetic local
     time (MLT) and L-shell at the snapshot time.
   - Separate color scales for 50 keV vs higher energies.

Usage example:
  python run_orient.py \
    --start_time 2013-06-01 \
    --input_time 2013-06-01 \
    --input_hour 12 \
    --end_time 2013-06-05 \
    --energy_levels "50,235,597,909" \
    --dst_source omni --al_source omni --sw_source omni \
    --get_mlt_flux true \
    --output_dir ./orient_output
"""
from __future__ import annotations
import argparse
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import LogLocator, LogFormatterMathtext 

# If developing locally (repo checkout), uncomment the next 4 lines to force-source import.
# import sys, os
# repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# if repo_root not in sys.path:
#     sys.path.insert(0, repo_root)

import ORIENT as orient  # library import (installed or forced via sys.path)


# ---------------------------- config / constants ---------------------------- #

ENERGY_TO_CHANNEL: Dict[str, int] = {
    "50": 3, "235": 11, "597": 14, "909": 16
}

# Per-energy plot scaling (time–L panels)
TIME_L_NORMS = {
    3:   dict(normmin=1e2,    normmax=1e7),     # 50 keV wants a wider range
    11:  dict(normmin=1,      normmax=10**4.5), # defaults
    14:  dict(normmin=1,      normmax=10**4.5),
    16:  dict(normmin=1,      normmax=10**4.5),
}

# MLT plot scaling (polar)
MLT_NORMS = {
    "50": dict(normmin=10**2, normmax=10**7),
    "*":  dict(normmin=1,   normmax=10**5.5),
}


# ---------------------------- data structures ------------------------------ #

@dataclass(frozen=True)
class CliArgs:
    start_time: str
    input_time: str
    input_hour: int  # legacy / ignored now
    end_time: str
    energy_levels: str
    dst_source: str
    al_source: str
    sw_source: str
    get_mlt_flux: str
    output_dir: str


@dataclass
class TimeWindow:
    start: datetime
    input: datetime
    end: datetime


# ---------------------------- tiny helpers --------------------------------- #

def parse_args() -> CliArgs:
    p = argparse.ArgumentParser(
        description="Run ORIENT electron flux model for one or more energies.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--start_time",
        required=True,
        help="Start datetime (UTC), format: 'YYYY-MM-DD HH:MM'",
    )
    p.add_argument(
        "--input_time",
        required=True,
        help="Prediction datetime (UTC), format: 'YYYY-MM-DD HH:MM'",
    )
    # Keep this for backwards compatibility, but ignore it in logic
    p.add_argument(
        "--input_hour",
        type=int,
        choices=range(24),
        help="Deprecated; ignored. Hour is taken from --input_time.",
    )
    p.add_argument(
        "--end_time",
        required=True,
        help="End datetime (UTC), format: 'YYYY-MM-DD HH:MM'",
    )
    p.add_argument("--energy_levels", required=True, help='CSV of energies, e.g. "50,235,597,909"')
    p.add_argument("--dst_source", default="omni", choices=["omni", "kyoto"])
    p.add_argument("--al_source",  default="omni", choices=["omni", "al_CB"])
    p.add_argument("--sw_source",  default="omni", choices=["omni", "ace"])
    p.add_argument("--get_mlt_flux", default="false", choices=["true", "false"])
    p.add_argument("--output_dir", default="./orient_output")
    a = p.parse_args()
    return CliArgs(**vars(a))



def parse_times(a: CliArgs) -> TimeWindow:
    fmt = "%Y-%m-%d %H:%M"

    try:
        start = datetime.strptime(a.start_time, fmt)
        end   = datetime.strptime(a.end_time,   fmt)
        it    = datetime.strptime(a.input_time, fmt)
    except ValueError as e:
        raise ValueError(
            "start_time, input_time, and end_time must all be in the format "
            "'YYYY-MM-DD HH:MM' (UTC)."
        ) from e

    if not (start <= it < end):
        raise ValueError("Time ordering invalid: require start_time ≤ input_time < end_time.")

    return TimeWindow(start=start, input=it, end=end)



def energies(a: CliArgs) -> List[str]:
    raw = [s.strip() for s in a.energy_levels.split(",") if s.strip()]
    invalid = [e for e in raw if e not in ENERGY_TO_CHANNEL]
    if invalid:
        raise ValueError(f"Unsupported energies: {invalid}. Supported: {list(ENERGY_TO_CHANNEL)}")
    return raw


def build_model(tw: TimeWindow, channel: int) -> orient.eflux.model.ElectronFlux:
    return orient.eflux.model.ElectronFlux(
        start_time=tw.start,
        end_time=tw.end,
        instrument="mageis",
        channel=channel,
    )


# ---------------------------- core pipeline -------------------------------- #

def run_one_energy(a: CliArgs, tw: TimeWindow, energy: str):
    """Run a single energy model and return the ElectronFlux instance."""
    ch = ENERGY_TO_CHANNEL[energy]
    print(f"→ Running energy {energy} keV (channel {ch})")

    eflux = build_model(tw, ch)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _ = eflux.get_flux(
            dst_source=a.dst_source,
            al_source=a.al_source,
            sw_source=a.sw_source,
            use_omni=True,
            use_traj=False,
            get_input_time=tw.input,
            get_MLT_flux=(a.get_mlt_flux.lower() == "true"),
            selected_MLT_datetime=tw.input,
        )
    return eflux


def make_time_L_panel(ax, eflux) -> Tuple[plt.Axes, object]:
    """Draw a time–L panel for one channel and return (ax, quadmesh)."""
    ch = eflux.channel
    norms = TIME_L_NORMS.get(ch, TIME_L_NORMS[11])
    qm = eflux.make_flux_plot(ax, **norms)
    # label
    energy_label = {3: "50", 11: "235", 14: "597", 16: "909"}.get(ch, str(ch))
    ax.set_ylabel("L Shell")
    ax.text(0.01, 0.95, f"{energy_label} keV", transform=ax.transAxes,
            fontsize=12, va="top", color="white",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.6))
    return ax, qm

def add_global_colorbars(fig, meshes: List[Tuple[object, int, plt.Axes]]):
    """
    Attach:
      - one tall colorbar shared by all non-50 keV panels (235, 597, 909)
      - one separate colorbar for 50 keV (channel 3), if present

    Assumes TIME_L_NORMS gives the same (normmin, normmax) for channels 11/14/16.
    """

    # Split meshes into 50 keV and others
    fifty = []
    others = []
    for qm, ch, ax in meshes:
        if ch == 3:   # 50 keV
            fifty.append((qm, ax))
        else:         # 235, 597, 909 keV
            others.append((qm, ax))

    # Helper: configure log-decade ticks
    def _setup_log_colorbar(cb, label: str, tick_labelsize: int = 10, labelsize: int = 10):
        locator = LogLocator(base=10.0, subs=(1.0,))
        formatter = LogFormatterMathtext(base=10.0, labelOnlyBase=True)
        cb.locator = locator
        cb.formatter = formatter
        cb.update_ticks()
        cb.ax.tick_params(labelsize=tick_labelsize)
        cb.set_label(label, fontsize=labelsize)

    # 50 keV colorbar (next to the 50 keV panel only)
    if fifty:
        qm_50, ax_50 = fifty[0]  # assume only one 50 keV panel
        cax_50 = inset_axes(
            ax_50,
            width="1%",
            height="100%",
            loc="lower left",
            bbox_to_anchor=(1.01, 0.0, 1, 1),
            bbox_transform=ax_50.transAxes,
            borderpad=0,
        )
        cb_50 = fig.colorbar(qm_50, cax=cax_50)
        _setup_log_colorbar(
            cb_50,
            r"Flux ($\mathrm{cm^{-2}\,s^{-1}\,sr^{-1}\,keV^{-1}}$) [50 keV]",
        )

    # Shared tall colorbar for 235/597/909 keV
    if others:
        # Use the first non-50 quadmesh as the representative (they share norms)
        qm_ref, _ = others[0]

        # Compute combined vertical extent (in figure coordinates) of all non-50 axes
        positions = [ax.get_position() for (_, ax) in others]
        y0 = min(pos.y0 for pos in positions)
        y1 = max(pos.y1 for pos in positions)
        x1_max = max(pos.x1 for pos in positions)

        # Add a tall colorbar axis just to the right of the non-50 panels
        width = 0.02  # fraction of figure width
        cax_other = fig.add_axes([x1_max + 0.01, y0, width, y1 - y0])

        cb_other = fig.colorbar(qm_ref, cax=cax_other)
        _setup_log_colorbar(
            cb_other,
            r"Flux ($\mathrm{cm^{-2}\,s^{-1}\,sr^{-1}\,keV^{-1}}$) [235–909 keV]",
            tick_labelsize=10,
            labelsize=10,
        )

def stacked_time_L(eflux_list: List[orient.eflux.model.ElectronFlux],
                   a: CliArgs, tw: TimeWindow, outdir: Path):
    """Build stacked time–L figure with inputs + per-energy panels."""
    plt.rcParams.update({
        "lines.linewidth": 1.5,
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 16,
        "font.family": "sans-serif",
    })

    n_energy = len(eflux_list)
    total = 5 + n_energy
    fig, axs = plt.subplots(total, 1, figsize=(16, 3.2 * total), sharex=True)
    if total == 1:
        axs = [axs]
    plt.subplots_adjust(hspace=0.1)

    # Inputs from ref model (same sources across energies)
    ref = eflux_list[0]
    inputs = [
        ("dst", "SYMH"),
        ("flow_speed", r"$V_{SW}$ (km/s)"),
        ("pressure", r"$P_{SW}$ (nPa)"),
        ("bz", r"$B_z$ (nT)"),
    ]
    colors = ["black", "blue", "green", "red"]

    for (i, (attr, ylabel)) in enumerate(inputs):
        series = getattr(ref, attr, None)
        if series is not None:
            axs[i].plot(series.index, series.values, color=colors[i])
            axs[i].set_ylabel(ylabel)
            axs[i].grid(True, alpha=0.3)

    # AL/AE
    if getattr(ref, "al", None) is not None:
        axs[4].plot(ref.al.index, ref.al.values, color="purple")
        axs[4].set_ylabel("AL (nT)")
    elif getattr(ref, "ae", None) is not None:
        axs[4].plot(ref.ae.index, ref.ae.values, color="purple")
        axs[4].set_ylabel("AE (nT)")
    axs[4].grid(True, alpha=0.3)

    # Energy panels
    meshes: List[Tuple[object, int, plt.Axes]] = []
    for i, eflux in enumerate(eflux_list):
        ax = axs[5 + i]
        _, qm = make_time_L_panel(ax, eflux)
        meshes.append((qm, eflux.channel, ax))

    # Global colorbar (non-50 keV)
    add_global_colorbars(fig, meshes)

    # Vertical input-time marker
    for ax in axs:
        ax.axvline(tw.input, color="red", ls="--", lw=1.5, alpha=0.7)

    # Title, limits, save
    axs[0].set_xlim(tw.input, tw.end)
    energies_str = ",".join(sorted({str({3:"50",11:"235",14:"597",16:"909"}.get(e.channel, e.channel))
                                    for e in eflux_list}))
    input_str = tw.input.strftime("%Y-%m-%d %H:%M")
    end_str   = tw.end.strftime("%Y-%m-%d %H:%M")

    fig.suptitle(
        f"ORIENT Electron Flux — energies: {energies_str}\n"
        f"Input: {input_str} UTC | End: {end_str} UTC"
    )

    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"ORIENT_stacked_{energies_str.replace(',','-')}keV.png"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Saved stacked plot → {png}")


def mlt_plots(eflux_list: List[orient.eflux.model.ElectronFlux],
              a: CliArgs, outdir: Path):
    if a.get_mlt_flux.lower() != "true":
        print("Skipping MLT plots (not requested)")
        return

    outdir.mkdir(parents=True, exist_ok=True)

    for eflux in eflux_list:
        # Map channel → nominal energy (keV)
        energy = {3: "50", 11: "235", 14: "597", 16: "909"}.get(eflux.channel, str(eflux.channel))

        print(f"   Plotting MLT plot @ {energy} keV")

        # Use fixed norms per energy for cross-run comparability
        norms = MLT_NORMS["50"] if energy == "50" else MLT_NORMS["*"]
        eflux.makeMLTplot(
            energy_label=f"{energy} keV",
            normmax=norms["normmax"],
            normmin=norms["normmin"],
        )

        fname = outdir / f"ORIENT_{energy}keV_MLT.png"
        plt.savefig(fname, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"        Complete {fname}")



def main():
    a = parse_args()
    tw = parse_times(a)
    outdir = Path(a.output_dir)

    print("ORIENT quick wrapper")
    print(f"  Time: {a.start_time} → {a.end_time} (input {a.input_time}Z)")
    print(f"  Energies: {a.energy_levels}")
    print(f"  Sources: dst={a.dst_source}, al={a.al_source}, sw={a.sw_source}")
    energies_list = energies(a)

    eflux_list = []
    for e in energies_list:
        eflux = run_one_energy(a, tw, e)
        eflux_list.append(eflux)

    stacked_time_L(eflux_list, a, tw, outdir)
    mlt_plots(eflux_list, a, outdir)
    print("Done.")


if __name__ == "__main__":
    main()
