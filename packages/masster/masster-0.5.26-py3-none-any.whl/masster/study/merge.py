"""
Unified merge module for the Study class.
Supports multiple merge methods: 'kd', 'qt', 'kd_chunked', 'qt_chunked'
"""

import time
import numpy as np
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm
import pyopenms as oms
import polars as pl
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from scipy.spatial import cKDTree
from masster.study.defaults import merge_defaults


def _process_kd_chunk_parallel(chunk_data):
    """
    Process a single KD chunk in parallel by reconstructing FeatureMaps from features_df slice.

    Args:
        chunk_data: Dictionary containing chunk processing parameters

    Returns:
        Tuple of (chunk_start_idx, serialized_consensus_features)
    """
    import pyopenms as oms

    chunk_start_idx = chunk_data["chunk_start_idx"]
    chunk_features_data = chunk_data["chunk_features_data"]  # List of feature dicts
    chunk_samples_data = chunk_data["chunk_samples_data"]  # List of sample dicts
    params_dict = chunk_data["params"]

    # Reconstruct FeatureMaps from features data for each sample in the chunk
    chunk_maps = []

    for sample_data in chunk_samples_data:
        sample_uid = sample_data["sample_uid"]

        # Filter features for this specific sample
        sample_features = [f for f in chunk_features_data if f["sample_uid"] == sample_uid]

        # Create FeatureMap for this sample
        feature_map = oms.FeatureMap()

        # Add each feature to the map
        for feature_dict in sample_features:
            feature = oms.Feature()
            feature.setRT(float(feature_dict["rt"]))
            feature.setMZ(float(feature_dict["mz"]))
            feature.setIntensity(float(feature_dict["inty"]))
            feature.setCharge(int(feature_dict.get("charge", 0)))

            # Set unique ID using feature_id for mapping back
            feature.setUniqueId(int(feature_dict["feature_id"]))

            feature_map.push_back(feature)

        chunk_maps.append(feature_map)

    # Create the chunk consensus map
    chunk_consensus_map = oms.ConsensusMap()

    # Set up file descriptions for chunk
    file_descriptions = chunk_consensus_map.getColumnHeaders()
    for j, (feature_map, sample_data) in enumerate(zip(chunk_maps, chunk_samples_data)):
        file_description = file_descriptions.get(j, oms.ColumnHeader())
        file_description.filename = sample_data["sample_name"]
        file_description.size = feature_map.size()
        file_description.unique_id = feature_map.getUniqueId()
        file_descriptions[j] = file_description

    chunk_consensus_map.setColumnHeaders(file_descriptions)

    # Use KD algorithm for chunk
    grouper = oms.FeatureGroupingAlgorithmKD()
    chunk_params = grouper.getParameters()
    chunk_params.setValue("mz_unit", "Da")
    chunk_params.setValue("nr_partitions", params_dict["nr_partitions"])
    chunk_params.setValue("warp:enabled", "true")
    chunk_params.setValue("warp:rt_tol", params_dict["rt_tol"])
    chunk_params.setValue("warp:mz_tol", params_dict["mz_tol"])
    chunk_params.setValue("link:rt_tol", params_dict["rt_tol"])
    chunk_params.setValue("link:mz_tol", params_dict["mz_tol"])
    chunk_params.setValue("link:min_rel_cc_size", params_dict["min_rel_cc_size"])
    chunk_params.setValue("link:max_pairwise_log_fc", params_dict["max_pairwise_log_fc"])
    chunk_params.setValue("link:max_nr_conflicts", params_dict["max_nr_conflicts"])

    grouper.setParameters(chunk_params)
    grouper.group(chunk_maps, chunk_consensus_map)

    # Serialize the consensus map result for cross-process communication
    consensus_features = []
    for consensus_feature in chunk_consensus_map:
        feature_data = {
            "rt": consensus_feature.getRT(),
            "mz": consensus_feature.getMZ(),
            "intensity": consensus_feature.getIntensity(),
            "quality": consensus_feature.getQuality(),
            "unique_id": str(consensus_feature.getUniqueId()),
            "features": [],
        }

        # Get constituent features
        for feature_handle in consensus_feature.getFeatureList():
            feature_handle_data = {
                "unique_id": str(feature_handle.getUniqueId()),
                "map_index": feature_handle.getMapIndex(),
            }
            feature_data["features"].append(feature_handle_data)

        consensus_features.append(feature_data)

    return chunk_start_idx, consensus_features


def _process_qt_chunk_parallel(chunk_data):
    """
    Process a single QT chunk in parallel by reconstructing FeatureMaps from features_df slice.

    Args:
        chunk_data: Dictionary containing chunk processing parameters

    Returns:
        Tuple of (chunk_start_idx, serialized_consensus_features)
    """
    import pyopenms as oms

    chunk_start_idx = chunk_data["chunk_start_idx"]
    chunk_features_data = chunk_data["chunk_features_data"]  # List of feature dicts
    chunk_samples_data = chunk_data["chunk_samples_data"]  # List of sample dicts
    params_dict = chunk_data["params"]

    # Reconstruct FeatureMaps from features data for each sample in the chunk
    chunk_maps = []

    for sample_data in chunk_samples_data:
        sample_uid = sample_data["sample_uid"]

        # Filter features for this specific sample
        sample_features = [f for f in chunk_features_data if f["sample_uid"] == sample_uid]

        # Create FeatureMap for this sample
        feature_map = oms.FeatureMap()

        # Add each feature to the map
        for feature_dict in sample_features:
            feature = oms.Feature()
            feature.setRT(float(feature_dict["rt"]))
            feature.setMZ(float(feature_dict["mz"]))
            feature.setIntensity(float(feature_dict["inty"]))
            feature.setCharge(int(feature_dict.get("charge", 0)))

            # Set unique ID using feature_id for mapping back
            feature.setUniqueId(int(feature_dict["feature_id"]))

            feature_map.push_back(feature)

        chunk_maps.append(feature_map)

    # Create the chunk consensus map
    chunk_consensus_map = oms.ConsensusMap()

    # Set up file descriptions for chunk
    file_descriptions = chunk_consensus_map.getColumnHeaders()
    for j, (feature_map, sample_data) in enumerate(zip(chunk_maps, chunk_samples_data)):
        file_description = file_descriptions.get(j, oms.ColumnHeader())
        file_description.filename = sample_data["sample_name"]
        file_description.size = feature_map.size()
        file_description.unique_id = feature_map.getUniqueId()
        file_descriptions[j] = file_description

    chunk_consensus_map.setColumnHeaders(file_descriptions)

    # Use QT algorithm for chunk
    grouper = oms.FeatureGroupingAlgorithmQT()
    chunk_params = grouper.getParameters()
    chunk_params.setValue("distance_RT:max_difference", params_dict["rt_tol"])
    chunk_params.setValue("distance_MZ:max_difference", params_dict["mz_tol"])
    chunk_params.setValue("distance_MZ:unit", "Da")
    chunk_params.setValue("ignore_charge", "true")
    chunk_params.setValue("nr_partitions", params_dict["nr_partitions"])

    grouper.setParameters(chunk_params)
    grouper.group(chunk_maps, chunk_consensus_map)

    # Serialize the consensus map result for cross-process communication
    consensus_features = []
    for consensus_feature in chunk_consensus_map:
        feature_data = {
            "rt": consensus_feature.getRT(),
            "mz": consensus_feature.getMZ(),
            "intensity": consensus_feature.getIntensity(),
            "quality": consensus_feature.getQuality(),
            "unique_id": str(consensus_feature.getUniqueId()),
            "features": [],
        }

        # Get constituent features
        for feature_handle in consensus_feature.getFeatureList():
            feature_handle_data = {
                "unique_id": str(feature_handle.getUniqueId()),
                "map_index": feature_handle.getMapIndex(),
            }
            feature_data["features"].append(feature_handle_data)

        consensus_features.append(feature_data)

    return chunk_start_idx, consensus_features


def merge(study, **kwargs) -> None:
    """
    Group features across samples into consensus features using various algorithms.

    This function provides a unified interface to multiple feature grouping algorithms,
    each optimized for different dataset sizes and analysis requirements.

    Parameters
    ----------
    **kwargs : dict
        Parameters from merge_defaults class:
        - method : str, default 'kd'
          Merge algorithm: 'kd', 'qt', 'kd_chunked', 'qt_chunked'
        - min_samples : int, default 2
          Minimum number of samples for consensus feature
        - rt_tol : float, default 5.0
          RT tolerance in seconds
        - mz_tol : float, default 0.01
          m/z tolerance in Da (Daltons) for all methods
        - chunk_size : int, default 500
          Chunk size for chunked methods
        - dechunking : str, default 'hierarchical'
          Cross-chunk merging algorithm: 'hierarchical', 'kdtree', 'qt', 'none'
        - threads : int, default None
          Number of parallel processes for chunked methods (None=sequential)
        - nr_partitions : int, default 1000
          Number of partitions in m/z dimension for KD algorithms
        - min_rel_cc_size : float, default 0.1
          Minimum relative connected component size for conflict resolution (chunked only)
        - max_pairwise_log_fc : float, default -1.0
          Maximum pairwise log fold change for conflict resolution (chunked only)
        - max_nr_conflicts : int, default 0
          Maximum number of conflicts allowed in consensus feature (chunked only)
        - link_ms2 : bool, default True
          Whether to link MS2 spectra to consensus features
        - extract_ms1 : bool, default True
          Whether to extract MS1 spectra for consensus features

    Algorithm Selection Guide
    ------------------------
    Choose your merge method based on dataset size and performance requirements:

    **KD (K-D Tree)** - *Recommended Default*
        - Fast O(n log n) algorithm with RT warping
        - Best balance of speed, accuracy, and memory usage
        - Suitable for most dataset sizes (50 - 5,000 samples)
        - Uses spatial partitioning for efficient feature matching

    **QT (Quality Threshold)**
        - Thorough O(n²) clustering algorithm
        - Most accurate but slowest method
        - Recommended for small datasets (<1,000 samples)
        - Guarantees quality threshold constraints

    **KD-Chunked** - *For Large Datasets*
        - Memory-optimized KD algorithm for very large datasets (>5,000 samples)
        - Processes data in chunks with cross-chunk consensus building
        - Supports parallel processing with threads parameter
        - Maintains high feature recovery through hierarchical dechunking

    **QT-Chunked** - *For Large Datasets with Maximum Accuracy*
        - Memory-optimized QT algorithm for very large datasets (>5,000 samples)
        - Uses QT clustering within chunks, then cross-chunk consensus
        - Slowest but most thorough for large datasets
        - Best when accuracy is more important than speed

    Cross-Chunk Merging (Dechunking) Methods
    ----------------------------------------
    For chunked methods, choose dechunking algorithm based on your priorities:

    **Hierarchical** - *Recommended Default*
        - Priority-based merging starting from high sample count features
        - Achieves ~97% feature recovery vs original ~10% recovery
        - Best overall balance of recovery and accuracy

    **KDTree** - *High Sample Feature Preservation*
        - Spatial indexing approach optimized for frequent features
        - ~95% high sample count feature recovery
        - Best for preserving features present in many samples

    Performance Guidelines
    ---------------------
    - **Small datasets (≤1,000 samples)**: Use 'qt' for maximum accuracy
    - **Medium datasets (1,000-5,000 samples)**: Use 'kd' (default)
    - **Large datasets (>5,000 samples)**: Use 'kd_chunked' or 'qt_chunked'
    - **Memory constrained**: Use chunked methods with smaller chunk_size
    - **Time constrained**: Use 'kd' or 'kd_chunked' with hierarchical dechunking

    Parallel Processing
    ------------------
    Chunked methods support parallel processing:
    - Set threads=N (where N is number of CPU cores to use)
    - Recommended: threads=4 to 8 for most systems
    - Each chunk is processed independently in parallel
    - Significantly reduces processing time for large datasets

    Tolerance Settings
    -----------------
    - **rt_tol**: RT tolerance in seconds (typical range: 1-10s)
      - Smaller values: more specific, may fragment features
      - Larger values: more permissive, may merge distinct features
    - **mz_tol**: m/z tolerance in Daltons (typical range: 0.005-0.05 Da)
      - High-resolution MS: 0.005-0.01 Da
      - Lower resolution MS: 0.01-0.05 Da

    Examples
    --------
    Basic usage with default KD algorithm:
        study.merge()

    High-accuracy small dataset:
        study.merge(method='qt', rt_tol=2.0, mz_tol=0.005, min_samples=5)

    Large dataset with parallel processing:
        study.merge(method='kd_chunked', threads=8, chunk_size=500,
                   dechunking='hierarchical')

    Custom tolerances for specific instrument:
        study.merge(method='kd', rt_tol=1.5, mz_tol=0.01, min_samples=10)

    Notes
    -----
    - Features must be loaded before merging (study.load_features())
    - Results are stored in study.consensus_df and study.consensus_mapping_df
    - Merge parameters are saved to study history for reproducibility
    - MS2 spectra are automatically linked when link_ms2=True
    - Adduct relationships are identified and stored after merging
    """
    # Initialize with defaults and override with kwargs
    params = merge_defaults()

    # Handle 'params' keyword argument specifically (like merge does)
    if "params" in kwargs:
        provided_params = kwargs.pop("params")
        if isinstance(provided_params, merge_defaults):
            params = provided_params
            study.logger.debug("Using provided merge_defaults parameters from 'params' argument")
        else:
            study.logger.warning("'params' argument is not an merge_defaults instance, ignoring")

    # Process remaining kwargs
    for key, value in kwargs.items():
        if isinstance(value, merge_defaults):
            params = value
            study.logger.debug("Using provided merge_defaults parameters")
        else:
            if hasattr(params, key):
                if params.set(key, value, validate=True):
                    study.logger.debug(f"Updated parameter {key} = {value}")
                else:
                    study.logger.warning(
                        f"Failed to set parameter {key} = {value} (validation failed)",
                    )
            else:
                study.logger.warning(f"Unknown parameter '{key}' ignored")

    # Backward compatibility: Map old method names to new names
    method_mapping = {
        "qtchunked": "qt_chunked",  # QT chunked variants
        "qt-chunked": "qt_chunked",
        "kdchunked": "kd_chunked",  # KD chunked variants
        "kd-chunked": "kd_chunked",
    }

    if params.method in method_mapping:
        old_method = params.method
        params.method = method_mapping[old_method]
        study.logger.info(f"Method '{old_method}' is deprecated. Using '{params.method}' instead.")

    # Validate method
    if params.method not in ["kd", "qt", "kd_chunked", "qt_chunked"]:
        raise ValueError(f"Invalid method '{params.method}'. Must be one of: ['kd', 'qt', 'kd_chunked', 'qt_chunked']")

    # Check if chunked method is advisable for large datasets
    num_samples = len(study.samples_df) if hasattr(study, "samples_df") and study.samples_df is not None else 0
    if num_samples == 0:
        raise ValueError("No samples loaded in study. Load features before merging.")
    if params.method == "kd" and num_samples > params.chunk_size:
        params.method = "kd_chunked"
        study.logger.info(
            f"Switching to chunked method for large dataset ({num_samples} samples > chunk_size {params.chunk_size})"
        )
    if params.method == "qt" and num_samples > params.chunk_size:
        params.method = "qt_chunked"
        study.logger.info(
            f"Switching to chunked method for large dataset ({num_samples} samples > chunk_size {params.chunk_size})"
        )

    if num_samples > 500:
        if params.method not in {"kd_chunked", "qt_chunked"}:
            study.logger.warning(
                f"Large dataset detected ({num_samples} samples > 500). Consider dropping chunk_size to 500 to use chunked methods."
            )

    # Persist last used params for diagnostics
    try:
        study._merge_params_last = params.to_dict()
    except Exception:
        study._merge_params_last = {}

    # Store merge parameters in history
    try:
        if hasattr(study, "store_history"):
            study.update_history(["merge"], params.to_dict())
        else:
            study.logger.warning("History storage not available - parameters not saved to history")
    except Exception as e:
        study.logger.warning(f"Failed to store merge parameters in history: {e}")

    # Ensure feature maps are available for merging (regenerate if needed)
    if len(study.features_maps) < len(study.samples_df):
        study.features_maps = []
        # Feature maps will be generated on-demand within each merge method

    study.logger.info(
        f"Merging samples using {params.method}, min_samples={params.min_samples}, rt_tol={params.rt_tol}s, mz_tol={params.mz_tol}Da"
    )
    if "chunked" in params.method:
        study.logger.info(f"threads={params.threads}, chunk_size={params.chunk_size}, dechunking='{params.dechunking}'")

    # Initialize
    study.consensus_df = pl.DataFrame()
    study.consensus_ms2 = pl.DataFrame()
    study.consensus_mapping_df = pl.DataFrame()

    # Cache adducts for performance (avoid repeated _get_adducts() calls)
    cached_adducts_df = None
    cached_valid_adducts = None
    try:
        cached_adducts_df = study._get_adducts()
        if not cached_adducts_df.is_empty():
            cached_valid_adducts = set(cached_adducts_df["name"].to_list())
        else:
            cached_valid_adducts = set()
    except Exception as e:
        study.logger.warning(f"Could not retrieve study adducts: {e}")
        cached_valid_adducts = set()

    # Always allow '?' adducts
    cached_valid_adducts.add("?")

    # Route to algorithm implementation
    if params.method == "kd":
        consensus_map = _merge_kd(study, params)
        # Extract consensus features
        _extract_consensus_features(study, consensus_map, params.min_samples, cached_adducts_df, cached_valid_adducts)
    elif params.method == "qt":
        consensus_map = _merge_qt(study, params)
        # Extract consensus features
        _extract_consensus_features(study, consensus_map, params.min_samples, cached_adducts_df, cached_valid_adducts)
    elif params.method == "kd_chunked":
        consensus_map = _merge_kd_chunked(study, params, cached_adducts_df, cached_valid_adducts)
        # Note: _merge_kd_chunked populates consensus_df directly, no need to extract
    elif params.method == "qt_chunked":
        consensus_map = _merge_qt_chunked(study, params, cached_adducts_df, cached_valid_adducts)
        # Note: _merge_qt_chunked populates consensus_df directly, no need to extract

    # Enhanced post-clustering to merge over-segmented features (for non-chunked methods)
    # Chunked methods already perform their own cross-chunk consensus building
    if params.method in ["qt", "kd"]:
        __consensus_cleanup(study, params.rt_tol, params.mz_tol)

    # Perform adduct grouping
    _perform_adduct_grouping(study, params.rt_tol, params.mz_tol)

    # Identify coeluting consensus features by mass shifts and update adduct information
    __identify_adduct_by_mass_shift(study, params.rt_tol, cached_adducts_df)

    # Post-processing for chunked methods: merge partial consensus features
    if params.method in ["qt_chunked", "kd_chunked"]:
        _merge_partial_consensus_features(study, params.rt_tol, params.mz_tol)

    # Finalize merge: filter by min_samples and add isotope/MS2 data
    __finalize_merge(study, params.link_ms2, params.extract_ms1, params.min_samples)


