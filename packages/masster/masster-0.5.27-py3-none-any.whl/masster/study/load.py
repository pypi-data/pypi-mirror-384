from __future__ import annotations

import os
import concurrent.futures
from datetime import datetime

import numpy as np
import polars as pl
import pyopenms as oms

from tqdm import tqdm

from masster.chromatogram import Chromatogram
from masster.study.defaults import fill_defaults
from masster.sample.sample import Sample
from masster.spectrum import Spectrum


# Pre-import heavy modules to avoid repeated loading in add_sample()
try:
    import alpharaw.sciex

    ALPHARAW_AVAILABLE = True
except ImportError:
    ALPHARAW_AVAILABLE = False

try:
    import pythonnet

    PYTHONNET_AVAILABLE = True
except ImportError:
    PYTHONNET_AVAILABLE = False

import glob


def add(self, folder=None, reset=False, adducts=None, max_files=None):
    """Add samples from a folder to the study.

    Args:
        folder (str, optional): Path to folder containing sample files.
            Defaults to study folder or current working directory.
        reset (bool, optional): Whether to reset the study before adding samples.
            Defaults to False.
        adducts (optional): Adducts to use for sample loading. Defaults to None.
        max_files (int, optional): Maximum number of files to process.
            Defaults to None (no limit).
    """
    if folder is None:
        if self.folder is not None:
            folder = self.folder
        else:
            folder = os.getcwd()

    self.logger.debug(f"Adding files from: {folder}")

    # Define file extensions to search for in order of priority
    extensions = [".sample5", ".wiff", ".raw", ".mzML"]

    # Check if folder contains glob patterns
    if not any(char in folder for char in ["*", "?", "[", "]"]):
        search_folder = folder
    else:
        search_folder = os.path.dirname(folder) if os.path.dirname(folder) else folder

    # Blacklist to track filenames without extensions that have already been processed
    blacklist = set()
    counter = 0
    not_zero = False
    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    # Search for files in order of priority
    for ext in extensions:
        if max_files is not None and counter >= max_files:
            break

        # Build search pattern
        if any(char in folder for char in ["*", "?", "[", "]"]):
            # If folder already contains glob patterns, use it as-is
            pattern = folder
        else:
            pattern = os.path.join(search_folder, "**", f"*{ext}")

        files = glob.glob(pattern, recursive=True)

        if len(files) > 0:
            # Limit files if max_files is specified
            remaining_slots = max_files - counter if max_files is not None else len(files)
            files = files[:remaining_slots]

            self.logger.debug(f"Found {len(files)} {ext} files")

            # Filter files not already processed and respect max_files limit
            files_to_process = []
            for file in files:
                if max_files is not None and counter >= max_files:
                    break

                # Get filename without extension for blacklist check
                basename = os.path.basename(file)
                filename_no_ext = os.path.splitext(basename)[0]

                # Check if this filename (without extension) is already in blacklist
                if filename_no_ext not in blacklist:
                    files_to_process.append(file)
                    if len(files_to_process) + counter >= (max_files or float("inf")):
                        break

            # Batch process all files of this extension using ultra-optimized method
            if files_to_process:
                self.logger.debug(
                    f"Batch processing {len(files_to_process)} {ext} files",
                )
                successful = _add_samples_batch(
                    self, files_to_process, reset=reset, adducts=adducts, blacklist=blacklist
                )
                counter += successful
                if successful > 0:
                    not_zero = True

    if max_files is not None and counter >= max_files:
        self.logger.debug(
            f"Reached maximum number of files to add: {max_files}. Stopping further additions.",
        )

    if not not_zero:
        self.logger.warning(
            f"No files found in {folder}. Please check the folder path or file patterns.",
        )
    else:
        self.logger.debug(f"Added {counter} samples to the study.")

    # Return a simple summary to suppress marimo's automatic object display
    return f"Added {counter} samples to study"


def add_sample(self, file, type=None, reset=False, adducts=None):
    """
    Add a single sample to the study.

    Args:
        file (str): Path to the sample file
        type (str, optional): File type to force. Defaults to None (auto-detect).
        reset (bool, optional): Whether to reset the study. Defaults to False.
        adducts (optional): Adducts to use for sample loading. Defaults to None.
        fast (bool, optional): Whether to use optimized loading that skips ms1_df
            for better performance. Defaults to True.

    Returns:
        bool: True if successful, False otherwise.
    """

    success = _add_sample_noms1(
        self,
        file,
        type=type,
        reset=reset,
        adducts=adducts,
        skip_color_reset=False,  # Do color reset for individual calls
        skip_schema_check=True,  # Skip schema check for performance (safe with diagonal concat)
    )

    return success


def load(self, filename=None):
    """
    Load a study from an HDF5 file.

    Args:
        study: The study object to load into
        filename (str, optional): The path to the HDF5 file to load the study from.
    """

    # Handle default filename
    if filename is None:
        if self.folder is not None:
            # search for *.study5 in folder
            study5_files = glob.glob(os.path.join(self.folder, "*.study5"))
            if study5_files:
                filename = study5_files[-1]
            else:
                self.logger.error("No .study5 files found in folder")
                return
        else:
            self.logger.error("Either filename or folder must be provided")
            return

    # self.logger.info(f"Loading study from {filename}")
    from masster.study.h5 import _load_study5

    _load_study5(self, filename)

    # After loading the study, check if we have consensus features before loading consensus XML
    # if (self.consensus_df is not None and not self.consensus_df.is_empty()):
    #    consensus_xml_path = filename.replace(".study5", ".consensusXML")
    #    if os.path.exists(consensus_xml_path):
    #        self._load_consensusXML(filename=consensus_xml_path)
    # self.logger.info(f"Automatically loaded consensus from {consensus_xml_path}")
    #    else:
    #        self.logger.warning(f"No consensus XML file found at {consensus_xml_path}")
    # else:
    #    self.logger.debug("No consensus features found, skipping consensusXML loading")

    self.filename = filename


