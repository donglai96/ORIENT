#!/usr/bin/env python
# coding: utf-8
"""
ORIENT Model Wrapper Script
Created: 06/13/2025
Author: Jack Topper
Purpose: Command-line interface for ORIENT electron flux model with automated pipeline support

Example usage:
python run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 3 --end_time 2013-06-02 --energy_levels "50,235" --output "/Documents"
"""

import sys
import os
import argparse
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

try:
    import ORIENT as orient
except ImportError as e:
    print(f"Error importing ORIENT module: {e}")
    print("Please ensure ORIENT is properly installed and in your Python path.")
    sys.exit(1)


class ORIENTModelRunner:
    """Main class for running ORIENT models with multiple energy levels."""
    
    # Supported energy levels and their corresponding channels
    ENERGY_CHANNELS = {
        '50': 3,
        '235': 11,
        '597': 14,
        '909': 16
    }
    
    def __init__(self, args):
        self.args = args
        self.energy_levels = self._parse_energy_levels()
        self.times = self._parse_times()
        self.eflux_models = []
        
    def _parse_energy_levels(self):
        """Parse and validate energy levels from command line input."""
        try:
            levels = [level.strip() for level in self.args.energy_levels.split(',')]
            # Validate energy levels
            invalid_levels = [level for level in levels if level not in self.ENERGY_CHANNELS]
            if invalid_levels:
                raise ValueError(f"Invalid energy levels: {invalid_levels}. "
                               f"Supported levels: {list(self.ENERGY_CHANNELS.keys())}")
            return levels
        except Exception as e:
            print(f"Error parsing energy levels: {e}")
            sys.exit(1)
    
    def _parse_times(self):
        """Parse and validate time inputs."""
        try:
            start_time = datetime.strptime(self.args.start_time, '%Y-%m-%d')
            input_time = datetime.strptime(self.args.input_time, '%Y-%m-%d').replace(
                hour=int(self.args.input_hour)
            )
            end_time = datetime.strptime(self.args.end_time, '%Y-%m-%d')
            
            # Validate time ordering
            if end_time <= input_time:
                raise ValueError("End time must be after input time")
            if input_time < start_time:
                raise ValueError("Input time must be after start time")
                
            return {
                'start': start_time,
                'input': input_time,
                'end': end_time
            }
        except ValueError as e:
            print(f"Error parsing times: {e}")
            sys.exit(1)
    
    def run_models(self):
        """Run ORIENT models for all specified energy levels."""
        print(f"Running ORIENT models for energy levels: {', '.join(self.energy_levels)} keV")
        
        for energy in self.energy_levels:
            channel = self.ENERGY_CHANNELS[energy]
            
            try:
                print(f"Initializing model for {energy} keV (channel {channel})...")
                
                eflux = orient.eflux.model.ElectronFlux(
                    self.times['start'], 
                    self.times['end'], 
                    instrument='mageis',
                    channel=channel
                )
                
                # Run the model
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")  # Suppress model warnings
                    
                    final_frame, X_input_total = eflux.get_flux(
                        dst_source=self.args.dst_source,
                        al_source=self.args.al_source,
                        sw_source=self.args.sw_source,
                        use_omni=True,
                        use_traj=False,
                        get_input_time=self.times['input'],
                        get_MLT_flux=(self.args.get_mlt_flux.lower() == 'true'),
                        selected_MLT_datetime=self.times['input']
                    )
                
                self.eflux_models.append(eflux)
                print(f"✓ Completed model for {energy} keV")
                
            except Exception as e:
                print(f"✗ Error running model for {energy} keV: {e}")
                continue
        
        if not self.eflux_models:
            print("No models completed successfully. Exiting.")
            sys.exit(1)
            
        return self.eflux_models
    
    def generate_stacked_plot(self):
        """Generate comprehensive stacked plot for all energy levels."""
        print("Generating stacked plot...")
        
        # Configure matplotlib for better appearance
        plt.rcParams.update({
            'lines.linewidth': 2,
            'axes.labelsize': 22,
            'axes.titlesize': 24,
            'xtick.labelsize': 20,
            'ytick.labelsize': 20,
            'legend.fontsize': 20,
            'figure.titlesize': 26,
            'font.family': 'sans-serif'
        })
        
        num_energy_plots = len(self.eflux_models)
        total_plots = 5 + num_energy_plots
        
        # Create figure with subplots
        fig, axs = plt.subplots(total_plots, 1, figsize=(20, 4 * total_plots), sharex=True)
        if total_plots == 1:
            axs = [axs]  # Ensure axs is always a list
        plt.subplots_adjust(hspace=0.1)
        
        # Use first model for input data (should be consistent across models)
        eflux_ref = self.eflux_models[0]
        
        # Plot input data
        self._plot_input_data(axs[:5], eflux_ref)
        
        # Plot flux data for each energy level
        flux_plots = self._plot_flux_data(axs[5:], self.eflux_models)
        
        # Add colorbar
        self._add_colorbar(fig, axs[-1], flux_plots[0])
        
        # Highlight input time
        self._highlight_input_time(axs)
        
        # Set title and save
        self._finalize_plot(fig, axs[0])
        
        return fig
    
    def _plot_input_data(self, axes, eflux_ref):
        """Plot input data (DST, solar wind, etc.)"""
        plot_configs = [
            ('dst', 'SYMH', 'black'),
            ('flow_speed', r'$V_{SW}$ (km/s)', 'blue'),
            ('pressure', r'$P_{SW}$ (nPa)', 'green'),
            ('bz', r'$B_z$ (nT)', 'red'),
        ]
        
        for i, (attr, ylabel, color) in enumerate(plot_configs):
            if hasattr(eflux_ref, attr) and getattr(eflux_ref, attr) is not None:
                data = getattr(eflux_ref, attr)
                axes[i].plot(data.index, data.values, color=color, linewidth=2)
                axes[i].set_ylabel(ylabel)
                axes[i].grid(True, alpha=0.3)
        
        # Handle AL/AE data
        if hasattr(eflux_ref, 'al') and eflux_ref.al is not None:
            axes[4].plot(eflux_ref.al.index, eflux_ref.al.values, color='purple', linewidth=2)
            axes[4].set_ylabel('AL Index (nT)')
        elif hasattr(eflux_ref, 'ae') and eflux_ref.ae is not None:
            axes[4].plot(eflux_ref.ae.index, eflux_ref.ae.values, color='purple', linewidth=2)
            axes[4].set_ylabel('AE Index (nT)')
        
        axes[4].grid(True, alpha=0.3)
        
        # Add data source annotations
        sources = [self.args.dst_source, self.args.sw_source, self.args.sw_source, 
                  self.args.sw_source, self.args.al_source]
        
        for i, source in enumerate(sources):
            axes[i].text(1.01, 0.8, "Source:", transform=axes[i].transAxes, 
                        fontsize=16, verticalalignment='top', color='black')
            axes[i].text(1.01, 0.6, source.upper(), transform=axes[i].transAxes, 
                        fontsize=16, verticalalignment='top', color='black', weight='bold')
    
    def _plot_flux_data(self, axes, eflux_models):
        """Plot flux data for each energy level"""
        flux_plots = []
        
        for i, (eflux, energy) in enumerate(zip(eflux_models, self.energy_levels)):
            axes[i].set_ylabel('L Shell')
            
            try:
                flux_plot = eflux.make_flux_plot(axes[i], normmax=10**4.5, normmin=1)
                flux_plots.append(flux_plot)
                
                # Add energy label
                axes[i].text(0.01, 0.95, f"{energy} keV", transform=axes[i].transAxes, 
                            fontsize=22, verticalalignment='top', color='white', 
                            bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
                            
            except Exception as e:
                print(f"Warning: Could not plot flux for {energy} keV: {e}")
                
        return flux_plots
    
    def _add_colorbar(self, fig, last_ax, flux_plot):
        """Add colorbar to the plot"""
        try:
            color_axis = inset_axes(last_ax, width="1%", height="300%", loc='lower left',
                                   bbox_to_anchor=(1.01, 0., 1, 1), 
                                   bbox_transform=last_ax.transAxes, borderpad=0)
            fig.colorbar(flux_plot, cax=color_axis, 
                        label=r'Flux ($cm^{-2}s^{-1}sr^{-1}keV^{-1}$)')
        except Exception as e:
            print(f"Warning: Could not add colorbar: {e}")
    
    def _highlight_input_time(self, axes):
        """Add vertical line at input time"""
        for ax in axes:
            ymin, ymax = ax.get_ylim()
            ax.axvline(self.times['input'], color='red', linestyle='--', 
                      linewidth=2, alpha=0.8, label='Input Time')
    
    def _finalize_plot(self, fig, first_ax):
        """Set title, limits, and save plot"""
        first_ax.set_xlim(self.times['input'], self.times['end'])
        
        energy_str = ", ".join([f"{e} keV" for e in self.energy_levels])
        plt.suptitle(f"ORIENT Electron Flux Model: {energy_str}\n"
                    f"Input: {self.args.input_time} {self.args.input_hour}:00 UTC | "
                    f"End: {self.args.end_time}")
        
        # Create output directory if it doesn't exist
        Path(self.args.output_dir).mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.args.output_dir}/ORIENT_stacked_{'-'.join(self.energy_levels)}keV.png"
        plt.savefig(filename, format='png', bbox_inches='tight', dpi=300)
        print(f"✓ Saved stacked plot: {filename}")
        
        plt.close(fig)  # Free memory
    
    def generate_mlt_plots(self):
        """Generate individual MLT plots for each energy level"""
        if self.args.get_mlt_flux.lower() != 'true':
            print("Skipping MLT plots (not requested)")
            return
            
        print("Generating MLT plots...")
        Path(self.args.output_dir).mkdir(parents=True, exist_ok=True)
        
        for eflux, energy in zip(self.eflux_models, self.energy_levels):
            try:
                print(f"  Generating MLT plot for {energy} keV...")
                eflux.makeMLTplot(normmax=10**5.5)
                
                filename = f"{self.args.output_dir}/ORIENT_{energy}keV_MLT.png"
                plt.savefig(filename, format='png', bbox_inches='tight', dpi=300)
                plt.close()  # Free memory
                print(f"  ✓ Saved: {filename}")
                
            except Exception as e:
                print(f"  ✗ Error generating MLT plot for {energy} keV: {e}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run ORIENT electron flux model with multiple energy levels',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 3 --end_time 2013-06-02 --energy_levels "50,235"
  python run_ORIENT.py --start_time 2013-06-01 --input_time 2013-06-01 --input_hour 12 --end_time 2013-06-05 --energy_levels "50,235,597,909" --get_mlt_flux true
        """
    )
    
    # Required parameters
    required = parser.add_argument_group('required arguments')
    required.add_argument('--start_time', type=str, required=True,
                         help='Start time for model initialization (YYYY-MM-DD)')
    required.add_argument('--input_time', type=str, required=True,
                         help='Input time for flux prediction (YYYY-MM-DD)')
    required.add_argument('--input_hour', type=int, required=True, choices=range(24),
                         help='Hour for flux prediction (0-23)')
    required.add_argument('--end_time', type=str, required=True,
                         help='End time for analysis (YYYY-MM-DD)')
    required.add_argument('--energy_levels', type=str, required=True,
                         help='Comma-separated energy levels: 50,235,597,909 (keV)')
    
    # Optional parameters
    parser.add_argument('--dst_source', type=str, default='omni', 
                       choices=['omni', 'kyoto'],
                       help='DST data source (default: omni)')
    parser.add_argument('--al_source', type=str, default='omni',
                       choices=['omni', 'al_CB'], 
                       help='AL data source (default: omni)')
    parser.add_argument('--sw_source', type=str, default='omni',
                       choices=['omni', 'ace'],
                       help='Solar wind data source (default: omni)')
    parser.add_argument('--get_mlt_flux', type=str, default='false',
                       choices=['true', 'false'],
                       help='Generate MLT flux plots (default: false)')
    parser.add_argument('--output_dir', type=str, default='./orient_output',
                       help='Output directory (default: ./orient_output)')
    
    return parser.parse_args()


def main():
    """Main execution function"""
    print("ORIENT Multi-Energy Electron Flux Model")
    print("=" * 40)
    
    try:
        args = parse_arguments()
        
        # Display run parameters
        print(f"Energy Levels: {args.energy_levels} keV")
        print(f"Time Range: {args.start_time} to {args.end_time}")
        print(f"Input Time: {args.input_time} {args.input_hour}:00 UTC")
        print(f"Output Directory: {args.output_dir}")
        print("-" * 40)
        
        # Initialize and run models
        runner = ORIENTModelRunner(args)
        runner.run_models()
        runner.generate_stacked_plot()
        runner.generate_mlt_plots()
        
        print("\n" + "=" * 40)
        print("ORIENT model run completed successfully!")
        
    except KeyboardInterrupt:
        print("\n Run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()