def _merge_kd(study, params: merge_defaults) -> oms.ConsensusMap:
    """KD-tree based merge (fast, recommended)"""

    # Generate temporary feature maps on-demand from features_df
    temp_feature_maps = _generate_feature_maps_on_demand(study)

    consensus_map = oms.ConsensusMap()
    file_descriptions = consensus_map.getColumnHeaders()

    for i, feature_map in enumerate(temp_feature_maps):
        file_description = file_descriptions.get(i, oms.ColumnHeader())
        file_description.filename = study.samples_df.row(i, named=True)["sample_name"]
        file_description.size = feature_map.size()
        file_description.unique_id = feature_map.getUniqueId()
        file_descriptions[i] = file_description

    consensus_map.setColumnHeaders(file_descriptions)

    # Configure KD algorithm
    grouper = oms.FeatureGroupingAlgorithmKD()
    params_oms = grouper.getParameters()

    params_oms.setValue("mz_unit", "Da")
    params_oms.setValue("nr_partitions", params.nr_partitions)
    params_oms.setValue("warp:enabled", "true")
    params_oms.setValue("warp:rt_tol", params.rt_tol)
    params_oms.setValue("warp:mz_tol", params.mz_tol)
    params_oms.setValue("link:rt_tol", params.rt_tol)
    params_oms.setValue("link:mz_tol", params.mz_tol)

    grouper.setParameters(params_oms)
    grouper.group(temp_feature_maps, consensus_map)

    return consensus_map


def _generate_feature_maps_on_demand(study):
    """
    Generate feature maps on-demand using Sample-level _load_ms1() for merge operations.
    Returns temporary feature maps that are not cached in the study.

    Args:
        study: Study object containing samples

    Returns:
        list: List of temporary FeatureMap objects
    """
    import polars as pl
    import pyopenms as oms
    import numpy as np

    # Check if we should use Sample-level loading instead of features_df
    use_sample_loading = True  # Default to Sample-level loading as requested

    # Use Sample-level loading if requested and samples_df is available
    # if use_sample_loading and hasattr(study, 'samples_df') and study.samples_df is not None and len(study.samples_df) > 0:
    #    study.logger.debug("Building feature maps using Sample-level _load_ms1() instead of features_df")
    #    return _generate_feature_maps_from_samples(study)

    # Fallback to original features_df approach
    if study.features_df is None or len(study.features_df) == 0:
        study.logger.error("No features_df available for generating feature maps")
        return []

    temp_feature_maps = []
    n_samples = len(study.samples_df)
    n_features = len(study.features_df)

    # Performance optimization: use efficient polars groupby for large datasets
    use_groupby_optimization = n_features > 5000
    if use_groupby_optimization:
        study.logger.debug(f"Using polars groupby optimization for {n_features} features across {n_samples} samples")

        # Pre-group features by sample_uid - this is much more efficient than repeated filtering
        features_by_sample = study.features_df.group_by("sample_uid").agg([
            pl.col("feature_id"),
            pl.col("mz"),
            pl.col("rt"),
            pl.col("inty"),
            pl.col("quality").fill_null(1.0),
            pl.col("charge").fill_null(0),
        ])

        # Convert to dictionary for fast lookups
        sample_feature_dict = {}
        for row in features_by_sample.iter_rows(named=True):
            sample_uid = row["sample_uid"]
            # Convert lists to numpy arrays for vectorized operations
            sample_feature_dict[sample_uid] = {
                "feature_id": np.array(row["feature_id"]),
                "mz": np.array(row["mz"]),
                "rt": np.array(row["rt"]),
                "inty": np.array(row["inty"]),
                "quality": np.array(row["quality"]),
                "charge": np.array(row["charge"]),
            }

    # Process each sample in order
    for sample_index, row_dict in enumerate(study.samples_df.iter_rows(named=True)):
        sample_uid = row_dict["sample_uid"]

        if use_groupby_optimization:
            # Use pre-grouped data with vectorized operations
            if sample_uid not in sample_feature_dict:
                feature_map = oms.FeatureMap()
                temp_feature_maps.append(feature_map)
                continue

            sample_data = sample_feature_dict[sample_uid]
            n_sample_features = len(sample_data["feature_id"])

            if n_sample_features == 0:
                feature_map = oms.FeatureMap()
                temp_feature_maps.append(feature_map)
                continue

            # Create new FeatureMap
            feature_map = oms.FeatureMap()

            # Use vectorized data directly (no conversion needed)
            for i in range(n_sample_features):
                try:
                    feature = oms.Feature()
                    feature.setUniqueId(int(sample_data["feature_id"][i]))
                    feature.setMZ(float(sample_data["mz"][i]))
                    feature.setRT(float(sample_data["rt"][i]))
                    feature.setIntensity(float(sample_data["inty"][i]))
                    feature.setOverallQuality(float(sample_data["quality"][i]))
                    feature.setCharge(int(sample_data["charge"][i]))
                    feature_map.push_back(feature)
                except (ValueError, TypeError) as e:
                    study.logger.warning(f"Skipping feature due to conversion error: {e}")
                    continue
        else:
            # Use original polars-based approach for smaller datasets
            sample_features = study.features_df.filter(pl.col("sample_uid") == sample_uid)

            # Create new FeatureMap
            feature_map = oms.FeatureMap()

            # Convert DataFrame features to OpenMS Features
            for feature_row in sample_features.iter_rows(named=True):
                feature = oms.Feature()

                # Set properties from DataFrame (handle missing values gracefully)
                try:
                    feature.setUniqueId(int(feature_row["feature_id"]))
                    feature.setMZ(float(feature_row["mz"]))
                    feature.setRT(float(feature_row["rt"]))
                    feature.setIntensity(float(feature_row["inty"]))
                    feature.setOverallQuality(float(feature_row["quality"]))
                    feature.setCharge(int(feature_row["charge"]))

                    # Add to feature map
                    feature_map.push_back(feature)
                except (ValueError, TypeError) as e:
                    study.logger.warning(f"Skipping feature due to conversion error: {e}")
                    continue

        temp_feature_maps.append(feature_map)

    study.logger.debug(f"Generated {len(temp_feature_maps)} temporary feature maps from features_df")
    return temp_feature_maps


def _merge_qt(study, params: merge_defaults) -> oms.ConsensusMap:
    """QT (Quality Threshold) based merge"""

    # Generate temporary feature maps on-demand from features_df
    temp_feature_maps = _generate_feature_maps_on_demand(study)

    n_samples = len(temp_feature_maps)
    if n_samples > 1000:
        study.logger.warning(f"QT with {n_samples} samples may be slow [O(n²)]. Consider KD [O(n log n)]")

    consensus_map = oms.ConsensusMap()
    file_descriptions = consensus_map.getColumnHeaders()

    for i, feature_map in enumerate(temp_feature_maps):
        file_description = file_descriptions.get(i, oms.ColumnHeader())
        file_description.filename = study.samples_df.row(i, named=True)["sample_name"]
        file_description.size = feature_map.size()
        file_description.unique_id = feature_map.getUniqueId()
        file_descriptions[i] = file_description

    consensus_map.setColumnHeaders(file_descriptions)

    # Configure QT algorithm
    grouper = oms.FeatureGroupingAlgorithmQT()
    params_oms = grouper.getParameters()

    params_oms.setValue("distance_RT:max_difference", params.rt_tol)
    params_oms.setValue("distance_MZ:max_difference", params.mz_tol)
    params_oms.setValue("distance_MZ:unit", "Da")  # QT now uses Da like all other methods
    params_oms.setValue("ignore_charge", "true")
    params_oms.setValue("nr_partitions", params.nr_partitions)

    grouper.setParameters(params_oms)
    grouper.group(temp_feature_maps, consensus_map)

    return consensus_map


def _merge_kd_chunked(
    study, params: merge_defaults, cached_adducts_df=None, cached_valid_adducts=None
) -> oms.ConsensusMap:
    """KD-based chunked merge with proper cross-chunk consensus building and optional parallel processing"""

    # Generate temporary feature maps on-demand from features_df
    temp_feature_maps = _generate_feature_maps_on_demand(study)

    n_samples = len(temp_feature_maps)
    if n_samples <= params.chunk_size:
        study.logger.info(f"Dataset size ({n_samples}) ≤ chunk_size, using KD merge")
        consensus_map = _merge_kd(study, params)
        # Extract consensus features to populate consensus_df for chunked method consistency
        _extract_consensus_features(study, consensus_map, params.min_samples, cached_adducts_df, cached_valid_adducts)
        return consensus_map

    # Process in chunks
    chunks = []
    for i in range(0, n_samples, params.chunk_size):
        chunk_end = min(i + params.chunk_size, n_samples)
        chunks.append((i, temp_feature_maps[i:chunk_end]))

    study.logger.debug(
        f"Processing {len(chunks)} chunks of max {params.chunk_size} samples using {params.threads or 'sequential'} thread(s)"
    )

    # Process each chunk to create chunk consensus maps
    chunk_consensus_maps = []

    if params.threads is None:
        # Sequential processing (original behavior)
        for chunk_idx, (chunk_start_idx, chunk_maps) in enumerate(
            tqdm(
                chunks,
                desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study.log_label}KD Chunk",
                disable=study.log_level not in ["TRACE", "DEBUG", "INFO"],
            )
        ):
            chunk_consensus_map = oms.ConsensusMap()

            # Set up file descriptions for chunk
            file_descriptions = chunk_consensus_map.getColumnHeaders()
            for j, feature_map in enumerate(chunk_maps):
                file_description = file_descriptions.get(j, oms.ColumnHeader())
                file_description.filename = study.samples_df.row(chunk_start_idx + j, named=True)["sample_name"]
                file_description.size = feature_map.size()
                file_description.unique_id = feature_map.getUniqueId()
                file_descriptions[j] = file_description

            chunk_consensus_map.setColumnHeaders(file_descriptions)

            # Use KD algorithm for chunk
            grouper = oms.FeatureGroupingAlgorithmKD()
            chunk_params = grouper.getParameters()
            chunk_params.setValue("mz_unit", "Da")
            chunk_params.setValue("nr_partitions", params.nr_partitions)
            chunk_params.setValue("warp:enabled", "true")
            chunk_params.setValue("warp:rt_tol", params.rt_tol)
            chunk_params.setValue("warp:mz_tol", params.mz_tol)
            chunk_params.setValue("link:rt_tol", params.rt_tol)
            chunk_params.setValue("link:mz_tol", params.mz_tol)
            chunk_params.setValue("link:min_rel_cc_size", params.min_rel_cc_size)
            chunk_params.setValue("link:max_pairwise_log_fc", params.max_pairwise_log_fc)
            chunk_params.setValue("link:max_nr_conflicts", params.max_nr_conflicts)

            grouper.setParameters(chunk_params)
            grouper.group(chunk_maps, chunk_consensus_map)

            chunk_consensus_maps.append((chunk_start_idx, chunk_consensus_map))

    else:
        # Parallel processing
        # study.logger.info(f"Processing chunks in parallel using {params.threads} processes")

        # Prepare chunk data for parallel processing using features_df slices
        chunk_data_list = []
        for chunk_idx, (chunk_start_idx, chunk_maps) in enumerate(chunks):
            # Get the sample UIDs for this chunk
            chunk_sample_uids = []
            chunk_samples_df_rows = []
            for j in range(len(chunk_maps)):
                sample_row = study.samples_df.row(chunk_start_idx + j, named=True)
                chunk_sample_uids.append(sample_row["sample_uid"])
                chunk_samples_df_rows.append(sample_row)

            # Create a DataFrame for this chunk's samples
            chunk_samples_df = pl.DataFrame(chunk_samples_df_rows)

            # Filter features_df for this chunk's samples and select only necessary columns
            chunk_features_df = study.features_df.filter(pl.col("sample_uid").is_in(chunk_sample_uids)).select([
                "sample_uid",
                "rt",
                "mz",
                "inty",
                "charge",
                "feature_id",
            ])

            # Convert DataFrames to serializable format (lists of dicts)
            chunk_features_data = chunk_features_df.to_dicts()
            chunk_samples_data = chunk_samples_df.to_dicts()

            chunk_data = {
                "chunk_start_idx": chunk_start_idx,
                "chunk_features_data": chunk_features_data,  # List of dicts instead of DataFrame
                "chunk_samples_data": chunk_samples_data,  # List of dicts instead of DataFrame
                "params": {
                    "nr_partitions": params.nr_partitions,
                    "rt_tol": params.rt_tol,
                    "mz_tol": params.mz_tol,
                    "min_rel_cc_size": params.min_rel_cc_size,
                    "max_pairwise_log_fc": params.max_pairwise_log_fc,
                    "max_nr_conflicts": params.max_nr_conflicts,
                },
            }
            chunk_data_list.append(chunk_data)

        # Process chunks in parallel - try ProcessPoolExecutor first, fallback to ThreadPoolExecutor on Windows
        try:
            with ProcessPoolExecutor(max_workers=params.threads) as executor:
                # Submit all chunk processing tasks
                future_to_chunk = {
                    executor.submit(_process_kd_chunk_parallel, chunk_data): i
                    for i, chunk_data in enumerate(chunk_data_list)
                }

                # Collect results with progress tracking
                completed_chunks = 0
                total_chunks = len(chunk_data_list)
                serialized_chunk_results = []

                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        chunk_start_idx, consensus_features = future.result()
                        serialized_chunk_results.append((chunk_start_idx, consensus_features))
                        completed_chunks += 1
                        n_samples_in_chunk = len(chunk_data_list[chunk_idx]["chunk_samples_data"])
                        study.logger.info(
                            f"Completed chunk {completed_chunks}/{total_chunks} (samples {chunk_start_idx + 1}-{chunk_start_idx + n_samples_in_chunk})"
                        )
                    except Exception as exc:
                        # Check if this is a BrokenProcessPool exception from Windows multiprocessing issues
                        if isinstance(exc, BrokenProcessPool) or "process pool" in str(exc).lower():
                            # Convert to RuntimeError so outer except block can catch it for fallback
                            raise RuntimeError(f"Windows multiprocessing failure: {exc}")
                        else:
                            study.logger.error(f"Chunk {chunk_idx} generated an exception: {exc}")
                            raise exc

        except (RuntimeError, OSError, BrokenProcessPool) as e:
            # Handle Windows multiprocessing issues - fallback to ThreadPoolExecutor
            if (
                "freeze_support" in str(e)
                or "spawn" in str(e)
                or "bootstrapping" in str(e)
                or "process pool" in str(e).lower()
                or "Windows multiprocessing failure" in str(e)
            ):
                study.logger.warning(f"ProcessPoolExecutor failed (likely Windows multiprocessing issue): {e}")
                study.logger.info(f"Falling back to ThreadPoolExecutor with {params.threads} threads")

                with ThreadPoolExecutor(max_workers=params.threads) as executor:
                    # Submit all chunk processing tasks
                    future_to_chunk = {
                        executor.submit(_process_kd_chunk_parallel, chunk_data): i
                        for i, chunk_data in enumerate(chunk_data_list)
                    }

                    # Collect results with progress tracking
                    completed_chunks = 0
                    total_chunks = len(chunk_data_list)
                    serialized_chunk_results = []

                    for future in as_completed(future_to_chunk):
                        chunk_idx = future_to_chunk[future]
                        try:
                            chunk_start_idx, consensus_features = future.result()
                            serialized_chunk_results.append((chunk_start_idx, consensus_features))
                            completed_chunks += 1
                            n_samples_in_chunk = len(chunk_data_list[chunk_idx]["chunk_samples_data"])
                            study.logger.info(
                                f"Completed chunk {completed_chunks}/{total_chunks} (samples {chunk_start_idx + 1}-{chunk_start_idx + n_samples_in_chunk})"
                            )
                        except Exception as exc:
                            study.logger.error(f"Chunk {chunk_idx} generated an exception: {exc}")
                            raise exc
            else:
                # Re-raise other exceptions
                raise

        # Store serialized results for _merge_chunk_results to handle directly
        chunk_consensus_maps = []
        for chunk_start_idx, consensus_features in sorted(serialized_chunk_results):
            # Store serialized data directly for _merge_chunk_results to handle
            chunk_consensus_maps.append((chunk_start_idx, consensus_features))

    # Merge chunk results with proper cross-chunk consensus building
    # _merge_chunk_results now handles both ConsensusMap objects (sequential) and serialized data (parallel)
    _dechunk_results(study, chunk_consensus_maps, params, cached_adducts_df, cached_valid_adducts)

    # Return a dummy consensus map for compatibility (consensus features are stored in study.consensus_df)
    consensus_map = oms.ConsensusMap()
    return consensus_map