def _fill_chrom_single_impl(
    self,
    uids=None,
    mz_tol: float = 0.010,
    rt_tol: float = 10.0,
    min_samples_rel: float = 0.0,
    min_samples_abs: int = 2,
):
    """Fill missing chromatograms by extracting from raw data.

    Simplified version that loads one sample at a time without preloading or batching.

    Args:
        uids: Consensus UIDs to process (default: all)
        mz_tol: m/z tolerance for extraction (default: 0.010 Da)
        rt_tol: RT tolerance for extraction (default: 10.0 seconds)
        min_samples_rel: Relative minimum sample threshold (default: 0.0)
        min_samples_abs: Absolute minimum sample threshold (default: 2)
    """
    uids = self._get_consensus_uids(uids)

    self.logger.info("Gap filling...")
    self.logger.debug(
        f"Parameters: mz_tol={mz_tol}, rt_tol={rt_tol}, min_samples_rel={min_samples_rel}, min_samples_abs={min_samples_abs}",
    )

    # Apply minimum sample filters
    min_number_rel = 1
    min_number_abs = 1
    if isinstance(min_samples_rel, float) and min_samples_rel > 0:
        min_number_rel = int(min_samples_rel * len(self.samples_df))
    if isinstance(min_samples_abs, int) and min_samples_abs >= 0:
        min_number_abs = int(min_samples_abs) if min_samples_abs > 0 else 0
    min_number = max(min_number_rel, min_number_abs)

    # Special case: if min_samples_abs is explicitly 0, allow 0-sample features (like library features)
    if isinstance(min_samples_abs, int) and min_samples_abs == 0:
        min_number = 0

    self.logger.debug(f"Threshold for gap filling: number_samples>={min_number}")

    if min_number > 0:
        original_count = len(uids)
        uids = self.consensus_df.filter(
            (pl.col("number_samples") >= min_number) & (pl.col("consensus_uid").is_in(uids)),
        )["consensus_uid"].to_list()
        self.logger.debug(
            f"Features to fill: {original_count} -> {len(uids)}",
        )
    self.logger.debug("Identifying missing features...")
    # Instead of building full chromatogram matrix, identify missing consensus/sample combinations directly
    missing_combinations = _get_missing_consensus_sample_combinations(self, uids)
    if not missing_combinations:
        self.logger.info("No missing features found to fill.")
        return

    # Build lookup dictionaries
    self.logger.debug("Building lookup dictionaries...")
    consensus_info = {}
    consensus_subset = self.consensus_df.select(
        [
            "consensus_uid",
            "rt_start_mean",
            "rt_end_mean",
            "mz",
            "rt",
        ],
    ).filter(pl.col("consensus_uid").is_in(uids))

    for row in consensus_subset.iter_rows(named=True):
        consensus_info[row["consensus_uid"]] = {
            "rt_start_mean": row["rt_start_mean"],
            "rt_end_mean": row["rt_end_mean"],
            "mz": row["mz"],
            "rt": row["rt"],
        }

    # Process each sample individually
    # Group missing combinations by sample for efficient processing
    missing_by_sample = {}
    for consensus_uid, sample_uid, sample_name, sample_path, sample_source in missing_combinations:
        if sample_name not in missing_by_sample:
            missing_by_sample[sample_name] = {
                "sample_uid": sample_uid,
                "sample_path": sample_path,
                "sample_source": sample_source,
                "missing_consensus_uids": [],
            }
        missing_by_sample[sample_name]["missing_consensus_uids"].append(consensus_uid)

    new_features: list[dict] = []
    new_mapping: list[dict] = []
    counter = 0

    self.logger.debug(
        f"Missing features: {len(missing_combinations)} in {len(missing_by_sample)} samples...",
    )

    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    for sample_name, sample_info in tqdm(
        missing_by_sample.items(),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}File",
        disable=tdqm_disable,
    ):
        # Load this sample
        sample_uid = sample_info["sample_uid"]
        sample_path = sample_info["sample_path"]
        sample_source = sample_info["sample_source"]
        missing_consensus_uids = sample_info["missing_consensus_uids"]

        try:
            # Load this sample using study._load_ms1() as suggested by user
            # Use sample_path (points to .sample5 files) not sample_source (points to .raw files)
            ms1_data = self._load_ms1(filename=sample_path)
            if ms1_data is None or ms1_data.is_empty():
                self.logger.warning(f"No MS1 data found for sample {sample_name}")
                continue

            # Create a temporary object to hold the MS1 data for processing
            class TempSample:
                def __init__(self, ms1_df):
                    self.ms1_df = ms1_df

            file = TempSample(ms1_data)
        except Exception as e:
            self.logger.warning(f"Failed to load sample {sample_name}: {e}")
            continue

        self.logger.debug(
            f"Sample {sample_name}: Processing {len(missing_consensus_uids)} missing features",
        )

        # Process each missing feature
        for consensus_uid in missing_consensus_uids:
            cons = consensus_info[consensus_uid]
            mz = cons["mz"]
            rt = cons["rt"]
            rt_start_mean = cons["rt_start_mean"]
            rt_end_mean = cons["rt_end_mean"]

            # Filter MS1 data for this feature
            if hasattr(file, "ms1_df") and not file.ms1_df.is_empty():
                # Special handling for RT=0 (library-derived features)
                if rt == 0.0:
                    # Step 1: Retrieve full chromatogram for the m/z
                    d_full = file.ms1_df.filter((pl.col("mz") >= mz - mz_tol) & (pl.col("mz") <= mz + mz_tol))

                    if not d_full.is_empty():
                        # Step 2: Find maximum intensity and its RT
                        max_inty_row = d_full.filter(pl.col("inty") == d_full["inty"].max()).head(1)

                        if not max_inty_row.is_empty():
                            max_rt = max_inty_row["rt"].item()

                            # Get eic_rt_tol from sample parameters if available
                            eic_rt_tol = rt_tol  # Default fallback
                            if hasattr(file, "parameters") and hasattr(file.parameters, "eic_rt_tol"):
                                eic_rt_tol = file.parameters.eic_rt_tol

                            # Step 3: Trim around max intensity using eic_rt_tol
                            d = d_full.filter(
                                (pl.col("rt") >= max_rt - eic_rt_tol) & (pl.col("rt") <= max_rt + eic_rt_tol)
                            )

                            # Update consensus RT info based on discovered peak
                            rt = max_rt
                            rt_start_mean = max_rt - eic_rt_tol
                            rt_end_mean = max_rt + eic_rt_tol
                        else:
                            d = pl.DataFrame()
                    else:
                        d = pl.DataFrame()
                else:
                    # Normal RT-based filtering for non-zero RT
                    d = file.ms1_df.filter(
                        (pl.col("mz") >= mz - mz_tol)
                        & (pl.col("mz") <= mz + mz_tol)
                        & (pl.col("rt") >= rt_start_mean - rt_tol)
                        & (pl.col("rt") <= rt_end_mean + rt_tol),
                    )
            else:
                d = pl.DataFrame()

            # Create chromatogram
            if d.is_empty():
                self.logger.debug(
                    f"Feature {consensus_uid}: No MS1 data found, creating empty chromatogram",
                )
                eic = Chromatogram(
                    rt=np.array([rt_start_mean, rt_end_mean]),
                    inty=np.array([0.0, 0.0]),
                    label=f"EIC mz={mz:.4f}",
                    file=sample_path,
                    mz=mz,
                    mz_tol=mz_tol,
                    feature_start=rt_start_mean,
                    feature_end=rt_end_mean,
                    feature_apex=rt,
                )
                max_inty = 0.0
                area = 0.0
            else:
                self.logger.debug(
                    f"Feature {consensus_uid}: Found {len(d)} MS1 points, creating EIC",
                )
                eic_rt = d.group_by("rt").agg(pl.col("inty").max()).sort("rt")

                if len(eic_rt) > 4:
                    eic = Chromatogram(
                        eic_rt["rt"].to_numpy(),
                        eic_rt["inty"].to_numpy(),
                        label=f"EIC mz={mz:.4f}",
                        file=sample_path,
                        mz=mz,
                        mz_tol=mz_tol,
                        feature_start=rt_start_mean,
                        feature_end=rt_end_mean,
                        feature_apex=rt,
                    ).find_peaks()
                    max_inty = np.max(eic.inty)
                    area = eic.feature_area
                else:
                    eic = Chromatogram(
                        eic_rt["rt"].to_numpy(),
                        eic_rt["inty"].to_numpy(),
                        label=f"EIC mz={mz:.4f}",
                        file=sample_path,
                        mz=mz,
                        mz_tol=mz_tol,
                        feature_start=rt_start_mean,
                        feature_end=rt_end_mean,
                        feature_apex=rt,
                    )
                    max_inty = 0.0
                    area = 0.0

            # Generate feature UID
            feature_uid = (
                self.features_df["feature_uid"].max() + len(new_features) + 1
                if not self.features_df.is_empty()
                else len(new_features) + 1
            )

            # Create new feature entry
            new_feature = {
                "sample_uid": sample_uid,
                "feature_uid": feature_uid,
                "feature_id": None,
                "mz": mz,
                "rt": rt,
                "rt_original": None,
                "rt_start": rt_start_mean,
                "rt_end": rt_end_mean,
                "rt_delta": rt_end_mean - rt_start_mean,
                "mz_start": None,
                "mz_end": None,
                "inty": max_inty,
                "quality": None,
                "charge": None,
                "iso": None,
                "iso_of": None,
                "adduct": None,
                "adduct_mass": None,
                "adduct_group": None,
                "chrom": eic,
                "chrom_coherence": None,
                "chrom_prominence": None,
                "chrom_prominence_scaled": None,
                "chrom_height_scaled": None,
                "ms2_scans": None,
                "ms2_specs": None,
                "filled": True,
                "chrom_area": area,
            }

            new_features.append(new_feature)
            new_mapping.append(
                {
                    "consensus_uid": consensus_uid,
                    "sample_uid": sample_uid,
                    "feature_uid": feature_uid,
                },
            )
            counter += 1

    # Add new features to DataFrames
    self.logger.debug(f"Adding {len(new_features)} new features to DataFrame...")
    if new_features:
        # Create properly formatted rows
        rows_to_add = []
        for feature_dict in new_features:
            new_row = {}
            for col in self.features_df.columns:
                if col in feature_dict:
                    new_row[col] = feature_dict[col]
                else:
                    new_row[col] = None
            rows_to_add.append(new_row)

        # Create and add new DataFrame
        if rows_to_add:
            # Ensure consistent data types by explicitly casting problematic columns
            for row in rows_to_add:
                # Cast numeric columns to ensure consistency
                for key, value in row.items():
                    if key in ["mz", "rt", "intensity", "area", "height"] and value is not None:
                        row[key] = float(value)
                    elif key in ["sample_id", "feature_id"] and value is not None:
                        row[key] = int(value)

            new_df = pl.from_dicts(rows_to_add, infer_schema_length=len(rows_to_add))
        else:
            # Handle empty case - create empty DataFrame with proper schema
            new_df = pl.DataFrame(schema=self.features_df.schema)

        # Cast columns to match existing schema
        cast_exprs = []
        for col in self.features_df.columns:
            existing_dtype = self.features_df[col].dtype
            cast_exprs.append(pl.col(col).cast(existing_dtype, strict=False))

        new_df = new_df.with_columns(cast_exprs)
        self.features_df = self.features_df.vstack(new_df)

        # Add consensus mapping
        new_mapping_df = pl.DataFrame(new_mapping)
        self.consensus_mapping_df = pl.concat(
            [self.consensus_mapping_df, new_mapping_df],
            how="diagonal",
        )

    self.logger.info(f"Filled {counter} chromatograms from raw data.")


