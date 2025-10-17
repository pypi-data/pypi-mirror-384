"""
Standalone Thermo RAW file reader module.

This module provides a standalone implementation for reading Thermo Fisher RAW files
using the Thermo Fisher .NET libraries directly. It offers functionality to extract
spectral data, retention times, MS levels, polarity information, and precursor details
from RAW files.

Key Features:
    - Direct RAW file reading using Thermo Fisher DLLs
    - Support for MS1 and MSn data extraction
    - Optional naive peak centroiding
    - Polarity detection from scan events
    - Precursor information extraction for MS/MS spectra
    - Context manager support for proper resource cleanup

Requirements:
    - pythonnet (pip install pythonnet)
    - Thermo Fisher DLLs available in alpharaw's ext/thermo_fisher directory
    - On Linux/macOS: mono runtime must be installed

Classes:
    ThermoRawFileReader: Low-level RAW file reader using .NET libraries
    ThermoRawData: High-level interface providing pandas DataFrames

Example:
    >>> from thermo import load_raw_file
    >>> raw_data = load_raw_file("sample.raw")
    >>> print(f"Found {len(raw_data.spectrum_df)} spectra")
    >>> mz, intensity = raw_data.get_peaks(0)  # Get first spectrum peaks

Note:
    The .NET imports (System, ThermoFisher) will only work when pythonnet
    is properly installed and configured. Without these dependencies, the
    module will still import but Thermo RAW file reading will be disabled.
"""

# Standard library imports
import ctypes
import os
import site
import warnings
from typing import Any, ClassVar

# Third-party imports
import numpy as np
import pandas as pd


