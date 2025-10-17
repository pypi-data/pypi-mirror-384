from __future__ import annotations

from datetime import datetime

import numpy as np
import polars as pl
import pyopenms as oms

from tqdm import tqdm

from masster.study.defaults import (
    align_defaults,
    find_ms2_defaults,
    integrate_defaults,
)


def align(self, **kwargs):
    """Align feature maps using pose clustering or KD algorithm and update feature RTs.

    Parameters can be provided as an ``align_defaults`` instance or as
    individual keyword arguments; they are validated against the defaults class.

    Key parameters (from ``align_defaults``):
        - rt_tol (float): Maximum RT difference for pair finding (seconds).
        - mz_max_diff (float): Maximum m/z difference for pair finding (Da).
        - rt_pair_distance_frac (float): RT fraction used by the superimposer.
        - mz_pair_max_distance (float): Max m/z distance for pair selection.
        - num_used_points (int): Number of points to use for alignment estimation.
        - save_features (bool): If True, save updated features after alignment.
        - skip_blanks (bool): If True, skip blank samples during alignment.
        - algorithm (str): Alignment algorithm ('pc' for PoseClustering, 'kd' for KD).

        KD algorithm specific parameters:
        - warp_mz_tol (float): m/z tolerance for the LOWESS fit.
    """
    # parameters initialization
    params = align_defaults()

    # Handle 'params' keyword argument specifically (like merge does)
    if "params" in kwargs:
        provided_params = kwargs.pop("params")
        if isinstance(provided_params, align_defaults):
            params = provided_params
            self.logger.debug("Using provided align_defaults parameters from 'params' argument")
        else:
            self.logger.warning("'params' argument is not an align_defaults instance, ignoring")

    # Process remaining kwargs
    for key, value in kwargs.items():
        if isinstance(value, align_defaults):
            params = value
            self.logger.debug("Using provided align_defaults parameters")
        else:
            if hasattr(params, key):
                if params.set(key, value, validate=True):
                    self.logger.debug(f"Updated parameter {key} = {value}")
                else:
                    self.logger.warning(
                        f"Failed to set parameter {key} = {value} (validation failed)",
                    )
            else:
                self.logger.warning(f"Unknown parameter '{key}' ignored")

    # Store parameters in the Study object
    self.update_history(["align"], params.to_dict())
    self.logger.debug("Parameters stored to align")

    # Ensure rt_original exists before starting alignment (both algorithms need this)
    if "rt_original" not in self.features_df.columns:
        # add column 'rt_original' after 'rt'
        rt_index = self.features_df.columns.get_loc("rt") + 1
        self.features_df.insert(rt_index, "rt_original", 0)
        self.features_df["rt_original"] = self.features_df["rt"]
        self.logger.debug("Created rt_original column from current rt values")

    # Choose alignment algorithm
    algorithm = params.get("algorithm").lower()

    if algorithm == "pc":
        _align_pose_clustering(self, params)

    elif algorithm == "kd":
        _align_kd_algorithm(self, params)
    else:
        self.logger.error(f"Unknown alignment algorithm '{algorithm}'")
        return

    # Reset consensus data structures after alignment since RT changes invalidate consensus
    consensus_reset_count = 0
    if not self.consensus_df.is_empty():
        self.consensus_df = pl.DataFrame()
        consensus_reset_count += 1
    if not self.consensus_mapping_df.is_empty():
        self.consensus_mapping_df = pl.DataFrame()
        consensus_reset_count += 1
    if not self.consensus_ms2.is_empty():
        self.consensus_ms2 = pl.DataFrame()
        consensus_reset_count += 1
    if not self.id_df.is_empty():
        self.id_df = pl.DataFrame()
        consensus_reset_count += 1

    # Remove merge and find_ms2 parameters from history since they need to be re-run
    keys_to_remove = ["merge", "find_ms2"]
    history_removed_count = 0
    if hasattr(self, "history") and self.history:
        for key in keys_to_remove:
            if key in self.history:
                del self.history[key]
                history_removed_count += 1
                self.logger.debug(f"Removed {key} from history")

    if consensus_reset_count > 0 or history_removed_count > 0:
        self.logger.debug(
            f"Alignment reset: {consensus_reset_count} consensus structures cleared, {history_removed_count} history entries removed",
        )

    if params.get("save_features"):
        self.save_samples()


def find_ms2(self, **kwargs):
    """
    Links MS2 spectra to consensus features and stores the result in self.consensus_ms2.

    Parameters:
        **kwargs: Keyword arguments for MS2 linking parameters. Can include:
            - A find_ms2_defaults instance to set all parameters at once
            - Individual parameter names and values (see find_ms2_defaults for details)
    """
    # Reset consensus_ms2 DataFrame at the start
    self.consensus_ms2 = pl.DataFrame()

    # parameters initialization
    params = find_ms2_defaults()
    for key, value in kwargs.items():
        if isinstance(value, find_ms2_defaults):
            params = value
            self.logger.debug("Using provided find_ms2_defaults parameters")
        else:
            if hasattr(params, key):
                if params.set(key, value, validate=True):
                    self.logger.debug(f"Updated parameter {key} = {value}")
                else:
                    self.logger.warning(
                        f"Failed to set parameter {key} = {value} (validation failed)",
                    )
            else:
                self.logger.debug(f"Unknown parameter {key} ignored")
    # end of parameter initialization

    # Store parameters in the Study object
    self.update_history(["find_ms2"], params.to_dict())
    self.logger.debug("Parameters stored to find_ms2")

    data = []
    if self.consensus_mapping_df.is_empty():
        self.logger.error(
            "No consensus mapping found. Please run merge() first.",
        )
        return
    self.logger.info("Linking MS2 spectra to consensus features...")

    # Build fast lookup for feature_uid to features_df row data
    feats = self.features_df
    feature_lookup = {}
    relevant_cols = [
        "ms2_specs",
        "ms2_scans",
        "inty",
        "chrom_coherence",
        "chrom_prominence_scaled",
    ]
    for row in feats.iter_rows(named=True):
        feature_uid = row["feature_uid"]
        feature_lookup[feature_uid] = {col: row[col] for col in relevant_cols if col in feats.columns}
    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    # Process consensus mapping in batch
    for mapping_row in tqdm(
        self.consensus_mapping_df.iter_rows(named=True),
        total=self.consensus_mapping_df.shape[0],
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}MS2 spectra",
        disable=tdqm_disable,
    ):
        feature_uid = mapping_row["feature_uid"]
        feature_data = feature_lookup.get(feature_uid)
        if feature_data is None or feature_data.get("ms2_specs") is None:
            continue
        ms2_specs = feature_data["ms2_specs"]
        ms2_scans = feature_data["ms2_scans"]
        inty = feature_data.get("inty")
        chrom_coherence = feature_data.get("chrom_coherence")
        chrom_prominence_scaled = feature_data.get("chrom_prominence_scaled")
        for j in range(len(ms2_specs)):
            spec = ms2_specs[j]
            scanid = ms2_scans[j]
            data.append(
                {
                    "consensus_uid": int(mapping_row["consensus_uid"]),
                    "feature_uid": int(mapping_row["feature_uid"]),
                    "sample_uid": int(mapping_row["sample_uid"]),
                    "scan_id": int(scanid),
                    "energy": round(spec.energy, 1) if hasattr(spec, "energy") and spec.energy is not None else None,
                    "prec_inty": round(inty, 0) if inty is not None else None,
                    "prec_coherence": round(chrom_coherence, 3) if chrom_coherence is not None else None,
                    "prec_prominence_scaled": round(chrom_prominence_scaled, 3)
                    if chrom_prominence_scaled is not None
                    else None,
                    "number_frags": len(spec.mz),
                    "spec": spec,
                },
            )
    self.consensus_ms2 = pl.DataFrame(data)
    if not self.consensus_ms2.is_empty():
        unique_consensus_features = self.consensus_ms2["consensus_uid"].n_unique()
    else:
        unique_consensus_features = 0
    self.logger.success(
        f"Linking completed. Found {len(self.consensus_ms2)} MS2 spectra associated to {unique_consensus_features} consensus features.",
    )