def fill_single(self, **kwargs):
    """Fill missing chromatograms by extracting from raw data.

    Simplified version that loads one sample at a time without preloading or batching.

    Parameters:
        **kwargs: Keyword arguments for fill_single parameters. Can include:
            - A fill_defaults instance to set all parameters at once
            - Individual parameter names and values (see fill_defaults for details)

    Key Parameters:
        uids: Consensus UIDs to process (default: all)
        mz_tol: m/z tolerance for extraction (default: 0.010 Da)
        rt_tol: RT tolerance for extraction (default: 10.0 seconds)
        min_samples_rel: Relative minimum sample threshold (default: 0.0)
        min_samples_abs: Absolute minimum sample threshold (default: 2)
    """
    # parameters initialization
    from masster.study.defaults import fill_defaults

    params = fill_defaults()

    for key, value in kwargs.items():
        if isinstance(value, fill_defaults):
            params = value
            self.logger.debug("Using provided fill_defaults parameters")
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
    self.update_history(["fill_single"], params.to_dict())
    self.logger.debug("Parameters stored to fill_single")

    # Call the original fill_chrom_single function with extracted parameters
    return _fill_chrom_single_impl(
        self,
        uids=params.get("uids"),
        mz_tol=params.get("mz_tol"),
        rt_tol=params.get("rt_tol"),
        min_samples_rel=params.get("min_samples_rel"),
        min_samples_abs=params.get("min_samples_abs"),
    )


def _build_rt_correction_mapping_per_sample(self, sample_uid):
    """
    Pre-compute RT correction mapping for a sample by getting all non-filled features.
    This avoids repeated DataFrame filtering for each feature.

    Args:
        sample_uid: Sample UID to build mapping for

    Returns:
        Polars DataFrame with rt, rt_original, and rt_delta columns, sorted by rt
        Returns empty DataFrame if no reference features found
    """
    # Get non-filled features from the same sample
    if "filled" in self.features_df.columns:
        sample_features = self.features_df.filter(
            (pl.col("sample_uid") == sample_uid)
            & (pl.col("filled") == False)
            & (pl.col("rt_original").is_not_null())
            & (pl.col("rt").is_not_null())
        )
    else:
        # If no filled column, assume all existing features are non-filled
        sample_features = self.features_df.filter(
            (pl.col("sample_uid") == sample_uid) & (pl.col("rt_original").is_not_null()) & (pl.col("rt").is_not_null())
        )

    if sample_features.is_empty():
        return pl.DataFrame(schema={"rt": pl.Float64, "rt_original": pl.Float64, "rt_delta": pl.Float64})

    # Pre-compute RT deltas and sort by RT for efficient lookup
    rt_mapping = sample_features.select([
        pl.col("rt"),
        pl.col("rt_original"),
        (pl.col("rt") - pl.col("rt_original")).alias("rt_delta"),
    ]).sort("rt")

    return rt_mapping


def _estimate_rt_original_from_mapping(self, rt_mapping, target_rt):
    """
    Fast RT original estimation using pre-computed mapping.

    Args:
        rt_mapping: Pre-computed RT mapping DataFrame from _build_rt_correction_mapping_per_sample
        target_rt: Target aligned RT for the filled feature

    Returns:
        Estimated rt_original value, or None if no mapping available
    """
    if rt_mapping.is_empty():
        return None

    # Find closest RT using vectorized operations
    rt_mapping_with_diff = rt_mapping.with_columns([(pl.col("rt") - target_rt).abs().alias("rt_diff")])

    # Get the RT delta from the closest feature
    closest_row = rt_mapping_with_diff.sort("rt_diff").head(1)
    if closest_row.is_empty():
        return None

    closest_rt_delta = closest_row["rt_delta"].item()
    return target_rt - closest_rt_delta


def _estimate_rt_original_for_filled_feature(self, sample_uid, target_rt, logger=None):
    """
    Estimate rt_original for a filled feature by finding the closest non-filled feature
    from the same sample and using its RT delta (rt - rt_original).

    Args:
        sample_uid: Sample UID to search within
        target_rt: Target aligned RT for the filled feature
        logger: Optional logger for debug messages

    Returns:
        Estimated rt_original value, or None if no suitable reference found
    """
    # Get non-filled features from the same sample
    if "filled" in self.features_df.columns:
        sample_features = self.features_df.filter(
            (pl.col("sample_uid") == sample_uid)
            & (pl.col("filled") == False)
            & (pl.col("rt_original").is_not_null())
            & (pl.col("rt").is_not_null())
        )
    else:
        # If no filled column, assume all existing features are non-filled
        sample_features = self.features_df.filter(
            (pl.col("sample_uid") == sample_uid) & (pl.col("rt_original").is_not_null()) & (pl.col("rt").is_not_null())
        )

    if sample_features.is_empty():
        if logger:
            logger.debug(f"No reference features found for sample {sample_uid} to estimate rt_original")
        return None

    # Calculate RT differences and find the closest feature
    sample_features_with_diff = sample_features.with_columns([
        (pl.col("rt") - target_rt).abs().alias("rt_diff"),
        (pl.col("rt") - pl.col("rt_original")).alias("rt_delta"),
    ])

    # Find the feature with minimum RT difference
    closest_feature = sample_features_with_diff.sort("rt_diff").head(1)

    if closest_feature.is_empty():
        return None

    # Get the RT delta from the closest feature
    closest_rt_diff = closest_feature["rt_diff"].item()
    closest_rt_delta = closest_feature["rt_delta"].item()

    # Estimate rt_original using the same delta: rt_original = rt - rt_delta
    estimated_rt_original = target_rt - closest_rt_delta

    if self.logger:
        self.logger.debug(
            f"Estimated rt_original={estimated_rt_original:.3f} for sample {sample_uid}, rt={target_rt:.3f} "
            f"using closest feature (rt_diff={closest_rt_diff:.3f}, rt_delta={closest_rt_delta:.3f})"
        )

    return estimated_rt_original


