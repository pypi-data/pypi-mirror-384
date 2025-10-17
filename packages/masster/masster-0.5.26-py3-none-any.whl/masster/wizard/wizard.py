"""
Wizard module for automated processing of mass spectrometry studies.

This module provides the Wizard class for fully automated processing of MS data
from raw files to final study results, including batch conversion, assembly,
alignment, merging, plotting, and export.

Key Features:
- Automated discovery and batch conversion of raw data files
- Intelligent resume capability for interrupted processes
- Parallel processing optimization for large datasets
- Adaptive study format based on study size
- Comprehensive logging and progress tracking
- Optimized memory management for large studies

Classes:
- Wizard: Main class for automated study processing
- wizard_def: Default parameters configuration class

Example Usage:
```python
from masster import Wizard, wizard_def

# Create wizard with default parameters
wizard = Wizard(
    source="./raw_data",
    folder="./processed_study",
    polarity="positive",
    num_cores=4
)

```
"""

from __future__ import annotations

from math import e
import os
import sys
import time
import importlib
import glob
import multiprocessing
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
import concurrent.futures
from datetime import datetime

# Import masster modules - use delayed import to avoid circular dependencies
from masster.logger import MassterLogger
from masster.study.defaults.study_def import study_defaults
from masster.study.defaults.align_def import align_defaults
from masster.study.defaults.merge_def import merge_defaults
from masster._version import __version__ as version


@dataclass
class wizard_def:
    """
    Default parameters for the Wizard automated processing system.

    This class provides comprehensive configuration for all stages of automated
    mass spectrometry data processing from raw files to final results.

    Attributes:
        # Core Configuration
        source (str): Path to directory containing raw data files
        folder (str): Output directory for processed study
        polarity (Optional[str]): Ion polarity mode ("positive", "negative", or None for auto-detection)
        num_cores (int): Number of CPU cores to use for parallel processing

        # File Discovery
        file_extensions (List[str]): File extensions to search for
        search_subfolders (bool): Whether to search subdirectories
        skip_patterns (List[str]): Filename patterns to skip

        # Processing Parameters
        adducts (List[str]): Adduct specifications for given polarity
        batch_size (int): Number of files to process per batch
        memory_limit_gb (float): Memory limit for processing (GB)

        # Resume & Recovery
        resume_enabled (bool): Enable automatic resume capability
        force_reprocess (bool): Force reprocessing of existing files
        backup_enabled (bool): Create backups of intermediate results

        # Output & Export
        generate_plots (bool): Generate visualization plots
        export_formats (List[str]): Output formats to generate
        compress_output (bool): Compress final study file

        # Logging
        log_level (str): Logging detail level
        log_to_file (bool): Save logs to file
        progress_interval (int): Progress update interval (seconds)
    """

    # === Core Configuration ===
    source: str = ""
    folder: str = ""
    polarity: Optional[str] = None
    num_cores: int = 4

    # === File Discovery ===
    file_extensions: List[str] = field(default_factory=lambda: [".wiff", ".raw", ".mzML"])
    search_subfolders: bool = True
    skip_patterns: List[str] = field(default_factory=lambda: ["blank", "test"])

    # === Processing Parameters ===
    adducts: List[str] = field(default_factory=list)  # Will be set based on polarity
    batch_size: int = 8
    memory_limit_gb: float = 16.0
    max_file_size_gb: float = 4.0

    # === Resume & Recovery ===
    resume_enabled: bool = True
    force_reprocess: bool = False
    backup_enabled: bool = True
    checkpoint_interval: int = 10  # Save progress every N files

    # === Study Assembly ===
    min_samples_for_merge: int = 2
    rt_tolerance: float = 1.5
    mz_max_diff: float = 0.01
    alignment_algorithm: str = "kd"
    merge_method: str = "qt"

    # === Feature Detection ===
    chrom_fwhm: float | None = None
    noise: float | None = None
    chrom_peak_snr: float = 5.0
    tol_ppm: float = 10.0
    detector_type: str = "unknown"  # Detected detector type ("orbitrap", "quadrupole", "unknown")

    # === Output & Export ===
    generate_plots: bool = True
    generate_interactive: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["csv", "mgf", "xlsx"])
    compress_output: bool = True
    adaptive_compression: bool = True  # Adapt based on study size

    # === Logging ===
    log_level: str = "INFO"
    log_to_file: bool = True
    progress_interval: int = 30  # seconds
    verbose_progress: bool = True

    # === Advanced Options ===
    use_process_pool: bool = True  # vs ThreadPoolExecutor
    optimize_memory: bool = True
    cleanup_temp_files: bool = True
    validate_outputs: bool = True

    _param_metadata: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "source": {
                "dtype": str,
                "description": "Path to directory containing raw data files",
                "required": True,
            },
            "folder": {
                "dtype": str,
                "description": "Output directory for processed study",
                "required": True,
            },
            "polarity": {
                "dtype": str,
                "description": "Ion polarity mode",
                "default": "positive",
                "allowed_values": ["positive", "negative", "pos", "neg"],
            },
            "num_cores": {
                "dtype": int,
                "description": "Number of CPU cores to use",
                "default": 4,
                "min_value": 1,
                "max_value": multiprocessing.cpu_count(),
            },
            "batch_size": {
                "dtype": int,
                "description": "Number of files to process per batch",
                "default": 8,
                "min_value": 1,
                "max_value": 32,
            },
            "memory_limit_gb": {
                "dtype": float,
                "description": "Memory limit for processing (GB)",
                "default": 16.0,
                "min_value": 1.0,
                "max_value": 128.0,
            },
        },
        repr=False,
    )

    def __post_init__(self):
        """Set polarity-specific defaults after initialization."""
        # Set default adducts based on polarity if not provided
        if not self.adducts:
            if self.polarity and self.polarity.lower() in ["positive", "pos"]:
                self.adducts = ["H:+:0.8", "Na:+:0.1", "NH4:+:0.1"]
            elif self.polarity and self.polarity.lower() in ["negative", "neg"]:
                self.adducts = ["H-1:-:1.0", "CH2O2:0:0.5"]
            else:
                # Default to positive if polarity is None or unknown
                self.adducts = ["H:+:0.8", "Na:+:0.1", "NH4:+:0.1"]

        # Validate num_cores
        max_cores = multiprocessing.cpu_count()
        if self.num_cores <= 0:
            self.num_cores = max_cores
        elif self.num_cores > max_cores:
            self.num_cores = max_cores

        # Ensure paths are absolute
        if self.source:
            self.source = os.path.abspath(self.source)
        if self.folder:
            self.folder = os.path.abspath(self.folder)