## TODO these are not modelled the same way as other ranges, harmonize for tuples
def filter_consensus(
    self,
    inplace=True,
    number_samples=None,
    quality=None,
    coherence=None,
):
    if self.consensus_df is None:
        self.logger.error("No consensus found.")
        return
    cons = self.consensus_df if inplace else self.consensus_df.copy()
    total_initial = len(cons)
    self.logger.info(f"Filtering consensus features with {total_initial} entries...")
    after_coherence = total_initial
    after_quality = total_initial
    if coherence is not None:
        if "chrom_coherence" not in cons.columns:
            self.logger.warning("No coherence data found in features.")
        else:
            if isinstance(coherence, tuple) and len(coherence) == 2:
                min_coherence, max_coherence = coherence
                cons = cons[(cons["chrom_coherence"] >= min_coherence) & (cons["chrom_coherence"] <= max_coherence)]
            else:
                cons = cons[cons["chrom_coherence"] >= coherence]
        after_coherence = len(cons)
        self.logger.info(
            f"Filtered {total_initial - after_coherence} entries based on coherence. Remaining {after_coherence} entries.",
        )

    if quality is not None:
        if isinstance(quality, tuple) and len(quality) == 2:
            min_quality, max_quality = quality
            cons = cons[(cons["quality"] >= min_quality) & (cons["quality"] <= max_quality)]
        else:
            cons = cons[cons["quality"] >= quality]
        after_quality = len(cons)
        self.logger.info(
            f"Filtered {after_coherence - after_quality} entries based on quality. Remaining {after_quality} entries.",
        )

    if number_samples is not None:
        if isinstance(number_samples, tuple) and len(number_samples) == 2:
            min_number, max_number = number_samples
            cons = cons[(cons["number_samples"] >= min_number) & (cons["number_samples"] <= max_number)]
        else:
            cons = cons[cons["number_samples"] >= number_samples]
        after_number_samples = len(cons)
        self.logger.info(
            f"Filtered {after_quality - after_number_samples} entries based on number of samples. Remaining {after_number_samples} entries.",
        )

    self.logger.success(f"Filtering completed. {len(cons)} entries remaining.")

    if inplace:
        self.consensus_df = cons
    else:
        return cons


