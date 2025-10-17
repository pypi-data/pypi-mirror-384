"""
lib.py

This module provides the Lib class for mass spectrometry compound library 
management and feature annotation.

The Lib class supports annotation of sample.features_df and study.consensus_df 
based on MS1 (rt, m/z, possibly isotopes) and MS2 data.

Key Features:
- **Lib Class**: Main class for managing compound libraries and annotations
- **Compound Libraries**: Load and manage compound databases with metadata
- **Adduct Calculations**: Handle various ionization adducts and charge states
- **Mass Calculations**: Precise mass calculations with adduct corrections
- **Target Matching**: Match detected features against compound libraries
- **Polarity Handling**: Support for positive and negative ionization modes
- **CSV Import**: Import compound data from CSV files with automatic adduct generation

Dependencies:
- `pyopenms`: For mass spectrometry algorithms and data structures
- `polars`: For efficient data manipulation and analysis
- `numpy`: For numerical computations and array operations
- `uuid`: For generating unique identifiers

Supported Adducts:
- Positive mode: [M+H]+, [M+Na]+, [M+K]+, [M+NH4]+, [M-H2O+H]+
- Negative mode: [M-H]-, [M+CH3COO]-, [M+HCOO]-, [M+Cl]-

Example Usage:
```python
from masster.lib import Lib

# Create library instance
lib = Lib()

# Import compounds from CSV
lib.import_csv("compounds.csv", polarity="positive")

# Access library data
print(f"Loaded {len(lib.lib_df)} compounds")
print(lib.lib_df.head())

# Annotate sample features
annotations = lib.annotate_features(sample.features_df)
```
"""

import os
import json
from typing import Optional, Union, List, Dict, Any, TYPE_CHECKING
import warnings

import polars as pl
import pyopenms as oms

if TYPE_CHECKING:
    import pandas as pd


def _calculate_formula_mass_shift(formula: str) -> float:
    """
    Calculate mass shift from formula string like "+H", "-H2O", "+Na-H", etc.

    Parameters
    ----------
    formula : str
        Formula string (e.g., "+H", "-H2O", "+Na-H")

    Returns
    -------
    float
        Mass shift in Daltons
    """
    # Standard atomic masses
    atomic_masses = {
        "H": 1.007825,
        "C": 12.0,
        "N": 14.003074,
        "O": 15.994915,
        "Na": 22.989769,
        "K": 38.963707,
        "Li": 7.016003,
        "Ca": 39.962591,
        "Mg": 23.985042,
        "Fe": 55.934938,
        "Cl": 34.968853,
        "Br": 78.918336,
        "I": 126.904473,
        "P": 30.973762,
        "S": 31.972071,
    }

    total_mass = 0.0

    # Parse formula by splitting on + and - while preserving the operators
    parts = []
    current_part = ""
    current_sign = 1

    for char in formula:
        if char == "+":
            if current_part:
                parts.append((current_sign, current_part))
            current_part = ""
            current_sign = 1
        elif char == "-":
            if current_part:
                parts.append((current_sign, current_part))
            current_part = ""
            current_sign = -1
        else:
            current_part += char

    if current_part:
        parts.append((current_sign, current_part))

    # Process each part
    for sign, part in parts:
        if not part:
            continue

        # Parse element and count (e.g., "H2O" -> H:2, O:1)
        elements = _parse_element_counts(part)

        for element, count in elements.items():
            if element in atomic_masses:
                total_mass += sign * atomic_masses[element] * count

    return total_mass


def _parse_element_counts(formula_part: str) -> Dict[str, int]:
    """Parse element counts from a formula part like 'H2O' -> {'H': 2, 'O': 1}"""
    elements = {}
    i = 0

    while i < len(formula_part):
        # Get element (uppercase letter, possibly followed by lowercase)
        element = formula_part[i]
        i += 1

        while i < len(formula_part) and formula_part[i].islower():
            element += formula_part[i]
            i += 1

        # Get count (digits following element)
        count_str = ""
        while i < len(formula_part) and formula_part[i].isdigit():
            count_str += formula_part[i]
            i += 1

        count = int(count_str) if count_str else 1
        elements[element] = elements.get(element, 0) + count

    return elements