def _merge_qt_chunked(
    study, params: merge_defaults, cached_adducts_df=None, cached_valid_adducts=None
) -> oms.ConsensusMap:
    """QT-based chunked merge with proper cross-chunk consensus building and optional parallel processing"""

    # Generate temporary feature maps on-demand from features_df
    temp_feature_maps = _generate_feature_maps_on_demand(study)

    n_samples = len(temp_feature_maps)
    if n_samples <= params.chunk_size:
        study.logger.info(f"Dataset size ({n_samples}) ≤ chunk_size, using QT merge")
        consensus_map = _merge_qt(study, params)
        # Extract consensus features to populate consensus_df for chunked method consistency
        _extract_consensus_features(study, consensus_map, params.min_samples, cached_adducts_df, cached_valid_adducts)
        return consensus_map

    # Process in chunks
    chunks = []
    for i in range(0, n_samples, params.chunk_size):
        chunk_end = min(i + params.chunk_size, n_samples)
        chunks.append((i, temp_feature_maps[i:chunk_end]))

    study.logger.debug(
        f"Processing {len(chunks)} chunks of max {params.chunk_size} samples using {params.threads or 'sequential'} thread(s)"
    )

    # Process each chunk to create chunk consensus maps
    chunk_consensus_maps = []

    if params.threads is None:
        # Sequential processing (original behavior)
        for chunk_idx, (chunk_start_idx, chunk_maps) in enumerate(
            tqdm(
                chunks,
                desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study.log_label}QT Chunk",
                disable=study.log_level not in ["TRACE", "DEBUG", "INFO"],
            )
        ):
            chunk_consensus_map = oms.ConsensusMap()

            # Set up file descriptions for chunk
            file_descriptions = chunk_consensus_map.getColumnHeaders()
            for j, feature_map in enumerate(chunk_maps):
                file_description = file_descriptions.get(j, oms.ColumnHeader())
                file_description.filename = study.samples_df.row(chunk_start_idx + j, named=True)["sample_name"]
                file_description.size = feature_map.size()
                file_description.unique_id = feature_map.getUniqueId()
                file_descriptions[j] = file_description

            chunk_consensus_map.setColumnHeaders(file_descriptions)

            # Use QT algorithm for chunk (main difference from KD chunked)
            grouper = oms.FeatureGroupingAlgorithmQT()
            chunk_params = grouper.getParameters()
            chunk_params.setValue("distance_RT:max_difference", params.rt_tol)
            chunk_params.setValue("distance_MZ:max_difference", params.mz_tol)
            chunk_params.setValue("distance_MZ:unit", "Da")
            chunk_params.setValue("ignore_charge", "true")
            chunk_params.setValue("nr_partitions", params.nr_partitions)

            grouper.setParameters(chunk_params)
            grouper.group(chunk_maps, chunk_consensus_map)

            chunk_consensus_maps.append((chunk_start_idx, chunk_consensus_map))

    else:
        # Parallel processing
        # study.logger.info(f"Processing chunks in parallel using {params.threads} processes")

        # Prepare chunk data for parallel processing using features_df slices
        chunk_data_list = []
        for chunk_idx, (chunk_start_idx, chunk_maps) in enumerate(chunks):
            # Get the sample UIDs for this chunk
            chunk_sample_uids = []
            chunk_samples_df_rows = []
            for j in range(len(chunk_maps)):
                sample_row = study.samples_df.row(chunk_start_idx + j, named=True)
                chunk_sample_uids.append(sample_row["sample_uid"])
                chunk_samples_df_rows.append(sample_row)

            # Create a DataFrame for this chunk's samples
            chunk_samples_df = pl.DataFrame(chunk_samples_df_rows)

            # Filter features_df for this chunk's samples and select only necessary columns
            chunk_features_df = study.features_df.filter(pl.col("sample_uid").is_in(chunk_sample_uids)).select([
                "sample_uid",
                "rt",
                "mz",
                "inty",
                "charge",
                "feature_id",
            ])

            # Convert DataFrames to serializable format (lists of dicts)
            chunk_features_data = chunk_features_df.to_dicts()
            chunk_samples_data = chunk_samples_df.to_dicts()

            chunk_data = {
                "chunk_start_idx": chunk_start_idx,
                "chunk_features_data": chunk_features_data,  # List of dicts instead of DataFrame
                "chunk_samples_data": chunk_samples_data,  # List of dicts instead of DataFrame
                "params": {
                    "nr_partitions": params.nr_partitions,
                    "rt_tol": params.rt_tol,
                    "mz_tol": params.mz_tol,
                },
            }
            chunk_data_list.append(chunk_data)

        # Process chunks in parallel - try ProcessPoolExecutor first, fallback to ThreadPoolExecutor on Windows
        executor_class = ProcessPoolExecutor
        executor_name = "processes"

        try:
            with ProcessPoolExecutor(max_workers=params.threads) as executor:
                # Submit all chunk processing tasks
                future_to_chunk = {
                    executor.submit(_process_qt_chunk_parallel, chunk_data): i
                    for i, chunk_data in enumerate(chunk_data_list)
                }

                # Collect results with progress tracking
                completed_chunks = 0
                total_chunks = len(chunk_data_list)
                serialized_chunk_results = []

                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        chunk_start_idx, consensus_features = future.result()
                        serialized_chunk_results.append((chunk_start_idx, consensus_features))
                        completed_chunks += 1
                        n_samples_in_chunk = len(chunk_data_list[chunk_idx]["chunk_samples_data"])
                        study.logger.info(
                            f"Completed chunk {completed_chunks}/{total_chunks} (samples {chunk_start_idx + 1}-{chunk_start_idx + n_samples_in_chunk})"
                        )
                    except Exception as exc:
                        # Check if this is a BrokenProcessPool exception from Windows multiprocessing issues
                        if isinstance(exc, BrokenProcessPool) or "process pool" in str(exc).lower():
                            # Convert to RuntimeError so outer except block can catch it for fallback
                            raise RuntimeError(f"Windows multiprocessing failure: {exc}")
                        else:
                            study.logger.error(f"Chunk {chunk_idx} generated an exception: {exc}")
                            raise exc

        except (RuntimeError, OSError, BrokenProcessPool) as e:
            # Handle Windows multiprocessing issues - fallback to ThreadPoolExecutor
            if (
                "freeze_support" in str(e)
                or "spawn" in str(e)
                or "bootstrapping" in str(e)
                or "process pool" in str(e).lower()
                or "Windows multiprocessing failure" in str(e)
            ):
                study.logger.warning(f"ProcessPoolExecutor failed (likely Windows multiprocessing issue): {e}")
                study.logger.info(f"Falling back to ThreadPoolExecutor with {params.threads} threads")

                with ThreadPoolExecutor(max_workers=params.threads) as executor:
                    # Submit all chunk processing tasks
                    future_to_chunk = {
                        executor.submit(_process_qt_chunk_parallel, chunk_data): i
                        for i, chunk_data in enumerate(chunk_data_list)
                    }

                    # Collect results with progress tracking
                    completed_chunks = 0
                    total_chunks = len(chunk_data_list)
                    serialized_chunk_results = []

                    for future in as_completed(future_to_chunk):
                        chunk_idx = future_to_chunk[future]
                        try:
                            chunk_start_idx, consensus_features = future.result()
                            serialized_chunk_results.append((chunk_start_idx, consensus_features))
                            completed_chunks += 1
                            n_samples_in_chunk = len(chunk_data_list[chunk_idx]["chunk_samples_data"])
                            study.logger.info(
                                f"Completed chunk {completed_chunks}/{total_chunks} (samples {chunk_start_idx + 1}-{chunk_start_idx + n_samples_in_chunk})"
                            )
                        except Exception as exc:
                            study.logger.error(f"Chunk {chunk_idx} generated an exception: {exc}")
                            raise exc
            else:
                # Re-raise other exceptions
                raise

        # Store serialized results for _merge_chunk_results to handle directly
        chunk_consensus_maps = []
        for chunk_start_idx, consensus_features in sorted(serialized_chunk_results):
            # Store serialized data directly for _merge_chunk_results to handle
            chunk_consensus_maps.append((chunk_start_idx, consensus_features))

    # Merge chunk results with proper cross-chunk consensus building
    # _merge_chunk_results now handles both ConsensusMap objects (sequential) and serialized data (parallel)
    _dechunk_results(study, chunk_consensus_maps, params, cached_adducts_df, cached_valid_adducts)

    # Return a dummy consensus map for compatibility (consensus features are stored in study.consensus_df)
    consensus_map = oms.ConsensusMap()
    return consensus_map


