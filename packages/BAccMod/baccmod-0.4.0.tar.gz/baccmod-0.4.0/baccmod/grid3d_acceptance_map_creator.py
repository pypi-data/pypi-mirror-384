# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Filename: grid3d_acceptance_map_creator.py
# Purpose: Class for creation of model based on a 3D grid (spatial and energy)
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# ---------------------------------------------------------------------


import logging
from typing import Tuple, List, Optional

import astropy.units as u
import gammapy
import numpy as np
from astropy.coordinates import AltAz
from astropy.coordinates.erfa_astrom import erfa_astrom, ErfaAstromInterpolator
from gammapy.data import Observations
from gammapy.datasets import MapDataset
from gammapy.irf import FoVAlignment, Background3D
from gammapy.maps import WcsNDMap, Map, MapAxis, RegionGeom
from iminuit import Minuit
from regions import SkyRegion

from .base_acceptance_map_creator import BaseAcceptanceMapCreator
from .modeling import FIT_FUNCTION, log_factorial, log_poisson
from baccmod.logging import MOREINFO

logger = logging.getLogger(__name__)


class Grid3DAcceptanceMapCreator(BaseAcceptanceMapCreator):

    def __init__(self,
                 energy_axis: MapAxis,
                 offset_axis: MapAxis,
                 oversample_map: int = 10,
                 energy_axis_computation: MapAxis = None,
                 exclude_regions: Optional[List[SkyRegion]] = None,
                 dynamic_energy_axis: bool = False,
                 dynamic_energy_axis_target_statistics: int = 500,
                 dynamic_energy_axis_maximum_wideness_bin: float = 0.5,
                 dynamic_energy_axis_merge_zeros_low_energy: bool = False,
                 dynamic_energy_axis_merge_zeros_high_energy: bool = False,
                 cos_zenith_binning_method: str = 'min_livetime',
                 cos_zenith_binning_parameter_value: int = 3600,
                 initial_cos_zenith_binning: float = 0.01,
                 max_angular_separation_wobble: u.Quantity = 0.4 * u.deg,
                 zenith_binning_run_splitting: bool = False,
                 max_fraction_pixel_rotation_fov: float = 0.5,
                 time_resolution: u.Quantity = 0.1 * u.s,
                 use_mini_irf_computation: bool = False,
                 mini_irf_time_resolution: u.Quantity = 1. * u.min,
                 method='stack',
                 fit_fnc='gaussian2d',
                 fit_seeds=None,
                 fit_bounds=None,
                 azimuth_east_west_splitting = False,
                 interpolation_zenith_type: str = 'linear',
                 activate_interpolation_zenith_cleaning: bool = False,
                 interpolation_cleaning_energy_relative_threshold: float = 1e-4,
                 interpolation_cleaning_spatial_relative_threshold: float = 1e-2) -> None:
        """
        Create the class for calculating 3D grid acceptance model

        Parameters
        ----------
        energy_axis : MapAxis
            The energy axis for the acceptance model
        offset_axis : MapAxis
            The offset axis for the acceptance model
        oversample_map : int, optional
            Oversample in number of pixel of the spatial axis used for the calculation
        energy_axis_computation : gammapy.maps.geom.MapAxis
            The energy axis used for computation of the models, the model will then be reinterpolated on energy axis, if None, energy_axis will be used
        exclude_regions : list of regions.SkyRegion, optional
            Region with known or putative gamma-ray emission, will be excluded of the calculation of the acceptance map
        dynamic_energy_axis: bool
            if True, the energy axis will for computation will be determined independently for each model, the algorithm will use the energy_axis_computation and grouped bin in order to reach the target statisctics
        dynamic_energy_axis_target_statistics: int
            the target statistics per spatial and energy bin, for spatial, it is computed based on an average and therefore doesn't guaranty is is meet in every bin
        dynamic_energy_axis_maximum_wideness_bin: float
            energy bin will not be merged if the resulting bin will be wider (in logorarithmic space) than this value
        dynamic_energy_axis_merge_zeros_low_energy: bool
            decides if empty energy bins at low energy are merged during the dynamic binning
        dynamic_energy_axis_merge_zeros_high_energy: bool
            decides if empty energy bins at high energy are merged during the dynamic binning
        cos_zenith_binning_method : str, optional
            The method used for cos zenith binning: 'min_livetime','min_n_observation'
        cos_zenith_binning_parameter_value : int, optional
            Minimum livetime (in seconds) or number of observations per zenith bins
        initial_cos_zenith_binning : float, optional
            Initial bin size for cos zenith binning
        max_angular_separation_wobble : u.Quantity, optional
            The maximum angular separation between identified wobbles, in degrees
        zenith_binning_run_splitting : float, optional
            If true, will split each run to match zenith binning for the base model computation
            Could be computationally expensive, especially at high zenith with a high resolution zenith binning
        max_fraction_pixel_rotation_fov : bool, optional
            For camera frame transformation the maximum size relative to a pixel a rotation is allowed
        time_resolution : astropy.units.Quantity, optional
            Time resolution to use for the computation of the rotation of the FoV and cut as function of the zenith bins
        method : str, optional
            Decide if the acceptance is a direct event stacking or a fitted model. 'stack' or 'fit'
        fit_fnc: str or function
            Two dimensional function to be fitted. Some built-in functions are provided and selected by passing a string
            The function needs to have a size parameter (integral charge) as first parameter.
        fit_seeds: dict, can optionally be None if using a built-in function
            Seeds of the parameters of the function to fit. Normalisation parameter is ignored if given.
        fit_bounds: dict, can optionally be None if using a built-in function
            Bounds of the parameters of the function to fit. Normalisation parameter is ignored if given.
        use_mini_irf_computation : bool, optional
            If true, in case the case of zenith interpolation or binning, each run will be divided in small subrun (the slicing is based on time).
            A model will be computed for each sub run before averaging them to obtain the final model for the run.
            Should improve the accuracy of the model, especially at high zenith angle.
        mini_irf_time_resolution : astropy.units.Quantity, optional
            Time resolution to use for mini irf used for computation of the final background model
        azimuth_east_west_splitting: bool, optional
            if true will make a separate model of east oriented and west oriented data
        interpolation_zenith_type: str, optional
            Select the type of interpolation to be used, could be either "log" or "linear", log tend to provided better results be could more easily create artefact that will cause issue
        activate_interpolation_zenith_cleaning: bool, optional
            If true, will activate the cleaning step after interpolation, it should help to eliminate artefact caused by interpolation
        interpolation_cleaning_energy_relative_threshold: float, optional
            To be considered value, the bin in energy need at least one adjacent bin with a relative difference within this range
        interpolation_cleaning_spatial_relative_threshold: float, optional
            To be considered value, the bin in space need at least one adjacent bin with a relative difference within this range
        """

        # If no exclusion region, default it as an empty list
        if exclude_regions is None:
            exclude_regions = []

        # Compute parameters for internal map
        self.offset_axis = offset_axis
        if not np.allclose(self.offset_axis.bin_width, self.offset_axis.bin_width[0]):
            raise Exception('Support only regular linear bin for offset axis')
        if not np.isclose(self.offset_axis.edges[0], 0. * u.deg):
            raise Exception('Offset axis need to start at 0')
        self.oversample_map = oversample_map
        spatial_resolution = np.min(
            np.abs(self.offset_axis.edges[1:] - self.offset_axis.edges[:-1])) / self.oversample_map
        max_offset = np.max(self.offset_axis.edges)

        # Initiate upper instance
        super().__init__(energy_axis=energy_axis,
                         max_offset=max_offset,
                         spatial_resolution=spatial_resolution,
                         energy_axis_computation=energy_axis_computation,
                         exclude_regions=exclude_regions,
                         dynamic_energy_axis=dynamic_energy_axis,
                         dynamic_energy_axis_target_statistics=dynamic_energy_axis_target_statistics,
                         dynamic_energy_axis_maximum_wideness_bin=dynamic_energy_axis_maximum_wideness_bin,
                         dynamic_energy_axis_merge_zeros_low_energy=dynamic_energy_axis_merge_zeros_low_energy,
                         dynamic_energy_axis_merge_zeros_high_energy=dynamic_energy_axis_merge_zeros_high_energy,
                         cos_zenith_binning_method=cos_zenith_binning_method,
                         cos_zenith_binning_parameter_value=cos_zenith_binning_parameter_value,
                         initial_cos_zenith_binning=initial_cos_zenith_binning,
                         max_angular_separation_wobble=max_angular_separation_wobble,
                         zenith_binning_run_splitting=zenith_binning_run_splitting,
                         max_fraction_pixel_rotation_fov=max_fraction_pixel_rotation_fov,
                         time_resolution=time_resolution,
                         use_mini_irf_computation=use_mini_irf_computation,
                         mini_irf_time_resolution=mini_irf_time_resolution,
                         interpolation_zenith_type=interpolation_zenith_type,
                         azimuth_east_west_splitting=azimuth_east_west_splitting,
                         activate_interpolation_zenith_cleaning=activate_interpolation_zenith_cleaning,
                         interpolation_cleaning_energy_relative_threshold=interpolation_cleaning_energy_relative_threshold,
                         interpolation_cleaning_spatial_relative_threshold=interpolation_cleaning_spatial_relative_threshold)

        self.method = method
        self.fit_fnc = fit_fnc
        self.fit_seeds = fit_seeds
        self.fit_bounds = fit_bounds

        self.sq_rel_residuals = {'mean': [], 'std': []}

    def fit_background(self, count_map, exp_map_total, exp_map):
        centers = self.offset_axis.center.to_value(u.deg)
        centers = np.concatenate((-np.flip(centers), centers), axis=None)
        raw_seeds = {}
        bounds = {}
        if type(self.fit_fnc) == str:
            try:
                fnc = FIT_FUNCTION[self.fit_fnc]
            except KeyError:
                logger.error(f"Invalid built-in fit_fnc. Use {FIT_FUNCTION.keys()} or a custom function.")
                raise
            raw_seeds = fnc.default_seeds.copy()
            bounds = fnc.default_bounds.copy()
        else:
            fnc = self.fit_fnc
        if self.fit_seeds is not None:
            raw_seeds.update(self.fit_seeds)
        if self.fit_bounds is not None:
            bounds.update(self.fit_bounds)

        mask = exp_map > 0  # Handles fully overlapping exclusion regions in the 'size' seed computation
        # Seeds the charge normalisation to the observed counts corrected for exclusion region reduction to exposure
        raw_seeds['size'] = np.sum(count_map[mask] * exp_map_total[mask] / exp_map[mask]) / np.mean(mask)
        bounds['size'] = (raw_seeds['size'] * 0.1, raw_seeds['size'] * 10)

        # reorder seeds to fnc parameter order
        param_fnc = list(fnc.__code__.co_varnames[:fnc.__code__.co_argcount])
        param_fnc.remove('x')
        param_fnc.remove('y')
        seeds = {key: raw_seeds[key] for key in param_fnc}

        x, y = np.meshgrid(centers, centers)

        log_factorial_count_map = log_factorial(count_map)

        def f(*args):
            return -np.sum(
                log_poisson(count_map, fnc(x, y, *args) * exp_map / exp_map_total, log_factorial_count_map))

        logger.debug( f"seeds :\n{seeds}")
        m = Minuit(f,
                   name=seeds.keys(),
                   *seeds.values())
        for key, bound in bounds.items():
            if bound is None:
                m.fixed[key] = True
            else:
                m.limits[key] = bound
        m.errordef = Minuit.LIKELIHOOD
        m.simplex().migrad()
        if not m.valid : logger.warning(f"Fit invalid in energy/Zd bin.")
        if logger.getEffectiveLevel() <= logging.INFO:
            func = fnc(x, y, **m.values.to_dict()) * exp_map / exp_map_total
            func[exp_map == 0] = 1
            rel_residuals = 100 * (count_map - func) / func
            sq_rel_residuals =  (count_map - func) / np.sqrt(func)
            logger.log(MOREINFO, f"Results ({fnc.__name__}) :\n{m.values.to_dict()}")
            logger.debug("Average relative residuals : %.1f %%," % (np.mean(rel_residuals)) +
                        "Std = %.2f %%" % (np.std(rel_residuals)) + "\n")
            self.sq_rel_residuals['mean'].append(np.mean(sq_rel_residuals))
            self.sq_rel_residuals['std'].append(np.std(sq_rel_residuals))

        return fnc(x, y, **m.values.to_dict())

    def create_model(self, observations: Observations) -> Background3D:
        """
        Calculate a 3D grid acceptance map

        Parameters
        ----------
        observations : gammapy.data.observations.Observations
            The collection of observations used to make the acceptance map

        Returns
        -------
        acceptance_map : gammapy.irf.background.Background3D
        """

        # Compute base data
        count_background, exp_map_background, exp_map_background_total, livetime, energy_axis_computation = self._create_base_computation_map(
            observations)

        # Downsample map to bkg model resolution
        exp_map_background_downsample = exp_map_background.downsample(self.oversample_map, preserve_counts=True)
        exp_map_background_total_downsample = exp_map_background_total.downsample(self.oversample_map,
                                                                                  preserve_counts=True)

        # Create axis for bkg model
        edges = self.offset_axis.edges
        extended_edges = np.concatenate((-np.flip(edges), edges[1:]), axis=None)
        extended_offset_axis_x = MapAxis.from_edges(extended_edges, name='fov_lon')
        bin_width_x = np.repeat(extended_offset_axis_x.bin_width[:, np.newaxis], extended_offset_axis_x.nbin, axis=1)
        extended_offset_axis_y = MapAxis.from_edges(extended_edges, name='fov_lat')
        bin_width_y = np.repeat(extended_offset_axis_y.bin_width[np.newaxis, :], extended_offset_axis_y.nbin, axis=0)

        # Compute acceptance_map

        if self.method == 'stack':
            corrected_counts = count_background * (exp_map_background_total_downsample.data /
                                                   exp_map_background_downsample.data)
        elif self.method == 'fit':
            logger.info(f"Performing the background fit using {self.fit_fnc}.")
            corrected_counts = np.empty(count_background.shape)
            self.sq_rel_residuals = {'mean': [], 'std': []}
            for e in range(count_background.shape[0]):
                logger.info(f"Energy bin : [{energy_axis_computation.edges[e]:.2f},{energy_axis_computation.edges[e + 1]:.2f}]")
                corrected_counts[e] = self.fit_background(count_background[e].astype(int),
                                                          exp_map_background_total_downsample.data[e],
                                                          exp_map_background_downsample.data[e],
                                                          )

            logger.info("Average event counts diff/sqrt(fit) for each energies : "
                        f"{np.round(self.sq_rel_residuals['mean'], 2)}\n" +
                        f"Std = {np.round(self.sq_rel_residuals['std'], 2)}")
        else:
            raise NotImplementedError(f"Requested method '{self.method}' is not valid.")
        solid_angle = 4. * (np.sin(bin_width_x / 2.) * np.sin(bin_width_y / 2.)) * u.steradian
        data_background = corrected_counts / solid_angle[np.newaxis, :, :] / energy_axis_computation.bin_width[:, np.newaxis,
                                                                             np.newaxis] / livetime

        data_background = self._interpolate_bkg_to_energy_axis(data_background, energy_axis_computation)

        acceptance_map = Background3D(axes=[self.energy_axis, extended_offset_axis_x, extended_offset_axis_y],
                                      data=data_background.to(u.Unit('s-1 MeV-1 sr-1')),
                                      fov_alignment=FoVAlignment.ALTAZ)

        return acceptance_map

    def _create_base_computation_map(self, observations: Observations) -> Tuple[np.ndarray, WcsNDMap, WcsNDMap, u.Quantity, MapAxis]:
        """
        From a list of observations return a stacked finely binned counts and exposure map in camera frame to compute a
        model

        Parameters
        ----------
        observations : gammapy.data.observations.Observations
            The list of observations

        Returns
        -------
        count_background : numpy.ndarray
            The background counts
        exp_map_background : gammapy.map.WcsNDMap
            The exposure map corrected for exclusion regions
        exp_map_background_total : gammapy.map.WcsNDMap
            The exposure map without correction for exclusion regions
        livetime : astropy.unit.Quantity
            The total exposure time for the model
        energy_axis : gammapy.maps.MapAxis
            The energy axis used for the computation
        """

        offset_edges = self.offset_axis.edges
        offset_bins = np.round(np.concatenate((-np.flip(offset_edges), offset_edges[1:]), axis=None), 3)

        energy_axis_computation = self.energy_axis_computation.copy()
        if self.dynamic_energy_axis:
            data_energy_distribution = np.zeros(self.energy_axis_computation.nbin, dtype=np.int64)
            for obs in observations:
                events_camera_frame = self._get_events_in_camera_frame(obs)
                mask_event = np.logical_and(np.abs(events_camera_frame.lon) <= self.max_offset,
                                            np.abs(events_camera_frame.lat) <= self.max_offset)
                distrib, _ = np.histogram(obs.events.energy[mask_event], energy_axis_computation.edges)
                data_energy_distribution += distrib
            energy_axis_computation = self._compute_dynamic_energy_axis(energy_axis_computation,
                                                                        data_energy_distribution,
                                                                        len(offset_bins)**2)

        map_bins = (energy_axis_computation.edges, offset_bins, offset_bins)
        geom = self._get_geom(energy_axis_computation)
        count_background = np.zeros((len(map_bins[0]) - 1,
                                     len(map_bins[1]) - 1,
                                     len(map_bins[2]) - 1))
        exp_map_background = WcsNDMap(geom=geom, unit=u.s)
        exp_map_background_total = WcsNDMap(geom=geom, unit=u.s)
        livetime = 0. * u.s

        with erfa_astrom.set(ErfaAstromInterpolator(1000 * u.s)):
            for raw_obs in observations:
                # Copy the observation to prevent modifying the original
                obs = raw_obs.copy(True)

                # Filter events in exclusion regions
                filtered_exclude_regions = self._get_exclusion_regions_for_obs(obs)
                if len(filtered_exclude_regions) > 0:
                    geom_exclude_regions = RegionGeom.from_regions(filtered_exclude_regions)
                    mask = geom_exclude_regions.contains(obs.events.radec)
                else:
                    mask = np.zeros(len(obs.events.energy), dtype=bool)
                obs._events = obs.events.select_row_subset(~mask)
                # Create a count map in camera frame
                events_camera_frame = self._get_events_in_camera_frame(obs)
                count_obs, _ = np.histogramdd((obs.events.energy,
                                               -events_camera_frame.lon,
                                               events_camera_frame.lat
                                               ),
                                              bins=map_bins)
                # Create exposure maps and fill them with the obs livetime
                exp_map_obs = MapDataset.create(geom=geom)
                exp_map_obs_total = MapDataset.create(geom=geom)
                exp_map_obs.counts.data = obs.observation_live_time_duration.value
                exp_map_obs_total.counts.data = obs.observation_live_time_duration.value

                # Evaluate the average exclusion mask in camera frame
                # by evaluating it on time intervals short compared to the field of view rotation
                exclusion_mask = np.zeros(exp_map_obs.counts.data.shape[1:])
                time_interval = self._compute_time_intervals_based_on_fov_rotation(obs)
                for i in range(len(time_interval) - 1):
                    # Compute the exclusion region in camera frame for the average time
                    dtime = time_interval[i + 1] - time_interval[i]
                    time = time_interval[i] + dtime / 2
                    average_alt_az_frame = AltAz(obstime=time,
                                                 location=obs.observatory_earth_location)
                    average_alt_az_pointing = obs.get_pointing_icrs(time).transform_to(average_alt_az_frame)
                    exclusion_region_camera_frame = self._transform_exclusion_region_to_camera_frame(
                        average_alt_az_pointing)
                    geom_image = geom.to_image()

                    exclusion_mask_t = ~geom_image.region_mask(exclusion_region_camera_frame) if len(
                        exclusion_region_camera_frame) > 0 else ~Map.from_geom(geom_image)
                    # Add the exclusion mask in camera frame weighted by the time interval duration
                    exclusion_mask += exclusion_mask_t * (dtime).value
                # Normalise the exclusion mask by the full observation duration
                exclusion_mask *= 1 / (time_interval[-1] - time_interval[0]).value

                # Correct the exposure map by the exclusion region
                for j in range(exp_map_obs.counts.data.shape[0]):
                    exp_map_obs.counts.data[j, :, :] = exp_map_obs.counts.data[j, :, :] * exclusion_mask

                # Stack counts and exposure maps and livetime of all observations
                count_background += count_obs
                exp_map_background.data += exp_map_obs.counts.data
                exp_map_background_total.data += exp_map_obs_total.counts.data
                livetime += obs.observation_live_time_duration

        return count_background, exp_map_background, exp_map_background_total, livetime, energy_axis_computation