def _process_sample_for_parallel_fill(
    self,
    sample_info,
    consensus_info,
    uids,
    mz_tol,
    rt_tol,
    missing_combinations_df,
    features_df_max_uid,
):
    sample_uid = sample_info["sample_uid"]
    sample_path = sample_info["sample_path"]
    sample_source = sample_info["sample_source"]

    new_features: list[dict] = []
    new_mapping: list[dict] = []
    counter = 0

    # Get missing features for this sample from precomputed combinations
    sample_missing_df = missing_combinations_df.filter(pl.col("sample_uid") == sample_uid)
    sample_consensus_uids = sample_missing_df["consensus_uid"].to_list()

    if not sample_consensus_uids:
        return new_features, new_mapping, counter

    # OPTIMIZATION: Pre-compute RT correction mapping per sample to avoid repeated DataFrame filtering
    rt_mapping = _build_rt_correction_mapping_per_sample(self, sample_uid)

    # OPTIMIZATION 1: Load MS1 data ONCE per sample instead of per feature
    try:
        ms1_data = self._load_ms1(filename=sample_path)
        if ms1_data is None or ms1_data.is_empty():
            # Create empty features for all missing consensus UIDs
            for i, consensus_uid in enumerate(sample_consensus_uids):
                info = consensus_info[consensus_uid]
                empty_eic = Chromatogram(
                    rt=np.array([info["rt_start_mean"], info["rt_end_mean"]]),
                    inty=np.array([0.0, 0.0]),
                    label=f"EIC mz={info['mz']:.4f}",
                    file=sample_path,
                    mz=info["mz"],
                    feature_start=info["rt_start_mean"],
                    feature_end=info["rt_end_mean"],
                    feature_apex=info["rt"],
                )

                new_feature = {
                    "uid": features_df_max_uid + counter,
                    "sample_uid": sample_uid,
                    "mz": info["mz"],
                    "rt": info["rt"],
                    "rt_original": 0.0
                    if info["rt"] == 0.0
                    else _estimate_rt_original_from_mapping(self, rt_mapping, info["rt"]),
                    "mz_centroid": None,
                    "rt_centroid": None,
                    "iso": None,
                    "iso_of": None,
                    "adduct": None,
                    "adduct_mass": None,
                    "adduct_group": None,
                    "chrom": empty_eic,
                    "filled": True,
                    "chrom_area": 0.0,
                    "chrom_coherence": None,
                    "chrom_prominence": None,
                    "chrom_prominence_scaled": None,
                    "chrom_height_scaled": None,
                    "ms2_scans": None,
                    "ms2_specs": None,
                }

                new_features.append(new_feature)
                new_mapping.append({
                    "consensus_uid": consensus_uid,
                    "sample_uid": sample_uid,
                    "feature_uid": features_df_max_uid + counter,
                })
                counter += 1
            return new_features, new_mapping, counter

    except Exception as e:
        # If MS1 loading fails, create empty features
        self.logger.debug(f"Failed to load MS1 data from {sample_path}: {e}")
        for i, consensus_uid in enumerate(sample_consensus_uids):
            info = consensus_info[consensus_uid]
            empty_eic = Chromatogram(
                rt=np.array([info["rt_start_mean"], info["rt_end_mean"]]),
                inty=np.array([0.0, 0.0]),
                label=f"EIC mz={info['mz']:.4f}",
                file=sample_path,
                mz=info["mz"],
                feature_start=info["rt_start_mean"],
                feature_end=info["rt_end_mean"],
                feature_apex=info["rt"],
            )

            new_feature = {
                "uid": features_df_max_uid + counter,
                "sample_uid": sample_uid,
                "mz": info["mz"],
                "rt": info["rt"],
                "rt_original": 0.0
                if info["rt"] == 0.0
                else _estimate_rt_original_from_mapping(self, rt_mapping, info["rt"]),
                "mz_centroid": None,
                "rt_centroid": None,
                "iso": None,
                "iso_of": None,
                "adduct": None,
                "adduct_mass": None,
                "adduct_group": None,
                "chrom": empty_eic,
                "filled": True,
                "chrom_area": 0.0,
                "chrom_coherence": None,
                "chrom_prominence": None,
                "chrom_prominence_scaled": None,
                "chrom_height_scaled": None,
                "ms2_scans": None,
                "ms2_specs": None,
            }

            new_features.append(new_feature)
            new_mapping.append({
                "consensus_uid": consensus_uid,
                "sample_uid": sample_uid,
                "feature_uid": features_df_max_uid + counter,
            })
            counter += 1
        return new_features, new_mapping, counter

    # OPTIMIZATION 2: Pre-filter MS1 data by m/z ranges to reduce memory and processing
    all_mzs = [consensus_info[uid]["mz"] for uid in sample_consensus_uids]
    mz_min = min(all_mzs) - mz_tol
    mz_max = max(all_mzs) + mz_tol

    # Pre-filter by broad m/z range
    ms1_filtered = ms1_data.filter((pl.col("mz") >= mz_min) & (pl.col("mz") <= mz_max))

    # Early exit if no data in m/z range
    if ms1_filtered.is_empty():
        for i, consensus_uid in enumerate(sample_consensus_uids):
            info = consensus_info[consensus_uid]
            empty_eic = Chromatogram(
                rt=np.array([info["rt_start_mean"], info["rt_end_mean"]]),
                inty=np.array([0.0, 0.0]),
                label=f"EIC mz={info['mz']:.4f}",
                file=sample_path,
                mz=info["mz"],
                feature_start=info["rt_start_mean"],
                feature_end=info["rt_end_mean"],
                feature_apex=info["rt"],
            )

            new_feature = {
                "uid": features_df_max_uid + counter,
                "sample_uid": sample_uid,
                "mz": info["mz"],
                "rt": info["rt"],
                "rt_original": 0.0
                if info["rt"] == 0.0
                else _estimate_rt_original_from_mapping(self, rt_mapping, info["rt"]),
                "mz_centroid": None,
                "rt_centroid": None,
                "iso": None,
                "iso_of": None,
                "adduct": None,
                "adduct_mass": None,
                "adduct_group": None,
                "chrom": empty_eic,
                "filled": True,
                "chrom_area": 0.0,
                "chrom_coherence": None,
                "chrom_prominence": None,
                "chrom_prominence_scaled": None,
                "chrom_height_scaled": None,
                "ms2_scans": None,
                "ms2_specs": None,
            }

            new_features.append(new_feature)
            new_mapping.append({
                "consensus_uid": consensus_uid,
                "sample_uid": sample_uid,
                "feature_uid": features_df_max_uid + counter,
            })
            counter += 1
        return new_features, new_mapping, counter

    # OPTIMIZATION 3: Process all features using the pre-loaded and filtered MS1 data
    for consensus_uid in sample_consensus_uids:
        info = consensus_info[consensus_uid]
        mz, rt = info["mz"], info["rt"]

        try:
            if rt == 0.0:
                # Handle RT=0 features - create empty chromatogram
                empty_eic = Chromatogram(
                    rt=np.array([info["rt_start_mean"], info["rt_end_mean"]]),
                    inty=np.array([0.0, 0.0]),
                    label=f"EIC mz={mz:.4f}",
                    file=sample_path,
                    mz=mz,
                    feature_start=info["rt_start_mean"],
                    feature_end=info["rt_end_mean"],
                    feature_apex=rt,
                )
                eic = empty_eic
                best_peak = None
            else:
                # Extract real chromatogram using pre-filtered MS1 data
                d = ms1_filtered.filter(
                    (pl.col("mz") >= mz - mz_tol)
                    & (pl.col("mz") <= mz + mz_tol)
                    & (pl.col("rt") >= rt - rt_tol)
                    & (pl.col("rt") <= rt + rt_tol)
                )

                # Create chromatogram from filtered data
                if d.is_empty():
                    # No MS1 data found - create empty chromatogram
                    eic = Chromatogram(
                        rt=np.array([info["rt_start_mean"], info["rt_end_mean"]]),
                        inty=np.array([0.0, 0.0]),
                        label=f"EIC mz={mz:.4f}",
                        file=sample_path,
                        mz=mz,
                        feature_start=info["rt_start_mean"],
                        feature_end=info["rt_end_mean"],
                        feature_apex=rt,
                    )
                    best_peak = None
                else:
                    # Aggregate intensities per retention time (get max inty per RT)
                    eic_rt = d.group_by("rt").agg(pl.col("inty").max()).sort("rt")

                    # Create chromatogram with real data and find peaks
                    eic = Chromatogram(
                        eic_rt["rt"].to_numpy(),
                        eic_rt["inty"].to_numpy(),
                        label=f"EIC mz={mz:.4f}",
                        file=sample_path,
                        mz=mz,
                        feature_start=info["rt_start_mean"],
                        feature_end=info["rt_end_mean"],
                        feature_apex=rt,
                    ).find_peaks()
                    best_peak = (
                        self._find_best_peak_in_eic(eic, rt, rt_tol)
                        if hasattr(self, "_find_best_peak_in_eic")
                        else None
                    )

            # Create feature with optimized RT original estimation
            rt_original_estimated = None
            if rt == 0.0:
                rt_original_estimated = 0.0  # RT=0 features
            else:
                rt_original_estimated = _estimate_rt_original_from_mapping(self, rt_mapping, rt)

            new_feature = {
                "uid": features_df_max_uid + counter,
                "sample_uid": sample_uid,
                "mz": mz,
                "rt": rt,
                "rt_original": rt_original_estimated,
                "mz_centroid": None,
                "rt_centroid": None,
                "iso": None,
                "iso_of": None,
                "adduct": None,
                "adduct_mass": None,
                "adduct_group": None,
                "chrom": eic,
                "filled": True,
                "chrom_area": best_peak.get("area", 0.0) if best_peak else 0.0,
                "chrom_coherence": best_peak.get("coherence") if best_peak else None,
                "chrom_prominence": best_peak.get("prominence") if best_peak else None,
                "chrom_prominence_scaled": best_peak.get("prominence_scaled") if best_peak else None,
                "chrom_height_scaled": best_peak.get("height_scaled") if best_peak else None,
                "ms2_scans": None,
                "ms2_specs": None,
            }

            new_features.append(new_feature)
            new_mapping.append({
                "consensus_uid": consensus_uid,
                "sample_uid": sample_uid,
                "feature_uid": features_df_max_uid + counter,
            })
            counter += 1

        except Exception as e:
            # Skip this feature if extraction fails but log the error
            self.logger.debug(f"Failed to extract feature {consensus_uid} from {sample_path}: {e}")
            continue

    return new_features, new_mapping, counter


