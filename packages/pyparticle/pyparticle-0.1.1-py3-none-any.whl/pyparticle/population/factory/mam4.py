#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a population from a PARTMC NetCDF file
@author: Laura Fierce
"""

from ..base import ParticlePopulation
from pyparticle import make_particle_from_masses
from pyparticle.species.registry import get_species

import numpy as np
import os
from pathlib import Path
from .registry import register
from ...constants import MOLAR_MASS_DRY_AIR, R, DENSITY_LIQUID_WATER
from ...utilities import power_moments_from_lognormal
from .binned_lognormals import build as build_binned_lognormals
try:
    import netCDF4
    _HAS_NETCDF4 = True
except ModuleNotFoundError:
    netCDF4 = None
    _HAS_NETCDF4 = False

if _HAS_NETCDF4:
    @register("mam4") # only registers if netCDF4 is available
    def build(config):
        mam4_dir = Path(config['mam4_dir'])
        timestep = config['timestep']
        GSDs = config['GSD']
        if config.get("D_is_wet", True):
            aero_spec_names = [['SO4','OC','H2O'],['SO4','OC','H2O'],['SO4','OC','H2O'],['SO4','OC','H2O']]
        else:
            aero_spec_names = [['SO4','OC'],['SO4','OC'],['SO4','OC'],['SO4','OC']]
        
        N_bins = config['N_bins']
        

        if timestep == 0:
            raise ValueError('timestep=0 is invalid. Specify timestep = 1 for initial conditions')
        elif timestep == 1:
            mam_input = mam4_dir / 'namelist'
            Ns = np.zeros([len(GSDs)])
            
            for kk in range(len(Ns)):
                Ns[kk] = get_mam_input(
                    'numc' + str(kk+1),
                    mam_input)
            
            # GMDs = np.zeros([len(GSDs)])
            # try:
            #     for kk in range(len(GMDs)):
            #         GMDs[kk] = get_mam_input(
            #             'dgn' + str(kk+1),
            #             mam_input)
            # except ValueError:
                # if dgn not in namelist, use default initial GMDs
            GMDs = config.get('GMD_init', [1.1e-7, 2.6e-8, 2e-6, 5e-8]) # default initial GMDs for MAM4 (check fresh BC mode)
            
            aero_spec_fracs = []
            for kk in range(len(Ns)):
                spec_frac = []
                total_frac = 0.
                print(kk, aero_spec_names[kk])
                for spec_name in aero_spec_names[kk]:
                    # fixme: come up with more elegant way to handle PartMC --> MAM4 species name mapping
                    if spec_name.lower() == 'oc':
                        spec_name = 'pom'
                    
                    if spec_name.lower() == 'h2o':
                        frac = 0. 
                        #raise Warning('H2O mass fraction cannot be specified in MAM4 namelist; it is computed internally based on other species and hygroscopic growth. Setting frac_H2O=0 here.')
                    else: 
                        frac = get_mam_input(
                            'mf' + spec_name.lower() + str(kk+1),
                            mam_input)
                                        
                    spec_frac.append(frac)
                    total_frac += frac
                spec_frac = np.array(spec_frac)
                spec_frac /= total_frac
                aero_spec_fracs.append(spec_frac)
            aero_spec_fracs = np.array(aero_spec_fracs)

            lognormals_cfg = {
                'type': 'binned_lognormals',
                'D_min':config.get('D_min',1e-9), #fixme: option for +/- sigmas
                'D_max':config.get('D_max',1e-4),
                'N_bins': N_bins,
                'N': Ns,
                'GMD': GMDs,
                'GSD': GSDs,
                'aero_spec_names': aero_spec_names,
                'aero_spec_fracs': aero_spec_fracs,
                }
        else:
            output_tt_idx = timestep - 2 # timestep=2 is output index 0 = after 1 time step

            # fixme: make this +/- certain number of sigmas (rather than min/max diams)
            D_min = config['D_min']
            D_max = config['D_max']
            N_bins = config['N_bins']
            species_modifications = config.get('species_modification',{}) # modify species properties during post-processing
            output_filename = mam4_dir / 'mam_output.nc'
            currnc = netCDF4.Dataset(output_filename)

            num_aer = currnc['num_aer']
            so4_aer = currnc['so4_aer']
            soa_aer = currnc['soa_aer']
            dgn_a = currnc['dgn_a']
            dgn_awet = currnc['dgn_awet']

            p = config['p']
            T = config['T']
            #from .binned_lognormals import build as build_binned_lognormals
            
            lognormals_cfg = config

            # fixme: make this right
            rho_dry_air = MOLAR_MASS_DRY_AIR * p / (R * T)
            Ns = num_aer[:,output_tt_idx] * rho_dry_air # N/m^3
            idx, = np.where(Ns>0)
            Ns = Ns[idx]
            D_is_wet = config.get("D_is_wet", True)
            GMDs_wet = dgn_awet[idx,output_tt_idx]
            GMDs = dgn_a[idx,output_tt_idx]
            
            mass_so4 = so4_aer[idx,output_tt_idx] * rho_dry_air
            mass_soa = soa_aer[idx,output_tt_idx] * rho_dry_air
            # fixme: not actually sure what assumptions go into this for MAM4, assuming same GSD to compute mass H2O
            mass_h2o = DENSITY_LIQUID_WATER * np.pi/6 * np.array(
                    [
                        (power_moments_from_lognormal(3,N,gmd_wet,gsd) 
                        - power_moments_from_lognormal(3, N, gmd, gsd)) 
                        for (N, gmd, gmd_wet, gsd) in zip(Ns, GMDs, GMDs_wet, GSDs)])
            if D_is_wet:
                aero_spec_names = [['SO4','OC','H2O'],['SO4','OC','H2O'],['SO4','OC','H2O'],['SO4','OC','H2O']]
                aero_spec_fracs = []
                for (m_so4,m_soa,m_h2o) in zip(mass_so4,mass_soa,mass_h2o):
                    spec_frac = np.array([m_so4,m_soa,m_h2o])
                    spec_frac /= np.sum(spec_frac)
                    spec_frac[np.isnan(spec_frac)] = 0.
                    aero_spec_fracs.append(spec_frac)
                
            else:
                aero_spec_names = [['SO4','OC'],['SO4','OC'],['SO4','OC'],['SO4','OC']]
                aero_spec_fracs = []
                for (m_so4,m_soa) in zip(mass_so4,mass_soa):
                    spec_frac = np.array([m_so4,m_soa])
                    spec_frac /= np.sum(spec_frac)
                    spec_frac[np.isnan(spec_frac)] = 0.
                    aero_spec_fracs.append(spec_frac)

            if D_is_wet:
                GMDs_cfg = GMDs_wet
            else:
                GMDs_cfg = GMDs
            lognormals_cfg = {
                "type": "binned_lognormals",
                "N": Ns,
                "D_is_wet": D_is_wet,
                "GMD": GMDs_cfg,
                "GSD": GSDs,
                "aero_spec_names": aero_spec_names,
                "aero_spec_fracs": aero_spec_fracs,
                "N_bins": N_bins,
                "D_min": D_min,
                "D_max": D_max,
            }
        mam4_population = build_binned_lognormals(lognormals_cfg)
        return mam4_population
    
    # Replace previous code with this:
    # 
    # GMDs = []
    # GSDs = []
    # Ns = []
    # aero_spec_names = []
    # aero_spec_fracs = []
    # for mode in scenario.size.modes:
    #     GMDs.append(mode.geom_mean_diam)
    #     GSDs.append(10.**mode.log10_geom_std_dev)
    #     Ns.append(mode.number)
    #     aero_spec_names_onemode = []
    #     aero_spec_fracs.append(mode.mass_fractions)
    #     for one_spec in scenario.size.modes[0].species:
    #         aero_spec_names_onemode.append(one_spec.name)
    #     aero_spec_names.append(aero_spec_names_onemode)
    
    # if timestep == 0:
    #     raise ValueError('timestep=0 is invalid. Specify timestep = 1 for initial conditions')
    # elif timestep == 1:
    #     scenario_dir = ensemble_output_dir + '/' + scenario_name + '/'
    #     # mam_input = scenario_dir + 'mam_input.nl'
    #     mam_input = scenario_dir + 'namelist'
    #     Ns = np.zeros([len(GSDs)])
    #     for kk in range(len(Ns)):
    #         Ns[kk] = get_mam_input(
    #             'numc' + str(kk+1),
    #             mam_input=mam_input)
        
        
    #     binned_lognormal_cfg = {
    #         'type': 'binned_lognormals',
    #         'D_min':1e-9, #fixme: option for +/- sigmas
    #         'D_max':1e-4,
    #         'N_bins': N_bins,
    #         'N': Ns,
    #         'GMD': GMDs,
    #         'GSD': GSDs,
    #         'aero_spec_names': aero_spec_names,
    #         'aero_spec_fracs': aero_spec_fracs,
    #         }
    #     particle_population = build_population(binned_lognormal_cfg)
        
    #     gas_cfg = {
    #         'H2SO4':get_mam_input(
    #                 'qh2so4',
    #                 mam_input=mam_input),
    #         'SO2':get_mam_input(
    #                 'qso2',
    #                 mam_input=mam_input),
    #         'units':'kg_per_kg'}
    #     gas_mixture = build_gas_mixture(gas_cfg)
        
    #     thermodynamics = { 
    #         'T':scenario.temperature,
    #         'p':scenario.temperature,
    #         'RH':scenario.relative_humidity}
        
    # else:
    #     output_filename = ensemble_output_dir + '/' + scenario_name + '/mam_output.nc'
    #     currnc = Dataset(output_filename)
    #     timestep = timestep - 1
    #     mam4_population_cfg = {
    #         'type':'mam4',
    #         'output_filename': output_filename,
    #         'timestep':timestep,
    #         'GSD':GSDs, #fixme: put in the correct GSD values!
    #         'D_min':1e-9, #fixme: option for +/- sigmas
    #         'D_max':1e-4,
    #         'N_bins':N_bins,
    #         'T':scenario.temperature,
    #         'p':scenario.pressure}
        
    #     particle_population = build_population(mam4_population_cfg)
    #     gas_cfg = {'H2SO4':currnc.variables['h2so4_gas'][timestep]}        
    #     # gas_cfg = {'SO2':currnc.variables['so2_gas'][timestep]}
    #     # gas_cfg = {'SOAG':currnc.variables['soa_gas'][timestep]}
    #     gas_cfg['units'] = 'kg_per_kg' # todo: double-check
    #     gas_mixture = build_gas_mixture(gas_cfg)
        
    #     thermodynamics = { 
    #         'T':scenario.temperature,
    #         'p':scenario.temperature,
    #         'RH':scenario.relative_humidity}
        

else:
    def build(config):
        raise ModuleNotFoundError(
            "Install netCDF4 to read MAM4 files: generate the environment-partmc.yml file using tools/create_conda_env.py, "
            "then create and activate the 'pyparticle' conda environment (conda env create -f environment-partmc.yml -n pyparticle)."
        )

def get_mam_input(varname,mam_input_filename):

    f_input = open(mam_input_filename,'r')
    input_lines = f_input.readlines()
    yep = 0
    for oneline in input_lines:
        if varname in oneline:
            yep += 1 
            idx1,=np.where([hi == '=' for hi in oneline])
            idx2,=np.where([hi == ',' for hi in oneline])
            vardat = float(''.join([oneline[ii] for ii in range(idx1[0]+1,idx2[0])]))
    if yep == 0:
        # raise ValueError(varname,'is not a MAM input parameter')
        vardat = 0.0
        print(varname,'is not a MAM input parameter; returning 0.0')    
    elif yep > 1:
        raise ValueError('more than one line in ', mam_input_filename, 'starts with', varname)
    return vardat

def get_ncfile(partmc_output_dir, timestep, repeat):
    for root, dirs, files in os.walk(partmc_output_dir):
        f = files[0]
    if f.startswith('urban_plume_wc_'):
        preface_string = 'urban_plume_wc_'
    elif f.startswith('urban_plume_'):
        preface_string = 'urban_plume_'
    else:
        try:
            idx = partmc_output_dir[(partmc_output_dir.find('/')+1):].find('/')
            prefix_str = partmc_output_dir[(partmc_output_dir.find('/')+1):][:idx] + '_'
        except:
            try:
                preface_string, repeat2, timestep2 = f.split('_')
                preface_string += '_'
            except:
                preface_string = 'YOU_NEED_TO_CHANGE_preface_string_'
    ncfile = partmc_output_dir / (preface_string + str(int(repeat)).zfill(4) + '_' + str(int(timestep)).zfill(8) + '.nc')
    return ncfile