def _format_adduct_name(components: List[Dict]) -> str:
    """Format adduct name from components like [M+H]1+ or [M+2H]2+"""
    if not components:
        return "[M]"

    # Count occurrences of each formula
    from collections import Counter

    formula_counts = Counter(comp["formula"] for comp in components)
    total_charge = sum(comp["charge"] for comp in components)

    # Build formula part with proper multipliers
    formula_parts = []
    for formula, count in sorted(
        formula_counts.items(),
    ):  # Sort for consistent ordering
        if count == 1:
            formula_parts.append(formula)
        else:
            # For multiple occurrences, use count prefix (e.g., 2H, 3Na)
            # Handle special case where formula might already start with + or -
            if formula.startswith(("+", "-")):
                sign = formula[0]
                base_formula = formula[1:]
                formula_parts.append(f"{sign}{count}{base_formula}")
            else:
                formula_parts.append(f"{count}{formula}")

    # Combine formula parts
    formula = "".join(formula_parts)

    # Format charge
    if total_charge == 0:
        charge_str = ""
    elif abs(total_charge) == 1:
        charge_str = "1+" if total_charge > 0 else "1-"
    else:
        charge_str = (
            f"{abs(total_charge)}+" if total_charge > 0 else f"{abs(total_charge)}-"
        )

    return f"[M{formula}]{charge_str}"