def _fill_chrom_impl(
    self,
    uids=None,
    mz_tol: float = 0.010,
    rt_tol: float = 10.0,
    min_samples_rel: float = 0.0,
    min_samples_abs: int = 2,
    threads=6,
):
    """Fill missing chromatograms by extracting from raw data using parallel processing.

    Args:
        uids: Consensus UIDs to process (default: all)
        mz_tol: m/z tolerance for extraction (default: 0.010 Da)
        rt_tol: RT tolerance for extraction (default: 10.0 seconds)
        min_samples_rel: Relative minimum sample threshold (default: 0.0)
        min_samples_abs: Absolute minimum sample threshold (default: 2)
        threads: Number of parallel threads (default: 6)
    """
    uids = self._get_consensus_uids(uids)

    self.logger.info(f"Gap filling with {threads} threads...")
    self.logger.debug(
        f"Parameters: mz_tol={mz_tol}, rt_tol={rt_tol}, min_samples_rel={min_samples_rel}, min_samples_abs={min_samples_abs}, threads={threads}",
    )

    # Apply minimum sample filters
    min_number_rel = 1
    min_number_abs = 1
    if isinstance(min_samples_rel, float) and min_samples_rel > 0:
        min_number_rel = int(min_samples_rel * len(self.samples_df))
    if isinstance(min_samples_abs, int) and min_samples_abs >= 0:
        min_number_abs = int(min_samples_abs) if min_samples_abs > 0 else 0
    min_number = max(min_number_rel, min_number_abs)

    # Special case: if min_samples_abs is explicitly 0, allow 0-sample features (like library features)
    if isinstance(min_samples_abs, int) and min_samples_abs == 0:
        min_number = 0

    self.logger.debug(f"Threshold for gap filling: number_samples>={min_number}")

    if min_number > 0:
        original_count = len(uids)
        uids = self.consensus_df.filter(
            (pl.col("number_samples") >= min_number) & (pl.col("consensus_uid").is_in(uids)),
        )["consensus_uid"].to_list()
        self.logger.debug(f"Features to fill: {original_count} -> {len(uids)}")

    # Get missing consensus/sample combinations using the optimized method
    self.logger.debug("Identifying missing features...")
    missing_combinations = _get_missing_consensus_sample_combinations(self, uids)

    if not missing_combinations or len(missing_combinations) == 0:
        self.logger.info("No missing features found to fill.")
        return

    # Convert to DataFrame for easier processing
    missing_combinations_df = pl.DataFrame(
        missing_combinations,
        schema={
            "consensus_uid": pl.Int64,
            "sample_uid": pl.Int64,
            "sample_name": pl.Utf8,
            "sample_path": pl.Utf8,
            "sample_source": pl.Utf8,
        },
        orient="row",
    )

    # Build lookup dictionaries
    self.logger.debug("Building lookup dictionaries...")
    consensus_info = {}
    consensus_subset = self.consensus_df.select(
        [
            "consensus_uid",
            "rt_start_mean",
            "rt_end_mean",
            "mz",
            "rt",
        ],
    ).filter(pl.col("consensus_uid").is_in(uids))

    for row in consensus_subset.iter_rows(named=True):
        consensus_info[row["consensus_uid"]] = {
            "rt_start_mean": row["rt_start_mean"],
            "rt_end_mean": row["rt_end_mean"],
            "mz": row["mz"],
            "rt": row["rt"],
        }

    # Get sample info for all samples that need processing
    samples_to_process = []
    unique_sample_uids = missing_combinations_df["sample_uid"].unique().to_list()

    for row in self.samples_df.filter(
        pl.col("sample_uid").is_in(unique_sample_uids),
    ).iter_rows(named=True):
        samples_to_process.append(
            {
                "sample_name": row["sample_name"],
                "sample_uid": row["sample_uid"],
                "sample_path": row["sample_path"],
                "sample_source": row["sample_source"],
            },
        )

    total_missing = len(missing_combinations_df)
    self.logger.debug(
        f"Gap filling for {total_missing} missing features across {len(samples_to_process)} samples...",
    )

    # Calculate current max feature_uid to avoid conflicts
    features_df_max_uid = self.features_df["feature_uid"].max() if not self.features_df.is_empty() else 0

    # Process samples in parallel
    all_new_features: list[dict] = []
    all_new_mapping: list[dict] = []
    total_counter = 0

    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all samples for processing
        future_to_sample = {}
        for sample_info in samples_to_process:
            future = executor.submit(
                _process_sample_for_parallel_fill,
                self,
                sample_info,
                consensus_info,
                uids,
                mz_tol,
                rt_tol,
                missing_combinations_df,
                features_df_max_uid,
            )
            future_to_sample[future] = sample_info

        # Collect results with progress bar
        with tqdm(
            total=len(samples_to_process),
            desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}Processing samples",
            disable=tdqm_disable,
        ) as pbar:
            for future in concurrent.futures.as_completed(future_to_sample):
                try:
                    new_features, new_mapping, counter = future.result()

                    # Adjust feature UIDs to ensure global uniqueness
                    uid_offset = features_df_max_uid + len(all_new_features)
                    for i, feature in enumerate(new_features):
                        feature["feature_uid"] = uid_offset + i + 1
                    for i, mapping in enumerate(new_mapping):
                        mapping["feature_uid"] = uid_offset + i + 1

                    # RT original estimation is now done inside parallel processing - PERFORMANCE OPTIMIZED!

                    all_new_features.extend(new_features)
                    all_new_mapping.extend(new_mapping)
                    total_counter += counter

                except Exception as e:
                    sample_info = future_to_sample[future]
                    self.logger.warning(
                        f"Sample {sample_info['sample_name']} failed: {e}",
                    )

                pbar.update(1)

    # Add new features to DataFrames
    self.logger.debug(f"Adding {len(all_new_features)} new features to DataFrame...")
    if all_new_features:
        # Create properly formatted rows
        rows_to_add = []
        for feature_dict in all_new_features:
            new_row = {}
            for col in self.features_df.columns:
                if col in feature_dict:
                    new_row[col] = feature_dict[col]
                else:
                    new_row[col] = None
            rows_to_add.append(new_row)

        # Create and add new DataFrame
        if rows_to_add:
            # Ensure consistent data types by explicitly casting problematic columns
            for row in rows_to_add:
                # Cast numeric columns to ensure consistency
                for key, value in row.items():
                    if key in ["mz", "rt", "intensity", "area", "height"] and value is not None:
                        row[key] = float(value)
                    elif key in ["sample_id", "feature_id"] and value is not None:
                        row[key] = int(value)

            new_df = pl.from_dicts(rows_to_add, infer_schema_length=len(rows_to_add))
        else:
            # Handle empty case - create empty DataFrame with proper schema
            new_df = pl.DataFrame(schema=self.features_df.schema)

        # Cast columns to match existing schema
        cast_exprs = []
        for col in self.features_df.columns:
            existing_dtype = self.features_df[col].dtype
            cast_exprs.append(pl.col(col).cast(existing_dtype, strict=False))

        new_df = new_df.with_columns(cast_exprs)
        self.features_df = self.features_df.vstack(new_df)

        # Add consensus mapping
        new_mapping_df = pl.DataFrame(all_new_mapping)
        self.consensus_mapping_df = pl.concat(
            [self.consensus_mapping_df, new_mapping_df],
            how="diagonal",
        )

    # Log statistics about rt_original estimation
    if all_new_features:
        estimated_count = sum(1 for feature in all_new_features if feature.get("rt_original") is not None)
        none_count = sum(1 for feature in all_new_features if feature.get("rt_original") is None)
        self.logger.debug(f"Features with estimated rt_original: {estimated_count}")
        self.logger.debug(f"Features with None rt_original: {none_count}")

    self.logger.info(
        f"Filled {total_counter} chromatograms from raw data.",
    )