def _dechunk_results(
    study, chunk_consensus_maps: list, params: merge_defaults, cached_adducts_df=None, cached_valid_adducts=None
) -> None:
    """
    Scalable aggregation of chunk consensus maps into final consensus_df.

    This function implements cross-chunk consensus building by:
    1. Extracting feature_uids from each chunk consensus map
    2. Aggregating features close in RT/m/z across chunks
    3. Building consensus_df and consensus_mapping_df directly
    """

    if len(chunk_consensus_maps) == 1:
        # Single chunk case - just extract using the true global min_samples.
        # No need for permissive threshold because we are not discarding singletons pre-aggregation.
        _extract_consensus_features(
            study,
            chunk_consensus_maps[0][1],
            params.min_samples,
            cached_adducts_df,
            cached_valid_adducts,
        )
        return

    # Build feature_uid to feature_data lookup for fast access
    feature_uid_map = {row["feature_id"]: row["feature_uid"] for row in study.features_df.iter_rows(named=True)}

    features_lookup = __merge_feature_lookup(study, study.features_df)

    # Extract all consensus features from chunks with their feature_uids
    all_chunk_consensus = []
    consensus_id_counter = 0

    for chunk_idx, (chunk_start_idx, chunk_data) in enumerate(chunk_consensus_maps):
        # Handle both ConsensusMap objects (sequential) and serialized data (parallel)
        if isinstance(chunk_data, list):
            # Parallel processing: chunk_data is a list of serialized consensus feature dictionaries
            consensus_features_data = chunk_data
        else:
            # Sequential processing: chunk_data is a ConsensusMap object
            chunk_consensus_map = chunk_data
            consensus_features_data = []

            # Extract data from ConsensusMap and convert to serialized format
            for consensus_feature in chunk_consensus_map:
                # Extract feature_uids from this consensus feature
                feature_uids = []
                feature_data_list = []
                sample_uids = []

                for feature_handle in consensus_feature.getFeatureList():
                    fuid = str(feature_handle.getUniqueId())
                    if fuid not in feature_uid_map:
                        continue

                    feature_uid = feature_uid_map[fuid]
                    feature_data = features_lookup.get(feature_uid)
                    if feature_data:
                        feature_uids.append(feature_uid)
                        feature_data_list.append(feature_data)

                        # Use feature_uid to lookup actual sample_uid instead of chunk position
                        actual_sample_uid = feature_data["sample_uid"]
                        sample_uids.append(actual_sample_uid)

                if not feature_data_list:
                    # No retrievable feature metadata (possible stale map reference) -> skip
                    continue

                # Convert ConsensusFeature to serialized format
                consensus_feature_data = {
                    "rt": consensus_feature.getRT(),
                    "mz": consensus_feature.getMZ(),
                    "intensity": consensus_feature.getIntensity(),
                    "quality": consensus_feature.getQuality(),
                    "feature_uids": feature_uids,
                    "feature_data_list": feature_data_list,
                    "sample_uids": sample_uids,
                }
                consensus_features_data.append(consensus_feature_data)

        # Process the consensus features (now all in serialized format)
        for consensus_feature_data in consensus_features_data:
            # For parallel processing, feature data is already extracted
            if isinstance(chunk_data, list):
                # Extract feature_uids and data from serialized format for parallel processing
                feature_uids = []
                feature_data_list = []
                sample_uids = []

                for handle_data in consensus_feature_data["features"]:
                    fuid = str(handle_data["unique_id"])
                    if fuid not in feature_uid_map:
                        continue

                    feature_uid = feature_uid_map[fuid]
                    feature_data = features_lookup.get(feature_uid)
                    if feature_data:
                        feature_uids.append(feature_uid)
                        feature_data_list.append(feature_data)

                        # Use feature_uid to lookup actual sample_uid instead of chunk position
                        actual_sample_uid = feature_data["sample_uid"]
                        sample_uids.append(actual_sample_uid)

                if not feature_data_list:
                    continue

                # Get RT/MZ from consensus feature data
                consensus_rt = consensus_feature_data["rt"]
                consensus_mz = consensus_feature_data["mz"]
                consensus_intensity = consensus_feature_data["intensity"]
                consensus_quality = consensus_feature_data["quality"]
            else:
                # Sequential processing: data is already extracted above
                feature_uids = consensus_feature_data["feature_uids"]
                feature_data_list = consensus_feature_data["feature_data_list"]
                sample_uids = consensus_feature_data["sample_uids"]
                consensus_rt = consensus_feature_data["rt"]
                consensus_mz = consensus_feature_data["mz"]
                consensus_intensity = consensus_feature_data["intensity"]
                consensus_quality = consensus_feature_data["quality"]

            if not feature_data_list:
                # No retrievable feature metadata (possible stale map reference) -> skip
                continue

            # Derive RT / m/z ranges from underlying features (used for robust cross-chunk stitching)
            rt_vals_local = [fd.get("rt") for fd in feature_data_list if fd.get("rt") is not None]
            mz_vals_local = [fd.get("mz") for fd in feature_data_list if fd.get("mz") is not None]
            if rt_vals_local:
                rt_min_local = min(rt_vals_local)
                rt_max_local = max(rt_vals_local)
            else:
                rt_min_local = rt_max_local = consensus_rt
            if mz_vals_local:
                mz_min_local = min(mz_vals_local)
                mz_max_local = max(mz_vals_local)
            else:
                mz_min_local = mz_max_local = consensus_mz

            # Store chunk consensus with feature tracking
            # Generate unique 16-character consensus_id string
            import uuid

            consensus_id_str = str(uuid.uuid4()).replace("-", "")[:16]

            chunk_consensus_data = {
                "consensus_id": consensus_id_str,
                "chunk_idx": chunk_idx,
                "chunk_start_idx": chunk_start_idx,
                "mz": consensus_mz,
                "rt": consensus_rt,
                "mz_min": mz_min_local,
                "mz_max": mz_max_local,
                "rt_min": rt_min_local,
                "rt_max": rt_max_local,
                "intensity": consensus_intensity,
                "quality": consensus_quality,
                "feature_uids": feature_uids,
                "feature_data_list": feature_data_list,
                "sample_uids": sample_uids,
                "sample_count": len(feature_data_list),
            }

            all_chunk_consensus.append(chunk_consensus_data)

    if not all_chunk_consensus:
        # No valid consensus features found
        study.consensus_df = pl.DataFrame()
        study.consensus_mapping_df = pl.DataFrame()
        return

    # CROSS-CHUNK DECHUNKING ALGORITHMS
    # Multiple algorithms available for combining chunk results

    class HierarchicalAnchorMerger:
        """
        Hierarchical Anchor Merger: Comprehensive cross-chunk feature preservation.
        Uses Union-Find clustering for transitive matching across multiple chunks.
        """

        def __init__(self, rt_tol: float, mz_tol: float):
            self.rt_tol = rt_tol
            self.mz_tol = mz_tol

        def merge(self, chunk_consensus_list: list) -> list:
            """Fixed hierarchical merging with union-find clustering for complete feature preservation"""
            if not chunk_consensus_list:
                return []

            study.logger.debug(f"FIXED HierarchicalAnchorMerger: processing {len(chunk_consensus_list)} chunk features")

            # Union-Find data structure for transitive clustering
            class UnionFind:
                def __init__(self, n):
                    self.parent = list(range(n))
                    self.rank = [0] * n

                def find(self, x):
                    if self.parent[x] != x:
                        self.parent[x] = self.find(self.parent[x])  # Path compression
                    return self.parent[x]

                def union(self, x, y):
                    px, py = self.find(x), self.find(y)
                    if px == py:
                        return False  # Already in same component
                    # Union by rank for balanced trees
                    if self.rank[px] < self.rank[py]:
                        px, py = py, px
                    self.parent[py] = px
                    if self.rank[px] == self.rank[py]:
                        self.rank[px] += 1
                    return True  # Union was performed

            n_features = len(chunk_consensus_list)
            uf = UnionFind(n_features)
            merges_made = 0

            # Optimized cross-chunk feature matching using KD-tree spatial indexing

            # Proper dimensional scaling for RT vs m/z
            rt_scale = 1.0  # RT in seconds (1-30 min range)
            mz_scale = 100.0  # m/z in Da (100-1000 range) - scale to match RT magnitude

            # Build spatial index with scaled coordinates
            points = np.array([[f["rt"] * rt_scale, f["mz"] * mz_scale] for f in chunk_consensus_list])
            tree = cKDTree(points, balanced_tree=True, compact_nodes=True)

            # Calculate proper Euclidean radius in scaled space
            scaled_rt_tol = self.rt_tol * rt_scale
            scaled_mz_tol = self.mz_tol * mz_scale
            radius = np.sqrt(scaled_rt_tol**2 + scaled_mz_tol**2)

            # Efficient neighbor search for feature matching
            for i in range(n_features):
                feature_i = chunk_consensus_list[i]
                chunk_i = feature_i.get("chunk_idx", -1)

                # Query spatial index for nearby features
                neighbor_indices = tree.query_ball_point(points[i], r=radius, p=2)

                for j in neighbor_indices:
                    if i >= j:  # Skip duplicates and self
                        continue

                    feature_j = chunk_consensus_list[j]
                    chunk_j = feature_j.get("chunk_idx", -1)

                    # Skip features from same chunk (already clustered within chunk)
                    if chunk_i == chunk_j:
                        continue

                    # Verify with precise original tolerances (more accurate than scaled)
                    rt_diff = abs(feature_i["rt"] - feature_j["rt"])
                    mz_diff = abs(feature_i["mz"] - feature_j["mz"])

                    if rt_diff <= self.rt_tol and mz_diff <= self.mz_tol:
                        if uf.union(i, j):  # Merge if not already connected
                            merges_made += 1

            study.logger.debug(f"FIXED HierarchicalAnchorMerger: made {merges_made} cross-chunk merges")

            # Group features by their connected component
            clusters = {}
            for i in range(n_features):
                root = uf.find(i)
                if root not in clusters:
                    clusters[root] = []
                clusters[root].append(chunk_consensus_list[i])

            # Merge each cluster into a single consensus feature
            result = []
            for cluster_features in clusters.values():
                merged = self._merge_cluster(cluster_features)
                result.append(merged)

            study.logger.debug(
                f"FIXED HierarchicalAnchorMerger: output {len(result)} merged features (from {n_features} inputs)"
            )

            # VERIFICATION: Ensure we haven't lost features
            if len(result) > len(chunk_consensus_list):
                study.logger.warning(
                    f"FIXED HierarchicalAnchorMerger: More outputs than inputs ({len(result)} > {n_features})"
                )

            return result

        def _merge_cluster(self, cluster: list) -> dict:
            """Merge cluster using sample-weighted consensus with robust error handling"""
            if len(cluster) == 1:
                return cluster[0]  # No merging needed for single feature

            # Calculate weights robustly to prevent division by zero
            weights = []
            for c in cluster:
                sample_count = c.get("sample_count", 0)
                # Use minimum weight of 1 to prevent zero weights
                weights.append(max(sample_count, 1))

            total_weight = sum(weights)
            # Fallback for edge cases
            if total_weight == 0:
                total_weight = len(cluster)
                weights = [1] * len(cluster)

            # Weighted consensus for RT/mz coordinates
            merged = {
                "consensus_id": cluster[0]["consensus_id"],  # Use first feature's ID
                "chunk_indices": [c.get("chunk_idx", 0) for c in cluster],
                "mz": sum(c["mz"] * w for c, w in zip(cluster, weights)) / total_weight,
                "rt": sum(c["rt"] * w for c, w in zip(cluster, weights)) / total_weight,
                "intensity": sum(c.get("intensity", 0) for c in cluster),
                "quality": sum(c.get("quality", 1) * w for c, w in zip(cluster, weights)) / total_weight,
                "feature_uids": [],
                "feature_data_list": [],
                "sample_uids": [],
                "sample_count": 0,
            }

            # Aggregate all features and samples from all chunks
            all_feature_uids = []
            all_feature_data = []
            all_sample_uids = []

            for chunk in cluster:
                # Collect feature UIDs
                chunk_feature_uids = chunk.get("feature_uids", [])
                all_feature_uids.extend(chunk_feature_uids)

                # Collect feature data
                chunk_feature_data = chunk.get("feature_data_list", [])
                all_feature_data.extend(chunk_feature_data)

                # Collect sample UIDs
                chunk_sample_uids = chunk.get("sample_uids", [])
                all_sample_uids.extend(chunk_sample_uids)

            # Remove duplicates properly and count unique samples
            merged["feature_uids"] = list(set(all_feature_uids))
            merged["feature_data_list"] = all_feature_data  # Keep all feature data
            merged["sample_uids"] = list(set(all_sample_uids))  # Unique sample UIDs only
            merged["sample_count"] = len(merged["sample_uids"])  # Count of unique samples

            return merged

    class KDTreeSpatialMerger:
        """
        KD-Tree Spatial Merger: Optimized for high-sample features.
        """

        def __init__(self, rt_tol: float, mz_tol: float):
            self.rt_tol = rt_tol
            self.mz_tol = mz_tol

        def merge(self, chunk_consensus_list: list) -> list:
            """KD-tree based spatial merging"""
            if not chunk_consensus_list:
                return []

            try:
                from scipy.spatial import cKDTree
                import numpy as np
            except ImportError:
                # Fallback to simple clustering if scipy not available
                return self._fallback_merge(chunk_consensus_list)

            # Build spatial index
            points = np.array([[c["rt"], c["mz"]] for c in chunk_consensus_list])
            tree = cKDTree(points)

            # Scale tolerances for KD-tree query
            rt_scale = 1.0 / self.rt_tol if self.rt_tol > 0 else 1.0
            mz_scale = 1.0 / self.mz_tol if self.mz_tol > 0 else 1.0
            scaled_points = points * np.array([rt_scale, mz_scale])
            scaled_tree = cKDTree(scaled_points)

            clusters = []
            used = set()

            # Priority processing for high-sample features
            high_sample_indices = [i for i, c in enumerate(chunk_consensus_list) if c["sample_count"] >= 100]
            remaining_indices = [i for i in range(len(chunk_consensus_list)) if i not in high_sample_indices]

            for idx in high_sample_indices + remaining_indices:
                if idx in used:
                    continue

                # Find neighbors in scaled space
                neighbors = scaled_tree.query_ball_point(scaled_points[idx], r=1.0)
                cluster_indices = [i for i in neighbors if i not in used and i != idx]
                cluster_indices.append(idx)

                if cluster_indices:
                    cluster = [chunk_consensus_list[i] for i in cluster_indices]
                    clusters.append(self._merge_cluster(cluster))
                    used.update(cluster_indices)

            return clusters

        def _fallback_merge(self, chunk_consensus_list: list) -> list:
            """Simple distance-based fallback when scipy unavailable"""
            clusters = []
            used = set()

            for i, anchor in enumerate(chunk_consensus_list):
                if i in used:
                    continue

                cluster = [anchor]
                used.add(i)

                for j, candidate in enumerate(chunk_consensus_list):
                    if j in used or j == i:
                        continue

                    rt_diff = abs(candidate["rt"] - anchor["rt"])
                    mz_diff = abs(candidate["mz"] - anchor["mz"])

                    if rt_diff <= self.rt_tol and mz_diff <= self.mz_tol:
                        cluster.append(candidate)
                        used.add(j)

                clusters.append(self._merge_cluster(cluster))

            return clusters

        def _merge_cluster(self, cluster: list) -> dict:
            """Merge cluster with intensity-weighted consensus"""
            if len(cluster) == 1:
                return cluster[0]

            # Weight by intensity for spatial accuracy
            total_intensity = sum(c["intensity"] for c in cluster)

            merged = {
                "consensus_id": cluster[0]["consensus_id"],
                "chunk_indices": [c["chunk_idx"] for c in cluster],
                "mz": sum(c["mz"] * c["intensity"] for c in cluster) / total_intensity,
                "rt": sum(c["rt"] * c["intensity"] for c in cluster) / total_intensity,
                "intensity": total_intensity,
                "quality": sum(c["quality"] for c in cluster) / len(cluster),
                "feature_uids": [],
                "feature_data_list": [],
                "sample_uids": [],
                "sample_count": 0,
            }

            # Aggregate features
            for chunk in cluster:
                merged["feature_uids"].extend(chunk["feature_uids"])
                merged["feature_data_list"].extend(chunk["feature_data_list"])
                merged["sample_uids"].extend(chunk["sample_uids"])

            merged["feature_uids"] = list(set(merged["feature_uids"]))
            merged["sample_count"] = len(set(merged["sample_uids"]))

            return merged

    # SELECT DECHUNKING ALGORITHM BASED ON PARAMETER
    if params.dechunking == "hierarchical":
        merger = HierarchicalAnchorMerger(params.rt_tol, params.mz_tol)
        final_consensus = merger.merge(all_chunk_consensus)
    elif params.dechunking == "kdtree":
        merger = KDTreeSpatialMerger(params.rt_tol, params.mz_tol)
        final_consensus = merger.merge(all_chunk_consensus)
    else:
        raise ValueError(f"Invalid dechunking method '{params.dechunking}'. Must be one of: ['hierarchical', 'kdtree']")

    # --- Stage 1: Cross-chunk clustering using selected dechunking algorithm ---
    # New algorithms return final consensus features, no further refinement needed
    # Convert each merged consensus feature to a "group" of one feature for compatibility
    refined_groups = [[feature] for feature in final_consensus]
    consensus_metadata = []
    consensus_mapping_list = []
    consensus_uid_counter = 0

    for group in refined_groups:
        if not group:
            continue

        # Aggregate underlying feature data (deduplicated by feature_uid)
        feature_data_acc = {}
        sample_uids_acc = set()
        rt_values_chunk = []  # use chunk-level centroids for statistic helper
        mz_values_chunk = []
        intensity_values_chunk = []
        quality_values_chunk = []

        for cf in group:
            rt_values_chunk.append(cf["rt"])
            mz_values_chunk.append(cf["mz"])
            intensity_values_chunk.append(cf.get("intensity", 0.0) or 0.0)
            quality_values_chunk.append(cf.get("quality", 1.0) or 1.0)

            for fd, samp_uid in zip(cf["feature_data_list"], cf["sample_uids"]):
                fid = fd.get("feature_uid") or fd.get("uid") or fd.get("feature_id")
                # feature_uid expected in fd under 'feature_uid'; fallback attempts just in case
                if fid is None:
                    continue
                if fid not in feature_data_acc:
                    feature_data_acc[fid] = fd
                sample_uids_acc.add(samp_uid)

        if not feature_data_acc:
            continue

        number_samples = len(sample_uids_acc)

        # This allows proper cross-chunk consensus building before final filtering

        metadata = _calculate_consensus_statistics(
            study,
            consensus_uid_counter,
            list(feature_data_acc.values()),
            rt_values_chunk,
            mz_values_chunk,
            intensity_values_chunk,
            quality_values_chunk,
            number_features=len(feature_data_acc),
            number_samples=number_samples,
            cached_adducts_df=cached_adducts_df,
            cached_valid_adducts=cached_valid_adducts,
        )

        # Validate RT and m/z spread don't exceed tolerance limits
        rt_spread = metadata.get("rt_max", 0) - metadata.get("rt_min", 0)
        mz_spread = metadata.get("mz_max", 0) - metadata.get("mz_min", 0)
        max_allowed_rt_spread = params.rt_tol * 2  # Allow 2x tolerance for chunked method
        max_allowed_mz_spread = params.mz_tol * 2  # Enforce strict m/z spread limit

        skip_feature = False
        skip_reason = ""

        if rt_spread > max_allowed_rt_spread:
            skip_feature = True
            skip_reason = f"RT spread {rt_spread:.3f}s > {max_allowed_rt_spread:.3f}s"

        if mz_spread > max_allowed_mz_spread:
            skip_feature = True
            if skip_reason:
                skip_reason += f" AND m/z spread {mz_spread:.4f} Da > {max_allowed_mz_spread:.4f} Da"
            else:
                skip_reason = f"m/z spread {mz_spread:.4f} Da > {max_allowed_mz_spread:.4f} Da"

        if skip_feature:
            # Skip consensus features with excessive spread
            study.logger.debug(f"Skipping consensus feature {consensus_uid_counter}: {skip_reason}")
            consensus_uid_counter += 1
            continue

        consensus_metadata.append(metadata)

        # Build mapping rows (deduplicated)
        for fid, fd in feature_data_acc.items():
            samp_uid = fd.get("sample_uid") or fd.get("sample_id") or fd.get("sample")

            # If absent we attempt to derive from original group sample_uids pairing
            # but most feature_data rows should include sample_uid already.
            if samp_uid is None:
                # fallback: search for cf containing this fid
                for cf in group:
                    for fd2, samp2 in zip(cf["feature_data_list"], cf["sample_uids"]):
                        f2id = fd2.get("feature_uid") or fd2.get("uid") or fd2.get("feature_id")
                        if f2id == fid:
                            samp_uid = samp2
                            break
                    if samp_uid is not None:
                        break
            if samp_uid is None:
                continue
            consensus_mapping_list.append({
                "consensus_uid": consensus_uid_counter,
                "sample_uid": samp_uid,
                "feature_uid": fid,
            })

        consensus_uid_counter += 1

    # Assign DataFrames
    study.consensus_df = pl.DataFrame(consensus_metadata, strict=False)
    study.consensus_mapping_df = pl.DataFrame(consensus_mapping_list, strict=False)

    # Ensure mapping only contains features from retained consensus_df
    if len(study.consensus_df) > 0:
        valid_consensus_ids = set(study.consensus_df["consensus_uid"].to_list())
        study.consensus_mapping_df = study.consensus_mapping_df.filter(
            pl.col("consensus_uid").is_in(list(valid_consensus_ids))
        )
    else:
        study.consensus_mapping_df = pl.DataFrame()

    # Attach empty consensus_map placeholder for downstream compatibility
    study.consensus_map = oms.ConsensusMap()
    return


def _calculate_consensus_statistics(
    study_obj,
    consensus_uid: int,
    feature_data_list: list,
    rt_values: list,
    mz_values: list,
    intensity_values: list,
    quality_values: list,
    number_features: int | None = None,
    number_samples: int | None = None,
    cached_adducts_df=None,
    cached_valid_adducts=None,
) -> dict:
    """
    Calculate comprehensive statistics for a consensus feature from aggregated feature data.

    Args:
        consensus_uid: Unique ID for this consensus feature
        feature_data_list: List of individual feature dictionaries
        rt_values: RT values from chunk consensus features
        mz_values: m/z values from chunk consensus features
        intensity_values: Intensity values from chunk consensus features
        quality_values: Quality values from chunk consensus features

    Returns:
        Dictionary with consensus feature metadata
    """
    if not feature_data_list:
        return {}

    # Convert feature data to numpy arrays for vectorized computation
    rt_feat_values = np.array([fd.get("rt", 0) for fd in feature_data_list if fd.get("rt") is not None])
    mz_feat_values = np.array([fd.get("mz", 0) for fd in feature_data_list if fd.get("mz") is not None])
    rt_start_values = np.array([fd.get("rt_start", 0) for fd in feature_data_list if fd.get("rt_start") is not None])
    rt_end_values = np.array([fd.get("rt_end", 0) for fd in feature_data_list if fd.get("rt_end") is not None])
    rt_delta_values = np.array([fd.get("rt_delta", 0) for fd in feature_data_list if fd.get("rt_delta") is not None])
    mz_start_values = np.array([fd.get("mz_start", 0) for fd in feature_data_list if fd.get("mz_start") is not None])
    mz_end_values = np.array([fd.get("mz_end", 0) for fd in feature_data_list if fd.get("mz_end") is not None])
    inty_values = np.array([fd.get("inty", 0) for fd in feature_data_list if fd.get("inty") is not None])
    coherence_values = np.array([
        fd.get("chrom_coherence", 0) for fd in feature_data_list if fd.get("chrom_coherence") is not None
    ])
    prominence_values = np.array([
        fd.get("chrom_prominence", 0) for fd in feature_data_list if fd.get("chrom_prominence") is not None
    ])
    prominence_scaled_values = np.array([
        fd.get("chrom_height_scaled", 0) for fd in feature_data_list if fd.get("chrom_height_scaled") is not None
    ])
    height_scaled_values = np.array([
        fd.get("chrom_prominence_scaled", 0)
        for fd in feature_data_list
        if fd.get("chrom_prominence_scaled") is not None
    ])
    iso_values = np.array([fd.get("iso", 0) for fd in feature_data_list if fd.get("iso") is not None])
    charge_values = np.array([fd.get("charge", 0) for fd in feature_data_list if fd.get("charge") is not None])

    # Process adducts with cached validation
    all_adducts = []
    valid_adducts = cached_valid_adducts if cached_valid_adducts is not None else set()
    valid_adducts.add("?")  # Always allow '?' adducts

    for fd in feature_data_list:
        adduct = fd.get("adduct")
        if adduct is not None:
            # Only include adducts that are valid (from cached study adducts or contain '?')
            if adduct in valid_adducts or "?" in adduct:
                all_adducts.append(adduct)

    # Calculate adduct consensus
    adduct_values = []
    adduct_top = None
    adduct_charge_top = None
    adduct_mass_neutral_top = None
    adduct_mass_shift_top = None

    if all_adducts:
        adduct_counts = {adduct: all_adducts.count(adduct) for adduct in set(all_adducts)}
        total_count = sum(adduct_counts.values())
        for adduct, count in adduct_counts.items():
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            adduct_values.append([str(adduct), int(count), float(round(percentage, 2))])

        adduct_values.sort(key=lambda x: x[1], reverse=True)

        if adduct_values:
            adduct_top = adduct_values[0][0]
            # Try to get charge and mass shift from cached study adducts
            adduct_found = False
            if cached_adducts_df is not None and not cached_adducts_df.is_empty():
                matching_adduct = cached_adducts_df.filter(
                    pl.col("name") == adduct_top,
                )
                if not matching_adduct.is_empty():
                    adduct_row = matching_adduct.row(0, named=True)
                    adduct_charge_top = adduct_row["charge"]
                    adduct_mass_shift_top = adduct_row["mass_shift"]
                    adduct_found = True

            if not adduct_found:
                # Set default charge and mass shift for top adduct
                adduct_charge_top = 1
                adduct_mass_shift_top = 1.007825
    else:
        # Default adduct based on study polarity
        study_polarity = getattr(study_obj, "polarity", "positive")
        if study_polarity in ["negative", "neg"]:
            adduct_top = "[M-?]1-"
            adduct_charge_top = -1
            adduct_mass_shift_top = -1.007825
        else:
            adduct_top = "[M+?]1+"
            adduct_charge_top = 1
            adduct_mass_shift_top = 1.007825

        adduct_values = [[adduct_top, 1, 100.0]]

    # Calculate neutral mass
    consensus_mz = round(float(np.mean(mz_values)), 4) if len(mz_values) > 0 else 0.0
    if adduct_charge_top and adduct_mass_shift_top is not None:
        adduct_mass_neutral_top = consensus_mz * abs(adduct_charge_top) - adduct_mass_shift_top

    # Calculate MS2 count
    ms2_count = 0
    for fd in feature_data_list:
        ms2_scans = fd.get("ms2_scans")
        if ms2_scans is not None:
            ms2_count += len(ms2_scans)

    # Build consensus metadata
    # Generate unique 16-character consensus_id string
    import uuid

    consensus_id_str = str(uuid.uuid4()).replace("-", "")[:16]

    return {
        "consensus_uid": int(consensus_uid),
        "consensus_id": consensus_id_str,  # Use unique 16-char string ID
        "quality": round(float(np.mean(quality_values)), 3) if len(quality_values) > 0 else 1.0,
        "number_samples": number_samples if number_samples is not None else len(feature_data_list),
        "rt": round(float(np.mean(rt_values)), 4) if len(rt_values) > 0 else 0.0,
        "mz": consensus_mz,
        "rt_min": round(float(np.min(rt_feat_values)), 3) if len(rt_feat_values) > 0 else 0.0,
        "rt_max": round(float(np.max(rt_feat_values)), 3) if len(rt_feat_values) > 0 else 0.0,
        "rt_mean": round(float(np.mean(rt_feat_values)), 3) if len(rt_feat_values) > 0 else 0.0,
        "rt_start_mean": round(float(np.mean(rt_start_values)), 3) if len(rt_start_values) > 0 else 0.0,
        "rt_end_mean": round(float(np.mean(rt_end_values)), 3) if len(rt_end_values) > 0 else 0.0,
        "rt_delta_mean": round(float(np.mean(rt_delta_values)), 3) if len(rt_delta_values) > 0 else 0.0,
        "mz_min": round(float(np.min(mz_feat_values)), 4) if len(mz_feat_values) > 0 else 0.0,
        "mz_max": round(float(np.max(mz_feat_values)), 4) if len(mz_feat_values) > 0 else 0.0,
        "mz_mean": round(float(np.mean(mz_feat_values)), 4) if len(mz_feat_values) > 0 else 0.0,
        "mz_start_mean": round(float(np.mean(mz_start_values)), 4) if len(mz_start_values) > 0 else 0.0,
        "mz_end_mean": round(float(np.mean(mz_end_values)), 4) if len(mz_end_values) > 0 else 0.0,
        "inty_mean": round(float(np.mean(inty_values)), 0) if len(inty_values) > 0 else 0.0,
        "bl": -1.0,
        "chrom_coherence_mean": round(float(np.mean(coherence_values)), 3) if len(coherence_values) > 0 else 0.0,
        "chrom_prominence_mean": round(float(np.mean(prominence_values)), 0) if len(prominence_values) > 0 else 0.0,
        "chrom_prominence_scaled_mean": round(float(np.mean(prominence_scaled_values)), 3)
        if len(prominence_scaled_values) > 0
        else 0.0,
        "chrom_height_scaled_mean": round(float(np.mean(height_scaled_values)), 3)
        if len(height_scaled_values) > 0
        else 0.0,
        "iso": None,  # Will be filled by find_iso() function
        "iso_mean": round(float(np.mean(iso_values)), 2) if len(iso_values) > 0 else 0.0,
        "charge_mean": round(float(np.mean(charge_values)), 2) if len(charge_values) > 0 else 0.0,
        "number_ms2": int(ms2_count),
        "adducts": adduct_values,
        "adduct_top": adduct_top,
        "adduct_charge_top": adduct_charge_top,
        "adduct_mass_neutral_top": round(adduct_mass_neutral_top, 6) if adduct_mass_neutral_top is not None else None,
        "adduct_mass_shift_top": round(adduct_mass_shift_top, 6) if adduct_mass_shift_top is not None else None,
        "id_top_name": None,
        "id_top_class": None,
        "id_top_adduct": None,
        "id_top_score": None,
        "id_source": None,
    }


