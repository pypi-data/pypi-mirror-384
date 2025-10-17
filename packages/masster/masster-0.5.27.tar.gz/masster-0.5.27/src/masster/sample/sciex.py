"""
Standalone Sciex WIFF file reader module.

This module provides a standalone implementation of Sciex WIFF file reading
functionality that uses the Sciex DLLs directly.

Requirements:
- pythonnet (pip install pythonnet)
- Sciex DLLs must be available in the ext/sciex directory
- On Linux/macOS: mono runtime must be installed

The .NET imports (System, Clearcore2, WiffOps4Python) will only work when
pythonnet is properly installed and configured.
"""

import os
import site
import warnings

from typing import Any, ClassVar

import numpy as np
import pandas as pd


# Import centroiding functionality (simplified naive centroid implementation)
def naive_centroid(
    peak_mzs: np.ndarray,
    peak_intensities: np.ndarray,
    centroiding_ppm: float = 20.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simplified naive centroiding implementation.

    Parameters
    ----------
    peak_mzs : np.ndarray
        Array of m/z values
    peak_intensities : np.ndarray
        Array of intensity values
    centroiding_ppm : float, default 20.0
        PPM tolerance for combining peaks

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Centroided m/z and intensity arrays
    """
    if len(peak_mzs) == 0:
        return np.array([]), np.array([])

    # Simple centroiding: combine peaks within tolerance
    centroided_mzs = []
    centroided_intensities = []

    i = 0
    while i < len(peak_mzs):
        current_mz = peak_mzs[i]
        current_intensity = peak_intensities[i]

        # Look for nearby peaks within tolerance
        j = i + 1
        total_intensity = current_intensity
        weighted_mz_sum = current_mz * current_intensity

        while j < len(peak_mzs):
            tolerance = current_mz * centroiding_ppm * 1e-6
            if abs(peak_mzs[j] - current_mz) <= tolerance:
                total_intensity += peak_intensities[j]
                weighted_mz_sum += peak_mzs[j] * peak_intensities[j]
                j += 1
            else:
                break

        # Calculate centroided m/z and intensity
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

    import ctypes

    import System  # noqa: F401

    from System.Globalization import CultureInfo
    from System.Runtime.InteropServices import GCHandle
    from System.Runtime.InteropServices import GCHandleType
    from System.Threading import Thread

    de_fr = CultureInfo("fr-FR")
    other = CultureInfo("en-US")

    Thread.CurrentThread.CurrentCulture = other
    Thread.CurrentThread.CurrentUICulture = other

    # Find the alpharaw ext/sciex directory in site-packages
    ext_dir = None
    for site_dir in site.getsitepackages():
        potential_ext_dir = os.path.join(site_dir, "alpharaw", "ext", "sciex")
        if os.path.exists(potential_ext_dir):
            ext_dir = potential_ext_dir
            break

    if ext_dir is None:
        # Try alternative locations
        import alpharaw

        alpharaw_dir = os.path.dirname(alpharaw.__file__)
        ext_dir = os.path.join(alpharaw_dir, "ext", "sciex")

    if not os.path.exists(ext_dir):
        raise ImportError("Could not find alpharaw ext/sciex directory with DLLs")

    # Add Sciex DLL references
    clr.AddReference(
        os.path.join(ext_dir, "Clearcore2.Data.AnalystDataProvider.dll"),
    )
    clr.AddReference(os.path.join(ext_dir, "Clearcore2.Data.dll"))
    clr.AddReference(os.path.join(ext_dir, "WiffOps4Python.dll"))

    import Clearcore2  # noqa: F401
    import WiffOps4Python  # noqa: F401

    from Clearcore2.Data.AnalystDataProvider import AnalystDataProviderFactory
    from Clearcore2.Data.AnalystDataProvider import AnalystWiffDataProvider
    from WiffOps4Python import WiffOps as DotNetWiffOps

    HAS_DOTNET = True
except Exception as e:
    # allows to use the rest of the code without clr
    warnings.warn(
        f"Dotnet-based dependencies could not be loaded. Sciex support is disabled. Error: {e}",
        stacklevel=2,
    )
    HAS_DOTNET = False


def dot_net_array_to_np_array(src) -> np.ndarray:
    """
    Convert .NET array to NumPy array.

    Parameters
    ----------
    src : .NET array or None
        Source .NET array to convert

    Returns
    -------
    np.ndarray
        Converted NumPy array

    Notes
    -----
    Based on approach from:
    https://mail.python.org/pipermail/pythondotnet/2014-May/001527.html
    """
    if src is None:
        return np.array([], dtype=np.float64)
    src_hndl = GCHandle.Alloc(src, GCHandleType.Pinned)
    try:
        src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()
        buf_type = ctypes.c_double * len(src)
        cbuf = buf_type.from_address(src_ptr)
        dest = np.frombuffer(cbuf, dtype="float64").copy()  # type: ignore[call-overload]
    finally:
        if src_hndl.IsAllocated:
            src_hndl.Free()
        return dest  # noqa: B012


class SciexWiffFileReader:
    """
    Direct implementation of Sciex WIFF file reader using the Sciex DLLs.
    """

    def __init__(self, filename: str):
        if not HAS_DOTNET:
            raise ValueError(
                "Dotnet-based dependencies are required for reading Sciex files. "
                "Do you have pythonnet and/or mono installed? "
                "Please ensure pythonnet and Sciex DLLs are properly installed.",
            )

        self._wiffDataProvider = AnalystWiffDataProvider()
        self._wiff_file = AnalystDataProviderFactory.CreateBatch(
            filename,
            self._wiffDataProvider,
        )
        self.sample_names = self._wiff_file.GetSampleNames()

    def close(self) -> None:
        """Close the file and clean up resources."""
        self._wiffDataProvider.Close()

    def __enter__(self) -> "SciexWiffFileReader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def load_sample(
        self,
        sample_id: int,
        centroid: bool = True,
        centroid_ppm: float = 20.0,
        ignore_empty_scans: bool = True,
        keep_k_peaks: int = 2000,
    ) -> dict[str, Any]:
        """
        Load a sample from the WIFF file and extract spectral data.

        Parameters
        ----------
        sample_id : int
            ID of the sample to load
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
            Dictionary containing spectral data
        """
        if sample_id < 0 or sample_id >= len(self.sample_names):
            raise ValueError("Incorrect sample number.")

        self.wiffSample = self._wiff_file.GetSample(sample_id)
        self.msSample = self.wiffSample.MassSpectrometerSample

        _peak_indices: list[int] = []
        peak_mz_array_list: list[np.ndarray] = []
        peak_intensity_array_list: list[np.ndarray] = []
        rt_list: list[float] = []
        ms_level_list: list[int] = []
        polarity_list: list[str] = []
        precursor_mz_list: list[float] = []
        precursor_charge_list: list[int] = []
        ce_list: list[float] = []
        isolation_lower_mz_list: list[float] = []
        isolation_upper_mz_list: list[float] = []

        exp_list = [self.msSample.GetMSExperiment(i) for i in range(self.msSample.ExperimentCount)]

        for j in range(exp_list[0].Details.NumberOfScans):
            for i in range(self.msSample.ExperimentCount):
                exp = exp_list[i]
                mass_spectrum = exp.GetMassSpectrum(j)
                mass_spectrum_info = exp.GetMassSpectrumInfo(j)
                details = exp.Details
                ms_level = mass_spectrum_info.MSLevel

                if ms_level > 1 and not details.IsSwath and mass_spectrum.NumDataPoints <= 0 and ignore_empty_scans:
                    continue
                if exp.Details.Polarity == exp.Details.Polarity.Positive:
                    pol = "positive"
                elif exp.Details.Polarity == exp.Details.Polarity.Negative:
                    pol = "negative"
                else:
                    pol = ""
                polarity_list.append(pol)

                mz_array = dot_net_array_to_np_array(mass_spectrum.GetActualXValues())
                int_array = dot_net_array_to_np_array(
                    mass_spectrum.GetActualYValues(),
                ).astype(np.float32)

                if centroid:
                    (mz_array, int_array) = naive_centroid(
                        mz_array,
                        int_array,
                        centroiding_ppm=centroid_ppm,
                    )

                if len(mz_array) > keep_k_peaks:
                    idxes = np.argsort(int_array)[-keep_k_peaks:]
                    idxes = np.sort(idxes)
                    mz_array = mz_array[idxes]
                    int_array = int_array[idxes]

                peak_mz_array_list.append(mz_array)
                peak_intensity_array_list.append(int_array)

                _peak_indices.append(len(peak_mz_array_list[-1]))
                rt_list.append(exp.GetRTFromExperimentCycle(j))

                ms_level_list.append(ms_level)

                center_mz = -1.0
                isolation_window = 0.0

                if ms_level > 1:
                    if details.IsSwath and details.MassRangeInfo.Length > 0:
                        center_mz = DotNetWiffOps.get_center_mz(details)
                        isolation_window = DotNetWiffOps.get_isolation_window(details)
                    if isolation_window <= 0:
                        isolation_window = 3.0
                    if center_mz <= 0:
                        center_mz = mass_spectrum_info.ParentMZ
                    precursor_mz_list.append(center_mz)
                    precursor_charge_list.append(mass_spectrum_info.ParentChargeState)
                    ce_list.append(float(mass_spectrum_info.CollisionEnergy))
                    isolation_lower_mz_list.append(center_mz - isolation_window / 2)
                    isolation_upper_mz_list.append(center_mz + isolation_window / 2)
                else:
                    precursor_mz_list.append(-1.0)
                    precursor_charge_list.append(0)
                    ce_list.append(0.0)
                    isolation_lower_mz_list.append(-1.0)
                    isolation_upper_mz_list.append(-1.0)

        peak_indices = np.empty(len(rt_list) + 1, np.int64)
        peak_indices[0] = 0
        peak_indices[1:] = np.cumsum(_peak_indices)

        return {
            "peak_indices": peak_indices,
            "peak_mz": np.concatenate(peak_mz_array_list),
            "peak_intensity": np.concatenate(peak_intensity_array_list),
            "rt": np.array(rt_list, dtype=np.float64),
            "ms_level": np.array(ms_level_list, dtype=np.int8),
            "polarity": np.array(polarity_list, dtype="U8"),
            "precursor_mz": np.array(precursor_mz_list, dtype=np.float64),
            "precursor_charge": np.array(precursor_charge_list, dtype=np.int8),
            "isolation_lower_mz": np.array(isolation_lower_mz_list),
            "isolation_upper_mz": np.array(isolation_upper_mz_list),
            "nce": np.array(ce_list, dtype=np.float32),
        }


class SciexWiffData:
    """
    Standalone Sciex WIFF data reader class that provides WIFF data reading
    functionality using Sciex DLLs directly.
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
        Parameters
        ----------
        centroided : bool, optional
            If peaks will be centroided after loading, by default True.
        """
        self.spectrum_df: pd.DataFrame = pd.DataFrame()
        self.peak_df: pd.DataFrame = pd.DataFrame()
        self._raw_file_path = ""
        self.centroided = centroided
        self.creation_time = ""
        self.type = "sciex"
        self.instrument = "sciex"

        if self.centroided:
            self.centroided = False
            warnings.warn(
                "Centroiding for Sciex data is not well implemented yet",
                stacklevel=2,
            )

        self.centroid_ppm = 20.0
        self.ignore_empty_scans = True
        self.keep_k_peaks_per_spec = 2000
        self.sample_id = 0

    @property
    def raw_file_path(self) -> str:
        """Get the raw file path."""
        return self._raw_file_path

    @raw_file_path.setter
    def raw_file_path(self, value: str):
        """Set the raw file path."""
        self._raw_file_path = value

    def import_raw(self, wiff_file_path: str) -> None:
        """
        Import raw data from a WIFF file.

        Parameters
        ----------
        wiff_file_path : str
            Path to the WIFF file
        """
        self.raw_file_path = wiff_file_path
        data_dict = self._import(wiff_file_path)
        self._set_dataframes(data_dict)

    def _import(self, _wiff_file_path: str) -> dict[str, Any]:
        """
        Implementation of data import interface.

        Parameters
        ----------
        _wiff_file_path : str
            Absolute or relative path of the sciex wiff file.

        Returns
        -------
        dict
            Spectrum information dict.
        """
        wiff_reader = SciexWiffFileReader(_wiff_file_path)
        data_dict = wiff_reader.load_sample(
            self.sample_id,
            centroid=self.centroided,
            centroid_ppm=self.centroid_ppm,
            ignore_empty_scans=self.ignore_empty_scans,
            keep_k_peaks=self.keep_k_peaks_per_spec,
        )
        self.creation_time = wiff_reader.wiffSample.Details.AcquisitionDateTime.ToString("O")
        wiff_reader.close()
        return data_dict

    def _set_dataframes(self, raw_data: dict[str, Any]) -> None:
        """
        Set the spectrum and peak dataframes from raw data dictionary.

        Parameters
        ----------
        raw_data : dict
            Dictionary containing the raw spectral data
        """
        self.create_spectrum_df(len(raw_data["rt"]))
        self.set_peak_df_by_indexed_array(
            raw_data["peak_mz"],
            raw_data["peak_intensity"],
            raw_data["peak_indices"][:-1],
            raw_data["peak_indices"][1:],
        )

        for col, val in raw_data.items():
            if col in self.column_dtypes:
                if self.column_dtypes[col] == "O":
                    self.spectrum_df[col] = list(val)
                else:
                    self.spectrum_df[col] = np.array(val, dtype=self.column_dtypes[col])

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
        return f"SciexWiffData(file_path='{self.raw_file_path}', spectra={len(self.spectrum_df)})"


# Convenience functions to maintain compatibility with existing code
def load_wiff_file(filename: str, **kwargs) -> SciexWiffData:
    """
    Load a WIFF file and return a SciexWiffData object.

    Parameters
    ----------
    filename : str
        Path to the WIFF file
    **kwargs
        Additional arguments to pass to SciexWiffData constructor

    Returns
    -------
    SciexWiffData
        Loaded WIFF data object
    """
    wiff_data = SciexWiffData(**kwargs)
    wiff_data.import_raw(filename)
    return wiff_data


def get_sample_names(filename: str) -> list[str]:
    """
    Get the sample names from a WIFF file.

    Parameters
    ----------
    filename : str
        Path to the WIFF file

    Returns
    -------
    list[str]
        List of sample names
    """
    with SciexWiffFileReader(filename) as reader:
        return list(reader.sample_names)


# Example usage and testing
if __name__ == "__main__":
    print("Standalone Sciex WIFF reader implementation")
    print("Usage example:")
    print("""
    from sciex import SciexWiffData, load_wiff_file

    # Create reader instance
    wiff_data = SciexWiffData(centroided=False)
    wiff_data.import_raw("path/to/file.wiff")

    # Or use convenience function
    wiff_data = load_wiff_file("path/to/file.wiff")

    # Access spectrum and peak data
    print(f"Number of spectra: {len(wiff_data.spectrum_df)}")
    print(f"Number of peaks: {len(wiff_data.peak_df)}")

    # Get peaks for first spectrum
    mz, intensity = wiff_data.get_peaks(0)
    """)

    # Test that the module can be imported and classes instantiated
    try:
        test_data = SciexWiffData()
        print(f"✓ SciexWiffData class instantiated successfully: {test_data}")
        print(f"✓ Has dotnet support: {HAS_DOTNET}")

        # Test with example WIFF file if available
        example_file = os.path.join(
            os.path.dirname(__file__),
            "data",
            "examples",
            "2025_01_14_VW_7600_LpMx_DBS_CID_2min_TOP15_030msecMS1_005msecReac_CE35_DBS-ON_3.wiff",
        )

        if os.path.exists(example_file):
            print(f"\n✓ Found example WIFF file: {example_file}")
            print("Testing WIFF file loading...")

            # Test loading the example file
            wiff_data = load_wiff_file(example_file)
            print("✓ Successfully loaded WIFF file")
            print(f"  - Number of spectra: {len(wiff_data.spectrum_df)}")
            print(f"  - Number of peaks: {len(wiff_data.peak_df)}")
            print(f"  - Creation time: {wiff_data.creation_time}")
            print(f"  - File type: {wiff_data.type}")
            print(f"  - Instrument: {wiff_data.instrument}")

            # Test getting peaks from first spectrum
            if len(wiff_data.spectrum_df) > 0:
                mz, intensity = wiff_data.get_peaks(0)
                print(f"  - First spectrum has {len(mz)} peaks")
                if len(mz) > 0:
                    print(f"  - m/z range: {mz.min():.2f} - {mz.max():.2f}")
                    print(
                        f"  - Intensity range: {intensity.min():.0f} - {intensity.max():.0f}",
                    )
        else:
            print(f"\n⚠ Example WIFF file not found at: {example_file}")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback

        traceback.print_exc()