def fill(self, **kwargs):
    """Fill missing chromatograms by extracting from raw data using parallel processing.

    Parameters:
        **kwargs: Keyword arguments for fill parameters. Can include:
            - A fill_defaults instance to set all parameters at once
            - Individual parameter names and values (see fill_defaults for details)

    Key Parameters:
        uids: Consensus UIDs to process (default: all)
        mz_tol: m/z tolerance for extraction (default: 0.010 Da)
        rt_tol: RT tolerance for extraction (default: 10.0 seconds)
        min_samples_rel: Relative minimum sample threshold (default: 0.05)
        min_samples_abs: Absolute minimum sample threshold (default: 5)
        threads: Number of parallel threads (default: 6)
    """
    # parameters initialization
    params = fill_defaults()

    # Handle backward compatibility for old parameter names
    if "workers" in kwargs:
        kwargs["threads"] = kwargs.pop("workers")
        self.logger.debug("Converted 'workers' parameter to 'threads' for backward compatibility")
    if "num_workers" in kwargs:
        kwargs["threads"] = kwargs.pop("num_workers")
        self.logger.debug("Converted 'num_workers' parameter to 'threads' for backward compatibility")

    for key, value in kwargs.items():
        if isinstance(value, fill_defaults):
            params = value
            self.logger.debug("Using provided fill_defaults parameters")
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
    self.update_history(["fill"], params.to_dict())
    self.logger.debug("Parameters stored to fill")

    # Call the original fill_chrom function with extracted parameters
    return _fill_chrom_impl(
        self,
        uids=params.get("uids"),
        mz_tol=params.get("mz_tol"),
        rt_tol=params.get("rt_tol"),
        min_samples_rel=params.get("min_samples_rel"),
        min_samples_abs=params.get("min_samples_abs"),
        threads=params.get("threads"),
    )