## TODO is uid supposed to be a list? rt_tol 0?
def _integrate_chrom_impl(self, **kwargs):
    """Integrate chromatogram intensities for consensus features.

    Integrates EICs for consensus features using parameters defined in
    :class:`integrate_defaults`. Pass an ``integrate_defaults`` instance via
    ``**kwargs`` or override individual parameters (they will be validated
    against the defaults class).

    Main parameters (from ``integrate_defaults``):

    - uids (Optional[list]): List of consensus UIDs to integrate; ``None`` means all.
    - rt_tol (float): RT tolerance (seconds) used when locating integration boundaries.

    Notes:
        This function batches updates to the study's feature table for efficiency.
    """
    # parameters initialization
    params = integrate_defaults()
    for key, value in kwargs.items():
        if isinstance(value, integrate_defaults):
            params = value
            self.logger.debug("Using provided integrate_chrom_defaults parameters")
        else:
            if hasattr(params, key):
                if params.set(key, value, validate=True):
                    self.logger.debug(f"Updated parameter {key} = {value}")
                else:
                    self.logger.warning(
                        f"Failed to set parameter {key} = {value} (validation failed)",
                    )
            else:
                self.logger.debug(f"Unknown parameter {key} ignored")
    # end of parameter initialization

    # Store parameters in the Study object
    self.update_history(["integrate_chrom"], params.to_dict())
    self.logger.debug("Parameters stored to integrate_chrom")

    # Get parameter values for use in the method
    uids = params.get("uids")
    rt_tol = params.get("rt_tol")

    if uids is None:
        # get all consensus_id from consensus_df
        ids = self.consensus_df["consensus_uid"].to_list()
    else:
        # keep only id that are in consensus_df
        ids = [i for i in uids if i in self.consensus_df["consensus_uid"].to_list()]

    # Ensure chrom_area column is Float64 to avoid dtype conflicts
    if "chrom_area" in self.features_df.columns:
        self.features_df = self.features_df.with_columns(
            pl.col("chrom_area").cast(pl.Float64, strict=False),
        )

    # Merge consensus_mapping with consensus_df to get rt_start_mean and rt_end_mean
    # Use Polars join operation instead of pandas merge
    consensus_subset = self.consensus_df.select(
        [
            "consensus_uid",
            "rt_start_mean",
            "rt_end_mean",
        ],
    )
    df1 = self.consensus_mapping_df.join(
        consensus_subset,
        on="consensus_uid",
        how="left",
    )
    df1 = df1.filter(pl.col("consensus_uid").is_in(ids))

    # Build a fast lookup for feature_uid to row index in features_df
    # Since Polars doesn't have index-based access like pandas, we'll use row position
    feature_uid_to_row = {}
    for i, row_dict in enumerate(self.features_df.iter_rows(named=True)):
        if "feature_uid" in row_dict:
            feature_uid_to_row[row_dict["feature_uid"]] = i
        elif "uid" in row_dict:  # fallback column name
            feature_uid_to_row[row_dict["uid"]] = i

    # Prepare lists for batch update
    update_rows = []
    chroms: list = []
    rt_starts: list[float] = []
    rt_ends: list[float] = []
    rt_deltas: list[float] = []
    chrom_areas = []

    self.logger.debug(f"Integrating {df1.shape[0]} features using consensus...")
    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]
    for row in tqdm(
        df1.iter_rows(named=True),
        total=df1.shape[0],
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}Integrate EICs by consensus",
        disable=tdqm_disable,
    ):
        feature_uid = row["feature_uid"]
        row_idx = feature_uid_to_row.get(feature_uid)
        if row_idx is None:
            continue

        # Get the feature row from Polars DataFrame
        feature_row = self.features_df.row(row_idx, named=True)
        # get chromatogram for the feature
        chrom = feature_row["chrom"]
        if chrom is None or len(chrom) == 0:
            update_rows.append(row_idx)
            chroms.append(None)
            rt_starts.append(float("nan"))
            rt_ends.append(float("nan"))
            rt_deltas.append(float("nan"))
            chrom_areas.append(-1.0)
            continue
        ## TODO expose parameters
        rt_start = _find_closest_valley(
            chrom,
            row["rt_start_mean"] - rt_tol,
            dir="left",
            threshold=0.9,
        )
        rt_end = _find_closest_valley(
            chrom,
            row["rt_end_mean"] + rt_tol,
            dir="right",
            threshold=0.9,
        )
        chrom.feature_start = rt_start
        chrom.feature_end = rt_end
        chrom.integrate()
        update_rows.append(row_idx)
        chroms.append(chrom)
        rt_starts.append(rt_start)
        rt_ends.append(rt_end)
        rt_deltas.append(rt_end - rt_start)
        chrom_areas.append(float(chrom.feature_area))

    # Batch update DataFrame - Polars style
    if update_rows:
        # Create mapping from row index to new values
        row_to_chrom = {update_rows[i]: chroms[i] for i in range(len(update_rows))}
        row_to_rt_start = {update_rows[i]: rt_starts[i] for i in range(len(update_rows))}
        row_to_rt_end = {update_rows[i]: rt_ends[i] for i in range(len(update_rows))}
        row_to_rt_delta = {update_rows[i]: rt_deltas[i] for i in range(len(update_rows))}
        row_to_chrom_area = {
            update_rows[i]: float(chrom_areas[i]) if chrom_areas[i] is not None else 0.0
            for i in range(len(update_rows))
        }

        # Use with_row_index to create a temporary row index column
        df_with_index = self.features_df.with_row_index("__row_idx")

        # Create update masks and values
        update_mask = pl.col("__row_idx").is_in(update_rows)

        # Update columns conditionally
        try:
            self.features_df = df_with_index.with_columns(
                [
                    # Update chrom column - use when() to update only specific rows
                    pl.when(update_mask)
                    .then(
                        pl.col("__row_idx").map_elements(
                            lambda x: row_to_chrom.get(x, None),
                            return_dtype=pl.Object,
                        ),
                    )
                    .otherwise(pl.col("chrom"))
                    .alias("chrom"),
                    # Update rt_start column
                    pl.when(update_mask)
                    .then(
                        pl.col("__row_idx").map_elements(
                            lambda x: row_to_rt_start.get(x, None),
                            return_dtype=pl.Float64,
                        ),
                    )
                    .otherwise(pl.col("rt_start"))
                    .alias("rt_start"),
                    # Update rt_end column
                    pl.when(update_mask)
                    .then(
                        pl.col("__row_idx").map_elements(
                            lambda x: row_to_rt_end.get(x, None),
                            return_dtype=pl.Float64,
                        ),
                    )
                    .otherwise(pl.col("rt_end"))
                    .alias("rt_end"),
                    # Update rt_delta column
                    pl.when(update_mask)
                    .then(
                        pl.col("__row_idx").map_elements(
                            lambda x: row_to_rt_delta.get(x, None),
                            return_dtype=pl.Float64,
                        ),
                    )
                    .otherwise(pl.col("rt_delta"))
                    .alias("rt_delta"),
                    # Update chrom_area column
                    pl.when(update_mask)
                    .then(
                        pl.col("__row_idx").map_elements(
                            lambda x: row_to_chrom_area.get(x, 0),
                            return_dtype=pl.Float64,
                        ),
                    )
                    .otherwise(pl.col("chrom_area"))
                    .alias("chrom_area"),
                ],
            ).drop("__row_idx")  # Remove the temporary row index column

            self.logger.success(
                f"Integration completed. Updated {len(update_rows)} features with chromatogram data.",
            )
        except Exception as e:
            self.logger.error(f"Failed to update features DataFrame: {e}")
    else:
        self.logger.debug("No features were updated during integration.")


def integrate(self, **kwargs):
    """Integrate chromatograms across consensus features.

    Wrapper that extracts parameters from :class:`integrate_defaults` and
    calls the underlying implementation. See ``integrate_defaults`` for
    the canonical parameter list and descriptions.
    """
    # parameters initialization
    params = integrate_defaults()
    for key, value in kwargs.items():
        if isinstance(value, integrate_defaults):
            params = value
            self.logger.debug("Using provided integrate_defaults parameters")
        else:
            if hasattr(params, key):
                if params.set(key, value, validate=True):
                    self.logger.debug(f"Updated parameter {key} = {value}")
                else:
                    self.logger.warning(
                        f"Failed to set parameter {key} = {value} (validation failed)",
                    )
            else:
                self.logger.debug(f"Unknown parameter {key} ignored")
    # end of parameter initialization

    # Store parameters in the Study object
    self.update_history(["integrate"], params.to_dict())
    self.logger.debug("Parameters stored to integrate")

    # Call the original integrate_chrom function with extracted parameters
    return _integrate_chrom_impl(
        self,
        uids=params.get("uids"),
        rt_tol=params.get("rt_tol"),
    )