class Wizard:
    """
    Simplified Wizard for automated mass spectrometry data processing.

    The Wizard provides a clean interface for creating and executing analysis scripts
    that process raw MS data through the complete pipeline: file discovery, feature
    detection, sample processing, study assembly, alignment, merging, and export.

    Core functions:
    - create_scripts(): Generate standalone analysis scripts
    - test_only(): Process only one file for parameter validation
    - test_and_run(): Test with single file, then run full batch if successful
    - run(): Execute full batch processing on all files

    Recommended workflow:
    1. wizard = Wizard(source="raw_data", folder="output")
    2. wizard.create_scripts()  # Generate analysis scripts
    3. wizard.test_only()       # Validate with single file
    4. wizard.run()             # Process all files
    """

    def __init__(
        self,
        source: str = "",
        folder: str = "",
        polarity: Optional[str] = None,
        adducts: Optional[List[str]] = None,
        num_cores: int = 6,
        **kwargs,
    ):
        """
        Initialize the Wizard with analysis parameters.

        Parameters:
            source: Directory containing raw data files
            folder: Output directory for processed study
            polarity: Ion polarity mode ("positive", "negative", or None for auto-detection)
            adducts: List of adduct specifications (auto-set if None)
            num_cores: Number of CPU cores (0 = auto-detect 75% of available)
            **kwargs: Additional parameters (see wizard_def for full list)
        """

        # Auto-detect optimal number of cores if not specified
        if num_cores <= 0:
            num_cores = max(1, int(multiprocessing.cpu_count() * 0.75))

        # Create parameters instance
        if "params" in kwargs and isinstance(kwargs["params"], wizard_def):
            self.params = kwargs.pop("params")
        else:
            # Create default parameters
            self.params = wizard_def(source=source, folder=folder, polarity=polarity, num_cores=num_cores)

            # Set adducts if provided
            if adducts is not None:
                self.params.adducts = adducts

            # Update with any additional parameters
            for key, value in kwargs.items():
                if hasattr(self.params, key):
                    setattr(self.params, key, value)

        # Validate required parameters
        if not self.params.source:
            raise ValueError("source is required")
        if not self.params.folder:
            raise ValueError("folder is required")

        # Create and validate paths
        self.source_path = Path(self.params.source)
        self.folder_path = Path(self.params.folder)
        self.folder_path.mkdir(parents=True, exist_ok=True)

        # Set default polarity if not specified
        if self.params.polarity is None:
            self.params.polarity = "positive"
            # Update adducts based on default polarity
            self.params.__post_init__()

    @property
    def polarity(self) -> Optional[str]:
        """Get the ion polarity mode."""
        return self.params.polarity

    @property
    def adducts(self) -> List[str]:
        """Get the adduct specifications."""
        return self.params.adducts

    def create_scripts(self) -> Dict[str, Any]:
        """
        Generate analysis scripts based on source file analysis.

        This method:
        1. Analyzes the source files to extract metadata
        2. Creates 1_masster_workflow.py with sample processing logic
        3. Creates 2_interactive_analysis.py marimo notebook for study exploration
        4. Returns instructions for next steps

        Returns:
            Dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - instructions: List of next steps
            - files_created: List of created file paths
            - source_info: Metadata about source files
        """
        try:
            # Step 1: Analyze source files to extract metadata
            source_info = self._analyze_source_files()

            # Report extracted information from first file
            print("\nInformation retrieval complete:")
            print(f"  Number of files found: {source_info.get('number_of_files', 0)}")
            print(f"  File types detected: {', '.join(source_info.get('file_types', []))}")
            #print(f"  First file: {source_info.get('first_file', 'None')}")
            if source_info.get('first_file'):
                print(f"  Detected polarity: {source_info.get('polarity', 'unknown')}")
                print(f"  Detected detector type: {source_info.get('detector_type', 'unknown')}")
                if source_info.get('baseline', 0) > 0:
                    print(f"  Estimated baseline intensity: {source_info.get('baseline', 0):.1f}")
                if source_info.get('length_minutes', 0) > 0:
                    print(f"  Run length: {source_info.get('length_minutes', 0):.1f} minutes")
                else:
                    print("  Run length: Could not determine")
                if source_info.get('ms1_scans_per_second', 0) > 0:
                    print(f"  MS1 scans per second: {source_info.get('ms1_scans_per_second', 0):.2f}")
            print()

            # Update wizard parameters based on detected metadata
            if source_info.get("polarity") and source_info["polarity"] != "positive":
                self.params.polarity = source_info["polarity"]

            files_created = []

            # Step 2: Create 1_masster_workflow.py
            workflow_script_path = self.folder_path / "1_masster_workflow.py"
            print(f"Creating workflow script: {workflow_script_path}")
            workflow_content = self._generate_workflow_script_content(source_info)
            
            # Apply test mode modifications
            workflow_content = self._add_test_mode_support(workflow_content)

            with open(workflow_script_path, "w", encoding="utf-8") as f:
                f.write(workflow_content)
            files_created.append(str(workflow_script_path))

            # Step 3: Create 2_interactive_analysis.py marimo notebook
            notebook_path = self.folder_path / "2_interactive_analysis.py"
            print(f"Creating interactive analysis notebook: {notebook_path}")
            notebook_content = self._generate_interactive_notebook_content(source_info)

            with open(notebook_path, "w", encoding="utf-8") as f:
                f.write(notebook_content)
            files_created.append(str(notebook_path))

            # Step 4: Generate instructions
            instructions = self._generate_instructions(source_info, files_created)

            return {
                "status": "success",
                "message": f"Successfully created {len(files_created)} script files",
                "instructions": instructions,
                "files_created": files_created,
                "source_info": source_info,
            }

        except Exception as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                line_number = tb[-1].lineno
                function_name = tb[-1].name
                error_location = f" (at line {line_number} in {function_name})"
            else:
                error_location = ""
            
            return {
                "status": "error",
                "message": f"Failed to create scripts: {e}{error_location}",
                "instructions": [],
                "files_created": [],
                "source_info": {},
            }

    def _analyze_source_files(self) -> Dict[str, Any]:
        """Analyze source files to extract metadata."""
        result = {
            "number_of_files": 0,
            "file_types": [],
            "detector_type": "tof",
            "polarity": None,
            "baseline": None,
            "length_minutes": 0.0,
            "ms1_scans_per_second": 0.0,            
            "first_file": None,

        }

        try:
            # Find raw data files
            extensions = [".wiff", ".raw", ".mzML"]
            raw_files = []

            for ext in extensions:
                pattern = f"**/*{ext}"
                files = list(self.source_path.rglob(pattern))
                if files:
                    raw_files.extend(files)
                    if ext not in result["file_types"]:
                        result["file_types"].append(ext)

            result["number_of_files"] = len(raw_files)

            if raw_files:
                result["first_file"] = str(raw_files[0])
                # load first file to infer polarity and length
                print(f"Analyzing first file: {raw_files[0]}")
                from masster import Sample
                sample = Sample(filename=result["first_file"], logging_level='WARNING')
                result['polarity'] = sample.polarity
                # take max from polars ms1_df['rt']
                if sample.ms1_df is not None:
                    if not sample.ms1_df.is_empty() and 'rt' in sample.ms1_df.columns:
                        max_rt = sample.ms1_df['rt'].max()
                        if max_rt is not None and isinstance(max_rt, (int, float)) and max_rt > 0:
                            result["length_minutes"] = float(max_rt) / 60.0
                            result["ms1_scans_per_second"] = len(sample.ms1_df) / float(max_rt) / 60.0
                        
                        baseline = sample.ms1_df['inty'].quantile(0.001)
                        if baseline is not None and isinstance(baseline, (int, float)):
                            result["baseline"] = float(baseline)
                            if baseline > 5e3:
                                result["detector_type"] = "orbitrap"
                            else:
                                result["detector_type"] = "tof"
                    
        except Exception as e:
            print(f"Warning: Could not analyze source files: {e}")

        return result

    def _generate_workflow_script_content(self, source_info: Dict[str, Any]) -> str:
        """Generate the content for 1_masster_workflow.py script."""

        # Logic 
        noise = self.params.noise
        if noise is None:
            if source_info.get("detector_type") == "orbitrap":
                noise = max(self.params.noise or 50.0, 5e4)
            elif source_info.get("detector_type") == "tof":
                default_noise = self.params.noise or 50.0
                baseline = source_info.get("baseline", default_noise / 2.0)
                noise = baseline * 2

        chrom_fwhm = self.params.chrom_fwhm
        if chrom_fwhm is None:
            if source_info.get("length_minutes", 0) > 0:
                if source_info["length_minutes"] < 10:
                    chrom_fwhm = 0.5
                else:
                    chrom_fwhm = 2.0


        # Generate script content     
        script_lines = [
           "#!/usr/bin/env python3",
           '"""',
           "Automated Mass Spectrometry Data Analysis Pipeline",
            "Generated by masster wizard",
            '"""',
            "",
            "import os",
            "import sys",
            "import time",
            "from pathlib import Path",
            "",
            "# Import masster modules",
            "from masster.study import Study",
            "from masster import __version__",
            "",
            "# Test mode configuration",
            'TEST = os.environ.get("MASSTER_TEST", "0") == "1"',
            'STOP_AFTER_TEST = os.environ.get("MASSTER_STOP_AFTER_TEST", "0") == "1"  # Only run test, don\'t continue to full batch',
            "",
            "# Analysis parameters",
            "PARAMS = {",
            "    # === Core Configuration ===",
            f'    "source": {str(self.source_path)!r},  # Directory containing raw data files',
            f'    "folder": {str(self.folder_path)!r},  # Output directory for processed study',
            f'    "polarity": {self.params.polarity!r},  # Ion polarity mode ("positive" or "negative")',
            f'    "num_cores": {self.params.num_cores},  # Number of CPU cores for parallel processing',
            "",
            "    # === Test Mode ===",
            '    "test": TEST,  # Process only first file for testing',
            '    "stop_after_test": STOP_AFTER_TEST,  # Stop after test, don\'t run full batch',
            "",
            "    # === File Discovery ===",
            f'    "file_extensions": {self.params.file_extensions!r},  # File extensions to search for',
            f'    "search_subfolders": {self.params.search_subfolders},  # Whether to search subdirectories recursively',
            f'    "skip_patterns": {self.params.skip_patterns!r},  # Filename patterns to skip',
            "",
            "    # === Processing Parameters ===",
            f'    "adducts": {self.params.adducts!r},  # Adduct specifications for feature detection and annotation',
            f'    "noise": {noise},  # Noise threshold for feature detection',
            f'    "chrom_fwhm": {chrom_fwhm},  # Chromatographic peak full width at half maximum (seconds)',
            f'    "chrom_peak_snr": {self.params.chrom_peak_snr},  # Minimum signal-to-noise ratio for chromatographic peaks',
            "",
            "    # === Alignment & Merging ===",
            f'    "rt_tol": {self.params.rt_tolerance},  # Retention time tolerance for alignment (seconds)',
            f'    "mz_tol": {self.params.mz_max_diff},  # Mass-to-charge ratio tolerance for alignment (Da)',
            f'    "alignment_method": {self.params.alignment_algorithm!r},  # Algorithm for sample alignment',
            f'    "min_samples_per_feature": {self.params.min_samples_for_merge},  # Minimum samples required per consensus feature',
            f'    "merge_method": {self.params.merge_method!r},  # Method for merging consensus features',
            "",
            "    # === Sample Processing (used in add_samples_from_folder) ===",
            f'    "batch_size": {self.params.batch_size},  # Number of files to process per batch',
            f'    "memory_limit_gb": {self.params.memory_limit_gb},  # Memory limit for processing (GB)',
            "",
            "    # === Script Options ===",
            f'    "resume_enabled": {self.params.resume_enabled},  # Enable automatic resume capability',
            f'    "force_reprocess": {self.params.force_reprocess},  # Force reprocessing of existing files',
            f'    "cleanup_temp_files": {self.params.cleanup_temp_files},  # Clean up temporary files after processing',
            "}",
            "",
            "",
            "def discover_raw_files(source_folder, file_extensions, search_subfolders=True):",
            '    """Discover raw data files in the source folder."""',
            "    source_path = Path(source_folder)",
            "    raw_files = []",
            "    ",
            "    for ext in file_extensions:",
            "        if search_subfolders:",
            '            pattern = f"**/*{ext}"',
            "            files = list(source_path.rglob(pattern))",
            "        else:",
            '            pattern = f"*{ext}"',
            "            files = list(source_path.glob(pattern))",
            "        raw_files.extend(files)",
            "    ",
            "    return raw_files",
            "",
            "",
            "def process_single_file(args):",
            '    """Process a single raw file to sample5 format - module level for multiprocessing."""',
            "    raw_file, output_folder = args",
            "    from masster.sample import Sample",
            "    ",
            "    try:",
            "        # Create sample5 filename",
            "        sample_name = raw_file.stem",
            '        sample5_path = Path(output_folder) / f"{sample_name}.sample5"',
            "        ",
            "        # Skip if sample5 already exists",
            '        if sample5_path.exists() and not PARAMS["force_reprocess"]:',
            '            print(f"  Skipping {raw_file.name} (sample5 already exists)")',
            "            return str(sample5_path)",
            "        ",
            '        print(f"  Converting {raw_file.name}...")',
            "        ",
            "        # Load and process raw file with full pipeline",
            "        sample = Sample(log_label=sample_name)",
            "        sample.load(filename=str(raw_file))",
            "        sample.find_features(",
            '            noise=PARAMS["noise"],',
            '            chrom_fwhm=PARAMS["chrom_fwhm"],',
            '            chrom_peak_snr=PARAMS["chrom_peak_snr"]',
            "        )",
            "        sample.find_ms2()",
            "        sample.find_iso()",
            "        # sample.export_mgf()",
            '        # sample.plot_2d(filename=f"{sample5_path.replace(".sample5", ".html")}")',
            "        sample.save(str(sample5_path))",
            "        ",
            '        # print(f"  Completed {raw_file.name} -> {sample5_path.name}")',
            "        return str(sample5_path)",
            "        ",
            "    except Exception as e:",
            '        print(f"  ERROR processing {raw_file.name}: {e}")',
            "        return None",
            "",
            "",
            "def convert_raw_to_sample5(raw_files, output_folder, polarity, num_cores):",
            '    """Convert raw data files to sample5 format."""',
            "    import concurrent.futures",
            "    import os",
            "    ",
            "    # Create output directory",
            "    os.makedirs(output_folder, exist_ok=True)",
            "    ",
            "    # Prepare arguments for multiprocessing",
            "    file_args = [(raw_file, output_folder) for raw_file in raw_files]",
            "    ",
            "    # Process files in parallel",
            "    sample5_files = []",
            "    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:",
            "        futures = [executor.submit(process_single_file, args) for args in file_args]",
            "        ",
            "        for future in concurrent.futures.as_completed(futures):",
            "            result = future.result()",
            "            if result:",
            "                sample5_files.append(result)",
            "    ",
            "    return sample5_files",
            "",
            "",
            "def main():",
            '    """Main analysis pipeline."""',
            "    try:",
            '        print("=" * 70)',
            f'        print("masster {version} - Automated MS Data Analysis")',
            '        print("=" * 70)',
            "        print(f\"Source: {PARAMS['source']}\")",
            "        print(f\"Output: {PARAMS['folder']}\")",
            "        print(f\"Polarity: {PARAMS['polarity']}\")",
            "        print(f\"CPU Cores: {PARAMS['num_cores']}\")",
            '        print("=" * 70)',
            "        ",
            "        start_time = time.time()",
            "        ",
            "        # Step 1: Discover raw data files",
            '        print("\\nStep 1/7: Discovering raw data files...")',
            "        raw_files = discover_raw_files(",
            "            PARAMS['source'],",
            "            PARAMS['file_extensions'],",
            "            PARAMS['search_subfolders']",
            "        )",
            "        ",
            "        if not raw_files:",
            '            print("No raw data files found!")',
            "            return False",
            "        ",
            '        print(f"Found {len(raw_files)} raw data files")',
            "        for f in raw_files[:5]:  # Show first 5 files",
            '            print(f"  {f.name}")',
            "        if len(raw_files) > 5:",
            '            print(f"  ... and {len(raw_files) - 5} more")',
            "        ",
            "        # Step 2: Process raw files",
            '        print("\\nStep 2/7: Processing raw files...")',
            "        sample5_files = convert_raw_to_sample5(",
            "            raw_files,",
            "            PARAMS['folder'],",
            "            PARAMS['polarity'],",
            "            PARAMS['num_cores']",
            "        )",
            "        ",
            "        if not sample5_files:",
            '            print("No sample5 files were created!")',
            "            return False",
            "        ",
            '        print(f"Successfully processed {len(sample5_files)} files to sample5")',
            "        ",
            "        # Step 3: Create and configure study",
            '        print("\\nStep 3/7: Initializing study...")',
            "        study = Study(folder=PARAMS['folder'])",
            "        study.polarity = PARAMS['polarity']",
            "        study.adducts = PARAMS['adducts']",
            "        ",
            "        # Step 4: Add sample5 files to study",
            '        print("\\nStep 4/7: Adding samples to study...")',
            "        study.add(str(Path(PARAMS['folder']) / \"*.sample5\"))",
            "        study.features_filter(study.features_select(chrom_coherence=0.1, chrom_prominence_scaled=1))",
            "        ",
            "        # Step 5: Core processing",
            '        print("\\nStep 5/7: Processing...")',
            "        study.align(",
            "            algorithm=PARAMS['alignment_method'],",
            "            rt_tol=PARAMS['rt_tol']",
            "        )",
            "        ",
            "        study.merge(",
            '            method="qt",',
            "            min_samples=PARAMS['min_samples_per_feature'],",
            "            threads=PARAMS['num_cores'],",
            "            rt_tol=PARAMS['rt_tol']",
            "        )",
            "        study.find_iso()",
            "        study.fill()",
            "        study.integrate()",
            "        ",
            "        # Step 6/7: Saving results",
            '        print("\\nStep 6/7: Saving results...")',
            "        study.save()",
            "        study.export_xlsx()",
            "        study.export_mgf()",
            "        study.export_mztab()",
            "        ",
            "        # Step 7: Plots",
            '        print("\\nStep 7/7: Exporting plots...")',
            '        study.plot_consensus_2d(filename="consensus.html")',
            '        study.plot_consensus_2d(filename="consensus.png")',
            '        study.plot_alignment(filename="alignment.html")',
            '        study.plot_alignment(filename="alignment.png")',
            '        study.plot_samples_pca(filename="pca.html")',
            '        study.plot_samples_pca(filename="pca.png")',
            '        study.plot_bpc(filename="bpc.html")',
            '        study.plot_bpc(filename="bpc.png")',
            '        study.plot_rt_correction(filename="rt_correction.html")',
            '        study.plot_rt_correction(filename="rt_correction.png")',
            "        ",
            "        # Print summary",
            "        study.info()",
            "        total_time = time.time() - start_time",
            '        print("\\n" + "=" * 70)',
            '        print("ANALYSIS COMPLETE")',
            '        print("=" * 70)',
            '        print(f"Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")',
            '        print(f"Raw files processed: {len(raw_files)}")',
            '        print(f"Sample5 files created: {len(sample5_files)}")',
            '        if hasattr(study, "consensus_df"):',
            '            print(f"Consensus features generated: {len(study.consensus_df)}")',
            '        print("=" * 70)',
            "        ",
            "        return True",
            "        ",
            "    except KeyboardInterrupt:",
            '        print("\\nAnalysis interrupted by user")',
            "        return False",
            "    except Exception as e:",
            '        print(f"Analysis failed with error: {e}")',
            "        import traceback",
            "        traceback.print_exc()",
            "        return False",
            "",
            "",
            'if __name__ == "__main__":',
            "    success = main()",
            "    sys.exit(0 if success else 1)",
        ]

        return "\n".join(script_lines)

    def _generate_interactive_notebook_content(self, source_info: Dict[str, Any]) -> str:
        """Generate the content for 2_interactive_analysis.py marimo notebook."""

        notebook_lines = [
            "import marimo",
            "",
            '__generated_with = "0.9.14"',
            'app = marimo.App(width="medium")',
            "",
            "@app.cell",
            "def __():",
            "    import marimo as mo",
            "    return (mo,)",
            "",
            "@app.cell",
            "def __(mo):",
            '    mo.md(r"""',
            "    # MASSter Interactive Analysis",
            "    ",
            f"    **Source:** {source_info.get('number_of_files', 0)} files detected",
            f"    **Polarity:** {source_info.get('polarity', 'unknown')}",
            "    ",
            "    This notebook provides interactive exploration of your processed study.",
            "    Make sure you have run `python 1_masster_workflow.py` first.",
            '    """)',
            '    return ()',
            '',
            '@app.cell',
            'def __():',
            '    import masster',
            '    return (masster,)',
            '',
            '@app.cell',
            'def __(masster):',
            f'    study = masster.Study(folder={str(self.folder_path)!r})',
            '    study.load()',
            '    return (study,)',
            '',
            '@app.cell',
            'def __(study):',
            '    study.info()',
            '    return ()',
            '',
            'if __name__ == "__main__":',
            "    app.run()",
        ]

        return "\n".join(notebook_lines)

    def _generate_instructions(self, source_info: Dict[str, Any], files_created: List[str]) -> List[str]:
        """Generate usage instructions for the created scripts."""
        instructions = [
            f"Source analysis: {source_info.get('number_of_files', 0)} files found",
            f"Polarity detected: {source_info.get('polarity', 'unknown')}",
            "Files created:",
        ]
        for file_path in files_created:
            instructions.append(f"  {str(Path(file_path).resolve())}")
        
        # Find the workflow script name from created files
        workflow_script_name = "1_masster_workflow.py"
        for file_path in files_created:
            if Path(file_path).name == "1_masster_workflow.py":
                workflow_script_name = Path(file_path).name
                break

        instructions.extend([
            "",
            "Next steps:",
            f"1. REVIEW PARAMETERS in {workflow_script_name}:",
            f"   In particular, verify the NOISE, CHROM_FWHM, and MIN_SAMPLES_FOR_MERGE",
            "",
            "2. TEST SINGLE FILE (RECOMMENDED):",
            f"   wizard.test_only()  # Validate parameters with first file only",
            "",
            "3. EXECUTE FULL BATCH:",
            f"   wizard.run()        # Process all files",
            f"   # OR: wizard.test_and_run()  # Test first, then run all",
            f"   # OR: uv run python {workflow_script_name}",
            "",
            "4. INTERACTIVE ANALYSIS:",
            f"   uv run marimo edit {Path('2_interactive_analysis.py').name}",
            "",
        ])

        return instructions

    def _add_test_mode_support(self, workflow_content: str) -> str:
        """Add test mode functionality to the generated workflow script."""
        lines = workflow_content.split("\n")

        # Insert test mode code after print statements in main function
        for i, line in enumerate(lines):
            # Add test mode print after the masster version line
            if 'print("masster' in line and 'Automated MS Data Analysis")' in line:
                lines.insert(i + 1, '        if TEST:')
                lines.insert(i + 2, '            print("TEST MODE: Processing single file only")')
                break

        # Add mode info after num_cores print
        for i, line in enumerate(lines):
            if "print(f\"CPU Cores: {PARAMS['num_cores']}\")" in line:
                lines.insert(i + 1, "        if TEST:")
                lines.insert(i + 2, "            print(f\"Mode: {'Test Only' if STOP_AFTER_TEST else 'Test + Full Batch'}\")")
                break

        # Add file limitation logic after file listing
        for i, line in enumerate(lines):
            if 'print(f"  ... and {len(raw_files) - 5} more")' in line:
                lines.insert(i + 1, '        ')
                lines.insert(i + 2, '        # Limit to first file in test mode')
                lines.insert(i + 3, '        if TEST:')
                lines.insert(i + 4, '            raw_files = raw_files[:1]')
                lines.insert(i + 5, '            print(f"\\nTEST MODE: Processing only first file: {raw_files[0].name}")')
                break

        # Modify num_cores for test mode
        for i, line in enumerate(lines):
            if "PARAMS['num_cores']" in line and "convert_raw_to_sample5(" in lines[i - 2 : i + 3]:
                lines[i] = line.replace(
                    "PARAMS['num_cores']", "PARAMS['num_cores'] if not TEST else 1  # Use single core for test"
                )
                break

        # Add test-only exit logic after successful processing
        for i, line in enumerate(lines):
            if 'print(f"Successfully processed {len(sample5_files)} files to sample5")' in line:
                lines.insert(i + 1, '        ')
                lines.insert(i + 2, '        # Stop here if stop-after-test mode')
                lines.insert(i + 3, '        if STOP_AFTER_TEST:')
                lines.insert(i + 4, '            print("\\nSTOP AFTER TEST mode: Stopping after successful single file processing")')
                lines.insert(i + 5, '            print(f"Test file created: {sample5_files[0]}")')
                lines.insert(i + 6, '            print("\\nTo run full batch, use: wizard.run()")')
                lines.insert(i + 7, "            total_time = time.time() - start_time")
                lines.insert(i + 8, '            print(f"\\nTest processing time: {total_time:.1f} seconds")')
                lines.insert(i + 9, "            return True")
                break

        return "\n".join(lines)

    def test_and_run(self) -> Dict[str, Any]:
        """
        Test the sample processing workflow with a single file, then run full batch.

        This method first runs the 1_masster_workflow.py script in test-only mode to process
        the first raw file for validation, then automatically continues with the
        full batch if the test succeeds. The script must already exist - call
        create_scripts() first if needed.

        Returns:
            Dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - instructions: List of next steps
        """
        # Step 1: Run test-only mode first
        print("Step 1/2: Testing with single file...")
        test_result = self._execute_workflow(test=True, run=False)
        
        if test_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Test failed: {test_result['message']}",
                "instructions": [
                    "Single file test failed",
                    "Review parameters in 1_masster_workflow.py",
                    "Fix issues and try again",
                ],
            }
        
        print("Test successful! Proceeding with full batch...")
        print("Step 2/2: Processing all files...")
        
        # Step 2: Run full batch mode
        full_result = self._execute_workflow(test=False, run=True)
        
        return full_result

    def test_only(self) -> Dict[str, Any]:
        """
        Test the sample processing workflow with a single file only.

        This method runs the 1_masster_workflow.py script in test-only mode to process
        only the first raw file and then stops (does not continue to full study processing).
        The script must already exist - call create_scripts() first if needed.

        Returns:
            Dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - instructions: List of next steps
            - test_file: Path to the processed test file (if successful)
        """
        return self._execute_workflow(test=True, run=False)

    def test(self) -> Dict[str, Any]:
        """
        Test the sample processing workflow with a single file only.

        This method runs the 1_masster_workflow.py script in test-only mode to process
        only the first raw file and then stops (does not continue to full study processing).
        The script must already exist - call create_scripts() first if needed.

        Returns:
            Dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - instructions: List of next steps
            - test_file: Path to the processed test file (if successful)
        """
        return self._execute_workflow(test=True, run=False)


    def run(self) -> Dict[str, Any]:
        """
        Run the sample processing workflow.

        This method runs the 1_masster_workflow.py script to process raw files.
        The script must already exist - call create_scripts() first if needed.

        Returns:
            Dictionary containing:
            - status: "success" or "error"
            - message: Status message
            - instructions: List of next steps
        """
        return self._execute_workflow(test=False, run=True)

    def _execute_workflow(self, test: bool = False, run: bool = True) -> Dict[str, Any]:
        """
        Execute the workflow script in either test or full mode.

        Args:
            test: If True, run in test mode (single file), otherwise full batch
            run: If False, stop after test (only used with test=True), if True continue with full processing
        """
        try:
            workflow_script_path = self.folder_path / "1_masster_workflow.py"

            # Check if workflow script exists
            if not workflow_script_path.exists():
                print("Workflow script not found. Creating scripts automatically...")
                create_result = self.create_scripts()
                
                if create_result["status"] == "error":
                    return {
                        "status": "error",
                        "message": f"Failed to create workflow script: {create_result['message']}",
                        "instructions": [
                            "Could not create 1_masster_workflow.py",
                            "Please check source path and permissions",
                        ],
                    }
                
                print(f"Created {len(create_result.get('files_created', []))} script files")
                for file_path in create_result.get('files_created', []):
                    print(f"  - {file_path}")
                print("Proceeding with workflow execution...")

            # Setup execution mode
            if test and not run:
                mode_label = "test-only"
            elif test:
                mode_label = "test"
            else:
                mode_label = "full batch"

            env = None
            if test:
                import os

                env = os.environ.copy()
                env["MASSTER_TEST"] = "1"
                if not run:
                    env["MASSTER_STOP_AFTER_TEST"] = "1"

            # Execute the workflow script
            print(f">> Executing {mode_label} processing workflow...")
            print(f"Running: {workflow_script_path.name}")
            print("=" * 60)

            import subprocess

            result = subprocess.run([sys.executable, str(workflow_script_path)], cwd=str(self.folder_path), env=env)

            success = result.returncode == 0

            if success:
                print("=" * 60)
                if test and not run:
                    print("Test-only processing completed successfully!")
                    print("Single file validated - ready for full batch")
                    print("   wizard.run()")
                elif test:
                    print("Test processing completed successfully!")
                    print("Next step: Run full batch")
                    print("   wizard.run()")
                else:
                    notebook_path = self.folder_path / "2_interactive_analysis.py"
                    print("Sample processing completed successfully!")
                    print("Next step: Run interactive analysis")
                    print(f"   uv run marimo edit {notebook_path}")
                print("=" * 60)

                next_step = "Next: wizard.run()" if test else f"Next: uv run marimo edit {self.folder_path / '2_interactive_analysis.py'}"

                return {
                    "status": "success",
                    "message": f"{mode_label.capitalize()} processing completed successfully",
                    "instructions": [
                        f"{mode_label.capitalize()} processing completed",
                        next_step
                    ]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Workflow execution failed with return code {result.returncode}",
                    "instructions": [
                        "Check the error messages above",
                        "Review parameters in 1_masster_workflow.py",
                        f"Try running manually: python {workflow_script_path.name}",
                    ],
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to execute workflow: {e}",
                "instructions": [
                    "Execution failed",
                    "Check that source files exist and are accessible",
                    "Verify folder permissions",
                ],
            }

    def _generate_script_content(self) -> str:
        """Generate the complete analysis script content."""

        # Convert Path objects to strings for JSON serialization
        params_dict = {}
        for key, value in self.params.__dict__.items():
            if key == "_param_metadata":  # Skip metadata in generated script
                continue
            if isinstance(value, Path):
                params_dict[key] = str(value)
            else:
                params_dict[key] = value

        # Obtain list of files in source with extension wiff, .raw, .mzML
        raw_files = []
        for ext in params_dict.get("file_extensions", []):
            raw_files.extend(glob.glob(f"{params_dict.get('source', '')}/**/*{ext}", recursive=True))

        # Create readable PARAMS dict with comments
        params_lines = []
        params_lines.append("# Analysis parameters")
        params_lines.append("PARAMS = {")

        # Core Configuration
        params_lines.append("    # === Core Configuration ===")
        params_lines.append(f'    "source": {params_dict.get("source", "")!r},  # Directory containing raw data files')
        params_lines.append(f'    "folder": {params_dict.get("folder", "")!r},  # Output directory for processed study')
        params_lines.append(
            f'    "polarity": {params_dict.get("polarity", "positive")!r},  # Ion polarity mode ("positive" or "negative")'
        )
        params_lines.append(
            f'    "num_cores": {params_dict.get("num_cores", 4)},  # Number of CPU cores for parallel processing'
        )
        params_lines.append("")

        # File Discovery
        params_lines.append("    # === File Discovery ===")
        params_lines.append(
            f'    "file_extensions": {params_dict.get("file_extensions", [".wiff", ".raw", ".mzML"])!r},  # File extensions to search for'
        )
        params_lines.append(
            f'    "search_subfolders": {params_dict.get("search_subfolders", True)},  # Whether to search subdirectories recursively'
        )
        params_lines.append(
            f'    "skip_patterns": {params_dict.get("skip_patterns", ["blank", "condition"])!r},  # Filename patterns to skip'
        )
        params_lines.append("")

        # Processing Parameters
        params_lines.append("    # === Processing Parameters ===")
        params_lines.append(
            f'    "adducts": {params_dict.get("adducts", [])!r},  # Adduct specifications for feature detection and annotation'
        )
        params_lines.append(
            f'    "detector_type": {params_dict.get("detector_type", "unknown")!r},  # MS detector type ("orbitrap", "tof", "unknown")'
        )
        params_lines.append(f'    "noise": {params_dict.get("noise", 50.0)},  # Noise threshold for feature detection')
        params_lines.append(
            f'    "chrom_fwhm": {params_dict.get("chrom_fwhm", 0.5)},  # Chromatographic peak full width at half maximum (seconds)'
        )
        params_lines.append(
            f'    "chrom_peak_snr": {params_dict.get("chrom_peak_snr", 5.0)},  # Minimum signal-to-noise ratio for chromatographic peaks'
        )
        params_lines.append("")

        # Alignment & Merging
        params_lines.append("    # === Alignment & Merging ===")
        params_lines.append(
            f'    "rt_tol": {params_dict.get("rt_tol", 2.0)},  # Retention time tolerance for alignment (seconds)'
        )
        params_lines.append(
            f'    "mz_tol": {params_dict.get("mz_tol", 0.01)},  # Mass-to-charge ratio tolerance for alignment (Da)'
        )
        params_lines.append(
            f'    "alignment_method": {params_dict.get("alignment_method", "kd")!r},  # Algorithm for sample alignment'
        )
        params_lines.append(
            f'    "min_samples_per_feature": {params_dict.get("min_samples_per_feature", 1)},  # Minimum samples required per consensus feature'
        )
        params_lines.append(
            f'    "merge_method": {params_dict.get("merge_method", "qt")!r},  # Method for merging consensus features'
        )
        params_lines.append("")

        # Sample Processing
        params_lines.append("    # === Sample Processing (used in add_samples_from_folder) ===")
        params_lines.append(
            f'    "batch_size": {params_dict.get("batch_size", 8)},  # Number of files to process per batch'
        )
        params_lines.append(
            f'    "memory_limit_gb": {params_dict.get("memory_limit_gb", 16.0)},  # Memory limit for processing (GB)'
        )
        params_lines.append("")

        # Script Options
        params_lines.append("    # === Script Options ===")
        params_lines.append(
            f'    "resume_enabled": {params_dict.get("resume_enabled", True)},  # Enable automatic resume capability'
        )
        params_lines.append(
            f'    "force_reprocess": {params_dict.get("force_reprocess", False)},  # Force reprocessing of existing files'
        )
        params_lines.append(
            f'    "cleanup_temp_files": {params_dict.get("cleanup_temp_files", True)},  # Clean up temporary files after processing'
        )

        params_lines.append("}")

        # Create script lines
        script_lines = [
            "#!/usr/bin/env python3",
            '"""',
            "Automated Mass Spectrometry Data Analysis Pipeline",
            f"Generated by masster wizard v{version}",
            '"""',
            "",
            "import sys",
            "import time",
            "from pathlib import Path",
            "",
            "# Import masster modules",
            "from masster.study import Study",
            "from masster import __version__",
            "",
        ]

        # Add the formatted PARAMS
        script_lines.extend(params_lines)

        # Add the main function and pipeline
        script_lines.extend([
            "",
            "",
            "def discover_raw_files(source_folder, file_extensions, search_subfolders=True):",
            '    """Discover raw data files in the source folder."""',
            "    source_path = Path(source_folder)",
            "    raw_files = []",
            "    ",
            "    for ext in file_extensions:",
            "        if search_subfolders:",
            '            pattern = f"**/*{ext}"',
            "            files = list(source_path.rglob(pattern))",
            "        else:",
            '            pattern = f"*{ext}"',
            "            files = list(source_path.glob(pattern))",
            "        raw_files.extend(files)",
            "    ",
            "    return raw_files",
            "",
            "",
            "def process_single_file(args):",
            '    """Process a single raw file to sample5 format - module level for multiprocessing."""',
            "    raw_file, output_folder = args",
            "    from masster.sample import Sample",
            "    ",
            "    try:",
            "        # Create sample5 filename",
            "        sample_name = raw_file.stem",
            '        sample5_path = Path(output_folder) / f"{sample_name}.sample5"',
            "        ",
            "        # Skip if sample5 already exists",
            "        if sample5_path.exists():",
            '            print(f"  Skipping {raw_file.name} (sample5 already exists)")',
            "            return str(sample5_path)",
            "        ",
            '        print(f"  Converting {raw_file.name}...")',
            "        ",
            "        # Load and process raw file with full pipeline",
            "        sample = Sample(log_label=sample_name)",
            "        sample.load(filename=str(raw_file))",
            "        sample.find_features(",
            "            noise=PARAMS['noise'],",
            "            chrom_fwhm=PARAMS['chrom_fwhm'],",
            "            chrom_peak_snr=PARAMS['chrom_peak_snr']",
            "        )",
            "        sample.find_adducts(adducts=PARAMS['adducts'])",
            "        sample.find_ms2()",
            "        sample.find_iso()",
            "        # sample.export_mgf()",
            "        # sample.export_mztab()",
            '        # sample.plot_2d(filename="{sample_name}.html")',
            "        sample.save(str(sample5_path))",
            "        ",
            '        # print(f"  Completed {raw_file.name} -> {sample5_path.name}")',
            "        return str(sample5_path)",
            "        ",
            "    except Exception as e:",
            '        print(f"  ERROR processing {raw_file.name}: {e}")',
            "        return None",
            "",
            "",
            "def convert_raw_to_sample5(raw_files, output_folder, polarity, num_cores):",
            '    """Convert raw data files to sample5 format."""',
            "    import concurrent.futures",
            "    import os",
            "    ",
            "    # Create output directory",
            "    os.makedirs(output_folder, exist_ok=True)",
            "    ",
            "    # Prepare arguments for multiprocessing",
            "    file_args = [(raw_file, output_folder) for raw_file in raw_files]",
            "    ",
            "    # Process files in parallel",
            "    sample5_files = []",
            "    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:",
            "        futures = [executor.submit(process_single_file, args) for args in file_args]",
            "        ",
            "        for future in concurrent.futures.as_completed(futures):",
            "            result = future.result()",
            "            if result:",
            "                sample5_files.append(result)",
            "    ",
            "    return sample5_files",
            "",
            "",
            "def main():",
            '    """Main analysis pipeline."""',
            "    try:",
            '        print("=" * 70)',
            f'        print("masster {version} - Automated MS Data Analysis")',
            '        print("=" * 70)',
            "        print(f\"Source: {PARAMS['source']}\")",
            "        print(f\"Output: {PARAMS['folder']}\")",
            "        print(f\"Polarity: {PARAMS['polarity']}\")",
            "        print(f\"CPU Cores: {PARAMS['num_cores']}\")",
            '        print("=" * 70)',
            "        ",
            "        start_time = time.time()",
            "        ",
            "        # Step 1: Discover raw data files",
            '        print("\\nStep 1/7: Discovering raw data files...")',
            "        raw_files = discover_raw_files(",
            "            PARAMS['source'],",
            "            PARAMS['file_extensions'],",
            "            PARAMS['search_subfolders']",
            "        )",
            "        ",
            "        if not raw_files:",
            '            print("No raw data files found!")',
            "            return False",
            "        ",
            '        print(f"Found {len(raw_files)} raw data files")',
            "        for f in raw_files[:5]:  # Show first 5 files",
            '            print(f"  {f.name}")',
            "        if len(raw_files) > 5:",
            '            print(f"  ... and {len(raw_files) - 5} more")',
            "        ",
            "        # Step 2: Process raw files",
            '        print("\\nStep 2/7: Processing raw files...")',
            "        sample5_files = convert_raw_to_sample5(",
            "            raw_files,",
            "            PARAMS['folder'],",
            "            PARAMS['polarity'],",
            "            PARAMS['num_cores']",
            "        )",
            "        ",
            "        if not sample5_files:",
            '            print("No sample5 files were created!")',
            "            return False",
            "        ",
            '        print(f"Successfully processed {len(sample5_files)} files to sample5")',
            "        ",
            "        # Step 3: Create and configure study",
            '        print("\\nStep 3/7: Initializing study...")',
            "        study = Study(folder=PARAMS['folder'])",
            "        study.polarity = PARAMS['polarity']",
            "        study.adducts = PARAMS['adducts']",
            "        ",
            "        # Step 4: Add sample5 files to study",
            '        print("\\nStep 4/7: Adding samples to study...")',
            "        study.add(str(Path(PARAMS['folder']) / \"*.sample5\"))",
            "        study.features_filter(study.features_select(chrom_coherence=0.1, chrom_prominence_scaled=1))",
            "        ",
            "        # Step 5: Core processing",
            '        print("\\nStep 5/7: Processing...")',
            "        study.align(",
            "            algorithm=PARAMS['alignment_method'],",
            "            rt_tol=PARAMS['rt_tol']",
            "        )",
            "        ",
            "        study.merge(",
            '            method="qt",',
            "            min_samples=PARAMS['min_samples_per_feature'],",
            "            threads=PARAMS['num_cores'],",
            "            rt_tol=PARAMS['rt_tol'],        )",
            "        study.find_iso()",
            "        study.fill()",
            "        study.integrate()",
            "        ",
            "        # Step 6/7: Saving results",
            '        print("\\nStep 6/7: Saving results...")',
            "        study.save()",
            "        study.export_xlsx()",
            "        study.export_mgf()",
            "        study.export_mztab()",
            "        ",
            "        # Step 7: Plots",
            '        print("\\nStep 7/7: Exporting plots...")',
            '        study.plot_consensus_2d(filename="consensus.html")',
            '        study.plot_consensus_2d(filename="consensus.png")',
            '        study.plot_alignment(filename="alignment.html")',
            '        study.plot_alignment(filename="alignment.png")',
            '        study.plot_samples_pca(filename="pca.html")',
            '        study.plot_samples_pca(filename="pca.png")',
            '        study.plot_bpc(filename="bpc.html")',
            '        study.plot_bpc(filename="bpc.png")',
            '        study.plot_rt_correction(filename="rt_correction.html")',
            '        study.plot_rt_correction(filename="rt_correction.png")',
            "        ",
            "        # Print summary",
            "        study.info()",
            "        total_time = time.time() - start_time",
            '        print("\\n" + "=" * 70)',
            '        print("ANALYSIS COMPLETE")',
            '        print("=" * 70)',
            '        print(f"Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")',
            '        print(f"Raw files processed: {len(raw_files)}")',
            '        print(f"Sample5 files created: {len(sample5_files)}")',
            '        if hasattr(study, "consensus_df"):',
            '            print(f"Consensus features generated: {len(study.consensus_df)}")',
            '        print("=" * 70)',
            "        ",
            "        return True",
            "        ",
            "    except KeyboardInterrupt:",
            '        print("\\nAnalysis interrupted by user")',
            "        return False",
            "    except Exception as e:",
            '        print(f"Analysis failed with error: {e}")',
            "        import traceback",
            "        traceback.print_exc()",
            "        return False",
            "",
            "",
            'if __name__ == "__main__":',
            "    success = main()",
            "    sys.exit(0 if success else 1)",
        ])

        return "\n".join(script_lines)