def naive_centroid(
    peak_mzs: np.ndarray,
    peak_intensities: np.ndarray,
    centroiding_ppm: float = 20.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simplified naive centroiding implementation.

    Combines nearby peaks within a PPM tolerance using intensity-weighted averaging.

    Parameters
    ----------
    peak_mzs : np.ndarray
        Array of m/z values (must be sorted)
    peak_intensities : np.ndarray
        Array of intensity values corresponding to peak_mzs
    centroiding_ppm : float, default 20.0
        PPM tolerance for combining peaks

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Centroided m/z and intensity arrays

    Notes
    -----
    This is a simple implementation that assumes input peaks are sorted by m/z.
    For production use, consider more sophisticated centroiding algorithms.
    """
    if len(peak_mzs) == 0:
        return np.array([]), np.array([])

    if len(peak_mzs) != len(peak_intensities):
        raise ValueError("peak_mzs and peak_intensities must have the same length")

    centroided_mzs = []
    centroided_intensities = []

    i = 0
    while i < len(peak_mzs):
        current_mz = peak_mzs[i]
        current_intensity = peak_intensities[i]

        # Calculate tolerance for current m/z
        tolerance = current_mz * centroiding_ppm * 1e-6

        # Find all peaks within tolerance
        total_intensity = current_intensity
        weighted_mz_sum = current_mz * current_intensity
        j = i + 1

        while j < len(peak_mzs) and abs(peak_mzs[j] - current_mz) <= tolerance:
            total_intensity += peak_intensities[j]
            weighted_mz_sum += peak_mzs[j] * peak_intensities[j]
            j += 1

        # Calculate intensity-weighted centroided m/z
        if total_intensity > 0:
            centroided_mz = weighted_mz_sum / total_intensity
            centroided_mzs.append(centroided_mz)
            centroided_intensities.append(total_intensity)

        i = j

    return np.array(centroided_mzs), np.array(centroided_intensities)


# CLR utilities implementation
try:
    # require pythonnet, pip install pythonnet on Windows
    import clr

    clr.AddReference("System")

    import System  # noqa: F401
    from System.Globalization import CultureInfo
    from System.Runtime.InteropServices import GCHandle, GCHandleType
    from System.Threading import Thread

    de_fr = CultureInfo("fr-FR")
    other = CultureInfo("en-US")

    Thread.CurrentThread.CurrentCulture = other
    Thread.CurrentThread.CurrentUICulture = other

    # Find the alpharaw ext/thermo_fisher directory in site-packages
    ext_dir = None
    for site_dir in site.getsitepackages():
        potential_ext_dir = os.path.join(site_dir, "alpharaw", "ext")
        if os.path.exists(potential_ext_dir):
            ext_dir = potential_ext_dir
            break

    if ext_dir is None:
        # Try alternative locations
        try:
            import alpharaw

            alpharaw_dir = os.path.dirname(alpharaw.__file__)
            ext_dir = os.path.join(alpharaw_dir, "ext")
        except ImportError:
            pass

    if not ext_dir or not os.path.exists(os.path.join(ext_dir, "thermo_fisher")):
        raise ImportError("Could not find alpharaw ext/thermo_fisher directory with DLLs")

    # Add Thermo Fisher DLL references
    clr.AddReference(
        os.path.join(ext_dir, "thermo_fisher", "ThermoFisher.CommonCore.Data.dll"),
    )
    clr.AddReference(os.path.join(ext_dir, "thermo_fisher", "ThermoFisher.CommonCore.RawFileReader.dll"))

    import ThermoFisher  # noqa: F401

    from ThermoFisher.CommonCore.Data.Business import Device
    from ThermoFisher.CommonCore.Data.Interfaces import IScanEvent, IScanEventBase  # noqa: F401
    from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter

    HAS_DOTNET = True
except ImportError as e:
    # Allow the rest of the code to work without .NET support
    warnings.warn(
        f"Thermo RAW file support is disabled. Install pythonnet and ensure Thermo Fisher DLLs "
        f"are available to enable Thermo RAW file reading. Error: {e}",
        UserWarning,
        stacklevel=2,
    )
    HAS_DOTNET = False
except Exception as e:
    # Catch any other .NET related errors
    warnings.warn(
        f"Failed to initialize .NET components for Thermo support. Error: {e}",
        UserWarning,
        stacklevel=2,
    )
    HAS_DOTNET = False


def dot_net_array_to_np_array(src) -> np.ndarray:
    """
    Convert .NET array to NumPy array with efficient memory handling.

    This function performs a zero-copy conversion from .NET arrays to NumPy arrays
    by directly accessing the underlying memory buffer. This is much faster than
    iterating through elements.

    Parameters
    ----------
    src : .NET array or None
        Source .NET array to convert (typically double[])

    Returns
    -------
    np.ndarray
        Converted NumPy array with dtype float64. Returns empty array if src is None.

    Notes
    -----
    Based on the approach from:
    https://mail.python.org/pipermail/pythondotnet/2014-May/001527.html

    The function uses GCHandle.Alloc to pin the .NET array in memory, allowing
    direct access to its underlying buffer via ctypes. The buffer is then
    wrapped as a NumPy array and copied to ensure memory safety.
    """
    if src is None:
        return np.array([], dtype=np.float64)

    # Pin the .NET array in memory to prevent garbage collection
    src_hndl = GCHandle.Alloc(src, GCHandleType.Pinned)
    try:
        # Get pointer to the pinned memory
        src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()

        # Create ctypes buffer pointing to the same memory
        buf_type = ctypes.c_double * len(src)
        cbuf = buf_type.from_address(src_ptr)

        # Convert to NumPy array and make a copy for safety
        dest = np.frombuffer(cbuf, dtype="float64").copy()  # type: ignore[call-overload]
    finally:
        # Always free the GC handle to prevent memory leaks
        if src_hndl.IsAllocated:
            src_hndl.Free()
        return dest  # noqa: B012


class ThermoRawFileReader:
    """
    Direct implementation of Thermo RAW file reader using the Thermo Fisher DLLs.
    """

    def __init__(self, filename: str):
        if not HAS_DOTNET:
            raise ImportError(
                "Thermo RAW file support requires .NET components. "
                "Install pythonnet (pip install pythonnet) and ensure Thermo Fisher DLLs "
                "are available in alpharaw's ext/thermo_fisher directory."
            )

        if not os.path.exists(filename):
            raise FileNotFoundError(f"RAW file not found: {filename}")

        try:
            self._raw_file = RawFileReaderAdapter.FileFactory(filename)
        except Exception as e:
            raise ValueError(f"Failed to create RAW file reader for '{filename}': {e}") from e

        if not self._raw_file.IsOpen:
            raise ValueError(f"Could not open RAW file: {filename}")

        try:
            # Get basic file information
            self._raw_file.SelectInstrument(Device.MS, 1)  # MS instrument
            self.first_scan = self._raw_file.RunHeaderEx.FirstSpectrum
            self.last_scan = self._raw_file.RunHeaderEx.LastSpectrum
            self.num_scans = self.last_scan - self.first_scan + 1
        except Exception as e:
            self.close()
            raise ValueError(f"Failed to read RAW file header information: {e}") from e

    def close(self) -> None:
        """Close the file and clean up resources."""
        if hasattr(self, "_raw_file") and self._raw_file is not None:
            self._raw_file.Dispose()

    def __enter__(self) -> "ThermoRawFileReader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def get_polarity_from_scan_event(self, scan_number: int) -> str:
        """
        Extract polarity information from scan event.

        Parameters
        ----------
        scan_number : int
            Scan number to extract polarity from

        Returns
        -------
        str
            'positive', 'negative', or '' if unknown
        """
        try:
            scan_event = self._raw_file.GetScanEventForScanNumber(scan_number)
            if scan_event is None:
                return ""

            # Try the direct Polarity property first (most reliable)
            if hasattr(scan_event, "Polarity"):
                polarity_str = str(scan_event.Polarity).lower()
                if "positive" in polarity_str:
                    return "positive"
                elif "negative" in polarity_str:
                    return "negative"

            # Fallback: parse the scan filter string
            filter_string = str(scan_event.ToString()).lower()
            if "+" in filter_string or "positive" in filter_string:
                return "positive"
            elif "-" in filter_string or "negative" in filter_string:
                return "negative"

        except Exception:
            # Log the exception if needed, but don't raise
            pass

        return ""  # Unknown polarity

    def _extract_precursor_info(self, scan_event, ms_level: int) -> tuple[float, int, float, float, float]:
        """Extract precursor information from scan event for MS2+ scans."""
        if ms_level <= 1 or scan_event is None:
            return -1.0, 0, 0.0, -1.0, -1.0

        try:
            precursor_mz = float(scan_event.GetMass(0))
        except Exception:
            precursor_mz = -1.0

        try:
            precursor_charge = int(scan_event.GetChargeState(0)) if hasattr(scan_event, "GetChargeState") else 0
        except Exception:
            precursor_charge = 0

        try:
            collision_energy = float(scan_event.GetEnergy(0)) if hasattr(scan_event, "GetEnergy") else 0.0
        except Exception:
            collision_energy = 0.0

        try:
            isolation_window = (
                float(scan_event.GetIsolationWidth(0)) if hasattr(scan_event, "GetIsolationWidth") else 3.0
            )
        except Exception:
            isolation_window = 3.0

        isolation_lower = precursor_mz - isolation_window / 2
        isolation_upper = precursor_mz + isolation_window / 2

        return precursor_mz, precursor_charge, collision_energy, isolation_lower, isolation_upper

    def _process_scan_data(
        self, scan_data, centroid: bool, centroid_ppm: float, keep_k_peaks: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Process scan data to extract and optionally centroid peaks."""
        if scan_data.Positions is not None and scan_data.Intensities is not None:
            mz_array = dot_net_array_to_np_array(scan_data.Positions)
            int_array = dot_net_array_to_np_array(scan_data.Intensities).astype(np.float32)
        else:
            return np.array([]), np.array([])

        if centroid and len(mz_array) > 0:
            mz_array, int_array = naive_centroid(
                mz_array,
                int_array,
                centroiding_ppm=centroid_ppm,
            )

        # Keep only top K peaks by intensity
        if len(mz_array) > keep_k_peaks:
            top_indices = np.argsort(int_array)[-keep_k_peaks:]
            top_indices = np.sort(top_indices)
            mz_array = mz_array[top_indices]
            int_array = int_array[top_indices]

        return mz_array, int_array

    def load_all_scans(
        self,
        centroid: bool = True,
        centroid_ppm: float = 20.0,
        ignore_empty_scans: bool = True,
        keep_k_peaks: int = 2000,
    ) -> dict[str, Any]:
        """
        Load all scans from the RAW file and extract spectral data.

        Parameters
        ----------
        centroid : bool
            Whether to centroid the data
        centroid_ppm : float
            PPM tolerance for centroiding
        ignore_empty_scans : bool
            Whether to skip empty scans
        keep_k_peaks : int
            Maximum number of peaks to keep per spectrum

        Returns
        -------
        dict
            Dictionary containing spectral data with keys:
            peak_indices, peak_mz, peak_intensity, rt, ms_level, polarity,
            precursor_mz, precursor_charge, isolation_lower_mz, isolation_upper_mz, nce
        """
        # Initialize data collection lists
        peak_indices_list: list[int] = []
        peak_mz_arrays: list[np.ndarray] = []
        peak_intensity_arrays: list[np.ndarray] = []
        rt_list: list[float] = []
        ms_level_list: list[int] = []
        polarity_list: list[str] = []
        precursor_mz_list: list[float] = []
        precursor_charge_list: list[int] = []
        ce_list: list[float] = []
        isolation_lower_mz_list: list[float] = []
        isolation_upper_mz_list: list[float] = []

        for scan_num in range(self.first_scan, self.last_scan + 1):
            # Get scan statistics and data
            scan_stats = self._raw_file.GetScanStatsForScanNumber(scan_num)
            if scan_stats is None:
                continue

            scan_data = self._raw_file.GetSegmentedScanFromScanNumber(scan_num, scan_stats)
            if scan_data is None or (ignore_empty_scans and scan_data.Positions is None):
                continue

            scan_event = self._raw_file.GetScanEventForScanNumber(scan_num)

            # Extract basic scan information
            rt = scan_stats.StartTime  # in minutes
            ms_level = int(scan_event.MSOrder) if scan_event else 1
            polarity = self.get_polarity_from_scan_event(scan_num)

            # Process peak data
            mz_array, int_array = self._process_scan_data(scan_data, centroid, centroid_ppm, keep_k_peaks)

            # Store scan data
            peak_mz_arrays.append(mz_array)
            peak_intensity_arrays.append(int_array)
            peak_indices_list.append(len(mz_array))

            rt_list.append(rt)
            ms_level_list.append(ms_level)
            polarity_list.append(polarity)

            # Extract precursor information
            precursor_mz, precursor_charge, collision_energy, isolation_lower, isolation_upper = (
                self._extract_precursor_info(scan_event, ms_level)
            )

            precursor_mz_list.append(precursor_mz)
            precursor_charge_list.append(precursor_charge)
            ce_list.append(collision_energy)
            isolation_lower_mz_list.append(isolation_lower)
            isolation_upper_mz_list.append(isolation_upper)

        if not rt_list:
            raise ValueError("No valid scans found in the RAW file")

        # Create cumulative peak indices array
        peak_indices = np.empty(len(rt_list) + 1, dtype=np.int64)
        peak_indices[0] = 0
        peak_indices[1:] = np.cumsum(peak_indices_list)

        return {
            "peak_indices": peak_indices,
            "peak_mz": np.concatenate(peak_mz_arrays) if peak_mz_arrays else np.array([]),
            "peak_intensity": np.concatenate(peak_intensity_arrays) if peak_intensity_arrays else np.array([]),
            "rt": np.array(rt_list, dtype=np.float64),
            "ms_level": np.array(ms_level_list, dtype=np.int8),
            "polarity": np.array(polarity_list, dtype="U8"),
            "precursor_mz": np.array(precursor_mz_list, dtype=np.float64),
            "precursor_charge": np.array(precursor_charge_list, dtype=np.int8),
            "isolation_lower_mz": np.array(isolation_lower_mz_list, dtype=np.float64),
            "isolation_upper_mz": np.array(isolation_upper_mz_list, dtype=np.float64),
            "nce": np.array(ce_list, dtype=np.float32),
        }


class ThermoRawData:
    """
    Standalone Thermo RAW data reader class that provides RAW data reading
    functionality using Thermo Fisher DLLs directly.
    """

    # Column data types mapping
    column_dtypes: ClassVar[dict[str, Any]] = {
        "rt": np.float64,
        "ms_level": np.int8,
        "polarity": "U8",
        "precursor_mz": np.float64,
        "isolation_lower_mz": np.float64,
        "isolation_upper_mz": np.float64,
        "precursor_charge": np.int8,
        "nce": np.float32,
        "injection_time": np.float32,
        "activation": "U",
    }

    def __init__(self, centroided: bool = True) -> None:
        """
        Initialize ThermoRawData reader.

        Parameters
        ----------
        centroided : bool, optional
            If peaks will be centroided after loading, by default True.
            Note: Centroiding is currently disabled due to implementation limitations.
        """
        # Initialize dataframes
        self.spectrum_df: pd.DataFrame = pd.DataFrame()
        self.peak_df: pd.DataFrame = pd.DataFrame()

        # File and instrument information
        self._raw_file_path = ""
        self.creation_time = ""
        self.type = "thermo"
        self.instrument = "thermo"

        # Processing parameters
        self.centroided = centroided
        self.centroid_ppm = 20.0
        self.ignore_empty_scans = True
        self.keep_k_peaks_per_spec = 2000

        # Disable centroiding for now
        if self.centroided:
            self.centroided = False
            warnings.warn(
                "Centroiding for Thermo data is not well implemented yet. Data will be processed in profile mode.",
                UserWarning,
                stacklevel=2,
            )

    @property
    def raw_file_path(self) -> str:
        """Get the raw file path."""
        return self._raw_file_path

    @raw_file_path.setter
    def raw_file_path(self, value: str):
        """Set the raw file path."""
        self._raw_file_path = value

    def import_raw(self, raw_file_path: str) -> None:
        """
        Import raw data from a RAW file.

        Parameters
        ----------
        raw_file_path : str
            Path to the RAW file
        """
        self.raw_file_path = raw_file_path
        data_dict = self._import(raw_file_path)
        self._set_dataframes(data_dict)

    def _import(self, raw_file_path: str) -> dict[str, Any]:
        """
        Import data from a Thermo RAW file.

        Parameters
        ----------
        raw_file_path : str
            Absolute or relative path of the Thermo RAW file.

        Returns
        -------
        dict
            Dictionary containing spectrum information and peak data.
        """
        with ThermoRawFileReader(raw_file_path) as raw_reader:
            data_dict = raw_reader.load_all_scans(
                centroid=self.centroided,
                centroid_ppm=self.centroid_ppm,
                ignore_empty_scans=self.ignore_empty_scans,
                keep_k_peaks=self.keep_k_peaks_per_spec,
            )

            # Try to get file creation time
            try:
                creation_info = raw_reader._raw_file.GetCreationDate()
                self.creation_time = creation_info.ToString("O") if creation_info else ""
            except Exception:
                self.creation_time = ""

        return data_dict

    def _set_dataframes(self, raw_data: dict[str, Any]) -> None:
        """
        Set the spectrum and peak dataframes from raw data dictionary.

        Parameters
        ----------
        raw_data : dict
            Dictionary containing the raw spectral data with keys like 'rt', 'peak_mz', etc.
        """
        num_spectra = len(raw_data["rt"])

        # Create spectrum dataframe
        self.create_spectrum_df(num_spectra)

        # Create peak dataframe with indexed arrays
        self.set_peak_df_by_indexed_array(
            raw_data["peak_mz"],
            raw_data["peak_intensity"],
            raw_data["peak_indices"][:-1],  # start indices
            raw_data["peak_indices"][1:],  # end indices
        )

        # Add spectrum-level data to spectrum dataframe
        for column_name, values in raw_data.items():
            if column_name in self.column_dtypes and column_name != "peak_mz" and column_name != "peak_intensity":
                dtype = self.column_dtypes[column_name]
                if dtype == "O":
                    self.spectrum_df[column_name] = list(values)
                else:
                    self.spectrum_df[column_name] = np.array(values, dtype=dtype)

    def create_spectrum_df(self, spectrum_num: int) -> None:
        """
        Create an empty spectrum dataframe from the number of spectra.

        Parameters
        ----------
        spectrum_num : int
            The number of spectra.
        """
        self.spectrum_df = pd.DataFrame(index=np.arange(spectrum_num, dtype=np.int64))
        self.spectrum_df["spec_idx"] = self.spectrum_df.index.values

    def set_peak_df_by_indexed_array(
        self,
        mz_array: np.ndarray,
        intensity_array: np.ndarray,
        peak_start_indices: np.ndarray,
        peak_stop_indices: np.ndarray,
    ) -> None:
        """
        Set peak dataframe using indexed arrays.

        Parameters
        ----------
        mz_array : np.ndarray
            Array of m/z values
        intensity_array : np.ndarray
            Array of intensity values
        peak_start_indices : np.ndarray
            Array of start indices for each spectrum
        peak_stop_indices : np.ndarray
            Array of stop indices for each spectrum
        """
        self.peak_df = pd.DataFrame()
        self.peak_df["mz"] = mz_array.astype(np.float64)
        self.peak_df["intensity"] = intensity_array.astype(np.float32)

        # Set peak start and stop indices in spectrum df
        self.spectrum_df["peak_start_idx"] = peak_start_indices
        self.spectrum_df["peak_stop_idx"] = peak_stop_indices

    def get_peaks(self, spec_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Get peaks for a specific spectrum.

        Parameters
        ----------
        spec_idx : int
            Spectrum index

        Returns
        -------
        tuple
            (mz_array, intensity_array)
        """
        start, end = self.spectrum_df.iloc[spec_idx][["peak_start_idx", "peak_stop_idx"]].values
        return (
            self.peak_df.mz.values[start:end],
            self.peak_df.intensity.values[start:end],
        )

    def __repr__(self) -> str:
        return f"ThermoRawData(file_path='{self.raw_file_path}', spectra={len(self.spectrum_df)})"


# Convenience functions to maintain compatibility with existing code
def load_raw_file(filename: str, **kwargs) -> ThermoRawData:
    """
    Load a RAW file and return a ThermoRawData object.

    Parameters
    ----------
    filename : str
        Path to the RAW file
    **kwargs
        Additional arguments to pass to ThermoRawData constructor

    Returns
    -------
    ThermoRawData
        Loaded RAW data object
    """
    raw_data = ThermoRawData(**kwargs)
    raw_data.import_raw(filename)
    return raw_data


def get_file_info(filename: str) -> dict[str, Any]:
    """
    Get basic information about a RAW file.

    Parameters
    ----------
    filename : str
        Path to the RAW file

    Returns
    -------
    dict
        Dictionary with file information including scan count, scan range, etc.
    """
    with ThermoRawFileReader(filename) as reader:
        return {
            "first_scan": reader.first_scan,
            "last_scan": reader.last_scan,
            "num_scans": reader.num_scans,
            "scan_range": f"{reader.first_scan}-{reader.last_scan}",
        }


def main() -> None:
    """
    Main function for testing and demonstrating the module functionality.

    This function provides usage examples and tests basic module functionality
    when the script is run directly.
    """
    print("Standalone Thermo RAW Reader")
    print("=" * 40)

    # Display usage example
    print("\nUsage Example:")
    print("-" * 20)
    example_code = """
from thermo import ThermoRawData, load_raw_file

# Method 1: Create reader instance
raw_data = ThermoRawData(centroided=False)
raw_data.import_raw("path/to/file.raw")

# Method 2: Use convenience function  
raw_data = load_raw_file("path/to/file.raw")

# Access data
print(f"Spectra: {len(raw_data.spectrum_df)}")
print(f"Peaks: {len(raw_data.peak_df)}")

# Get peaks for first spectrum
mz, intensity = raw_data.get_peaks(0)

# Check available polarities
polarities = raw_data.spectrum_df['polarity'].unique()
print(f"Polarities: {polarities}")
"""
    print(example_code)

    # Test module functionality
    print("\nModule Status:")
    print("-" * 20)

    try:
        # Test class instantiation
        test_data = ThermoRawData()
        print("✓ ThermoRawData instantiated successfully")

        # Check .NET support
        if HAS_DOTNET:
            print("✓ .NET support available")
            print("  • Thermo Fisher DLLs loaded")
            print("  • RAW file reading enabled")
        else:
            print("⚠ .NET support not available")
            print("  • Install pythonnet to enable RAW file reading")
            print("  • Ensure Thermo Fisher DLLs are in alpharaw ext directory")

    except Exception as e:
        print(f"✗ Error during module testing: {e}")


if __name__ == "__main__":
    main()