class Lib:
    """
    A class for managing compound libraries and feature annotation in mass spectrometry data.
    
    The Lib class provides functionality to:
    - Load compound libraries from CSV files
    - Generate adduct variants for compounds
    - Annotate MS1 features based on mass and retention time
    - Support both positive and negative ionization modes
    - Manage compound metadata (SMILES, InChI, formulas, etc.)
    
    Attributes:
        lib_df (pl.DataFrame): Polars DataFrame containing the library data with columns:
            - lib_uid: Unique identifier for each library entry
            - name: Compound name
            - smiles: SMILES notation
            - inchi: InChI identifier
            - inchikey: InChI key
            - formula: Molecular formula
            - adduct: Adduct type
            - m: Mass with adduct
            - z: Charge state
            - mz: Mass-to-charge ratio
            - rt: Retention time (if available)
    
    Example:
        >>> lib = Lib()
        >>> lib.import_csv("compounds.csv", polarity="positive")
        >>> print(f"Loaded {len(lib.lib_df)} library entries")
    """
    
    # Default adduct definitions using OpenMS format
    DEFAULT_ADDUCTS = {
        "positive": [
            "+H:1:0.65",
            "+Na:1:0.15",
            "+K:1:0.05",
            "+NH4:1:0.15",
            "-H2O:0:0.15",
        ],
        "negative": [
            "-H:-1:0.9",
            "+Cl:-1:0.1",
            "+CH2O2:0:0.15",
            "-H2O:0:0.15",
        ]
    }
    
    def __init__(self):
        """Initialize an empty Lib instance."""
        self.lib_df = None
        self._initialize_empty_dataframe()
    
    def _initialize_empty_dataframe(self):
        """Initialize an empty DataFrame with the required schema."""
        self.lib_df = pl.DataFrame({
            "lib_uid": pl.Series([], dtype=pl.Int64),
            "cmpd_uid": pl.Series([], dtype=pl.Int64),
            "source_id": pl.Series([], dtype=pl.Utf8),
            "name": pl.Series([], dtype=pl.Utf8),
            "shortname": pl.Series([], dtype=pl.Utf8),
            "class": pl.Series([], dtype=pl.Utf8),
            "smiles": pl.Series([], dtype=pl.Utf8),
            "inchi": pl.Series([], dtype=pl.Utf8),
            "inchikey": pl.Series([], dtype=pl.Utf8),
            "formula": pl.Series([], dtype=pl.Utf8),
            "iso": pl.Series([], dtype=pl.Int64),
            "adduct": pl.Series([], dtype=pl.Utf8),
            "probability": pl.Series([], dtype=pl.Float64),
            "m": pl.Series([], dtype=pl.Float64),
            "z": pl.Series([], dtype=pl.Int8),
            "mz": pl.Series([], dtype=pl.Float64),
            "rt": pl.Series([], dtype=pl.Float64),
            "quant_group": pl.Series([], dtype=pl.Int64),
            "db_id": pl.Series([], dtype=pl.Utf8),
            "db": pl.Series([], dtype=pl.Utf8),
        })
    
    def _get_adducts(self, 
                    adducts_list: Optional[List[str]] = None, 
                    polarity: Optional[str] = None,
                    min_probability: float = 0.03,
                    **kwargs) -> pl.DataFrame:
        """
        Generate comprehensive adduct specifications for the library.
        
        This method creates a DataFrame of adduct combinations following the same
        syntax as Study() and Sample() classes.
        
        Args:
            adducts_list: List of adduct specifications in OpenMS format (e.g., "+H:1:0.65")
            polarity: "positive", "negative", or None for both
            min_probability: Minimum probability threshold to filter adducts
            **kwargs: Additional parameters for adduct generation
            
        Returns:
            DataFrame with columns:
            - name: Formatted adduct name like "[M+H]1+"
            - charge: Total charge of the adduct
            - mass_shift: Total mass shift in Da
            - probability: Combined probability score
            - complexity: Number of adduct components
        """
        # Get adduct specifications
        if adducts_list is None:
            if polarity is None:
                # Use positive by default
                adducts_list = self.DEFAULT_ADDUCTS["positive"]
            elif polarity.lower() in ["positive", "pos"]:
                adducts_list = self.DEFAULT_ADDUCTS["positive"]
            elif polarity.lower() in ["negative", "neg"]:
                adducts_list = self.DEFAULT_ADDUCTS["negative"]
            else:
                raise ValueError(f"Unknown polarity: {polarity}")
        
        # Parameters
        charge_min = kwargs.get("charge_min", -2)
        charge_max = kwargs.get("charge_max", 2)
        max_combinations = kwargs.get("max_combinations", 2)
        
        # Parse base adduct specifications
        base_specs = []
        
        for adduct_str in adducts_list:
            if not isinstance(adduct_str, str) or ":" not in adduct_str:
                continue
                
            try:
                parts = adduct_str.split(":")
                if len(parts) != 3:
                    continue
                    
                formula_part = parts[0]
                charge = int(parts[1])
                probability = float(parts[2])
                
                # Calculate mass shift from formula
                mass_shift = _calculate_formula_mass_shift(formula_part)
                
                base_specs.append({
                    "formula": formula_part,
                    "charge": charge,
                    "mass_shift": mass_shift,
                    "probability": probability,
                    "raw_string": adduct_str,
                })
                
            except (ValueError, IndexError):
                continue
        
        if not base_specs:
            # Return empty DataFrame with correct schema
            return pl.DataFrame({
                "name": [],
                "charge": [],
                "mass_shift": [],
                "probability": [],
                "complexity": [],
            })
        
        # Generate all valid combinations
        combinations_list = []
        
        # Separate specs by charge type
        positive_specs = [spec for spec in base_specs if spec["charge"] > 0]
        negative_specs = [spec for spec in base_specs if spec["charge"] < 0]
        neutral_specs = [spec for spec in base_specs if spec["charge"] == 0]
        
        # 1. Single adducts
        for spec in base_specs:
            if charge_min <= spec["charge"] <= charge_max:
                formatted_name = _format_adduct_name([spec])
                combinations_list.append({
                    "components": [spec],
                    "formatted_name": formatted_name,
                    "total_mass_shift": spec["mass_shift"],
                    "total_charge": spec["charge"],
                    "combined_probability": spec["probability"],
                    "complexity": 1,
                })
        
        # 2. Generate multiply charged versions (2H+, 3H+, etc.)
        if max_combinations >= 2:
            for spec in positive_specs + negative_specs:
                base_charge = spec["charge"]
                for multiplier in range(2, min(max_combinations + 1, 4)):
                    total_charge = base_charge * multiplier
                    if charge_min <= total_charge <= charge_max:
                        components = [spec] * multiplier
                        formatted_name = _format_adduct_name(components)
                        
                        combinations_list.append({
                            "components": components,
                            "formatted_name": formatted_name,
                            "total_mass_shift": spec["mass_shift"] * multiplier,
                            "total_charge": total_charge,
                            "combined_probability": spec["probability"] ** multiplier,
                            "complexity": multiplier,
                        })
        
        # 3. Mixed combinations (positive + neutral)
        if max_combinations >= 2:
            for pos_spec in positive_specs:
                for neut_spec in neutral_specs:
                    total_charge = pos_spec["charge"] + neut_spec["charge"]
                    if charge_min <= total_charge <= charge_max:
                        components = [pos_spec, neut_spec]
                        formatted_name = _format_adduct_name(components)
                        combinations_list.append({
                            "components": components,
                            "formatted_name": formatted_name,
                            "total_mass_shift": pos_spec["mass_shift"] + neut_spec["mass_shift"],
                            "total_charge": total_charge,
                            "combined_probability": pos_spec["probability"] * neut_spec["probability"],
                            "complexity": 2,
                        })
        
        # Convert to polars DataFrame
        if combinations_list:
            combinations_list.sort(
                key=lambda x: (-x["combined_probability"], x["complexity"])
            )
            
            adducts_df = pl.DataFrame([
                {
                    "name": combo["formatted_name"],
                    "charge": combo["total_charge"],
                    "mass_shift": combo["total_mass_shift"],
                    "probability": combo["combined_probability"],
                    "complexity": combo["complexity"],
                }
                for combo in combinations_list
            ])
        else:
            # Return empty DataFrame with correct schema
            adducts_df = pl.DataFrame({
                "name": [],
                "charge": [],
                "mass_shift": [],
                "probability": [],
                "complexity": [],
            })
        
        # Filter by minimum probability
        if min_probability > 0.0 and len(adducts_df) > 0:
            adducts_df = adducts_df.filter(pl.col("probability") >= min_probability)
        
        return adducts_df
    
    def _calculate_accurate_mass(self, formula: str) -> Optional[float]:
        """
        Calculate the accurate mass for a molecular formula using PyOpenMS.
        
        Args:
            formula: Molecular formula string
            
        Returns:
            Accurate mass as float, or None if calculation fails
        """
        # Skip obviously invalid formulas
        if not formula or not isinstance(formula, str):
            return None
        
        # Clean up whitespace
        formula = formula.strip()
        
        # Skip formulas that are obviously invalid
        invalid_patterns = [
            # Contains parentheses with multipliers like (C12H19NO19S3)nH2O
            lambda f: '(' in f and ')' in f and any(c.isalpha() and not c.isupper() for c in f.split(')')[1:]),
            # Contains words instead of chemical symbols
            lambda f: any(word in f.lower() for word in ['and', 'or', 'not', 'with', 'without']),
            # Contains lowercase letters at the start (element symbols should be uppercase)
            lambda f: f and f[0].islower(),
            # Contains unusual characters that shouldn't be in formulas
            lambda f: any(char in f for char in ['@', '#', '$', '%', '^', '&', '*', '=', '+', '?', '/', '\\', '|']),
            # Empty or very short non-standard formulas
            lambda f: len(f) < 2 and not f.isupper(),
        ]
        
        for pattern_check in invalid_patterns:
            try:
                if pattern_check(formula):
                    warnings.warn(f"Skipping obviously invalid formula: '{formula}'")
                    return None
            except Exception:
                # If pattern checking fails, continue to PyOpenMS parsing
                pass
        
        try:
            empirical_formula = oms.EmpiricalFormula(formula)
            return empirical_formula.getMonoWeight()
        except Exception as e:
            warnings.warn(f"Error calculating accurate mass for formula '{formula}': {e}")
            return None
    
    def _generate_adduct_variants(self, 
                                compound_data: Dict[str, Any], 
                                adducts: Optional[List[str]] = None,
                                polarity: Optional[str] = None,
                                lib_id_counter: Optional[int] = None,
                                min_probability: float = 0.03) -> tuple[List[Dict[str, Any]], int]:
        """
        Generate adduct variants for a given compound using the new adduct system.
        
        Args:
            compound_data: Dictionary containing compound information
            adducts: List of specific adducts to generate. If None, uses defaults for polarity
            polarity: Ionization polarity ("positive", "negative", or None for positive)
            lib_id_counter: Counter for generating unique lib_uid values
            min_probability: Minimum probability threshold for adduct filtering
            
        Returns:
            Tuple of (list of dictionaries representing adduct variants, updated counter)
        """
        variants = []
        counter = lib_id_counter or 1
        
        # Calculate base accurate mass
        accurate_mass = self._calculate_accurate_mass(compound_data["formula"])
        if accurate_mass is None:
            return variants, counter
        
        # Get adduct specifications using _get_adducts
        adducts_df = self._get_adducts(
            adducts_list=adducts,
            polarity=polarity,
            min_probability=min_probability
        )
        
        if len(adducts_df) == 0:
            return variants, counter
        
        # Generate variants for each adduct
        for adduct_row in adducts_df.iter_rows(named=True):
            adduct_name = adduct_row["name"]
            charge = adduct_row["charge"]
            mass_shift = adduct_row["mass_shift"]
            probability = adduct_row["probability"]
            
            # Calculate adducted mass and m/z
            adducted_mass = accurate_mass + mass_shift
            mz = abs(adducted_mass / charge) if charge != 0 else adducted_mass
            
            # Create variant entry
            variant = {
                "lib_uid": counter,
                "cmpd_uid": compound_data.get("cmpd_uid", None),
                "source_id": compound_data.get("source_id", None),
                "name": compound_data.get("name", ""),
                "shortname": compound_data.get("shortname", ""),
                "class": compound_data.get("class", ""),
                "smiles": compound_data.get("smiles", ""),
                "inchi": compound_data.get("inchi", ""),
                "inchikey": compound_data.get("inchikey", ""),
                "formula": compound_data["formula"],
                "iso": 0,  # Default to zero
                "adduct": adduct_name,
                "probability": probability,
                "m": adducted_mass,
                "z": charge,
                "mz": mz,
                "rt": compound_data.get("rt", None),
                "quant_group": counter,  # Use same as lib_uid for default
                "db_id": compound_data.get("db_id", None),
                "db": compound_data.get("db", None),
            }
            variants.append(variant)
            counter += 1
        
        return variants, counter
    
    def import_csv(self, 
                  csvfile: str, 
                  polarity: Optional[str] = None,
                  adducts: Optional[List[str]] = None,
                  min_probability: float = 0.03) -> None:
        """
        Import compound library from a CSV file.
        
        This method reads a CSV file and generates adduct variants for each compound.
        Missing columns will be filled with appropriate default values.
        
        Args:
            csvfile: Path to the CSV file
            polarity: Ionization polarity ("positive", "negative", or None for positive)
            adducts: Specific adducts to generate. If None, generates defaults for the polarity
            min_probability: Minimum probability threshold for adduct filtering
            
        Expected CSV columns (case-insensitive):
            - Required: Formula (or formula)
            - Optional: Name/name/Compound/compound, SMILES/smiles, InChI/inchi, 
                      InChIKey/inchikey, RT/rt, RT2/rt2
        
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing
        """
        if not os.path.exists(csvfile):
            raise FileNotFoundError(f"CSV file not found: {csvfile}")
        
        # Read CSV file with robust error handling
        try:
            df = pl.read_csv(csvfile, truncate_ragged_lines=True, ignore_errors=True)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}") from e
        
        # Find column mappings (case-insensitive)
        column_mapping = self._map_csv_columns(df.columns)
        
        # Validate required columns
        if "formula" not in column_mapping:
            raise ValueError("Required column 'Formula' (or 'formula') not found in CSV file")
        
        # Process each compound
        all_variants = []
        cmpd_id_counter = 1
        lib_id_counter = 1
        total_compounds = 0
        skipped_compounds = 0
        
        for row in df.iter_rows(named=True):
            total_compounds += 1
            
            # Extract compound data
            # assign a compound-level uid so all adducts share the same cmpd_uid
            compound_level_uid = cmpd_id_counter
            cmpd_id_counter += 1

            compound_data = {
                "name": row.get(column_mapping.get("name", ""), ""),
                "shortname": row.get(column_mapping.get("shortname", ""), ""),
                "class": row.get(column_mapping.get("class", ""), ""),                
                "smiles": row.get(column_mapping.get("smiles", ""), ""),
                "inchi": row.get(column_mapping.get("inchi", ""), ""),
                "inchikey": row.get(column_mapping.get("inchikey", ""), ""),
                "formula": row[column_mapping["formula"]],
                "rt": self._safe_float_conversion(row.get(column_mapping.get("rt", ""), None)),
                "db_id": row.get(column_mapping.get("db_id", ""), None),
                "db": row.get(column_mapping.get("db", ""), None),
                "cmpd_uid": compound_level_uid,
            }
            
            # Generate adduct variants
            variants, lib_id_counter = self._generate_adduct_variants(
                compound_data, adducts=adducts, polarity=polarity, 
                lib_id_counter=lib_id_counter, min_probability=min_probability
            )
            all_variants.extend(variants)
            
            # Track if compound was skipped due to invalid formula
            if len(variants) == 0:
                skipped_compounds += 1
            
            # Handle RT2 column if present
            if "rt2" in column_mapping and len(variants) > 0:  # Only if main variants were created
                rt2_value = self._safe_float_conversion(row.get(column_mapping["rt2"], None))
                if rt2_value is not None:
                    # Create additional variants with RT2
                    compound_data_rt2 = compound_data.copy()
                    compound_data_rt2["rt"] = rt2_value
                    compound_data_rt2["name"] = compound_data["name"] + " II"
                    
                    variants_rt2, lib_id_counter = self._generate_adduct_variants(
                        compound_data_rt2, adducts=adducts, polarity=polarity, 
                        lib_id_counter=lib_id_counter, min_probability=min_probability
                    )
                    all_variants.extend(variants_rt2)
        
        # Convert to DataFrame and store
        if all_variants:
            new_lib_df = pl.DataFrame(all_variants)
            
            # Combine with existing data if any
            if self.lib_df is not None and len(self.lib_df) > 0:
                self.lib_df = pl.concat([self.lib_df, new_lib_df])
            else:
                self.lib_df = new_lib_df
                
            #successful_compounds = total_compounds - skipped_compounds
            print(f"Imported {len(all_variants)} library entries from {csvfile}")
            #print(f"Processed {total_compounds} compounds: {successful_compounds} successful, {skipped_compounds} skipped due to invalid formulas")
        else:
            print(f"No valid compounds found in {csvfile}")
            if skipped_compounds > 0:
                print(f"All {total_compounds} compounds were skipped due to invalid formulas")
    
    def import_json(self, 
                   jsonfile: str, 
                   polarity: Optional[str] = None,
                   adducts: Optional[List[str]] = None,
                   min_probability: float = 0.03) -> None:
        """
        Import compound library from a JSON file created by csv_to_json.py.
        
        This method reads a JSON file with the structure created by csv_to_json.py
        and generates adduct variants for each compound.
        
        Args:
            jsonfile: Path to the JSON file
            polarity: Ionization polarity ("positive", "negative", or None for positive)
            adducts: Specific adducts to generate. If None, generates defaults for the polarity
            min_probability: Minimum probability threshold for adduct filtering
            
        Expected JSON structure:
            {
                "version": "1.0",
                "creation_date": "2025-10-07T09:17:06.142290",
                "description": "Converted from CSV file...",
                "source_file": "filename.csv",
                "record_count": 123,
                "data": [
                    {
                        "name": "compound name",
                        "smiles": "SMILES string",
                        "inchikey": "InChI key",
                        "formula": "molecular formula",
                        "db_id": "database ID",
                        "db": "database name"
                    },
                    ...
                ]
            }
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If JSON structure is invalid or required data is missing
        """
        if not os.path.exists(jsonfile):
            raise FileNotFoundError(f"JSON file not found: {jsonfile}")
        
        # Read and parse JSON file
        try:
            with open(jsonfile, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}") from e
        except Exception as e:
            raise ValueError(f"Error reading JSON file: {e}") from e
        
        # Validate JSON structure
        if not isinstance(json_data, dict):
            raise ValueError("JSON file must contain a dictionary at root level")
        
        if "data" not in json_data:
            raise ValueError("JSON file must contain a 'data' field with compound records")
        
        data = json_data["data"]
        if not isinstance(data, list):
            raise ValueError("'data' field must be a list of compound records")
        
        # Extract metadata for reporting
        version = json_data.get("version", "unknown")
        source_file = json_data.get("source_file", "unknown")
        record_count = json_data.get("record_count", len(data))
        
        print(f"Loading JSON library: version {version}, source: {source_file}, records: {record_count}")
        
        # Process each compound
        all_variants = []
        cmpd_id_counter = 1
        lib_id_counter = 1
        total_compounds = 0
        skipped_compounds = 0
        
        for compound_record in data:
            total_compounds += 1
            
            # Validate required fields
            if not isinstance(compound_record, dict):
                skipped_compounds += 1
                continue
            
            formula = compound_record.get("formula", "")
            if not formula or not isinstance(formula, str):
                skipped_compounds += 1
                continue
            
            # Extract compound data, handling both CSV column names and JSON field names
            compound_level_uid = cmpd_id_counter
            cmpd_id_counter += 1
            
            compound_data = {
                "name": compound_record.get("name", compound_record.get("Name", "")),
                "shortname": compound_record.get("shortname", ""),
                "class": compound_record.get("class", ""),
                "smiles": compound_record.get("smiles", compound_record.get("SMILES", "")),
                "inchi": compound_record.get("inchi", compound_record.get("InChI", "")),
                "inchikey": compound_record.get("inchikey", compound_record.get("InChIKey", "")),
                "formula": formula,
                "rt": self._safe_float_conversion(compound_record.get("rt", compound_record.get("RT", None))),
                "db_id": compound_record.get("db_id", compound_record.get("database_id", None)),
                "db": compound_record.get("db", compound_record.get("database", None)),
                "cmpd_uid": compound_level_uid,
            }
            
            # Generate adduct variants
            variants, lib_id_counter = self._generate_adduct_variants(
                compound_data, adducts=adducts, polarity=polarity, 
                lib_id_counter=lib_id_counter, min_probability=min_probability
            )
            all_variants.extend(variants)
            
            # Track if compound was skipped due to invalid formula
            if len(variants) == 0:
                skipped_compounds += 1
        
        # Convert to DataFrame and store
        if all_variants:
            new_lib_df = pl.DataFrame(all_variants)
            
            # Combine with existing data if any
            if self.lib_df is not None and len(self.lib_df) > 0:
                self.lib_df = pl.concat([self.lib_df, new_lib_df])
            else:
                self.lib_df = new_lib_df
                
            print(f"Imported {len(all_variants)} library entries from {jsonfile}")
        else:
            print(f"No valid compounds found in {jsonfile}")
            if skipped_compounds > 0:
                print(f"All {total_compounds} compounds were skipped due to invalid formulas")
    
    def _map_csv_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Map CSV column names to standardized internal names (case-insensitive).
        
        Args:
            columns: List of column names from CSV
            
        Returns:
            Dictionary mapping internal names to actual column names
        """
        mapping = {}
        columns_lower = [col.lower() for col in columns]
        
        # Name mapping
        for name_variant in ["name", "compound"]:
            if name_variant in columns_lower:
                mapping["name"] = columns[columns_lower.index(name_variant)]
                break
        
        # Formula mapping
        for formula_variant in ["formula"]:
            if formula_variant in columns_lower:
                mapping["formula"] = columns[columns_lower.index(formula_variant)]
                break
        
        # SMILES mapping
        for smiles_variant in ["smiles"]:
            if smiles_variant in columns_lower:
                mapping["smiles"] = columns[columns_lower.index(smiles_variant)]
                break
        
        # InChI mapping
        for inchi_variant in ["inchi"]:
            if inchi_variant in columns_lower:
                mapping["inchi"] = columns[columns_lower.index(inchi_variant)]
                break
        
        # InChIKey mapping
        for inchikey_variant in ["inchikey", "inchi_key"]:
            if inchikey_variant in columns_lower:
                mapping["inchikey"] = columns[columns_lower.index(inchikey_variant)]
                break
        
        # RT mapping
        for rt_variant in ["rt", "retention_time", "retentiontime"]:
            if rt_variant in columns_lower:
                mapping["rt"] = columns[columns_lower.index(rt_variant)]
                break
        
        # RT2 mapping
        for rt2_variant in ["rt2", "retention_time2", "retentiontime2"]:
            if rt2_variant in columns_lower:
                mapping["rt2"] = columns[columns_lower.index(rt2_variant)]
                break
        
        # Database ID mapping
        for db_id_variant in ["db_id", "database_id", "dbid"]:
            if db_id_variant in columns_lower:
                mapping["db_id"] = columns[columns_lower.index(db_id_variant)]
                break
        
        # Database mapping
        for db_variant in ["db", "database"]:
            if db_variant in columns_lower:
                mapping["db"] = columns[columns_lower.index(db_variant)]
                break
        
        return mapping
    
    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """
        Safely convert a value to float, returning None if conversion fails.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None
        """
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def annotate_features(self, 
                         features_df: Union[pl.DataFrame, "pd.DataFrame"],
                         mz_tolerance: float = 0.01,
                         rt_tolerance: Optional[float] = None) -> pl.DataFrame:
        """
        Annotate features based on library matches using m/z and retention time.
        
        Args:
            features_df: DataFrame containing features with 'mz' and optionally 'rt' columns
            mz_tolerance: Mass tolerance in Da for matching
            rt_tolerance: Retention time tolerance in minutes for matching (if None, RT not used)
            
        Returns:
            DataFrame with annotation results
        """
        if self.lib_df is None or len(self.lib_df) == 0:
            raise ValueError("Library is empty. Import compounds first.")
        
        # Convert pandas DataFrame to Polars if needed
        if hasattr(features_df, 'to_pandas'):  # It's already a Polars DataFrame
            features_pl = features_df
        elif hasattr(features_df, 'values'):  # It's likely a pandas DataFrame
            try:
                import pandas as pd
                if isinstance(features_df, pd.DataFrame):
                    features_pl = pl.from_pandas(features_df)
                else:
                    features_pl = features_df
            except ImportError:
                features_pl = features_df
        else:
            features_pl = features_df
        
        annotations = []
        
        for feature_row in features_pl.iter_rows(named=True):
            feature_mz = feature_row.get("mz")
            feature_rt = feature_row.get("rt")
            
            if feature_mz is None:
                continue
            
            # Find matching library entries
            mz_matches = self.lib_df.filter(
                (pl.col("mz") >= feature_mz - mz_tolerance) &
                (pl.col("mz") <= feature_mz + mz_tolerance)
            )
            
            # Apply RT filter if both RT tolerance and feature RT are available
            if rt_tolerance is not None and feature_rt is not None:
                # Filter library entries that have RT values
                rt_matches = mz_matches.filter(
                    pl.col("rt").is_not_null() &
                    (pl.col("rt") >= feature_rt - rt_tolerance) &
                    (pl.col("rt") <= feature_rt + rt_tolerance)
                )
                if len(rt_matches) > 0:
                    matches = rt_matches
                else:
                    matches = mz_matches  # Fall back to m/z-only matches
            else:
                matches = mz_matches
            
            # Create annotation entries
            for match_row in matches.iter_rows(named=True):
                annotation = {
                    "feature_mz": feature_mz,
                    "feature_rt": feature_rt,
                    "lib_uid": match_row["lib_uid"],
                    "cmpd_uid": match_row.get("cmpd_uid"),
                    "source_id": match_row.get("source_id"),
                    "name": match_row["name"],
                    "shortname": match_row["shortname"],
                    "class": match_row["class"],
                    "formula": match_row["formula"],
                    "iso": match_row.get("iso", 0),
                    "adduct": match_row["adduct"],
                    "smiles": match_row["smiles"],
                    "inchi": match_row["inchi"],
                    "inchikey": match_row["inchikey"],
                    "lib_mz": match_row["mz"],
                    "lib_rt": match_row["rt"],
                    "quant_group": match_row.get("quant_group"),
                    "delta_mz": abs(feature_mz - match_row["mz"]),
                    "delta_rt": abs(feature_rt - match_row["rt"]) if feature_rt is not None and match_row["rt"] is not None else None,
                }
                annotations.append(annotation)
        
        return pl.DataFrame(annotations) if annotations else pl.DataFrame()
    
    def get_adducts_for_polarity(self, polarity: str) -> List[str]:
        """
        Get list of supported adducts for a given polarity.
        
        Args:
            polarity: "positive" or "negative"
            
        Returns:
            List of adduct names
        """
        adducts_df = self._get_adducts(polarity=polarity, min_probability=0.0)
        return adducts_df.select("name").to_series().to_list()
    
    def __len__(self) -> int:
        """Return number of library entries."""
        return len(self.lib_df) if self.lib_df is not None else 0
    
    def _reload(self):
        """
        Reloads all masster modules to pick up any changes to their source code,
        and updates the instance's class reference to the newly reloaded class version.
        This ensures that the instance uses the latest implementation without restarting the interpreter.
        """
        import importlib
        import sys

        # Get the base module name (masster)
        base_modname = self.__class__.__module__.split(".")[0]
        current_module = self.__class__.__module__

        # Dynamically find all lib submodules
        lib_modules = []
        lib_module_prefix = f"{base_modname}.lib."

        # Get all currently loaded modules that are part of the lib package
        for module_name in sys.modules:
            if module_name.startswith(lib_module_prefix) and module_name != current_module:
                lib_modules.append(module_name)

        # Add core masster modules
        core_modules = [
            f"{base_modname}._version",
            f"{base_modname}.chromatogram",
            f"{base_modname}.spectrum",
            f"{base_modname}.logger",
        ]

        '''# Add study submodules (for cross-dependencies)
        study_modules = []
        study_module_prefix = f"{base_modname}.study."
        for module_name in sys.modules:
            if module_name.startswith(study_module_prefix) and module_name != current_module:
                study_modules.append(module_name)'''

        '''# Add sample submodules (for cross-dependencies)
        sample_modules = []
        sample_module_prefix = f"{base_modname}.sample."
        for module_name in sys.modules:
            if module_name.startswith(sample_module_prefix) and module_name != current_module:
                sample_modules.append(module_name)'''

        all_modules_to_reload = core_modules + lib_modules # sample_modules + study_modules + 

        # Reload all discovered modules
        for full_module_name in all_modules_to_reload:
            try:
                if full_module_name in sys.modules:
                    mod = sys.modules[full_module_name]
                    importlib.reload(mod)
                    # Note: Lib class doesn't have a logger by default, so we just print or use warnings
                    #print(f"Reloaded module: {full_module_name}")
            except Exception as e:
                print(f"Warning: Failed to reload module {full_module_name}: {e}")

        # Finally, reload the current module (lib.py)
        try:
            mod = __import__(current_module, fromlist=[current_module.split(".")[0]])
            importlib.reload(mod)

            # Get the updated class reference from the reloaded module
            new = getattr(mod, self.__class__.__name__)
            # Update the class reference of the instance
            self.__class__ = new

            print("Lib module reload completed")
        except Exception as e:
            print(f"Error: Failed to reload current module {current_module}: {e}")
    
    def __str__(self) -> str:
        """String representation of the library."""
        if self.lib_df is None or len(self.lib_df) == 0:
            return "Empty Lib instance"
        
        unique_compounds = self.lib_df.select("name").unique().height
        unique_adducts = self.lib_df.select("adduct").unique().height
        
        return f"Lib instance with {len(self)} entries ({unique_compounds} unique compounds, {unique_adducts} adduct types)"