def _extract_consensus_features(study, consensus_map, min_samples, cached_adducts_df=None, cached_valid_adducts=None):
    """Extract consensus features and build metadata."""
    # create a dict to map uid to feature_uid using study.features_df
    feature_uid_map = {row["feature_id"]: row["feature_uid"] for row in study.features_df.iter_rows(named=True)}
    imax = consensus_map.size()

    study.logger.debug(f"Found {imax} feature groups by clustering.")

    # Pre-build fast lookup tables for features_df data using optimized approach
    features_lookup = __merge_feature_lookup(study, study.features_df)

    # create a list to store the consensus mapping
    consensus_mapping = []
    metadata_list = []

    tqdm_disable = study.log_level not in ["TRACE", "DEBUG"]

    for i, feature in enumerate(
        tqdm(
            consensus_map,
            total=imax,
            disable=tqdm_disable,
            desc=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | INFO     | {study.log_label}Extract metadata",
        ),
    ):
        # get all features in the feature map with the same unique id as the consensus feature
        features_list = feature.getFeatureList()
        uids = []
        feature_data_list = []

        for _j, f in enumerate(features_list):
            fuid = str(f.getUniqueId())
            if fuid not in feature_uid_map:
                # this is a feature that was removed but is still in the feature maps
                continue
            fuid = feature_uid_map[fuid]
            consensus_mapping.append(
                {
                    "consensus_uid": i,
                    "sample_uid": f.getMapIndex() + 1,
                    "feature_uid": fuid,
                },
            )
            uids.append(fuid)

            # Get feature data from lookup instead of DataFrame filtering
            feature_data = features_lookup.get(fuid)
            if feature_data:
                feature_data_list.append(feature_data)

        if not feature_data_list:
            # Skip this consensus feature if no valid features found
            continue

        # Compute statistics using vectorized operations on collected data
        # Convert to numpy arrays for faster computation
        rt_values = np.array(
            [fd.get("rt", 0) for fd in feature_data_list if fd.get("rt") is not None],
        )
        mz_values = np.array(
            [fd.get("mz", 0) for fd in feature_data_list if fd.get("mz") is not None],
        )
        rt_start_values = np.array(
            [fd.get("rt_start", 0) for fd in feature_data_list if fd.get("rt_start") is not None],
        )
        rt_end_values = np.array(
            [fd.get("rt_end", 0) for fd in feature_data_list if fd.get("rt_end") is not None],
        )
        rt_delta_values = np.array(
            [fd.get("rt_delta", 0) for fd in feature_data_list if fd.get("rt_delta") is not None],
        )
        mz_start_values = np.array(
            [fd.get("mz_start", 0) for fd in feature_data_list if fd.get("mz_start") is not None],
        )
        mz_end_values = np.array(
            [fd.get("mz_end", 0) for fd in feature_data_list if fd.get("mz_end") is not None],
        )
        inty_values = np.array(
            [fd.get("inty", 0) for fd in feature_data_list if fd.get("inty") is not None],
        )
        coherence_values = np.array(
            [fd.get("chrom_coherence", 0) for fd in feature_data_list if fd.get("chrom_coherence") is not None],
        )
        prominence_values = np.array(
            [fd.get("chrom_prominence", 0) for fd in feature_data_list if fd.get("chrom_prominence") is not None],
        )
        prominence_scaled_values = np.array(
            [fd.get("chrom_height_scaled", 0) for fd in feature_data_list if fd.get("chrom_height_scaled") is not None],
        )
        height_scaled_values = np.array(
            [
                fd.get("chrom_prominence_scaled", 0)
                for fd in feature_data_list
                if fd.get("chrom_prominence_scaled") is not None
            ],
        )
        iso_values = np.array(
            [fd.get("iso", 0) for fd in feature_data_list if fd.get("iso") is not None],
        )
        charge_values = np.array(
            [fd.get("charge", 0) for fd in feature_data_list if fd.get("charge") is not None],
        )

        # adduct_values
        # Collect all adducts from feature_data_list to create consensus adduct information
        # Only consider adducts that are in study._get_adducts() plus items with '?'
        all_adducts = []
        adduct_masses = {}

        # Get valid adducts from cached result (avoid repeated _get_adducts() calls)
        valid_adducts = cached_valid_adducts if cached_valid_adducts is not None else set()
        valid_adducts.add("?")  # Always allow '?' adducts

        for fd in feature_data_list:
            # Get individual adduct and mass from each feature data (fd)
            adduct = fd.get("adduct")
            adduct_mass = fd.get("adduct_mass")

            if adduct is not None:
                # Only include adducts that are valid (from study._get_adducts() or contain '?')
                if adduct in valid_adducts or "?" in adduct:
                    all_adducts.append(adduct)
                    if adduct_mass is not None:
                        adduct_masses[adduct] = adduct_mass

        # Calculate adduct_values for the consensus feature
        adduct_values = []
        if all_adducts:
            adduct_counts = {adduct: all_adducts.count(adduct) for adduct in set(all_adducts)}
            total_count = sum(adduct_counts.values())
            for adduct, count in adduct_counts.items():
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                # Store as list with [name, num, %] format for the adducts column
                adduct_values.append(
                    [
                        str(adduct),
                        int(count),
                        float(round(percentage, 2)),
                    ],
                )

        # Sort adduct_values by count in descending order
        adduct_values.sort(key=lambda x: x[1], reverse=True)  # Sort by count (index 1)
        # Store adduct_values for use in metadata
        consensus_adduct_values = adduct_values

        # Extract top adduct information for new columns
        adduct_top = None
        adduct_charge_top = None
        adduct_mass_neutral_top = None
        adduct_mass_shift_top = None

        if consensus_adduct_values:
            top_adduct_name = consensus_adduct_values[0][0]  # Get top adduct name
            adduct_top = top_adduct_name

            # Parse adduct information to extract charge and mass shift
            # Handle "?" as "H" and parse common adduct formats
            if top_adduct_name == "?" or top_adduct_name == "[M+?]+":
                adduct_charge_top = 1
                adduct_mass_shift_top = 1.007825  # H mass
            elif top_adduct_name == "[M+?]-":
                adduct_charge_top = -1
                adduct_mass_shift_top = -1.007825  # -H mass
            else:
                # Try to get charge and mass shift from cached study adducts
                adduct_found = False
                if cached_adducts_df is not None and not cached_adducts_df.is_empty():
                    # Look for exact match in study adducts
                    matching_adduct = cached_adducts_df.filter(
                        pl.col("name") == top_adduct_name,
                    )
                    if not matching_adduct.is_empty():
                        adduct_row = matching_adduct.row(0, named=True)
                        adduct_charge_top = adduct_row["charge"]
                        adduct_mass_shift_top = adduct_row["mass_shift"]
                        adduct_found = True

                if not adduct_found:
                    # Fallback to regex parsing
                    import re

                    # Pattern for adducts like [M+H]+, [M-H]-, [M+Na]+, etc.
                    pattern = r"\[M([+\-])([A-Za-z0-9]+)\]([0-9]*)([+\-])"
                    match = re.match(pattern, top_adduct_name)

                    if match:
                        sign = match.group(1)
                        element = match.group(2)
                        multiplier_str = match.group(3)
                        charge_sign = match.group(4)

                        multiplier = int(multiplier_str) if multiplier_str else 1
                        charge = multiplier if charge_sign == "+" else -multiplier
                        adduct_charge_top = charge

                        # Calculate mass shift based on element
                        element_masses = {
                            "H": 1.007825,
                            "Na": 22.989769,
                            "K": 38.963708,
                            "NH4": 18.033823,
                            "Li": 7.016930,
                            "Cl": 34.969401,
                            "Br": 78.918885,
                            "HCOO": 44.998201,
                            "CH3COO": 59.013851,
                            "H2O": 18.010565,
                        }

                        base_mass = element_masses.get(
                            element,
                            1.007825,
                        )  # Default to H if unknown
                        mass_shift = base_mass * multiplier if sign == "+" else -base_mass * multiplier
                        adduct_mass_shift_top = mass_shift
                    else:
                        # Default fallback
                        adduct_charge_top = 1
                        adduct_mass_shift_top = 1.007825
        else:
            # No valid adducts found - assign default based on study polarity
            study_polarity = getattr(study, "polarity", "positive")
            if study_polarity in ["negative", "neg"]:
                # Negative mode default
                adduct_top = "[M-?]1-"
                adduct_charge_top = -1
                adduct_mass_shift_top = -1.007825  # -H mass (loss of proton)
            else:
                # Positive mode default (includes 'positive', 'pos', or any other value)
                adduct_top = "[M+?]1+"
                adduct_charge_top = 1
                adduct_mass_shift_top = 1.007825  # H mass (gain of proton)

            # Create a single default adduct entry in the adducts list for consistency
            consensus_adduct_values = [[adduct_top, 1, 100.0]]

        # Calculate neutral mass from consensus mz (for both cases)
        consensus_mz = round(float(np.mean(mz_values)), 4) if len(mz_values) > 0 else 0.0
        if adduct_charge_top and adduct_mass_shift_top is not None:
            adduct_mass_neutral_top = consensus_mz * abs(adduct_charge_top) - adduct_mass_shift_top

        # Calculate number of MS2 spectra
        ms2_count = 0
        for fd in feature_data_list:
            ms2_scans = fd.get("ms2_scans")
            if ms2_scans is not None:
                ms2_count += len(ms2_scans)

        # Generate unique 16-character consensus_id string (UUID-based)
        import uuid

        consensus_id_str = str(uuid.uuid4()).replace("-", "")[:16]

        metadata_list.append(
            {
                "consensus_uid": int(i),  # "consensus_id": i,
                "consensus_id": consensus_id_str,  # Use unique 16-char string ID
                "quality": round(float(feature.getQuality()), 3),
                "number_samples": len(feature_data_list),
                # "number_ext": int(len(features_list)),
                "rt": round(float(np.mean(rt_values)), 4) if len(rt_values) > 0 else 0.0,
                "mz": round(float(np.mean(mz_values)), 4) if len(mz_values) > 0 else 0.0,
                "rt_min": round(float(np.min(rt_values)), 3) if len(rt_values) > 0 else 0.0,
                "rt_max": round(float(np.max(rt_values)), 3) if len(rt_values) > 0 else 0.0,
                "rt_mean": round(float(np.mean(rt_values)), 3) if len(rt_values) > 0 else 0.0,
                "rt_start_mean": round(float(np.mean(rt_start_values)), 3) if len(rt_start_values) > 0 else 0.0,
                "rt_end_mean": round(float(np.mean(rt_end_values)), 3) if len(rt_end_values) > 0 else 0.0,
                "rt_delta_mean": round(float(np.ptp(rt_delta_values)), 3) if len(rt_delta_values) > 0 else 0.0,
                "mz_min": round(float(np.min(mz_values)), 4) if len(mz_values) > 0 else 0.0,
                "mz_max": round(float(np.max(mz_values)), 4) if len(mz_values) > 0 else 0.0,
                "mz_mean": round(float(np.mean(mz_values)), 4) if len(mz_values) > 0 else 0.0,
                "mz_start_mean": round(float(np.mean(mz_start_values)), 4) if len(mz_start_values) > 0 else 0.0,
                "mz_end_mean": round(float(np.mean(mz_end_values)), 4) if len(mz_end_values) > 0 else 0.0,
                "inty_mean": round(float(np.mean(inty_values)), 0) if len(inty_values) > 0 else 0.0,
                "bl": -1.0,
                "chrom_coherence_mean": round(float(np.mean(coherence_values)), 3)
                if len(coherence_values) > 0
                else 0.0,
                "chrom_prominence_mean": round(float(np.mean(prominence_values)), 0)
                if len(prominence_values) > 0
                else 0.0,
                "chrom_prominence_scaled_mean": round(
                    float(np.mean(prominence_scaled_values)),
                    3,
                )
                if len(prominence_scaled_values) > 0
                else 0.0,
                "chrom_height_scaled_mean": round(
                    float(np.mean(height_scaled_values)),
                    3,
                )
                if len(height_scaled_values) > 0
                else 0.0,
                "iso": None,  # Will be filled by find_iso() function
                "iso_mean": round(float(np.mean(iso_values)), 2) if len(iso_values) > 0 else 0.0,
                "charge_mean": round(float(np.mean(charge_values)), 2) if len(charge_values) > 0 else 0.0,
                "number_ms2": int(ms2_count),
                "adducts": consensus_adduct_values if consensus_adduct_values else [],  # Ensure it's always a list
                # New columns for top-ranked adduct information
                "adduct_top": adduct_top,
                "adduct_charge_top": adduct_charge_top,
                "adduct_mass_neutral_top": round(adduct_mass_neutral_top, 6)
                if adduct_mass_neutral_top is not None
                else None,
                "adduct_mass_shift_top": round(adduct_mass_shift_top, 6) if adduct_mass_shift_top is not None else None,
                # New columns for top-scoring identification results
                "id_top_name": None,
                "id_top_class": None,
                "id_top_adduct": None,
                "id_top_score": None,
                "id_source": None,
            },
        )

    consensus_mapping_df = pl.DataFrame(consensus_mapping)
    # remove all rows in consensus_mapping_df where consensus_id is not in study.featured_df['uid']
    l1 = len(consensus_mapping_df)
    consensus_mapping_df = consensus_mapping_df.filter(
        pl.col("feature_uid").is_in(study.features_df["feature_uid"].to_list()),
    )
    study.logger.debug(
        f"Filtered {l1 - len(consensus_mapping_df)} orphan features from maps.",
    )
    study.consensus_mapping_df = consensus_mapping_df
    study.consensus_df = pl.DataFrame(metadata_list, strict=False)

    if min_samples is None:
        min_samples = 1
    if min_samples < 1:
        min_samples = int(min_samples * len(study.samples_df))

    # Validate that min_samples doesn't exceed the number of samples
    if min_samples > len(study.samples_df):
        study.logger.warning(
            f"min_samples ({min_samples}) exceeds the number of samples ({len(study.samples_df)}). "
            f"Setting min_samples to {len(study.samples_df)}.",
        )
        min_samples = len(study.samples_df)

    # filter out consensus features with less than min_samples features
    l1 = len(study.consensus_df)
    study.consensus_df = study.consensus_df.filter(
        pl.col("number_samples") >= min_samples,
    )
    study.logger.debug(
        f"Filtered {l1 - len(study.consensus_df)} consensus features with less than {min_samples} samples.",
    )
    # filter out consensus mapping with less than min_samples features
    study.consensus_mapping_df = study.consensus_mapping_df.filter(
        pl.col("consensus_uid").is_in(study.consensus_df["consensus_uid"].to_list()),
    )

    # Log final counts
    study.logger.info(f"Extracted {len(study.consensus_df)} consensus features with at least {min_samples} samples.")