# Backward compatibility alias
integrate_chrom = integrate


def _find_closest_valley(chrom, rt, dir="left", threshold=0.9):
    # find closest index to rt in chrom['rt']
    chrom.rt = chrom.rt.astype(np.float64)
    chrom.inty = chrom.inty.astype(np.float64)
    idx = np.abs(chrom.rt - rt).argmin()
    # ensure rt and inty are float64
    if dir == "left":
        inty = np.inf
        # iterate left from idx to the end od the peaks until we find a valley
        for i in range(idx, 0, -1):
            if chrom.inty[i] < inty * threshold:
                idx = i
                inty = chrom.inty[i]
            else:
                break
    if dir == "right":
        inty = np.inf
        # iterate right from idx to the end od the peaks until we find a valley
        for i in range(idx, len(chrom.inty)):
            if chrom.inty[i] < inty * threshold:
                idx = i
                inty = chrom.inty[i]
            else:
                break
    return chrom.rt[idx]


def _align_pose_clustering(study_obj, params):
    """Perform alignment using PoseClustering algorithm."""
    import pyopenms as oms
    import polars as pl
    from tqdm import tqdm
    from datetime import datetime

    # Generate temporary feature maps on-demand from features_df for PoseClustering
    study_obj.logger.debug("Generating feature maps on-demand from features_df for PoseClustering alignment")

    tdqm_disable = study_obj.log_level not in ["TRACE", "DEBUG", "INFO"]
    fmaps = []

    # Process each sample in order with progress bar
    for sample_index, row_dict in tqdm(
        list(enumerate(study_obj.samples_df.iter_rows(named=True))),
        total=len(study_obj.samples_df),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study_obj.log_label}Generate feature maps",
        disable=tdqm_disable,
    ):
        sample_uid = row_dict["sample_uid"]
        sample_name = row_dict["sample_name"]

        # Get features for this sample from features_df
        sample_features = study_obj.features_df.filter(pl.col("sample_uid") == sample_uid)

        # Create new FeatureMap
        feature_map = oms.FeatureMap()

        # Convert DataFrame features to OpenMS Features
        for feature_row in sample_features.iter_rows(named=True):
            feature = oms.Feature()

            # Set properties from DataFrame (handle missing values gracefully)
            try:
                # Skip features with missing critical data
                if feature_row["mz"] is None:
                    study_obj.logger.warning("Skipping feature due to missing mz")
                    continue
                if feature_row["rt"] is None:
                    study_obj.logger.warning("Skipping feature due to missing rt")
                    continue
                if feature_row["inty"] is None:
                    study_obj.logger.warning("Skipping feature due to missing inty")
                    continue

                feature.setUniqueId(int(feature_row["feature_id"]))
                feature.setMZ(float(feature_row["mz"]))
                feature.setRT(float(feature_row["rt"]))
                feature.setIntensity(float(feature_row["inty"]))

                # Handle optional fields that might be None
                if feature_row.get("quality") is not None:
                    feature.setOverallQuality(float(feature_row["quality"]))
                if feature_row.get("charge") is not None:
                    feature.setCharge(int(feature_row["charge"]))

                # Add to feature map
                feature_map.push_back(feature)
            except (ValueError, TypeError) as e:
                study_obj.logger.warning(f"Skipping feature due to conversion error: {e}")
                continue

        fmaps.append(feature_map)

    study_obj.logger.debug(f"Generated {len(fmaps)} feature maps from features_df for PoseClustering alignment")

    # Create PC-specific OpenMS parameters
    params_oms = oms.Param()
    params_oms.setValue("pairfinder:distance_intensity:log_transform", "disabled")
    params_oms.setValue("pairfinder:ignore_charge", "true")
    params_oms.setValue("max_num_peaks_considered", 1000)
    params_oms.setValue("pairfinder:distance_RT:max_difference", params.get("rt_tol"))
    params_oms.setValue(
        "pairfinder:distance_MZ:max_difference",
        params.get("mz_max_diff"),
    )
    params_oms.setValue(
        "superimposer:rt_pair_distance_fraction",
        params.get("rt_pair_distance_frac"),
    )
    params_oms.setValue(
        "superimposer:mz_pair_max_distance",
        params.get("mz_pair_max_distance"),
    )
    params_oms.setValue("superimposer:num_used_points", params.get("num_used_points"))
    params_oms.setValue("pairfinder:distance_MZ:exponent", 3.0)
    params_oms.setValue("pairfinder:distance_RT:exponent", 2.0)

    aligner = oms.MapAlignmentAlgorithmPoseClustering()
    study_obj.logger.info(
        f"Align RTs with Pose clustering: rt_tol={params.get('rt_tol')}",
    )

    # Set ref_index to feature map index with largest number of features
    ref_index = [i[0] for i in sorted(enumerate([fm.size() for fm in fmaps]), key=lambda x: x[1])][-1]

    aligner.setParameters(params_oms)
    aligner.setReference(fmaps[ref_index])
    study_obj.logger.debug(f"Parameters for alignment: {params}")

    # Perform alignment and transformation of feature maps to the reference map (exclude reference map)
    for index, fm in tqdm(
        list(enumerate(fmaps)),
        total=len(fmaps),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study_obj.log_label}Align feature maps",
        disable=tdqm_disable,
    ):
        if index == ref_index:
            continue
        if params.get("skip_blanks") and study_obj.samples_df.row(index, named=True)["sample_type"] == "blank":
            continue

        # Skip feature maps with insufficient data points for alignment
        if fm.size() < 2:
            sample_name = study_obj.samples_df.row(index, named=True)["sample_name"]
            study_obj.logger.warning(
                f"Skipping alignment for sample '{sample_name}' - insufficient features ({fm.size()} features)"
            )
            continue

        try:
            trafo = oms.TransformationDescription()
            aligner.align(fm, trafo)
            transformer = oms.MapAlignmentTransformer()
            transformer.transformRetentionTimes(fm, trafo, True)
        except RuntimeError as e:
            sample_name = study_obj.samples_df.row(index, named=True)["sample_name"]
            study_obj.logger.warning(f"Failed to align sample '{sample_name}': {e}")
            continue

    study_obj.alignment_ref_index = ref_index

    # Process feature maps and update features_df with transformed retention times
    # Build a fast lookup for (sample_uid, featureUid) to index in features_df
    feats = study_obj.features_df

    # Pre-build sample_uid lookup for faster access
    study_obj.logger.debug("Build sample_uid lookup for fast access...")
    sample_uid_lookup = {
        idx: row_dict["sample_uid"] for idx, row_dict in enumerate(study_obj.samples_df.iter_rows(named=True))
    }

    # Build the main lookup using feature_uid (not feature_id)
    if "feature_id" in feats.columns:
        # Create lookup mapping (sample_uid, feature_id) to DataFrame index using Polars
        # Since we need a pandas-style index lookup, we'll create a simple dict
        sample_uids = feats.get_column("sample_uid").to_list()

        # Handle feature_id column - it might be Object type due to conversion
        feature_id_col = feats.get_column("feature_id")
        if feature_id_col.dtype == pl.Object:
            # If it's Object type, convert to list and let Python handle the conversion
            feature_ids = feature_id_col.to_list()
            # Convert to strings if they're not already
            feature_ids = [str(fid) if fid is not None else None for fid in feature_ids]
        else:
            # Safe to cast normally
            feature_ids = feature_id_col.cast(pl.Utf8).to_list()

        lookup = {
            (sample_uid, feature_id): idx
            for idx, (sample_uid, feature_id) in enumerate(
                zip(sample_uids, feature_ids, strict=True),
            )
        }
    else:
        # fallback: skip if feature_uid column missing
        lookup = {}
        study_obj.logger.warning("feature_id column not found in features_df")

    # Pre-allocate update lists for better performance
    all_update_idx = []
    all_update_rt = []
    all_update_rt_original = []

    for index, fm in tqdm(
        list(enumerate(fmaps)),
        total=len(fmaps),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study_obj.log_label}Extract RTs",
        disable=tdqm_disable,
    ):
        sample_uid = sample_uid_lookup.get(index)
        if sample_uid is None:
            continue

        # Collect all updates for this feature map
        for f in fm:
            feature_uid = str(f.getUniqueId())
            idx = lookup.get((sample_uid, feature_uid))
            if idx is not None:
                rt = round(f.getRT(), 3)
                # rt_or = round(f.getMetaValue("original_RT"), 3) if f.metaValueExists("original_RT") else rt
                all_update_idx.append(idx)
                all_update_rt.append(rt)
                # all_update_rt_original.append(rt_or)

    # Single batch update for all features at once
    if all_update_idx:
        # Build a full-length Python list of rt values, update specified indices,
        # then replace the DataFrame column with a Series that has the same length
        try:
            current_rt = study_obj.features_df["rt"].to_list()
        except Exception:
            current_rt = [None] * study_obj.features_df.height

        # Defensive: ensure list length equals dataframe height
        if len(current_rt) != study_obj.features_df.height:
            current_rt = [None] * study_obj.features_df.height

        for idx, new_rt in zip(all_update_idx, all_update_rt):
            current_rt[idx] = new_rt

        new_cols = [pl.Series("rt", current_rt)]

        # Update rt_original if corresponding updates were collected
        if "all_update_rt_original" in locals() and all_update_rt_original:
            try:
                current_rt_orig = (
                    study_obj.features_df["rt_original"].to_list()
                    if "rt_original" in study_obj.features_df.columns
                    else [None] * study_obj.features_df.height
                )
            except Exception:
                current_rt_orig = [None] * study_obj.features_df.height

            if len(current_rt_orig) != study_obj.features_df.height:
                current_rt_orig = [None] * study_obj.features_df.height

            for idx, new_orig in zip(all_update_idx, all_update_rt_original):
                current_rt_orig[idx] = new_orig

            new_cols.append(pl.Series("rt_original", current_rt_orig))

        # Replace columns in one call
        study_obj.features_df = study_obj.features_df.with_columns(*new_cols)

    # Clean up temporary feature maps to release memory
    del fmaps
    study_obj.logger.debug("Temporary feature maps deleted to release memory")

    # Resolve reference sample UID from the reference index
    ref_sample_uid = sample_uid_lookup.get(ref_index)
    study_obj.logger.success(
        f"Alignment completed. Reference sample UID {ref_sample_uid}.",
    )


