#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 10:40:26 2024

@author: Andrea
"""

import os
import pandas as pd

from autoemxsp.core.EM_particle_finder import EM_Particle_Finder
import autoemxsp.tools.constants as cnst

# --------------------------
# Define sample
# --------------------------
sample_ID = 'example_particle_stats'
input_dir = 'input'

# --------------------------
# Define particles and frames to filter out
# --------------------------
particles_IDs_to_filter = [1, 3]         # Particle IDs to remove
frame_IDs_to_filter = ["A1"]       # Example frame IDs to remove (strings match the Frame ID column)

#%%
# --------------------------
# Code
# --------------------------
# Check if sample exists
sample_dir = os.path.join(input_dir, sample_ID)
if not os.path.exists(sample_dir):
    raise FileNotFoundError(f"Could not find sample at {sample_dir}. Please check 'sample_ID' and 'input_dir'.")

# Load particle size data
par_data_path = os.path.join(sample_dir, f"{sample_ID}_{cnst.PARTICLE_SIZES_FILENAME}.csv")
if not os.path.exists(par_data_path):
    raise FileNotFoundError(f"Particle size file not found at {par_data_path}")

par_data = pd.read_csv(par_data_path)

# Remove rows with matching Particle ID
if particles_IDs_to_filter is not None:
    par_data = par_data[~par_data[cnst.PAR_ID_DF_KEY].isin(particles_IDs_to_filter)]

# Remove rows with matching Frame ID
if frame_IDs_to_filter is not None:
    par_data = par_data[~par_data[cnst.FRAME_ID_DF_KEY].isin(frame_IDs_to_filter)]

# Re-calculate statistics and save filtered results
calculator = EM_Particle_Finder(None, None, results_dir=sample_dir, verbose=True)
calculator._sample_ID = sample_ID
calculator.analyzed_pars = list(
    zip(par_data[cnst.PAR_ID_DF_KEY], par_data[cnst.FRAME_ID_DF_KEY], par_data[cnst.PAR_AREA_UM_KEY])
)
if len(par_data) > 0:
    calculator.save_particle_statistics(output_file_suffix='_processed')
else:
    print("No particles left to build statistics. Ensure you do not filter out all particles through:"
          "particles_IDs_to_filter and frame_IDs_to_filter")