def _perform_adduct_grouping(study, rt_tol, mz_tol):
    """Perform adduct grouping on consensus features."""
    import polars as pl

    # Add adduct grouping and adduct_of assignment
    if len(study.consensus_df) > 0:
        # Get relevant columns for grouping
        consensus_data = []
        for row in study.consensus_df.iter_rows(named=True):
            consensus_data.append(
                {
                    "consensus_uid": row["consensus_uid"],
                    "rt": row["rt"],
                    "mz": row["mz"],
                    "adduct_mass_neutral_top": row.get("adduct_mass_neutral_top"),
                    "adduct_top": row.get("adduct_top"),
                    "inty_mean": row.get("inty_mean", 0),
                },
            )

        adduct_group_list, adduct_of_list = __merge_adduct_grouping(study, consensus_data, rt_tol / 3, mz_tol)

        # Add the new columns to consensus_df
        study.consensus_df = study.consensus_df.with_columns(
            [
                pl.Series("adduct_group", adduct_group_list, dtype=pl.Int64),
                pl.Series("adduct_of", adduct_of_list, dtype=pl.Int64),
            ],
        )


def _count_tight_clusters(study, mz_tol: float = 0.04, rt_tol: float = 0.3) -> int:
    """
    Count consensus features grouped in tight clusters.

    Args:
        mz_tol: m/z tolerance in Daltons for cluster detection
        rt_tol: RT tolerance in seconds for cluster detection

    Returns:
        Number of tight clusters found
    """
    if len(study.consensus_df) < 2:
        return 0

    # Extract consensus feature coordinates efficiently
    feature_coords = study.consensus_df.select([pl.col("consensus_uid"), pl.col("mz"), pl.col("rt")]).to_numpy()

    n_features = len(feature_coords)
    processed = [False] * n_features
    tight_clusters_count = 0

    # Use vectorized distance calculations for efficiency
    for i in range(n_features):
        if processed[i]:
            continue

        # Find all features within tolerance of feature i
        cluster_members = [i]
        rt_i, mz_i = feature_coords[i][2], feature_coords[i][1]

        for j in range(i + 1, n_features):
            if processed[j]:
                continue

            rt_j, mz_j = feature_coords[j][2], feature_coords[j][1]

            if abs(rt_i - rt_j) <= rt_tol and abs(mz_i - mz_j) <= mz_tol:
                cluster_members.append(j)

        # Mark cluster as tight if it has 2+ members
        if len(cluster_members) >= 2:
            tight_clusters_count += 1
            for idx in cluster_members:
                processed[idx] = True

    return tight_clusters_count


def _merge_partial_consensus_features(study, rt_tol, mz_tol):
    """
    Merge partial consensus features that likely represent the same compound but were
    split across chunks. This is specifically for chunked methods.
    """
    if len(study.consensus_df) == 0:
        return

    initial_count = len(study.consensus_df)
    study.logger.debug(
        f"Post-processing chunked results: merging partial consensus features from {initial_count} features"
    )

    # Convert to list of dictionaries for easier processing
    consensus_features = []
    for row in study.consensus_df.iter_rows(named=True):
        consensus_features.append({
            "consensus_uid": row["consensus_uid"],
            "rt": row["rt"],
            "mz": row["mz"],
            "number_samples": row.get("number_samples", 0),
            "inty_mean": row.get("inty_mean", 0.0),
        })

    # Use Union-Find to group features that should be merged
    class UnionFind:
        def __init__(self, n):
            self.parent = list(range(n))

        def find(self, x):
            if self.parent[x] != x:
                self.parent[x] = self.find(self.parent[x])
            return self.parent[x]

        def union(self, x, y):
            px, py = self.find(x), self.find(y)
            if px != py:
                self.parent[py] = px

    n_features = len(consensus_features)
    uf = UnionFind(n_features)

    # Find features that should be merged using original tolerances
    for i in range(n_features):
        for j in range(i + 1, n_features):
            feature_a = consensus_features[i]
            feature_b = consensus_features[j]

            rt_diff = abs(feature_a["rt"] - feature_b["rt"])
            mz_diff = abs(feature_a["mz"] - feature_b["mz"])

            # Merge if within tolerance
            if rt_diff <= rt_tol and mz_diff <= mz_tol:
                uf.union(i, j)

    # Group features by their root
    groups = {}
    for i, feature in enumerate(consensus_features):
        root = uf.find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(consensus_features[i])

    # Create merged features
    merged_features = []
    merged_mapping_data = []
    uids_to_remove = set()

    for group in groups.values():
        if len(group) < 2:
            # Single feature, keep as is
            continue
        else:
            # Multiple features, merge them
            # Find best representative feature (highest sample count, then intensity)
            best_feature = max(group, key=lambda x: (x["number_samples"], x["inty_mean"]))

            # Calculate merged properties
            total_samples = sum(f["number_samples"] for f in group)
            weighted_rt = (
                sum(f["rt"] * f["number_samples"] for f in group) / total_samples
                if total_samples > 0
                else best_feature["rt"]
            )
            weighted_mz = (
                sum(f["mz"] * f["number_samples"] for f in group) / total_samples
                if total_samples > 0
                else best_feature["mz"]
            )
            mean_intensity = (
                sum(f["inty_mean"] * f["number_samples"] for f in group) / total_samples
                if total_samples > 0
                else best_feature["inty_mean"]
            )

            # Keep the best feature's UID but update its properties
            merged_features.append({
                "consensus_uid": best_feature["consensus_uid"],
                "rt": weighted_rt,
                "mz": weighted_mz,
                "number_samples": total_samples,
                "inty_mean": mean_intensity,
            })

            # Mark other features for removal
            for f in group:
                if f["consensus_uid"] != best_feature["consensus_uid"]:
                    uids_to_remove.add(f["consensus_uid"])

    if merged_features:
        study.logger.debug(f"Merging {len(merged_features)} groups of partial consensus features")

        # Update consensus_df with merged features
        for merged_feature in merged_features:
            study.consensus_df = study.consensus_df.with_columns([
                pl.when(pl.col("consensus_uid") == merged_feature["consensus_uid"])
                .then(pl.lit(merged_feature["rt"]))
                .otherwise(pl.col("rt"))
                .alias("rt"),
                pl.when(pl.col("consensus_uid") == merged_feature["consensus_uid"])
                .then(pl.lit(merged_feature["mz"]))
                .otherwise(pl.col("mz"))
                .alias("mz"),
                pl.when(pl.col("consensus_uid") == merged_feature["consensus_uid"])
                .then(pl.lit(merged_feature["number_samples"]))
                .otherwise(pl.col("number_samples"))
                .alias("number_samples"),
                pl.when(pl.col("consensus_uid") == merged_feature["consensus_uid"])
                .then(pl.lit(merged_feature["inty_mean"]))
                .otherwise(pl.col("inty_mean"))
                .alias("inty_mean"),
            ])

        # Remove duplicate features
        if uids_to_remove:
            study.consensus_df = study.consensus_df.filter(~pl.col("consensus_uid").is_in(list(uids_to_remove)))

            # Also update consensus_mapping_df - reassign mappings from removed UIDs
            if hasattr(study, "consensus_mapping_df") and not study.consensus_mapping_df.is_empty():
                study.consensus_mapping_df = study.consensus_mapping_df.with_columns(
                    pl.when(pl.col("consensus_uid").is_in(list(uids_to_remove)))
                    .then(pl.lit(None))  # Will be handled by subsequent operations
                    .otherwise(pl.col("consensus_uid"))
                    .alias("consensus_uid")
                )

        final_count = len(study.consensus_df)
        study.logger.debug(f"Partial consensus merging: {initial_count} → {final_count} features")


def __consensus_cleanup(study, rt_tol, mz_tol):
    """
    Consensus cleanup to merge over-segmented consensus features and remove isotopic features.

    This function:
    1. Identifies and merges consensus features that are likely over-segmented
       (too many features in very tight m/z and RT windows)
    2. Performs deisotoping to remove +1 and +2 isotopic features
    """
    if len(study.consensus_df) == 0:
        return

    initial_count = len(study.consensus_df)

    # Only perform enhanced post-clustering if there are many features
    if initial_count < 50:
        return

    study.logger.debug(f"Enhanced post-clustering: processing {initial_count} consensus features")

    # Find tight clusters using spatial binning
    consensus_data = []
    for row in study.consensus_df.iter_rows(named=True):
        consensus_data.append({
            "consensus_uid": row["consensus_uid"],
            "mz": row["mz"],
            "rt": row["rt"],
            "inty_mean": row.get("inty_mean", 0),
            "number_samples": row.get("number_samples", 0),
        })

    # Parameters for tight clustering detection - more lenient for effective merging
    tight_rt_tol = min(0.5, rt_tol * 0.5)  # More lenient RT tolerance (max 0.5s)
    tight_mz_tol = min(0.05, max(0.03, mz_tol * 2.0))  # More lenient m/z tolerance (min 30 mDa, max 50 mDa)

    # Build spatial index using smaller RT and m/z bins for better coverage
    rt_bin_size = tight_rt_tol / 4  # Smaller bins to ensure nearby features are captured
    mz_bin_size = tight_mz_tol / 4  # Smaller bins to ensure nearby features are captured

    bins = defaultdict(list)
    for feature in consensus_data:
        rt_bin = int(feature["rt"] / rt_bin_size)
        mz_bin = int(feature["mz"] / mz_bin_size)
        bins[(rt_bin, mz_bin)].append(feature)

    # Find clusters that need merging
    merge_groups = []
    processed_uids = set()

    for bin_key, bin_features in bins.items():
        # Check current bin and extended neighboring bins for complete cluster
        rt_bin, mz_bin = bin_key
        cluster_features = list(bin_features)

        # Check a larger neighborhood (±2 bins) to ensure we capture all nearby features
        for dr in [-2, -1, 0, 1, 2]:
            for dm in [-2, -1, 0, 1, 2]:
                if dr == 0 and dm == 0:
                    continue
                neighbor_key = (rt_bin + dr, mz_bin + dm)
                if neighbor_key in bins:
                    cluster_features.extend(bins[neighbor_key])

        # Remove duplicates
        seen_uids = set()
        unique_features = []
        for f in cluster_features:
            if f["consensus_uid"] not in seen_uids:
                unique_features.append(f)
                seen_uids.add(f["consensus_uid"])

        # Only proceed if we have at least 2 features after including neighbors
        if len(unique_features) < 2:
            continue

        # Calculate cluster bounds
        mzs = [f["mz"] for f in unique_features]
        rts = [f["rt"] for f in unique_features]

        mz_spread = max(mzs) - min(mzs)
        rt_spread = max(rts) - min(rts)

        # Only merge if features are tightly clustered
        if mz_spread <= tight_mz_tol and rt_spread <= tight_rt_tol:
            # Filter out features that were already processed
            uids_in_cluster = {f["consensus_uid"] for f in unique_features}
            unprocessed_features = [f for f in unique_features if f["consensus_uid"] not in processed_uids]

            # Only proceed if we have at least 2 unprocessed features that still form a tight cluster
            if len(unprocessed_features) >= 2:
                # Recalculate bounds for unprocessed features only
                unprocessed_mzs = [f["mz"] for f in unprocessed_features]
                unprocessed_rts = [f["rt"] for f in unprocessed_features]

                unprocessed_mz_spread = max(unprocessed_mzs) - min(unprocessed_mzs)
                unprocessed_rt_spread = max(unprocessed_rts) - min(unprocessed_rts)

                # Check if unprocessed features still meet tight clustering criteria
                if unprocessed_mz_spread <= tight_mz_tol and unprocessed_rt_spread <= tight_rt_tol:
                    merge_groups.append(unprocessed_features)
                    processed_uids.update({f["consensus_uid"] for f in unprocessed_features})

    if not merge_groups:
        return

    study.logger.debug(f"Found {len(merge_groups)} over-segmented clusters to merge")

    # Merge clusters by keeping the most representative feature
    uids_to_remove = set()

    for group in merge_groups:
        if len(group) < 2:
            continue

        # Find the most representative feature (highest intensity and sample count)
        best_feature = max(group, key=lambda x: (x["number_samples"], x["inty_mean"]))

        # Mark other features for removal
        for f in group:
            if f["consensus_uid"] != best_feature["consensus_uid"]:
                uids_to_remove.add(f["consensus_uid"])

    if uids_to_remove:
        # Remove merged features from consensus_df
        study.consensus_df = study.consensus_df.filter(~pl.col("consensus_uid").is_in(list(uids_to_remove)))

        # Also update consensus_mapping_df if it exists
        if hasattr(study, "consensus_mapping_df") and not study.consensus_mapping_df.is_empty():
            study.consensus_mapping_df = study.consensus_mapping_df.filter(
                ~pl.col("consensus_uid").is_in(list(uids_to_remove))
            )

        final_count = len(study.consensus_df)
        reduction = initial_count - final_count
        reduction_pct = (reduction / initial_count) * 100

        if reduction > 0:
            study.logger.debug(
                f"Enhanced post-clustering: {initial_count} → {final_count} features ({reduction_pct:.1f}% reduction)"
            )

    # Step 2: Deisotoping - Remove +1 and +2 isotopic consensus features
    pre_deisotoping_count = len(study.consensus_df)
    isotope_uids_to_remove = set()

    # Use strict tolerances for deisotoping (same as declustering)
    deisotope_rt_tol = min(0.3, rt_tol * 0.3)  # Strict RT tolerance for isotope detection
    deisotope_mz_tol = min(0.01, mz_tol * 0.5)  # Strict m/z tolerance for isotope detection

    # Get current consensus data for isotope detection
    current_consensus_data = []
    for row in study.consensus_df.iter_rows(named=True):
        current_consensus_data.append({
            "consensus_uid": row["consensus_uid"],
            "mz": row["mz"],
            "rt": row["rt"],
            "number_samples": row.get("number_samples", 0),
        })

    # Sort by m/z for efficient searching
    current_consensus_data.sort(key=lambda x: x["mz"])
    n_current = len(current_consensus_data)

    for i in range(n_current):
        feature_i = current_consensus_data[i]

        # Skip if already marked for removal
        if feature_i["consensus_uid"] in isotope_uids_to_remove:
            continue

        # Look for potential +1 and +2 isotopes (higher m/z)
        for j in range(i + 1, n_current):
            feature_j = current_consensus_data[j]

            # Skip if already marked for removal
            if feature_j["consensus_uid"] in isotope_uids_to_remove:
                continue

            mz_diff = feature_j["mz"] - feature_i["mz"]

            # Break if m/z difference is too large (features are sorted by m/z)
            if mz_diff > 2.1:  # Beyond +2 isotope range
                break

            rt_diff = abs(feature_j["rt"] - feature_i["rt"])

            # Check for +1 isotope (C13 mass difference ≈ 1.003354 Da)
            if (0.995 <= mz_diff <= 1.011) and rt_diff <= deisotope_rt_tol:
                # Potential +1 isotope - should have fewer samples than main feature
                if feature_j["number_samples"] < feature_i["number_samples"]:
                    isotope_uids_to_remove.add(feature_j["consensus_uid"])
                    continue

            # Check for +2 isotope (2 * C13 mass difference ≈ 2.006708 Da)
            if (1.995 <= mz_diff <= 2.018) and rt_diff <= deisotope_rt_tol:
                # Potential +2 isotope - should have fewer samples than main feature
                if feature_j["number_samples"] < feature_i["number_samples"]:
                    isotope_uids_to_remove.add(feature_j["consensus_uid"])
                    continue

    # Remove isotopic features
    if isotope_uids_to_remove:
        study.consensus_df = study.consensus_df.filter(~pl.col("consensus_uid").is_in(list(isotope_uids_to_remove)))

        # Also update consensus_mapping_df if it exists
        if hasattr(study, "consensus_mapping_df") and not study.consensus_mapping_df.is_empty():
            study.consensus_mapping_df = study.consensus_mapping_df.filter(
                ~pl.col("consensus_uid").is_in(list(isotope_uids_to_remove))
            )

        post_deisotoping_count = len(study.consensus_df)
        isotope_reduction = pre_deisotoping_count - post_deisotoping_count

        if isotope_reduction > 0:
            study.logger.debug(
                f"Deisotoping: {pre_deisotoping_count} → {post_deisotoping_count} features ({isotope_reduction} isotopic features removed)"
            )

    # Final summary
    final_count = len(study.consensus_df)
    total_reduction = initial_count - final_count
    if total_reduction > 0:
        total_reduction_pct = (total_reduction / initial_count) * 100
        study.logger.debug(
            f"Consensus cleanup complete: {initial_count} → {final_count} features ({total_reduction_pct:.1f}% total reduction)"
        )