def _align_kd_algorithm(study_obj, params):
    """
    Custom KD-tree / reference-based alignment working directly with features_df.
    """
    import bisect
    import statistics
    import pyopenms as oms
    import polars as pl
    from datetime import datetime

    # Pull parameter values - map standard align params to our algorithm
    # Use rt_tol (standard align param) instead of warp_rt_tol for RT tolerance
    rt_pair_tol = float(params.get("rt_tol")) if params.get("rt_tol") is not None else 2.0
    # Use mz_max_diff (standard align param) converted to ppm
    mz_max_diff_da = float(params.get("mz_max_diff")) if params.get("mz_max_diff") is not None else 0.02
    # Convert Da to ppm (assuming ~400 m/z average for metabolomics): 0.01 Da / 400 * 1e6 = 25 ppm
    ppm_tol = mz_max_diff_da / 400.0 * 1e6
    # Allow override with warp_mz_tol if specifically set (but not from defaults)
    try:
        warp_mz_from_params = params.get("warp_mz_tol")
        if warp_mz_from_params is not None and warp_mz_from_params != params.__class__().warp_mz_tol:
            ppm_tol = float(warp_mz_from_params)
    except (KeyError, AttributeError):
        pass

    # Safely retrieve optional parameter max_anchor_points (not yet part of defaults)
    try:
        _raw_mp = params.get("max_anchor_points")
    except KeyError:
        _raw_mp = None
    max_points = int(_raw_mp) if _raw_mp is not None else 1000
    study_obj.logger.info(
        f"Align RTs with KD-Tree: rt_tol={params.get('rt_tol')}, max_points={max_points}",
    )

    # Work directly with features_df instead of feature maps
    if study_obj.features_df is None or study_obj.features_df.is_empty():
        study_obj.logger.error("No features_df available for alignment. Cannot proceed with KD alignment.")
        raise ValueError(
            "No features_df available for alignment. This usually indicates that features were not detected properly."
        )

    # OPTIMIZATION 1: Group all features by sample_uid in ONE operation instead of filtering repeatedly
    study_obj.logger.debug("Grouping features efficiently (major speedup)...")

    # rt_original should already exist (created in main align() function)
    if "rt_original" not in study_obj.features_df.columns:
        raise ValueError("rt_original column missing - this should have been created by align() function")

    sample_groups = study_obj.features_df.group_by("sample_uid", maintain_order=True)
    sample_feature_data = sample_groups.agg([
        pl.len().alias("feature_count"),
        pl.col("mz").alias("mzs"),
        pl.col("rt_original").alias("rt_originals"),  # Use original RT values for alignment
    ]).sort("feature_count", descending=True)

    if sample_feature_data.is_empty():
        study_obj.logger.error("No features found in any sample for alignment.")
        raise ValueError("No features found in any sample for alignment.")

    # Choose reference sample (sample with most features)
    ref_sample_uid = sample_feature_data.row(0, named=True)["sample_uid"]

    # Find the index of this sample in samples_df
    ref_index = None
    sample_uid_to_index = {}
    for idx, row_dict in enumerate(study_obj.samples_df.iter_rows(named=True)):
        sample_uid = row_dict["sample_uid"]
        sample_uid_to_index[sample_uid] = idx
        if sample_uid == ref_sample_uid:
            ref_index = idx

    if ref_index is None:
        study_obj.logger.error(f"Could not find reference sample {ref_sample_uid} in samples_df")
        raise ValueError(f"Could not find reference sample {ref_sample_uid} in samples_df")

    study_obj.alignment_ref_index = ref_index

    # OPTIMIZATION 2: Get reference features efficiently from pre-grouped data
    # Always use rt_original for alignment input to ensure consistent results
    ref_row = sample_feature_data.filter(pl.col("sample_uid") == ref_sample_uid).row(0, named=True)
    ref_mzs_list = ref_row["mzs"]
    ref_rts_list = ref_row["rt_originals"]  # Use original RT values

    # Create sorted reference features for binary search
    ref_features = list(zip(ref_mzs_list, ref_rts_list))
    ref_features.sort(key=lambda x: x[0])
    ref_mzs = [mz for mz, _ in ref_features]

    study_obj.logger.debug(
        f"Reference sample UID {ref_sample_uid} (index {ref_index}, sample: {study_obj.samples_df.row(ref_index, named=True)['sample_name']}) has {len(ref_features)} features",
    )

    def find_best_match(mz: float, rt: float):
        mz_tol_abs = mz * ppm_tol * 1e-6
        left = bisect.bisect_left(ref_mzs, mz - mz_tol_abs)
        right = bisect.bisect_right(ref_mzs, mz + mz_tol_abs)
        best = None
        best_drt = None
        for idx in range(left, right):
            ref_mz, ref_rt = ref_features[idx]
            drt = abs(ref_rt - rt)
            ppm_err = abs(ref_mz - mz) / ref_mz * 1e6 if ref_mz else 1e9
            if ppm_err <= ppm_tol:
                if best_drt is None or drt < best_drt:
                    best = (rt, ref_rt)
                    best_drt = drt
        return best

    def _set_pairs(
        td_obj: oms.TransformationDescription,
        pairs,
    ):  # Helper for pyopenms API variability
        # Always provide list of lists to satisfy strict type expectations
        conv = [[float(a), float(b)] for a, b in pairs]
        try:
            td_obj.setDataPoints(conv)
        except Exception:
            # Fallback: attempt tuple form (older bindings) if list of lists fails
            try:
                td_obj.setDataPoints([tuple(p) for p in conv])  # type: ignore[arg-type]
            except Exception:
                pass

    # OPTIMIZATION 3: Process samples using pre-grouped data (eliminates expensive filtering)
    transformations = {}

    for row in sample_feature_data.iter_rows(named=True):
        sample_uid = row["sample_uid"]
        sample_mzs = row["mzs"]
        sample_rts = row["rt_originals"]  # Use original RT values for alignment input

        td = oms.TransformationDescription()
        sample_index = sample_uid_to_index.get(sample_uid)

        if sample_index is None:
            study_obj.logger.warning(f"Sample UID {sample_uid} not found in samples_df, skipping")
            continue

        # Skip empty samples
        if not sample_mzs or not sample_rts:
            transformations[sample_uid] = td
            continue

        # Identity for reference sample
        if sample_uid == ref_sample_uid:
            rts = [rt for rt in sample_rts if rt is not None]
            lo, hi = (min(rts), max(rts)) if rts else (0.0, 0.0)
            try:
                _set_pairs(td, [(lo, lo), (hi, hi)])
                td.fitModel("linear", oms.Param())
            except Exception:
                pass
            transformations[sample_uid] = td
            continue

        # OPTIMIZATION 4: Process pairs using pre-loaded data arrays (no DataFrame operations)
        pairs_raw = []
        for mz, rt in zip(sample_mzs, sample_rts):
            if mz is not None and rt is not None:
                match = find_best_match(mz, rt)
                if match:
                    obs_rt, ref_rt = match
                    if abs(obs_rt - ref_rt) <= rt_pair_tol:
                        pairs_raw.append((obs_rt, ref_rt))

        if not pairs_raw:
            # Fallback identity
            rts = [rt for rt in sample_rts if rt is not None]
            lo, hi = (min(rts), max(rts)) if rts else (0.0, 0.0)
            try:
                _set_pairs(td, [(lo, lo), (hi, hi)])
                td.fitModel("linear", oms.Param())
            except Exception:
                pass
            transformations[sample_uid] = td
            study_obj.logger.debug(f"Sample {sample_uid}: no anchors -> identity transform")
            continue

        # Deduplicate and downsample
        seen_obs = set()
        pairs_unique = []
        for obs_rt, ref_rt in sorted(pairs_raw):
            key = round(obs_rt, 6)
            if key in seen_obs:
                continue
            seen_obs.add(key)
            pairs_unique.append((obs_rt, ref_rt))

        if len(pairs_unique) > max_points:
            stride = len(pairs_unique) / max_points
            sampled = []
            idx = 0.0
            while int(idx) < len(pairs_unique) and len(sampled) < max_points:
                sampled.append(pairs_unique[int(idx)])
                idx += stride
            pairs_use = sampled
        else:
            pairs_use = pairs_unique

        shifts = [ref - obs for (obs, ref) in pairs_use]
        med_shift = statistics.median(shifts) if shifts else 0.0
        model = "lowess" if len(pairs_use) >= 20 else "linear"
        try:
            _set_pairs(td, pairs_use)
            td.fitModel(model, oms.Param())
        except Exception as e:
            study_obj.logger.debug(
                f"Sample {sample_uid}: {model} fitting failed ({e}); fallback to linear two-point shift",
            )
            rts = [rt for rt in sample_rts if rt is not None]
            lo, hi = (min(rts), max(rts)) if rts else (0.0, 1.0)
            td = oms.TransformationDescription()
            try:
                _set_pairs(td, [(lo, lo + med_shift), (hi, hi + med_shift)])
                td.fitModel("linear", oms.Param())
            except Exception:
                pass

        study_obj.logger.debug(
            f"Sample {sample_uid}: anchors raw={len(pairs_raw)} used={len(pairs_use)} model={model} median_shift={med_shift:.4f}s",
        )
        transformations[sample_uid] = td

    # OPTIMIZATION 5: Apply transformations efficiently using vectorized operations
    study_obj.logger.debug("Applying RT transformations efficiently...")

    # Apply transformations to RT values starting from rt_original
    def transform_rt_vectorized(sample_uid: int, rt_original: float) -> float:
        if sample_uid in transformations and rt_original is not None:
            try:
                trafo = transformations[sample_uid]
                return trafo.apply(float(rt_original))
            except Exception:
                return rt_original
        return rt_original

    # Use Polars' efficient struct operations for vectorized transformation
    # Apply transformation to rt_original and store result in rt column
    study_obj.features_df = study_obj.features_df.with_columns(
        pl.struct(["sample_uid", "rt_original"])
        .map_elements(lambda x: transform_rt_vectorized(x["sample_uid"], x["rt_original"]), return_dtype=pl.Float64)
        .alias("rt")
    )

    study_obj.logger.success(
        f"Alignment completed. Reference sample UID {ref_sample_uid}.",
    )


