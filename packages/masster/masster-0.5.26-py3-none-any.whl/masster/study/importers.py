"""
import.py

Module providing import functionality for Study class, specifically for importing
oracle identification data into consensus features.
"""

from __future__ import annotations

import os
import pandas as pd
import polars as pl


def import_oracle(
    self,
    folder,
    min_id_level=None,
    max_id_level=None,
):
    """
    Import oracle identification data and map it to consensus features.

    This method reads oracle identification results from folder/diag/annotation_full.csv
    and creates lib_df and id_df DataFrames with detailed library and identification information.
    It also updates consensus_df with top identification results.

    Parameters:
        folder (str): Path to oracle folder containing diag/annotation_full.csv
        min_id_level (int, optional): Minimum identification level to include
        max_id_level (int, optional): Maximum identification level to include

    Returns:
        None: Updates consensus_df, creates lib_df and id_df in-place with oracle identification data

    Raises:
        FileNotFoundError: If the oracle annotation file doesn't exist
        ValueError: If consensus_df is empty or doesn't have required columns

    Example:
        >>> study.import_oracle(
        ...     folder="path/to/oracle_results",
        ...     min_id_level=2,
        ...     max_id_level=4
        ... )
    """

    self.logger.info(f"Starting oracle import from folder: {folder}")

    # Validate inputs
    if self.consensus_df is None or self.consensus_df.is_empty():
        raise ValueError("consensus_df is empty or not available. Run merge() first.")

    if "consensus_uid" not in self.consensus_df.columns:
        raise ValueError("consensus_df must contain 'consensus_uid' column")

    # Check if oracle file exists
    oracle_file_path = os.path.join(folder, "diag", "annotation_full.csv")
    if not os.path.exists(oracle_file_path):
        raise FileNotFoundError(f"Oracle annotation file not found: {oracle_file_path}")

    self.logger.debug(f"Loading oracle data from: {oracle_file_path}")

    try:
        # Read oracle data using pandas first for easier processing
        oracle_data = pd.read_csv(oracle_file_path)
        self.logger.info(f"Oracle data loaded successfully with {len(oracle_data)} rows")
    except Exception as e:
        self.logger.error(f"Could not read {oracle_file_path}: {e}")
        raise

    # Extract consensus_uid from scan_title column (format: "uid:XYZ, ...")
    self.logger.debug("Extracting consensus UIDs from oracle scan_title using pattern 'uid:(\\d+)'")
    oracle_data["consensus_uid"] = oracle_data["scan_title"].str.extract(r"uid:(\d+)", expand=False)

    # Remove rows where consensus_uid extraction failed
    initial_count = len(oracle_data)
    oracle_data = oracle_data.dropna(subset=["consensus_uid"])
    oracle_data["consensus_uid"] = oracle_data["consensus_uid"].astype(int)

    self.logger.debug(f"Extracted consensus UIDs for {len(oracle_data)}/{initial_count} oracle entries")

    # Apply id_level filters if specified
    if min_id_level is not None:
        oracle_data = oracle_data[oracle_data["level"] >= min_id_level]
        self.logger.debug(f"After min_id_level filter ({min_id_level}): {len(oracle_data)} entries")

    if max_id_level is not None:
        oracle_data = oracle_data[oracle_data["level"] <= max_id_level]
        self.logger.debug(f"After max_id_level filter ({max_id_level}): {len(oracle_data)} entries")

    if len(oracle_data) == 0:
        self.logger.warning("No oracle entries remain after filtering")
        return

    # === CREATE LIB_DF ===
    self.logger.debug("Creating lib_df from Oracle annotation data")
    self.logger.debug(f"Oracle data shape before lib_df creation: {oracle_data.shape}")

    # Create unique lib_uid for each library entry
    oracle_data["lib_uid"] = range(len(oracle_data))

    # Map Oracle columns to lib_df schema
    lib_data = []
    for _, row in oracle_data.iterrows():
        # Convert cmpd_uid to integer, using lib_uid as fallback
        cmpd_uid = row["lib_uid"]  # Use lib_uid as integer compound identifier
        try:
            if row.get("lib_id") is not None:
                cmpd_uid = int(float(str(row["lib_id"])))  # Convert to int, handling potential float strings
        except (ValueError, TypeError):
            pass  # Keep lib_uid as fallback

        lib_entry = {
            "lib_uid": row["lib_uid"],
            "cmpd_uid": cmpd_uid,  # Integer compound identifier
            "source_id": "LipidOracle",  # Fixed source identifier
            "name": row.get("name", None),
            "shortname": row.get("species", None),
            "class": row.get("hg", None),
            "smiles": None,  # Not available in Oracle data
            "inchi": None,  # Not available in Oracle data
            "inchikey": None,  # Not available in Oracle data
            "formula": row.get("formula", None),
            "iso": 0,  # Fixed isotope value
            "adduct": row.get("ion", None),
            "probability": row.get("score", None),
            "m": None,  # Would need to calculate from formula
            "z": 1 if row.get("ion", "").find("+") != -1 else (-1 if row.get("ion", "").find("-") != -1 else None),
            "mz": row.get("mz", None),  # Use mz column from annotation_full.csv
            "rt": None,  # Set to null as requested
            "quant_group": None,  # Set to null as requested
            "db_id": row.get("lib_id", None),
            "db": row.get("lib", None),
        }
        lib_data.append(lib_entry)

    self.logger.debug(f"Created {len(lib_data)} lib_data entries")

    # Create lib_df as Polars DataFrame with error handling for mixed types
    try:
        lib_df_temp = pl.DataFrame(lib_data)
    except Exception as e:
        self.logger.warning(f"Error creating lib_df with polars: {e}")
        # Fallback: convert to pandas first, then to polars
        lib_df_pandas = pd.DataFrame(lib_data)
        lib_df_temp = pl.from_pandas(lib_df_pandas)

    # Ensure uniqueness by name and adduct combination
    # Sort by lib_uid and keep first occurrence (earliest in processing order)
    self.lib_df = lib_df_temp.sort("lib_uid").unique(subset=["name", "adduct"], keep="first")

    self.logger.info(
        f"Created lib_df with {len(self.lib_df)} library entries ({len(lib_data) - len(self.lib_df)} duplicates removed)"
    )

    # === CREATE ID_DF ===
    self.logger.debug("Creating id_df from Oracle identification matches")

    # Create identification matches
    id_data = []
    for _, row in oracle_data.iterrows():
        # Use dmz from annotation_full.csv directly for mz_delta
        mz_delta = None
        if row.get("dmz") is not None:
            try:
                mz_delta = float(row["dmz"])
            except (ValueError, TypeError):
                pass

        # Use rt_err from annotation_full.csv for rt_delta, None if NaN
        rt_delta = None
        rt_err_value = row.get("rt_err")
        if rt_err_value is not None and not (isinstance(rt_err_value, float) and pd.isna(rt_err_value)):
            try:
                rt_delta = float(rt_err_value)
            except (ValueError, TypeError):
                pass

        # Create matcher as "lipidoracle-" + score_metric from annotation_full.csv
        matcher = "lipidoracle"  # default fallback
        if row.get("score_metric") is not None:
            try:
                score_metric = str(row["score_metric"])
                matcher = f"lipidoracle-{score_metric}"
            except (ValueError, TypeError):
                pass

        id_entry = {
            "consensus_uid": row["consensus_uid"],
            "lib_uid": row["lib_uid"],
            "mz_delta": mz_delta,
            "rt_delta": rt_delta,
            "matcher": matcher,
            "score": row.get("score", None),
        }
        id_data.append(id_entry)

    # Create id_df as Polars DataFrame with error handling
    try:
        id_df_temp = pl.DataFrame(id_data)
    except Exception as e:
        self.logger.warning(f"Error creating id_df with polars: {e}")
        # Fallback: convert to pandas first, then to polars
        id_df_pandas = pd.DataFrame(id_data)
        id_df_temp = pl.from_pandas(id_df_pandas)

    # Filter id_df to only include lib_uids that exist in the final unique lib_df
    unique_lib_uids = self.lib_df.select("lib_uid").to_series()
    self.id_df = id_df_temp.filter(pl.col("lib_uid").is_in(unique_lib_uids))

    self.logger.info(f"Created id_df with {len(self.id_df)} identification matches")

    # === UPDATE CONSENSUS_DF (existing functionality) ===
    self.logger.debug("Updating consensus_df with top identification results")

    # Convert to polars for efficient joining with error handling
    try:
        oracle_pl = pl.DataFrame(oracle_data)
    except Exception as e:
        self.logger.warning(f"Error converting oracle_data to polars: {e}")
        # Convert using from_pandas properly
        oracle_pl = pl.from_pandas(oracle_data.reset_index(drop=True))

    # Group by consensus_uid and select the best identification (highest level)
    # In case of ties, take the first one
    best_ids = (
        oracle_pl.group_by("consensus_uid")
        .agg([pl.col("level").max().alias("max_level")])
        .join(oracle_pl, on="consensus_uid")
        .filter(pl.col("level") == pl.col("max_level"))
        .group_by("consensus_uid")
        .first()  # In case of ties, take the first
    )

    self.logger.debug(f"Selected best identifications for {len(best_ids)} consensus features")

    # Prepare the identification columns
    id_columns = {
        "id_top_name": best_ids.select("consensus_uid", "name"),
        "id_top_adduct": best_ids.select("consensus_uid", "ion"),
        "id_top_class": best_ids.select("consensus_uid", "hg"),
        "id_top_score": best_ids.select("consensus_uid", pl.col("score").round(3).alias("score")),
        "id_source": best_ids.select(
            "consensus_uid",
            pl.when(pl.col("level") == 1)
            .then(pl.lit("lipidoracle ms1"))
            .otherwise(pl.lit("lipidoracle ms2"))
            .alias("id_source"),
        ),
    }

    # Initialize identification columns in consensus_df if they don't exist
    for col_name in id_columns.keys():
        if col_name not in self.consensus_df.columns:
            if col_name == "id_top_score":
                self.consensus_df = self.consensus_df.with_columns(pl.lit(None, dtype=pl.Float64).alias(col_name))
            else:
                self.consensus_df = self.consensus_df.with_columns(pl.lit(None, dtype=pl.String).alias(col_name))

    # Update consensus_df with oracle identifications
    for col_name, id_data_col in id_columns.items():
        oracle_column = id_data_col.columns[1]  # second column (after consensus_uid)

        # Create update dataframe
        update_data = id_data_col.rename({oracle_column: col_name})

        # Join and update
        self.consensus_df = (
            self.consensus_df.join(update_data, on="consensus_uid", how="left", suffix="_oracle")
            .with_columns(pl.coalesce([f"{col_name}_oracle", col_name]).alias(col_name))
            .drop(f"{col_name}_oracle")
        )

    # Replace NaN values with None in identification columns
    id_col_names = ["id_top_name", "id_top_adduct", "id_top_class", "id_top_score", "id_source"]
    for col_name in id_col_names:
        if col_name in self.consensus_df.columns:
            # For string columns, replace empty strings and "nan" with None
            if col_name != "id_top_score":
                self.consensus_df = self.consensus_df.with_columns(
                    pl.when(
                        pl.col(col_name).is_null()
                        | (pl.col(col_name) == "")
                        | (pl.col(col_name) == "nan")
                        | (pl.col(col_name) == "NaN")
                    )
                    .then(None)
                    .otherwise(pl.col(col_name))
                    .alias(col_name)
                )
            # For numeric columns, replace NaN with None
            else:
                self.consensus_df = self.consensus_df.with_columns(
                    pl.when(pl.col(col_name).is_null() | pl.col(col_name).is_nan())
                    .then(None)
                    .otherwise(pl.col(col_name))
                    .alias(col_name)
                )

    # Count how many consensus features were updated
    updated_count = self.consensus_df.filter(pl.col("id_top_name").is_not_null()).height
    total_consensus = len(self.consensus_df)

    self.logger.success(
        f"LipidOracle import completed. {updated_count}/{total_consensus} "
        f"consensus features now have identifications ({updated_count / total_consensus * 100:.1f}%)"
    )

    # Update history
    self.update_history(
        ["import_oracle"],
        {
            "folder": folder,
            "min_id_level": min_id_level,
            "max_id_level": max_id_level,
            "updated_features": updated_count,
            "total_features": total_consensus,
            "lib_entries": len(self.lib_df),
            "id_matches": len(self.id_df),
        },
    )