def __identify_adduct_by_mass_shift(study, rt_tol, cached_adducts_df=None):
    """
    Identify coeluting consensus features by characteristic mass shifts between adducts
    and update their adduct information accordingly.

    This function:
    1. Generates a catalogue of mass shifts between adducts using _get_adducts()
    2. Searches for pairs of consensus features with same RT (within strict RT tolerance)
       and matching m/z shifts (±0.005 Da)
    3. Updates adduct_* columns based on identified relationships

    Args:
        rt_tol: RT tolerance in seconds (strict tolerance for coelution detection)
        cached_adducts_df: Pre-computed adducts DataFrame for performance
    """
    import polars as pl

    # Check if consensus_df exists and has features
    if len(study.consensus_df) == 0:
        study.logger.debug("No consensus features for adduct identification by mass shift")
        return

    # Get adducts DataFrame if not provided
    if cached_adducts_df is None or cached_adducts_df.is_empty():
        try:
            # Use lower min_probability for better adduct coverage in mass shift identification
            cached_adducts_df = study._get_adducts(min_probability=0.01)
        except Exception as e:
            study.logger.warning(f"Could not retrieve adducts for mass shift identification: {e}")
            return

    if cached_adducts_df.is_empty():
        study.logger.debug("No adducts available for mass shift identification")
        return

    # Build catalogue of mass shifts between adducts
    mass_shift_catalog = {}
    adduct_info = {}

    # Extract adduct information
    adducts_data = cached_adducts_df.select(["name", "charge", "mass_shift"]).to_dicts()

    for adduct in adducts_data:
        name = adduct["name"]
        charge = adduct["charge"]
        mass_shift = adduct["mass_shift"]

        adduct_info[name] = {"charge": charge, "mass_shift": mass_shift}

    # Generate pairwise mass differences for catalog
    for adduct1 in adducts_data:
        for adduct2 in adducts_data:
            if adduct1["name"] == adduct2["name"]:
                continue

            name1, charge1, ms1 = adduct1["name"], adduct1["charge"], adduct1["mass_shift"]
            name2, charge2, ms2 = adduct2["name"], adduct2["charge"], adduct2["mass_shift"]

            # Only consider shifts between adducts that have the same charge (same ionization state)
            if charge1 != charge2:
                continue

            # Calculate expected m/z difference
            if charge1 != 0 and charge2 != 0:
                mz_diff = (ms1 - ms2) / abs(charge1)
            else:
                continue  # Skip neutral adducts for this analysis

            # Store the mass shift relationship
            shift_key = round(mz_diff, 4)  # Round to 4 decimal places for matching
            if shift_key not in mass_shift_catalog:
                mass_shift_catalog[shift_key] = []
            mass_shift_catalog[shift_key].append({
                "from_adduct": name1,
                "to_adduct": name2,
                "mz_shift": mz_diff,
                "from_charge": charge1,
                "to_charge": charge2,
            })

    study.logger.debug(f"Generated mass shift catalog with {len(mass_shift_catalog)} unique shifts")

    # Get consensus features data
    consensus_data = []
    for i, row in enumerate(study.consensus_df.iter_rows(named=True)):
        consensus_data.append({
            "index": i,
            "consensus_uid": row["consensus_uid"],
            "rt": row["rt"],
            "mz": row["mz"],
            "adduct_top": row.get("adduct_top", "[M+?]1+"),
            "adduct_charge_top": row.get("adduct_charge_top", 1),
            "adduct_mass_neutral_top": row.get("adduct_mass_neutral_top"),
            "adduct_mass_shift_top": row.get("adduct_mass_shift_top"),
            "inty_mean": row.get("inty_mean", 0),
        })

    # Sort by RT for efficient searching
    consensus_data.sort(key=lambda x: x["rt"])
    n_features = len(consensus_data)

    # Track updates to make
    adduct_updates = {}  # consensus_uid -> new_adduct_info

    # Strict RT tolerance for coelution (convert to minutes)
    rt_tol_strict = rt_tol * 0.5  # Use half the merge tolerance for strict coelution
    mz_tol_shift = 0.005  # ±5 mDa tolerance for mass shift matching

    # Search for coeluting pairs with characteristic mass shifts
    updated_count = 0

    for i in range(n_features):
        feature1 = consensus_data[i]
        rt1 = feature1["rt"]
        mz1 = feature1["mz"]
        adduct1 = feature1["adduct_top"]

        # Conservative approach: Don't skip features here - let algorithm find pairs first
        # We'll check for inappropriate assignments later in the pair processing logic

        # Search for coeluting features within strict RT tolerance
        for j in range(i + 1, n_features):
            feature2 = consensus_data[j]
            rt2 = feature2["rt"]

            # Break if RT difference exceeds tolerance (sorted by RT)
            if abs(rt2 - rt1) > rt_tol_strict:
                break

            mz2 = feature2["mz"]
            adduct2 = feature2["adduct_top"]

            # Conservative approach: Don't skip feature2 here either - process all potential pairs

            # Calculate observed m/z difference
            mz_diff = mz2 - mz1
            shift_key = round(mz_diff, 4)

            # Check if this mass shift matches any known adduct relationships
            for catalog_shift, relationships in mass_shift_catalog.items():
                if abs(shift_key - catalog_shift) <= mz_tol_shift:
                    # Found a matching mass shift!

                    # Choose the best relationship based on common adducts
                    best_rel = None
                    best_score = 0

                    for rel in relationships:
                        # Prioritize common adducts ([M+H]+, [M+Na]+, [M+NH4]+)
                        score = 0
                        if "H]" in rel["from_adduct"]:
                            score += 3
                        if "Na]" in rel["from_adduct"]:
                            score += 2
                        if "NH4]" in rel["from_adduct"]:
                            score += 2
                        if "H]" in rel["to_adduct"]:
                            score += 3
                        if "Na]" in rel["to_adduct"]:
                            score += 2
                        if "NH4]" in rel["to_adduct"]:
                            score += 2

                        if score > best_score:
                            best_score = score
                            best_rel = rel

                    if best_rel:
                        # Determine which feature gets which adduct based on intensity
                        inty1 = feature1["inty_mean"]
                        inty2 = feature2["inty_mean"]

                        # Assign higher intensity to [M+H]+ if possible
                        if "H]" in best_rel["from_adduct"] and inty1 >= inty2:
                            # Feature 1 = from_adduct, Feature 2 = to_adduct
                            from_feature = feature1
                            to_feature = feature2
                            from_adduct_name = best_rel["from_adduct"]
                            to_adduct_name = best_rel["to_adduct"]
                        elif "H]" in best_rel["to_adduct"] and inty2 >= inty1:
                            # Feature 2 = to_adduct (reverse), Feature 1 = from_adduct
                            from_feature = feature2
                            to_feature = feature1
                            from_adduct_name = best_rel["to_adduct"]
                            to_adduct_name = best_rel["from_adduct"]
                        else:
                            # Assignment based on mass shift direction
                            # catalog_shift = (ms1 - ms2) / abs(charge1) where ms1 = from_adduct mass shift, ms2 = to_adduct mass shift
                            # If catalog_shift > 0: from_adduct has higher mass shift than to_adduct
                            # If catalog_shift < 0: from_adduct has lower mass shift than to_adduct
                            # observed mz_diff = mz2 - mz1 (always positive for mz2 > mz1)
                            #
                            # CRITICAL FIX: Correct assignment logic
                            # When mz_diff matches positive catalog_shift:
                            #   - from_adduct is the heavier adduct (higher mass shift)
                            #   - to_adduct is the lighter adduct (lower mass shift)
                            #   - Higher m/z feature should get the heavier adduct (from_adduct)
                            #   - Lower m/z feature should get the lighter adduct (to_adduct)

                            if abs(mz_diff - catalog_shift) <= abs(mz_diff - (-catalog_shift)):
                                # mz_diff matches catalog_shift direction
                                if catalog_shift > 0:
                                    # from_adduct is heavier, to_adduct is lighter
                                    from_feature = feature2  # Higher m/z gets heavier adduct
                                    to_feature = feature1  # Lower m/z gets lighter adduct
                                    from_adduct_name = best_rel["from_adduct"]  # Heavier adduct
                                    to_adduct_name = best_rel["to_adduct"]  # Lighter adduct
                                else:
                                    # from_adduct is lighter, to_adduct is heavier
                                    from_feature = feature1  # Lower m/z gets lighter adduct
                                    to_feature = feature2  # Higher m/z gets heavier adduct
                                    from_adduct_name = best_rel["from_adduct"]  # Lighter adduct
                                    to_adduct_name = best_rel["to_adduct"]  # Heavier adduct
                            else:
                                # mz_diff matches reverse direction of catalog_shift
                                if catalog_shift > 0:
                                    # Reverse: from_adduct becomes lighter, to_adduct becomes heavier
                                    from_feature = feature1  # Lower m/z gets lighter adduct
                                    to_feature = feature2  # Higher m/z gets heavier adduct
                                    from_adduct_name = best_rel["to_adduct"]  # Now lighter adduct
                                    to_adduct_name = best_rel["from_adduct"]  # Now heavier adduct
                                else:
                                    # Reverse: from_adduct becomes heavier, to_adduct becomes lighter
                                    from_feature = feature2  # Higher m/z gets heavier adduct
                                    to_feature = feature1  # Lower m/z gets lighter adduct
                                    from_adduct_name = best_rel["to_adduct"]  # Now heavier adduct
                                    to_adduct_name = best_rel["from_adduct"]  # Now lighter adduct

                        # Get adduct details from catalog
                        from_adduct_info = adduct_info.get(from_adduct_name, {})
                        to_adduct_info = adduct_info.get(to_adduct_name, {})

                        # Calculate neutral masses
                        from_charge = from_adduct_info.get("charge", 1)
                        to_charge = to_adduct_info.get("charge", 1)
                        from_mass_shift = from_adduct_info.get("mass_shift", 1.007825)
                        to_mass_shift = to_adduct_info.get("mass_shift", 1.007825)

                        from_neutral_mass = from_feature["mz"] * abs(from_charge) - from_mass_shift
                        to_neutral_mass = to_feature["mz"] * abs(to_charge) - to_mass_shift

                        # Smart conservative check: prevent inappropriate assignments to isolated features
                        # Check if both features are isolated (single-member groups) with [M+?]1+ assignments
                        def is_isolated_unknown_feature(feature):
                            """Check if a feature is isolated with unknown adduct"""
                            if not feature["adduct_top"] or "[M+?]" not in feature["adduct_top"]:
                                return False  # Not unknown, safe to process

                            # Check group size
                            try:
                                feature_row = study.consensus_df.filter(
                                    study.consensus_df["consensus_uid"] == feature["consensus_uid"]
                                )
                                if len(feature_row) > 0:
                                    adduct_group = feature_row["adduct_group"].iloc[0]
                                    if adduct_group > 0:
                                        group_members = study.consensus_df.filter(
                                            study.consensus_df["adduct_group"] == adduct_group
                                        )
                                        return len(group_members) <= 1  # Isolated if group size <= 1
                            except Exception:
                                pass
                            return True  # Default to isolated if can't determine

                        from_isolated = is_isolated_unknown_feature(from_feature)
                        to_isolated = is_isolated_unknown_feature(to_feature)

                        # Only skip assignment if BOTH features are isolated AND would get the SAME adduct
                        # (This prevents inappropriate duplicate assignments to isolated features)
                        skip_assignment = from_isolated and to_isolated and from_adduct_name == to_adduct_name

                        if skip_assignment:
                            study.logger.debug(
                                f"Skipping inappropriate assignment: both isolated features would get {from_adduct_name} "
                                f"(UIDs {from_feature['consensus_uid']}, {to_feature['consensus_uid']})"
                            )
                            continue  # Skip this pair, continue to next relationship

                        # Store updates (legitimate pair or at least one feature already has specific adduct)
                        adduct_updates[from_feature["consensus_uid"]] = {
                            "adduct_top": from_adduct_name,
                            "adduct_charge_top": from_charge,
                            "adduct_mass_neutral_top": from_neutral_mass,
                            "adduct_mass_shift_top": from_mass_shift,
                        }

                        adduct_updates[to_feature["consensus_uid"]] = {
                            "adduct_top": to_adduct_name,
                            "adduct_charge_top": to_charge,
                            "adduct_mass_neutral_top": to_neutral_mass,
                            "adduct_mass_shift_top": to_mass_shift,
                        }

                        updated_count += 2
                        study.logger.debug(
                            f"Identified adduct pair: {from_adduct_name} (m/z {from_feature['mz']:.4f}) "
                            f"<-> {to_adduct_name} (m/z {to_feature['mz']:.4f}), "
                            f"RT {rt1:.2f}s, Δm/z {mz_diff:.4f}"
                        )
                        break  # Found match, no need to check other relationships

    # Apply updates to consensus_df
    if adduct_updates:
        # Prepare update data
        consensus_uids = study.consensus_df["consensus_uid"].to_list()

        new_adduct_top = []
        new_adduct_charge_top = []
        new_adduct_mass_neutral_top = []
        new_adduct_mass_shift_top = []

        for uid in consensus_uids:
            if uid in adduct_updates:
                update = adduct_updates[uid]
                new_adduct_top.append(update["adduct_top"])
                new_adduct_charge_top.append(update["adduct_charge_top"])
                new_adduct_mass_neutral_top.append(update["adduct_mass_neutral_top"])
                new_adduct_mass_shift_top.append(update["adduct_mass_shift_top"])
            else:
                # Keep existing values
                row_idx = consensus_uids.index(uid)
                row = study.consensus_df.row(row_idx, named=True)
                new_adduct_top.append(row.get("adduct_top"))
                new_adduct_charge_top.append(row.get("adduct_charge_top"))
                new_adduct_mass_neutral_top.append(row.get("adduct_mass_neutral_top"))
                new_adduct_mass_shift_top.append(row.get("adduct_mass_shift_top"))

        # Update the DataFrame
        study.consensus_df = study.consensus_df.with_columns([
            pl.Series("adduct_top", new_adduct_top),
            pl.Series("adduct_charge_top", new_adduct_charge_top),
            pl.Series("adduct_mass_neutral_top", new_adduct_mass_neutral_top),
            pl.Series("adduct_mass_shift_top", new_adduct_mass_shift_top),
        ])
        study.logger.info(f"Adduct information updated for {updated_count} consensus features.")
    else:
        study.logger.debug("No consensus features updated based on mass shift analysis")


def __finalize_merge(study, link_ms2, extract_ms1, min_samples):
    """Complete the merge process with final calculations and cleanup."""
    import polars as pl

    # Check if consensus_df is empty or missing required columns
    if len(study.consensus_df) == 0 or "number_samples" not in study.consensus_df.columns:
        study.logger.debug("No consensus features found or consensus_df is empty. Skipping finalize merge.")
        return

    # Validate min_samples parameter
    if min_samples is None:
        min_samples = 1
    if min_samples < 1:
        min_samples = int(min_samples * len(study.samples_df))

    # Validate that min_samples doesn't exceed the number of samples
    if min_samples > len(study.samples_df):
        study.logger.warning(
            f"min_samples ({min_samples}) exceeds the number of samples ({len(study.samples_df)}). "
            f"Setting min_samples to {len(study.samples_df)}.",
        )
        min_samples = len(study.samples_df)

    # Filter out consensus features with less than min_samples features
    l1 = len(study.consensus_df)
    study.consensus_df = study.consensus_df.filter(
        pl.col("number_samples") >= min_samples,
    )
    study.logger.debug(
        f"Filtered {l1 - len(study.consensus_df)} consensus features with less than {min_samples} samples.",
    )

    # Filter out consensus mapping with less than min_samples features
    study.consensus_mapping_df = study.consensus_mapping_df.filter(
        pl.col("consensus_uid").is_in(study.consensus_df["consensus_uid"].to_list()),
    )

    # Calculate the completeness of the consensus map
    # Log completion with tight cluster metrics
    if len(study.consensus_df) > 0 and len(study.samples_df) > 0:
        c = len(study.consensus_mapping_df) / len(study.consensus_df) / len(study.samples_df)

        # Count tight clusters with specified thresholds
        tight_clusters = _count_tight_clusters(study, mz_tol=0.04, rt_tol=0.3)

        study.logger.success(
            f"Merging completed. Consensus features: {len(study.consensus_df)}. "
            f"Completeness: {c:.2f}. Tight clusters: {tight_clusters}.",
        )
    else:
        study.logger.warning(
            f"Merging completed with empty result. Consensus features: {len(study.consensus_df)}. "
            f"This may be due to min_samples ({min_samples}) being too high for the available data.",
        )

    # add iso data from raw files.
    if link_ms2:
        study.find_ms2()
    if extract_ms1:
        study.find_iso()


def __merge_feature_lookup(study_obj, features_df):
    """
    Optimized feature lookup creation using Polars operations.
    """
    study_obj.logger.debug("Creating optimized feature lookup...")
    start_time = time.time()

    # Use Polars select for faster conversion
    feature_columns = [
        "feature_uid",
        "sample_uid",
        "rt",
        "mz",
        "rt_start",
        "rt_end",
        "rt_delta",
        "mz_start",
        "mz_end",
        "inty",
        "chrom_coherence",
        "chrom_prominence",
        "chrom_prominence_scaled",
        "chrom_height_scaled",
        "iso",
        "charge",
        "ms2_scans",
        "adduct",
        "adduct_mass",
    ]

    # Filter to only existing columns
    existing_columns = [col for col in feature_columns if col in features_df.columns]

    # Convert to dictionary more efficiently
    selected_df = features_df.select(existing_columns)

    features_lookup = {}
    for row in selected_df.iter_rows(named=True):
        feature_uid = row["feature_uid"]
        # Keep feature_uid in the dictionary for chunked merge compatibility
        features_lookup[feature_uid] = {k: v for k, v in row.items()}

    lookup_time = time.time() - start_time
    if len(features_lookup) > 50000:
        study_obj.logger.debug(f"Feature lookup created in {lookup_time:.2f}s for {len(features_lookup)} features")
    return features_lookup