def create_scripts(
    source: str = "",
    folder: str = "",
    polarity: Optional[str] = None,
    adducts: Optional[List[str]] = None,
    num_cores: int = 0,
    **kwargs,
) -> Dict[str, Any]:
    """
    Create analysis scripts without explicitly instantiating a Wizard.

    This is a convenience function that creates a Wizard instance internally
    and calls its create_scripts() method.

    Parameters:
        source: Directory containing raw data files
        folder: Output directory for processed study
        polarity: Ion polarity mode ("positive", "negative", or None for auto-detection)
        adducts: List of adduct specifications (auto-set if None)
        num_cores: Number of CPU cores (0 = auto-detect)
        **kwargs: Additional parameters

    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Status message
        - instructions: List of next steps
        - files_created: List of created file paths
        - source_info: Metadata about source files

    Example:
        >>> import masster.wizard
        >>> result = masster.wizard.create_scripts(
        ...     source=r'D:\\Data\\raw_files',
        ...     folder=r'D:\\Data\\output',
        ...     polarity='negative'
        ... )
        >>> print("Status:", result["status"])
    """

    try:
        # Auto-detect optimal number of cores if not specified
        if num_cores <= 0:
            num_cores = max(1, int(multiprocessing.cpu_count() * 0.75))

        # Create Wizard instance
        wizard = Wizard(source=source, folder=folder, polarity=polarity, adducts=adducts, num_cores=num_cores, **kwargs)

        # Call the instance method
        return wizard.create_scripts()

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create scripts: {e}",
            "instructions": [],
            "files_created": [],
            "source_info": {},
        }


# Export the main classes and functions
__all__ = ["Wizard", "wizard_def", "create_scripts"]