def _get_missing_consensus_sample_combinations(self, uids):
    """
    Efficiently identify which consensus_uid/sample combinations are missing.
    Returns a list of tuples: (consensus_uid, sample_uid, sample_name, sample_path)

    Optimized for common scenarios:
    - Early termination for fully-filled studies
    - Efficient dictionary lookups instead of expensive DataFrame joins
    - Smart handling of sparse vs dense missing data patterns
    - Special handling for consensus features with no mappings (e.g., library-derived RT=0 features)
    """
    if not uids:
        return []

    n_consensus = len(uids)
    n_samples = len(self.samples_df)
    total_possible = n_consensus * n_samples

    # Identify consensus features that have NO mappings at all (e.g., library-derived RT=0 features)
    uids_set = set(uids)
    mapped_consensus_uids = set(
        self.consensus_mapping_df.filter(pl.col("consensus_uid").is_in(uids))["consensus_uid"].to_list()
    )
    unmapped_consensus_uids = uids_set - mapped_consensus_uids

    # Get all sample info once for efficiency
    all_samples = list(
        self.samples_df.select(
            ["sample_uid", "sample_name", "sample_path", "sample_source"],
        ).iter_rows(),
    )

    missing_combinations = []

    # For unmapped consensus features (e.g., RT=0), ALL samples are missing
    if unmapped_consensus_uids:
        self.logger.debug(
            f"Found {len(unmapped_consensus_uids)} consensus features with no mappings (e.g., RT=0 library features)"
        )
        for consensus_uid in unmapped_consensus_uids:
            for sample_uid, sample_name, sample_path, sample_source in all_samples:
                missing_combinations.append((consensus_uid, sample_uid, sample_name, sample_path, sample_source))

    # If all consensus features are unmapped, return early
    if len(mapped_consensus_uids) == 0:
        return missing_combinations

    # Continue with existing logic for mapped consensus features
    mapped_uids_list = list(mapped_consensus_uids)

    # Quick early termination check for fully/nearly filled studies
    # This handles the common case where fill() is run on an already-filled study
    consensus_counts = (
        self.consensus_mapping_df.filter(pl.col("consensus_uid").is_in(mapped_uids_list))
        .group_by("consensus_uid")
        .agg(pl.count("feature_uid").alias("count"))
    )

    total_existing = consensus_counts["count"].sum() if not consensus_counts.is_empty() else 0

    # Calculate total possible for mapped features only
    mapped_total_possible = len(mapped_uids_list) * n_samples

    # If >95% filled, likely no gaps (common case)
    if total_existing >= mapped_total_possible * 0.95:
        self.logger.debug(
            f"Study appears {total_existing / mapped_total_possible * 100:.1f}% filled, using sparse optimization",
        )

        # For sparse missing data, check each consensus feature individually
        # Build efficient lookups
        feature_to_sample = dict(
            self.features_df.select(["feature_uid", "sample_uid"]).iter_rows(),
        )

        # Get existing combinations for target UIDs only (mapped features)
        existing_by_consensus = {}
        for consensus_uid, feature_uid in self.consensus_mapping_df.select(
            [
                "consensus_uid",
                "feature_uid",
            ],
        ).iter_rows():
            if consensus_uid in mapped_consensus_uids and feature_uid in feature_to_sample:
                if consensus_uid not in existing_by_consensus:
                    existing_by_consensus[consensus_uid] = set()
                existing_by_consensus[consensus_uid].add(feature_to_sample[feature_uid])

        # Check for missing combinations for mapped features
        for consensus_uid in mapped_uids_list:
            existing_samples = existing_by_consensus.get(consensus_uid, set())
            for sample_uid, sample_name, sample_path, sample_source in all_samples:
                if sample_uid not in existing_samples:
                    missing_combinations.append(
                        (consensus_uid, sample_uid, sample_name, sample_path, sample_source),
                    )

        return missing_combinations

    else:
        # For studies with many gaps, use bulk operations
        self.logger.debug(
            f"Study {total_existing / mapped_total_possible * 100:.1f}% filled, using bulk optimization",
        )

        # Build efficient lookups
        feature_to_sample = dict(
            self.features_df.select(["feature_uid", "sample_uid"]).iter_rows(),
        )

        # Build existing combinations set for mapped features only
        existing_combinations = {
            (consensus_uid, feature_to_sample[feature_uid])
            for consensus_uid, feature_uid in self.consensus_mapping_df.select(
                [
                    "consensus_uid",
                    "feature_uid",
                ],
            ).iter_rows()
            if consensus_uid in mapped_consensus_uids and feature_uid in feature_to_sample
        }

        # Generate missing combinations for mapped features
        for consensus_uid in mapped_uids_list:
            for sample_uid, sample_name, sample_path, sample_source in all_samples:
                if (consensus_uid, sample_uid) not in existing_combinations:
                    missing_combinations.append((consensus_uid, sample_uid, sample_name, sample_path, sample_source))

        return missing_combinations


def _sanitize(self):
    """
    Sanitize features DataFrame to ensure all complex objects are properly typed.
    Convert serialized objects back to their proper types (Chromatogram, Spectrum).
    """
    if self.features_df is None or self.features_df.is_empty():
        return

    self.logger.debug(
        "Sanitizing features DataFrame to ensure all complex objects are properly typed.",
    )
    tdqm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    # Check if we have object columns that need sanitization
    has_chrom = "chrom" in self.features_df.columns
    has_ms2_specs = "ms2_specs" in self.features_df.columns

    if not has_chrom and not has_ms2_specs:
        self.logger.debug("No object columns found that need sanitization.")
        return

    # Convert to list of dictionaries for easier manipulation
    rows_data = []

    for row_dict in tqdm(
        self.features_df.iter_rows(named=True),
        total=len(self.features_df),
        desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     |{self.log_label}Sanitize features",
        disable=tdqm_disable,
    ):
        row_data = dict(row_dict)

        # Sanitize chrom column
        if has_chrom and row_data["chrom"] is not None:
            if not isinstance(row_data["chrom"], Chromatogram):
                try:
                    # Create new Chromatogram and populate from dict if needed
                    new_chrom = Chromatogram(rt=np.array([]), inty=np.array([]))
                    if hasattr(row_data["chrom"], "__dict__"):
                        new_chrom.from_dict(row_data["chrom"].__dict__)
                    else:
                        # If it's already a dict
                        new_chrom.from_dict(row_data["chrom"])
                    row_data["chrom"] = new_chrom
                except Exception as e:
                    self.logger.warning(f"Failed to sanitize chrom object: {e}")
                    row_data["chrom"] = None

        # Sanitize ms2_specs column
        if has_ms2_specs and row_data["ms2_specs"] is not None:
            if isinstance(row_data["ms2_specs"], list):
                sanitized_specs = []
                for ms2_specs in row_data["ms2_specs"]:
                    if not isinstance(ms2_specs, Spectrum):
                        try:
                            new_ms2_specs = Spectrum(
                                mz=np.array([0]),
                                inty=np.array([0]),
                            )
                            if hasattr(ms2_specs, "__dict__"):
                                new_ms2_specs.from_dict(ms2_specs.__dict__)
                            else:
                                new_ms2_specs.from_dict(ms2_specs)
                            sanitized_specs.append(new_ms2_specs)
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to sanitize ms2_specs object: {e}",
                            )
                            sanitized_specs.append(None)
                    else:
                        sanitized_specs.append(ms2_specs)
                row_data["ms2_specs"] = sanitized_specs
            elif not isinstance(row_data["ms2_specs"], Spectrum):
                try:
                    new_ms2_specs = Spectrum(mz=np.array([0]), inty=np.array([0]))
                    if hasattr(row_data["ms2_specs"], "__dict__"):
                        new_ms2_specs.from_dict(row_data["ms2_specs"].__dict__)
                    else:
                        new_ms2_specs.from_dict(row_data["ms2_specs"])
                    row_data["ms2_specs"] = new_ms2_specs
                except Exception as e:
                    self.logger.warning(f"Failed to sanitize ms2_specs object: {e}")
                    row_data["ms2_specs"] = None

        rows_data.append(row_data)

    # Recreate the DataFrame with sanitized data
    try:
        self.features_df = pl.DataFrame(rows_data)
        self.logger.success("Features DataFrame sanitization completed successfully.")
    except Exception as e:
        self.logger.error(f"Failed to recreate sanitized DataFrame: {e}")