def _align_pose_clustering_fallback(study_obj, fmaps, params):
    """Fallback PoseClustering alignment with minimal parameters."""
    import pyopenms as oms

    aligner = oms.MapAlignmentAlgorithmPoseClustering()
    ref_index = [i[0] for i in sorted(enumerate([fm.size() for fm in fmaps]), key=lambda x: x[1])][-1]

    # Set up basic parameters for pose clustering
    pc_params = oms.Param()
    pc_params.setValue("max_num_peaks_considered", 1000)
    pc_params.setValue("pairfinder:distance_RT:max_difference", params.get("rt_tol"))
    pc_params.setValue(
        "pairfinder:distance_MZ:max_difference",
        params.get("mz_max_diff"),
    )

    aligner.setParameters(pc_params)
    aligner.setReference(fmaps[ref_index])

    for index, fm in enumerate(fmaps):
        if index == ref_index:
            continue
        trafo = oms.TransformationDescription()
        aligner.align(fm, trafo)
        transformer = oms.MapAlignmentTransformer()
        transformer.transformRetentionTimes(fm, trafo, True)

    study_obj.alignment_ref_index = ref_index


def find_iso(self, rt_tol=0.1, mz_tol=0.01, uids=None):
    """
    Find isotope patterns for consensus features by searching raw MS1 data.
    OPTIMIZED VERSION: Each sample file is loaded only once for maximum efficiency.

    For each consensus feature:
    1. Find the associated feature with highest intensity
    2. Load the corresponding sample5 file to access raw MS1 data
    3. Use original_rt (before alignment) to find the correct scan
    4. Search for isotope patterns in raw MS1 spectra
    5. Look for isotope patterns: 0.33, 0.50, 0.66, 1.00, 1.50, 2.00, 3.00, 4.00, 5.00 Da
    6. Store results as numpy arrays with [mz, inty] in the iso column

    Parameters:
        rt_tol (float): RT tolerance for scan matching in seconds
        mz_tol (float): Additional m/z tolerance for isotope matching in Da
        uids (list, optional): List of consensus_uid values to process. If None, process all consensus features.
    """
    if self.consensus_df is None or self.consensus_df.is_empty():
        self.logger.error("No consensus features found. Please run merge() first.")
        return

    if self.consensus_mapping_df is None or self.consensus_mapping_df.is_empty():
        self.logger.error("No consensus mapping found. Please run merge() first.")
        return

    if self.features_df is None or self.features_df.is_empty():
        self.logger.error("No features found.")
        return

    if self.samples_df is None or self.samples_df.is_empty():
        self.logger.error("No samples found.")
        return

    # Add iso column if it doesn't exist
    if "iso" not in self.consensus_df.columns:
        self.consensus_df = self.consensus_df.with_columns(pl.lit(None, dtype=pl.Object).alias("iso"))

    self.logger.info("Extracting isotopomers from raw MS1 data...")

    # Filter consensus features if uids is specified
    if uids is not None:
        if not isinstance(uids, (list, tuple)):
            uids = [uids]
        # Filter consensus_df to only process specified UIDs
        consensus_df_filtered = self.consensus_df.filter(pl.col("consensus_uid").is_in(uids))
        if consensus_df_filtered.is_empty():
            self.logger.warning(f"No consensus features found with specified UIDs: {uids}")
            return
        self.logger.debug(f"Processing {len(consensus_df_filtered)} consensus features (UIDs: {uids})")
    else:
        consensus_df_filtered = self.consensus_df
        self.logger.debug(f"Processing all {len(consensus_df_filtered)} consensus features")

    # Isotope mass shifts to search for (up to 7x 13C isotopes)
    isotope_shifts = [
        0.33,
        0.50,
        0.66,
        1.00335,
        1.50502,
        2.00670,
        3.01005,
        4.01340,
        5.01675,
        6.02010,
        7.02345,
    ]

    consensus_iso_data = {}

    # SUPER OPTIMIZATION: Vectorized pre-calculation using joins (10-100x faster)
    self.logger.debug("Building sample-to-consensus mapping using vectorized operations...")

    # Step 1: Join consensus_mapping with features to get intensities in one operation
    # Apply UID filtering if specified
    if uids is not None:
        consensus_mapping_filtered = self.consensus_mapping_df.filter(pl.col("consensus_uid").is_in(uids))
    else:
        consensus_mapping_filtered = self.consensus_mapping_df

    consensus_with_features = consensus_mapping_filtered.join(
        self.features_df.select(["feature_uid", "sample_uid", "inty", "mz", "rt", "rt_original"]),
        on=["feature_uid", "sample_uid"],
        how="left",
    )

    # Step 2: Find the best feature (highest intensity) for each consensus using window functions
    best_features = (
        consensus_with_features.with_columns(
            pl.col("inty").fill_null(0)  # Handle null intensities
        )
        .with_columns(pl.col("inty").max().over("consensus_uid").alias("max_inty"))
        .filter(pl.col("inty") == pl.col("max_inty"))
        .group_by("consensus_uid")
        .first()
    )  # Take first if there are ties

    # Step 3: Join with samples to get sample paths in one operation
    best_features_with_paths = best_features.join(
        self.samples_df.select(["sample_uid", "sample_path"]), on="sample_uid", how="left"
    ).filter(pl.col("sample_path").is_not_null())

    # Step 4: Group by sample path for batch processing (much faster than nested loops)
    sample_to_consensus = {}
    for row in best_features_with_paths.iter_rows(named=True):
        sample_path = row["sample_path"]
        consensus_uid = row["consensus_uid"]

        # Create feature data dictionary for compatibility
        feature_data = {
            "mz": row["mz"],
            "rt": row["rt"],
            "rt_original": row.get("rt_original", row["rt"]),
            "inty": row["inty"],
        }

        if sample_path not in sample_to_consensus:
            sample_to_consensus[sample_path] = []

        sample_to_consensus[sample_path].append((consensus_uid, feature_data))

    # Initialize failed consensus features (those not in the mapping)
    processed_consensus_uids = set(best_features_with_paths["consensus_uid"].to_list())
    for consensus_row in consensus_df_filtered.iter_rows(named=True):
        consensus_uid = consensus_row["consensus_uid"]
        if consensus_uid not in processed_consensus_uids:
            consensus_iso_data[consensus_uid] = None

    self.logger.debug(
        f"Will read {len(sample_to_consensus)} unique sample files for {len(consensus_df_filtered)} consensus features"
    )

    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    # OPTIMIZATION 2: Process by sample file (load each file only once)
    for sample_path, consensus_list in tqdm(
        sample_to_consensus.items(),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}Process from files",
        disable=tdqm_disable,
    ):
        try:
            # Load MS1 data once per sample
            ms1_df = self._load_ms1(sample_path)

            if ms1_df is None or ms1_df.is_empty():
                # Mark all consensus features from this sample as failed
                for consensus_uid, _ in consensus_list:
                    consensus_iso_data[consensus_uid] = None
                continue

            # Process all consensus features for this sample
            for consensus_uid, best_feature in consensus_list:
                # Get the original RT (before alignment correction)
                base_mz = best_feature["mz"]
                original_rt = best_feature.get("rt_original", best_feature["rt"])

                # Skip if RT or mz is None or invalid
                if original_rt is None:
                    original_rt = best_feature["rt"]
                    self.logger.debug(f"original_rt is None. Using aligned rt instead")

                if base_mz is None:
                    self.logger.warning(f"Skipping consensus_uid {consensus_uid}: base_mz is None")
                    consensus_iso_data[consensus_uid] = None
                    continue

                # Find MS1 scans near the original RT
                rt_min = original_rt - rt_tol
                rt_max = original_rt + rt_tol

                # Filter MS1 data for scans within RT window
                ms1_window = ms1_df.filter((pl.col("rt") >= rt_min) & (pl.col("rt") <= rt_max))

                if ms1_window.is_empty():
                    consensus_iso_data[consensus_uid] = None
                    continue

                isotope_matches = []

                # Search for each isotope shift
                for shift in isotope_shifts:
                    target_mz = base_mz + shift
                    mz_min_iso = target_mz - mz_tol
                    mz_max_iso = target_mz + mz_tol

                    # Find peaks in MS1 data within m/z tolerance
                    isotope_peaks = ms1_window.filter((pl.col("mz") >= mz_min_iso) & (pl.col("mz") <= mz_max_iso))

                    if not isotope_peaks.is_empty():
                        # Get the peak with maximum intensity for this isotope
                        max_peak = isotope_peaks.filter(pl.col("inty") == pl.col("inty").max()).row(0, named=True)

                        # Store as float with specific precision: m/z to 4 decimals, intensity rounded to integer
                        mz_formatted = round(float(max_peak["mz"]), 4)
                        inty_formatted = float(round(max_peak["inty"]))  # Round to integer, but keep as float
                        isotope_matches.append([mz_formatted, inty_formatted])

                # Store results as numpy array
                if isotope_matches:
                    consensus_iso_data[consensus_uid] = np.array(isotope_matches)
                else:
                    consensus_iso_data[consensus_uid] = None

        except Exception as e:
            self.logger.warning(f"Failed to load MS1 data from {sample_path}: {e}")
            # Mark all consensus features from this sample as failed
            for consensus_uid, _ in consensus_list:
                consensus_iso_data[consensus_uid] = None
            continue

    # Update consensus_df with isotope data
    # Create mapping function for update
    def get_iso_data(uid):
        return consensus_iso_data.get(uid, None)

    # Update the iso column
    self.consensus_df = self.consensus_df.with_columns(
        pl.col("consensus_uid").map_elements(lambda uid: get_iso_data(uid), return_dtype=pl.Object).alias("iso")
    )

    # Count how many consensus features have isotope data
    iso_count = sum(1 for data in consensus_iso_data.values() if data is not None and len(data) > 0)

    self.logger.success(
        f"Isotope detection completed. Found isotope patterns for {iso_count}/{len(self.consensus_df)} consensus features."
    )


def reset_iso(self):
    """
    Reset the iso column in consensus_df to None, clearing all isotope data.

    This function clears any previously computed isotope patterns from the
    consensus_df, setting the 'iso' column to None for all features. This
    is useful before re-running isotope detection with different parameters
    or to clear isotope data entirely.

    Returns:
        None
    """
    if self.consensus_df is None:
        self.logger.warning("No consensus_df found. Nothing to reset.")
        return

    if "iso" not in self.consensus_df.columns:
        self.logger.warning("No 'iso' column found in consensus_df. Nothing to reset.")
        return

    # Count how many features currently have isotope data
    iso_count = self.consensus_df.select(pl.col("iso").is_not_null().sum().alias("count")).item(0, "count")

    # Reset the iso column to None
    self.consensus_df = self.consensus_df.with_columns(pl.lit(None, dtype=pl.Object).alias("iso"))

    self.logger.info(f"Reset isotope data for {iso_count} features. All 'iso' values set to None.")