def _get_features_matrix(study, consensus_data, quant_col="inty"):
    """
    Create a local intensity matrix from features_df for correlation calculations.

    Args:
        study: Study object with features_df and samples_df
        consensus_data: List of consensus feature dictionaries
        quant_col: Column name to use for quantification (default: "inty")

    Returns:
        pandas.DataFrame: Matrix with consensus_uid as index, sample names as columns
    """
    import pandas as pd
    import numpy as np

    # Get all sample names
    sample_names = study.samples_df["sample_name"].to_list()
    consensus_uids = [int(f["consensus_uid"]) for f in consensus_data]

    # Initialize matrix with zeros
    matrix_data = pd.DataFrame(
        index=pd.Index(consensus_uids, name="consensus_uid"), columns=sample_names, data=0.0, dtype=float
    )

    study.logger.debug(f"Building local features matrix: {len(consensus_uids)} features x {len(sample_names)} samples")

    # Fill matrix with actual intensity values
    features_df_pandas = study.features_df.to_pandas()
    samples_df_pandas = study.samples_df.to_pandas()
    consensus_mapping_pandas = study.consensus_mapping_df.to_pandas()

    # Create sample_uid to sample_name mapping
    uid_to_name = dict(zip(samples_df_pandas["sample_uid"], samples_df_pandas["sample_name"]))

    # For each consensus feature, get intensities from all samples
    for consensus_uid in consensus_uids:
        # Get all feature_uids that map to this consensus_uid
        feature_mappings = consensus_mapping_pandas[consensus_mapping_pandas["consensus_uid"] == consensus_uid]

        for _, mapping in feature_mappings.iterrows():
            feature_uid = mapping["feature_uid"]
            sample_uid = mapping["sample_uid"]
            sample_name = uid_to_name.get(sample_uid, f"sample_{sample_uid}")

            # Get intensity for this feature
            feature_row = features_df_pandas[
                (features_df_pandas["feature_uid"] == feature_uid) & (features_df_pandas["sample_uid"] == sample_uid)
            ]

            if len(feature_row) > 0:
                intensity = feature_row[quant_col].iloc[0]
                if pd.notna(intensity):
                    matrix_data.loc[consensus_uid, sample_name] = float(intensity)

    # Convert any remaining NaN to 0
    matrix_data = matrix_data.fillna(0.0)

    study.logger.debug(f"Local matrix built successfully with shape {matrix_data.shape}")

    return matrix_data


def _get_adduct_deltas_with_likelihood(study):
    """
    Extract all pairwise mass differences between adducts with joint likelihood scoring.

    Args:
        study: Study object with _get_adducts method

    Returns:
        List of tuples: (mass_delta, joint_likelihood, adduct1_name, adduct2_name)
        Sorted by joint_likelihood descending (most likely pairs first)
    """
    try:
        adducts_df = study._get_adducts()

        if adducts_df is None or adducts_df.is_empty():
            study.logger.warning("No adducts dataframe available for study")
            return []

        # Convert to pandas for easier manipulation
        adducts_pd = adducts_df.to_pandas()

        # Check if we have likelihood/probability information
        likelihood_col = None
        for col in ["likelihood", "probability", "freq", "frequency", "score"]:
            if col in adducts_pd.columns:
                likelihood_col = col
                break

        # If no likelihood column, estimate based on adduct type
        if likelihood_col is None:
            adducts_pd["estimated_likelihood"] = adducts_pd.apply(_estimate_adduct_likelihood, axis=1)
            likelihood_col = "estimated_likelihood"

        # Get mass column (try different possible column names)
        mass_col = None
        for col_name in ["mass_shift", "mass", "mass_shift_da", "mass_da"]:
            if col_name in adducts_pd.columns:
                mass_col = col_name
                break

        if mass_col is None:
            study.logger.warning(
                f"No mass column found in adducts dataframe. Available columns: {list(adducts_pd.columns)}"
            )
            return []

        # Calculate all pairwise differences with joint likelihoods
        adduct_pairs = []
        for i in range(len(adducts_pd)):
            for j in range(i + 1, len(adducts_pd)):
                row_i = adducts_pd.iloc[i]
                row_j = adducts_pd.iloc[j]

                # Skip if masses are NaN or invalid
                if (hasattr(row_i[mass_col], "__iter__") and not isinstance(row_i[mass_col], str)) or (
                    hasattr(row_j[mass_col], "__iter__") and not isinstance(row_j[mass_col], str)
                ):
                    continue

                mass_i = float(row_i[mass_col])
                mass_j = float(row_j[mass_col])
                delta = abs(mass_i - mass_j)

                if delta > 0.1:  # Only meaningful mass differences
                    # Joint likelihood is sum of individual likelihoods
                    joint_likelihood = float(row_i[likelihood_col]) + float(row_j[likelihood_col])

                    adduct1_name = row_i.get("adduct", row_i.get("name", f"adduct_{i}"))
                    adduct2_name = row_j.get("adduct", row_j.get("name", f"adduct_{j}"))

                    # CRITICAL FIX: Order adducts consistently from lower mass to higher mass
                    # This ensures consistent assignment: lower mass adduct = from_adduct, higher mass adduct = to_adduct
                    if mass_i <= mass_j:
                        # row_i has lower or equal mass shift -> from_adduct
                        # row_j has higher mass shift -> to_adduct
                        adduct_pairs.append((round(delta, 4), joint_likelihood, adduct1_name, adduct2_name))
                    else:
                        # row_j has lower mass shift -> from_adduct
                        # row_i has higher mass shift -> to_adduct
                        adduct_pairs.append((round(delta, 4), joint_likelihood, adduct2_name, adduct1_name))

        # Sort by joint likelihood descending (most likely pairs first)
        adduct_pairs.sort(key=lambda x: x[1], reverse=True)

        study.logger.debug(f"Extracted {len(adduct_pairs)} adduct pairs with likelihood scoring")
        return adduct_pairs

    except Exception as e:
        study.logger.warning(
            f"Could not extract adduct deltas with likelihood: {e}. No adducts defined - returning empty list."
        )
        return []


def _estimate_adduct_likelihood(adduct_row):
    """
    Estimate likelihood of an adduct based on common knowledge.

    Args:
        adduct_row: pandas Series with adduct information

    Returns:
        float: Estimated likelihood (0.0 to 1.0)
    """
    adduct_name = str(adduct_row.get("adduct", adduct_row.get("name", ""))).lower()

    # Common likelihood estimates based on adduct frequency in positive mode
    likelihood_map = {
        "[m+h]": 0.9,  # Most common
        "[m+na]": 0.7,  # Very common
        "[m+nh4]": 0.6,  # Common
        "[m+k]": 0.3,  # Less common
        "[m+2h]": 0.2,  # Doubly charged, less frequent
        "[m+3h]": 0.1,  # Triply charged, rare
        "[m+h-h2o]": 0.4,  # Loss adducts, moderately common
    }

    # Find best match
    for pattern, likelihood in likelihood_map.items():
        if pattern in adduct_name:
            return likelihood

    # Default for unknown adducts
    return 0.2


def _get_adduct_deltas(study):
    """
    Extract all pairwise mass differences between adducts from study adducts data.

    Args:
        study: Study object with _get_adducts method

    Returns:
        List of mass differences (deltas) for adduct filtering
    """
    # Use the enhanced function and extract just the deltas for backward compatibility
    adduct_pairs = _get_adduct_deltas_with_likelihood(study)
    return [pair[0] for pair in adduct_pairs]  # Extract just the mass deltas


def _fast_correlation(vec1, vec2):
    """
    Fast Pearson correlation coefficient calculation.
    Optimized for repeated use in tight loops.
    """
    if len(vec1) != len(vec2):
        return 0.0

    # Remove NaN values and corresponding positions
    mask = ~(np.isnan(vec1) | np.isnan(vec2))
    if np.sum(mask) < 2:  # Need at least 2 valid points
        return 0.0

    v1 = vec1[mask]
    v2 = vec2[mask]

    # Fast correlation using numpy built-in
    try:
        corr_matrix = np.corrcoef(v1, v2)
        return corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0
    except Exception:
        return 0.0


def __merge_adduct_grouping(study, consensus_data, rt_tol, mz_tol):
    """
    Groups consensus features that represent the same molecule with different adducts.
    Uses multi-step filtering:
    1. Build local intensity matrix once
    2. RT coelution filtering with spatial indexing
    3. Mass shift validation with hash lookup
    4. Hierarchical boss structure (prevent transitivity)
    5. Correlation-based confirmation
    6. Intensity-based ranking for final selection

    Args:
        study: Study object
        consensus_data: List of consensus feature dictionaries
        rt_tol: Retention time tolerance (seconds)
        mz_tol: M/z tolerance (Da)

    Returns:
        Tuple of (adduct_group_list, adduct_of_list)
    """

    if not consensus_data:
        return [], []

    n_features = len(consensus_data)
    study.logger.info(f"Starting adduct grouping for {n_features} features")

    # Step 1: Build local intensity matrix ONCE
    try:
        intensity_matrix_pd = _get_features_matrix(study, consensus_data, quant_col="inty")

        if intensity_matrix_pd is None or len(intensity_matrix_pd) == 0:
            study.logger.warning("Could not build local intensity matrix - creating single-feature groups")
            adduct_group_list = list(range(1, len(consensus_data) + 1))
            adduct_of_list = [0] * len(consensus_data)
            return adduct_group_list, adduct_of_list

        study.logger.debug(
            f"Built local intensity matrix: {len(intensity_matrix_pd)} features x {len(intensity_matrix_pd.columns)} samples"
        )

    except Exception as e:
        study.logger.warning(f"Could not build local intensity matrix: {e}. Creating single-feature groups.")
        adduct_group_list = list(range(1, len(consensus_data) + 1))
        adduct_of_list = [0] * len(consensus_data)
        return adduct_group_list, adduct_of_list

    # Step 2: Get adduct pairs with likelihood information and build hash map for fast lookup
    adduct_pairs_with_likelihood = _get_adduct_deltas_with_likelihood(study)
    study.logger.debug(f"Using {len(adduct_pairs_with_likelihood)} adduct pairs with likelihood scoring")

    # Build hash map for O(1) mass shift lookup
    mass_shift_map = {}  # rounded_delta -> [(likelihood, adduct1, adduct2), ...]
    for mass_delta, joint_likelihood, adduct1, adduct2 in adduct_pairs_with_likelihood:
        key = round(mass_delta / mz_tol) * mz_tol  # Round to tolerance grid
        if key not in mass_shift_map:
            mass_shift_map[key] = []
        mass_shift_map[key].append((joint_likelihood, adduct1, adduct2))

    # Sort each mass shift group by likelihood (highest first)
    for key in mass_shift_map:
        mass_shift_map[key].sort(key=lambda x: x[0], reverse=True)

    # Step 3: Pre-compute feature properties and sort by RT for spatial filtering
    feature_props = []
    for i, feature in enumerate(consensus_data):
        uid = feature["consensus_uid"]
        rt = feature["rt"]
        mz = feature["mz"]
        intensity = feature.get("inty_mean", 0)

        # Get matrix vector once
        matrix_vector = intensity_matrix_pd.loc[uid].values if uid in intensity_matrix_pd.index else None

        feature_props.append({
            "index": i,
            "uid": uid,
            "rt": rt,
            "mz": mz,
            "intensity": intensity,
            "vector": matrix_vector,
            "feature": feature,
        })

    # Sort by RT for efficient spatial filtering
    feature_props.sort(key=lambda x: x["rt"])

    # Initialize grouping structures
    uid_to_boss = {}  # Hierarchical structure: uid -> boss_uid
    boss_to_members = {}  # boss_uid -> [member_uids]
    processed_uids = set()

    # Step 4: Process features with optimized RT filtering
    for i, boss_prop in enumerate(feature_props):
        boss_uid = boss_prop["uid"]

        if boss_uid in processed_uids:
            continue

        if boss_prop["vector"] is None:
            processed_uids.add(boss_uid)
            continue

        # Initialize as boss
        if boss_uid not in uid_to_boss:
            uid_to_boss[boss_uid] = boss_uid
            boss_to_members[boss_uid] = []

        boss_rt = boss_prop["rt"]
        boss_mz = boss_prop["mz"]
        boss_vector = boss_prop["vector"]

        # Step 5: Efficient RT coelution filtering using sorted array
        candidate_pairs = []

        # Search backwards from current position
        j = i - 1
        while j >= 0 and (boss_rt - feature_props[j]["rt"]) <= rt_tol:
            candidate = feature_props[j]
            if candidate["uid"] not in processed_uids and candidate["vector"] is not None:
                if candidate["uid"] not in uid_to_boss or uid_to_boss[candidate["uid"]] == candidate["uid"]:
                    # Calculate mz difference and check mass shift
                    mz_diff = abs(boss_mz - candidate["mz"])
                    mass_shift_key = round(mz_diff / mz_tol) * mz_tol

                    if mass_shift_key in mass_shift_map:
                        likelihood, adduct1, adduct2 = mass_shift_map[mass_shift_key][0]  # Best likelihood
                        candidate_pairs.append((candidate, likelihood, (adduct1, adduct2)))
            j -= 1

        # Search forwards from current position
        j = i + 1
        while j < len(feature_props) and (feature_props[j]["rt"] - boss_rt) <= rt_tol:
            candidate = feature_props[j]
            if candidate["uid"] not in processed_uids and candidate["vector"] is not None:
                if candidate["uid"] not in uid_to_boss or uid_to_boss[candidate["uid"]] == candidate["uid"]:
                    # Calculate mz difference and check mass shift
                    mz_diff = abs(boss_mz - candidate["mz"])
                    mass_shift_key = round(mz_diff / mz_tol) * mz_tol

                    if mass_shift_key in mass_shift_map:
                        likelihood, adduct1, adduct2 = mass_shift_map[mass_shift_key][0]  # Best likelihood
                        candidate_pairs.append((candidate, likelihood, (adduct1, adduct2)))
            j += 1

        # Sort candidates by likelihood (descending) to prioritize chemically meaningful pairs
        candidate_pairs.sort(key=lambda x: x[1], reverse=True)

        # Step 6: Process candidates in likelihood priority order
        for candidate_prop, likelihood, adduct_info in candidate_pairs:
            candidate_uid = candidate_prop["uid"]
            candidate_vector = candidate_prop["vector"]

            # Correlation confirmation with optimized threshold
            try:
                correlation = _fast_correlation(boss_vector, candidate_vector)

                if correlation < 0.5:  # More permissive for legitimate adduct relationships
                    continue

            except Exception:
                continue

            # Step 7: Hierarchical assignment (merge groups if needed)
            if candidate_uid in boss_to_members:
                old_members = boss_to_members[candidate_uid].copy()
                del boss_to_members[candidate_uid]

                # Reassign old members to new boss
                for member in old_members:
                    uid_to_boss[member] = boss_uid
                    boss_to_members[boss_uid].append(member)

            # Assign candidate to current boss
            uid_to_boss[candidate_uid] = boss_uid
            boss_to_members[boss_uid].append(candidate_uid)
            processed_uids.add(candidate_uid)

        processed_uids.add(boss_uid)

    # Step 8: Intensity-based ranking within groups (optimized)
    for boss_uid in list(boss_to_members.keys()):
        members = boss_to_members[boss_uid]
        if len(members) == 0:
            continue

        all_group_members = [boss_uid] + members

        # Find member with highest intensity efficiently
        max_intensity = -1
        new_boss = boss_uid

        for member_uid in all_group_members:
            # Find member_uid in feature_props
            member_intensity = next((fp["intensity"] for fp in feature_props if fp["uid"] == member_uid), 0)
            if member_intensity > max_intensity:
                max_intensity = member_intensity
                new_boss = member_uid

        # Update boss if needed
        if new_boss != boss_uid:
            boss_to_members[new_boss] = [m for m in all_group_members if m != new_boss]
            del boss_to_members[boss_uid]

            # Update all member references
            for member in all_group_members:
                uid_to_boss[member] = new_boss

    # Count and log results
    total_groups = len(boss_to_members)
    multi_member_groups = sum(1 for members in boss_to_members.values() if len(members) > 0)
    total_grouped_features = sum(len(members) + 1 for members in boss_to_members.values())

    study.logger.info(
        f"Grouping results: {total_groups} groups ({multi_member_groups} multi-member, {total_grouped_features} features)"
    )

    # Step 9: Convert to return format (optimized)
    uid_to_index = {fp["uid"]: fp["index"] for fp in feature_props}
    adduct_group_list = [0] * n_features
    adduct_of_list = [0] * n_features

    group_counter = 1
    for boss_uid, members in boss_to_members.items():
        # Assign boss
        boss_idx = uid_to_index[boss_uid]
        adduct_group_list[boss_idx] = group_counter
        adduct_of_list[boss_idx] = 0

        # Assign members
        for member_uid in members:
            member_idx = uid_to_index[member_uid]
            adduct_group_list[member_idx] = group_counter
            adduct_of_list[member_idx] = boss_uid

        group_counter += 1

    # Handle ungrouped features
    for i in range(n_features):
        if adduct_group_list[i] == 0:
            adduct_group_list[i] = group_counter
            adduct_of_list[i] = 0
            group_counter += 1

    return adduct_group_list, adduct_of_list


def _fast_correlation(x, y):
    """
    Fast correlation coefficient calculation for consensus matrix data.

    In the consensus matrix:
    - Negative values (typically -1.0) indicate missing features
    - Zero and positive values are actual intensities
    - Only consider intensities >= 1000 for meaningful correlation

    Args:
        x, y: numpy arrays of the same length

    Returns:
        Correlation coefficient (float), 0 if cannot be calculated
    """
    import numpy as np

    # For consensus matrix: exclude negative values (missing features) and very low intensities
    # Use a very low threshold since processed matrix values are often scaled/normalized
    valid = ~(np.isnan(x) | np.isnan(y) | (x < 0) | (y < 0) | (x < 0.1) | (y < 0.1))

    if np.sum(valid) < 3:  # Need at least 3 valid pairs
        return 0.0

    x_valid = x[valid]
    y_valid = y[valid]

    # If all values are the same (e.g., all zeros), correlation is undefined
    if np.var(x_valid) == 0 or np.var(y_valid) == 0:
        return 0.0

    # Fast correlation using numpy
    try:
        correlation_matrix = np.corrcoef(x_valid, y_valid)
        correlation = correlation_matrix[0, 1]

        # Handle NaN result
        if np.isnan(correlation):
            return 0.0

        return correlation

    except Exception:
        return 0.0