def _add_samples_batch(self, files, reset=False, adducts=None, blacklist=None):
    """
    Optimized batch addition of samples.

    Args:
        files (list): List of file paths to process
        reset (bool): Whether to reset features before processing
        adducts: Adducts to use for sample loading
        blacklist (set): Set of filenames already processed

    Performance optimizations:
    1. No per-sample color reset
    2. No schema enforcement during addition
    3. Simplified DataFrame operations
    4. Batch progress reporting
    """
    if not files:
        return 0

    if blacklist is None:
        blacklist = set()

    self.logger.debug(
        f"Starting batch addition of {len(files)} samples...",
    )

    successful_additions = 0
    failed_additions = 0

    # Progress reporting setup
    tqdm_disable = self.log_level not in ["TRACE", "DEBUG", "INFO"]

    for i, file in enumerate(
        tqdm(
            files,
            total=len(files),
            desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {self.log_label}Add samples",
            disable=tqdm_disable,
        ),
    ):
        try:
            # Choose between optimized and standard loading
            success = _add_sample_noms1(
                self,
                file,
                reset=reset,
                adducts=adducts,
                skip_color_reset=True,  # Skip color reset during batch
                skip_schema_check=True,  # Skip schema enforcement
            )

            if success:
                # Add to blacklist for filename tracking
                basename = os.path.basename(file)
                filename_no_ext = os.path.splitext(basename)[0]
                blacklist.add(filename_no_ext)
                successful_additions += 1

        except Exception as e:
            self.logger.warning(f"Failed to add sample {file}: {e}")
            failed_additions += 1
            continue

    # Final cleanup operations done once at the end
    if successful_additions > 0:
        self.logger.debug("Performing final batch cleanup...")

        # Optional: Only do schema enforcement if specifically needed (usually not required)
        # self._ensure_features_df_schema_order()

        # Color assignment done once for all samples
        self.set_samples_color()

        self.logger.debug(
            f"Add samples complete: {successful_additions} successful, {failed_additions} failed",
        )

    return successful_additions


def _add_sample_noms1(
    self,
    file,
    type=None,
    reset=False,
    adducts=None,
    skip_color_reset=True,
    skip_schema_check=True,
):
    """
    Optimized add_sample with performance improvements integrated.

    Removes:
    - Schema enforcement (_ensure_features_df_schema_order)
    - Complex column alignment and type casting
    - Per-addition color reset
    - Unnecessary column reordering

    Returns True if successful, False otherwise.
    """
    self.logger.debug(f"Adding: {file}")

    # Basic validation
    basename = os.path.basename(file)
    sample_name = os.path.splitext(basename)[0]

    if sample_name in self.samples_df["sample_name"].to_list():
        self.logger.warning(f"Sample {sample_name} already exists. Skipping.")
        return False

    if not os.path.exists(file):
        self.logger.error(f"File {file} does not exist.")
        return False

    if not file.endswith((".sample5", ".wiff", ".raw", ".mzML")):
        self.logger.error(f"Unsupported file type: {file}")
        return False

    # Load sample
    ddaobj = Sample()
    ddaobj.logger_update(level="WARNING", label=os.path.basename(file))

    # Try optimized loading first (study-specific, skips ms1_df for better performance)

    if file.endswith(".sample5"):
        ddaobj.load_noms1(file)
        # restore _oms_features_map
        ddaobj._get_feature_map()
    else:
        try:
            ddaobj.load(file)
            ddaobj.find_features()
            ddaobj.find_adducts(adducts=adducts)
            ddaobj.find_ms2()
        except Exception as e:
            self.logger.warning(f"Failed to add sample {file}: {e}")
            return False

    # Check polarity compatibility
    sample_polarity = getattr(ddaobj, "polarity", None)
    study_polarity = getattr(self, "polarity", None)

    if sample_polarity is not None and study_polarity is not None:
        # Normalize polarity names for comparison
        sample_pol_norm = (
            "positive"
            if sample_polarity in ["pos", "positive"]
            else "negative"
            if sample_polarity in ["neg", "negative"]
            else sample_polarity
        )
        study_pol_norm = (
            "positive"
            if study_polarity in ["pos", "positive"]
            else "negative"
            if study_polarity in ["neg", "negative"]
            else study_polarity
        )

        if sample_pol_norm != study_pol_norm:
            self.logger.warning(
                f"Sample {sample_name} polarity ({sample_polarity}) differs from study polarity ({study_polarity}). Skipping sample."
            )
            return False

    # self.features_maps.append(ddaobj._oms_features_map)

    # Determine sample type
    sample_type = "sample" if type is None else type
    if "qc" in sample_name.lower():
        sample_type = "qc"
    if "blank" in sample_name.lower():
        sample_type = "blank"

    map_id_value = len(self.features_maps) - 1

    # Handle file paths
    if file.endswith(".sample5"):
        final_sample_path = file
        # self.logger.debug(f"Using existing .sample5 file: {final_sample_path}")
    else:
        if self.folder is not None:
            if not os.path.exists(self.folder):
                os.makedirs(self.folder)
            final_sample_path = os.path.join(self.folder, sample_name + ".sample5")
        else:
            final_sample_path = os.path.join(os.getcwd(), sample_name + ".sample5")
        ddaobj.save(final_sample_path)
        self.logger.debug(f"Saved converted sample: {final_sample_path}")

    # Efficient scan counting
    ms1_count = ms2_count = 0
    if hasattr(ddaobj, "scans_df") and ddaobj.scans_df is not None and not ddaobj.scans_df.is_empty():
        scan_counts = ddaobj.scans_df.group_by("ms_level").len().to_dict(as_series=False)
        ms_levels = scan_counts.get("ms_level", [])
        counts = scan_counts.get("len", [])
        for level, count in zip(ms_levels, counts):
            if level == 1:
                ms1_count = count
            elif level == 2:
                ms2_count = count

    # Create sample entry
    next_sequence = len(self.samples_df) + 1 if not self.samples_df.is_empty() else 1
    new_sample = pl.DataFrame(
        {
            "sample_uid": [int(len(self.samples_df) + 1)],
            "sample_name": [sample_name],
            "sample_path": [final_sample_path],
            "sample_type": [sample_type],
            "map_id": [map_id_value],
            "sample_source": [getattr(ddaobj, "file_source", file)],
            "sample_color": [None],  # Will be set in batch at end
            "sample_group": [""],
            "sample_batch": [1],
            "sample_sequence": [next_sequence],
            "num_features": [int(ddaobj._oms_features_map.size())],
            "num_ms1": [ms1_count],
            "num_ms2": [ms2_count],
        },
    )

    self.samples_df = pl.concat([self.samples_df, new_sample])

    # SIMPLIFIED feature processing
    current_sample_uid = len(self.samples_df)

    # Add required columns with minimal operations
    columns_to_add = [
        pl.lit(current_sample_uid).alias("sample_uid"),
        pl.lit(False).alias("filled"),
        pl.lit(-1.0).alias("chrom_area"),
    ]

    # Only add rt_original if it doesn't exist
    if "rt_original" not in ddaobj.features_df.columns:
        columns_to_add.append(pl.col("rt").alias("rt_original"))

    f_df = ddaobj.features_df.with_columns(columns_to_add)

    if self.features_df.is_empty():
        # First sample
        self.features_df = f_df.with_columns(
            pl.int_range(pl.len()).add(1).alias("feature_uid"),
        )
    else:
        # Subsequent samples - minimal overhead
        offset = self.features_df["feature_uid"].max() + 1
        f_df = f_df.with_columns(
            pl.int_range(pl.len()).add(offset).alias("feature_uid"),
        )

        # OPTIMIZED: Use diagonal concatenation without any schema enforcement
        # This is the fastest concatenation method in Polars and handles type mismatches automatically
        self.features_df = pl.concat([self.features_df, f_df], how="diagonal")

    # REMOVED ALL EXPENSIVE OPERATIONS:
    # - No _ensure_features_df_schema_order()
    # - No complex column alignment
    # - No type casting loops
    # - No set_samples_color(by=None) call needed

    self.logger.debug(
        f"Added sample {sample_name} with {ddaobj._oms_features_map.size()} features (optimized)",
    )
    return True
