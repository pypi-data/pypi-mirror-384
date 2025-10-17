"""
_plots.py

This module provides visualization functions for mass spectrometry data analysis.
It contains plotting utilities for extracted ion chromatograms (EICs), 2D data maps,
feature visualizations, and interactive dashboards using modern visualization libraries.

Key Features:
- **Extracted Ion Chromatograms (EICs)**: Interactive chromatographic plotting with feature annotations.
- **2D Data Visualization**: Mass spectrometry data visualization with datashader for large datasets.
- **Feature Plotting**: Visualize detected features with retention time and m/z information.
- **Interactive Dashboards**: Create interactive panels for data exploration and analysis.
- **Multi-Sample Plotting**: Comparative visualizations across multiple samples.
- **Export Capabilities**: Save plots in various formats (HTML, PNG, SVG).

Dependencies:
- `holoviews`: For high-level data visualization and interactive plots.
- `datashader`: For rendering large datasets efficiently.
- `panel`: For creating interactive web applications and dashboards.
- `bokeh`: For low-level plotting control and customization.
- `polars` and `pandas`: For data manipulation and processing.
- `numpy`: For numerical computations.

Functions:
- `plot_chrom()`: Generate chromatograms with feature overlays.
- `plot_2d()`: Create 2D mass spectrometry data visualizations.
- `plot_features()`: Visualize detected features in retention time vs m/z space.
- Various utility functions for plot styling and configuration.

Supported Plot Types:
- Chromatograms
- Total Ion Chromatograms (TIC)
- Base Peak Chromatograms (BPC)
- 2D intensity maps (RT vs m/z)
- Feature scatter plots
- Interactive dashboards

See Also:
- `parameters._plot_parameters`: For plot-specific parameter configuration.
- `single.py`: For applying plotting methods to ddafile objects.
- `study.py`: For study-level visualization functions.

"""

import os
import warnings

import datashader as ds
import holoviews as hv
import holoviews.operation.datashader as hd
import numpy as np
import pandas as pd
import panel
import polars as pl

from bokeh.models import HoverTool
from holoviews import dim
from holoviews.plotting.util import process_cmap

from cmap import Colormap

# Parameters removed - using hardcoded defaults
# hv.extension("bokeh")


def _process_cmap(cmap, fallback="viridis", logger=None):
    """
    Process colormap using the cmap package, similar to study's implementation.

    Parameters:
        cmap: Colormap specification (string name, cmap.Colormap object, or None)
        fallback: Fallback colormap name if cmap processing fails
        logger: Logger for warnings (optional)

    Returns:
        list: List of hex color strings for the colormap
    """
    # Handle None case
    if cmap is None:
        cmap = "viridis"
    elif cmap == "grey":
        cmap = "greys"

    # If cmap package is not available, fall back to process_cmap
    if Colormap is None:
        if logger:
            logger.warning("cmap package not available, using holoviews process_cmap")
        return process_cmap(cmap, provider="bokeh")

    try:
        # Handle colormap using cmap.Colormap
        if isinstance(cmap, str):
            colormap = Colormap(cmap)
            # Generate 256 colors and convert to hex
            import matplotlib.colors as mcolors

            colors = colormap(np.linspace(0, 1, 256))
            palette = [mcolors.rgb2hex(color) for color in colors]
        else:
            colormap = cmap
            # Try to use to_bokeh() method first
            try:
                palette = colormap.to_bokeh()
                # Ensure we got a color palette, not another mapper
                if not isinstance(palette, (list, tuple)):
                    # Fall back to generating colors manually
                    import matplotlib.colors as mcolors

                    colors = colormap(np.linspace(0, 1, 256))
                    palette = [mcolors.rgb2hex(color) for color in colors]
            except AttributeError:
                # Fall back to generating colors manually
                import matplotlib.colors as mcolors

                colors = colormap(np.linspace(0, 1, 256))
                palette = [mcolors.rgb2hex(color) for color in colors]

        return palette

    except (AttributeError, ValueError, TypeError) as e:
        # Fallback to process_cmap if cmap interpretation fails
        if logger:
            logger.warning(f"Could not interpret colormap '{cmap}': {e}, falling back to {fallback}")
        return process_cmap(fallback, provider="bokeh")


def _is_notebook_environment():
    """
    Detect if code is running in a notebook environment (Jupyter, JupyterLab, or Marimo).

    Returns:
        bool: True if running in a notebook, False otherwise
    """
    try:
        # Check for Jupyter/JupyterLab
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is not None:
            # Check if we're in a notebook context
            shell = ipython.__class__.__name__
            if shell in ["ZMQInteractiveShell", "Shell"]:  # Jupyter notebook/lab
                return True

        # Check for Marimo - multiple ways to detect it
        import sys

        # Check if marimo is in modules
        if "marimo" in sys.modules:
            return True

        # Check for marimo in the call stack or environment
        import inspect

        frame = inspect.currentframe()
        try:
            while frame:
                if frame.f_globals.get("__name__", "").startswith("marimo"):
                    return True
                frame = frame.f_back
        finally:
            del frame

        # Additional check for notebook environments via builtins
        if hasattr(__builtins__, "__IPYTHON__") or hasattr(__builtins__, "_ih"):
            return True

    except (ImportError, AttributeError):
        pass

    return False


def _display_plot(plot_object, layout=None):
    """
    Display a plot object in the appropriate way based on the environment.

    Args:
        plot_object: The plot object to display (holoviews overlay, etc.)
        layout: Optional panel layout object

    Returns:
        The plot object for inline display in notebooks, None for browser display
    """
    if _is_notebook_environment():
        # In notebook environments, return the plot object for inline display
        # For Jupyter notebooks, holoviews/panel objects display automatically when returned
        if layout is not None:
            # Return the layout object which will display inline in notebooks
            return layout
        else:
            # Return the plot object directly for holoviews automatic display
            return plot_object
    else:
        # Display in browser (original behavior)
        if layout is not None:
            layout.show()
        else:
            # Create a simple layout for browser display
            simple_layout = panel.Column(plot_object)
            simple_layout.show()
        return None


def _export_with_webdriver_manager(plot_obj, filename, format_type, logger=None):
    """
    Export plot to PNG or SVG using webdriver-manager for automatic driver management.

    Parameters:
        plot_obj: Bokeh plot object or holoviews object to export
        filename: Output filename
        format_type: Either "png" or "svg"
        logger: Logger for error reporting (optional)

    Returns:
        bool: True if export successful, False otherwise
    """
    try:
        # Convert holoviews to bokeh if needed
        if hasattr(plot_obj, "opts"):  # Likely a holoviews object
            import holoviews as hv

            bokeh_plot = hv.render(plot_obj)
        else:
            bokeh_plot = plot_obj

        # Try webdriver-manager export first
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            # Set up Chrome options for headless operation
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")

            # Use webdriver-manager to automatically get the correct ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Export with managed webdriver
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                # Filter out bokeh.io.export warnings specifically
                warnings.filterwarnings("ignore", module="bokeh.io.export")

                if format_type == "png":
                    from bokeh.io import export_png

                    export_png(bokeh_plot, filename=filename, webdriver=driver)
                elif format_type == "svg":
                    from bokeh.io import export_svg

                    export_svg(bokeh_plot, filename=filename, webdriver=driver)
                else:
                    raise ValueError(f"Unsupported format: {format_type}")

            driver.quit()
            return True

        except ImportError:
            if logger:
                logger.debug(f"webdriver-manager not available, using default {format_type.upper()} export")
            # Fall back to default export
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                # Filter out bokeh.io.export warnings specifically
                warnings.filterwarnings("ignore", module="bokeh.io.export")

                if format_type == "png":
                    from bokeh.io import export_png

                    export_png(bokeh_plot, filename=filename)
                elif format_type == "svg":
                    from bokeh.io import export_svg

                    export_svg(bokeh_plot, filename=filename)
            return True

        except Exception as e:
            if logger:
                logger.debug(
                    f"{format_type.upper()} export with webdriver-manager failed: {e}, using default {format_type.upper()} export"
                )
            try:
                # Final fallback to default export
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    # Filter out bokeh.io.export warnings specifically
                    warnings.filterwarnings("ignore", module="bokeh.io.export")

                    if format_type == "png":
                        from bokeh.io import export_png

                        export_png(bokeh_plot, filename=filename)
                    elif format_type == "svg":
                        from bokeh.io import export_svg

                        export_svg(bokeh_plot, filename=filename)
                return True
            except Exception as e2:
                if logger:
                    logger.error(f"{format_type.upper()} export failed: {e2}")
                return False

    except Exception as e:
        if logger:
            logger.error(f"Export preparation failed: {e}")
        return False


def _handle_sample_plot_output(self, plot_obj, filename=None, plot_type="bokeh"):
    """
    Helper function to handle consistent save/display behavior for sample plots.

    Parameters:
        plot_obj: The plot object (bokeh figure, holoviews layout, or panel object)
        filename: Optional filename to save the plot
        plot_type: Type of plot object ("bokeh", "panel", "holoviews")
    """
    if filename is not None:
        # Convert relative paths to absolute paths using sample folder as base
        import os

        if hasattr(self, "folder") and self.folder and not os.path.isabs(filename):
            filename = os.path.join(self.folder, filename)

        # Convert to absolute path for logging
        abs_filename = os.path.abspath(filename)

        if filename.endswith(".html"):
            if plot_type == "panel":
                plot_obj.save(filename, embed=True)  # type: ignore[attr-defined]
            elif plot_type == "holoviews":
                import panel

                panel.panel(plot_obj).save(filename, embed=True)  # type: ignore[attr-defined]
            elif plot_type == "bokeh":
                from bokeh.plotting import output_file
                from bokeh.io import save

                output_file(filename)
                save(plot_obj)
            self.logger.success(f"Plot saved to: {abs_filename}")
        elif filename.endswith(".png"):
            success = _export_with_webdriver_manager(plot_obj, filename, "png", self.logger)
            if success:
                self.logger.success(f"Plot saved to: {abs_filename}")
            else:
                # Fall back to HTML if PNG export fails completely
                html_filename = filename.replace(".png", ".html")
                abs_html_filename = os.path.abspath(html_filename)
                if plot_type == "panel":
                    plot_obj.save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "holoviews":
                    import panel

                    panel.panel(plot_obj).save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "bokeh":
                    from bokeh.plotting import output_file
                    from bokeh.io import save

                    output_file(html_filename)
                    save(plot_obj)
                self.logger.warning(f"PNG export not available, saved as HTML instead: {abs_html_filename}")
        elif filename.endswith(".svg"):
            success = _export_with_webdriver_manager(plot_obj, filename, "svg", self.logger)
            if success:
                self.logger.success(f"Plot saved to: {abs_filename}")
            else:
                # Fall back to HTML if SVG export fails completely
                html_filename = filename.replace(".svg", ".html")
                abs_html_filename = os.path.abspath(html_filename)
                if plot_type == "panel":
                    plot_obj.save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "holoviews":
                    import panel

                    panel.panel(plot_obj).save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "bokeh":
                    from bokeh.plotting import output_file
                    from bokeh.io import save

                    output_file(html_filename)
                    save(plot_obj)
                self.logger.warning(f"SVG export not available, saved as HTML instead: {abs_html_filename}")
        elif filename.endswith(".pdf"):
            # Try to save as PDF, fall back to HTML if not available
            try:
                if plot_type == "bokeh":
                    from bokeh.io.export import export_pdf

                    export_pdf(plot_obj, filename=filename)
                elif plot_type in ["panel", "holoviews"]:
                    import holoviews as hv

                    hv.save(plot_obj, filename, fmt="pdf")
                self.logger.success(f"Plot saved to: {abs_filename}")
            except ImportError:
                # Fall back to HTML if PDF export not available
                html_filename = filename.replace(".pdf", ".html")
                abs_html_filename = os.path.abspath(html_filename)
                if plot_type == "panel":
                    plot_obj.save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "holoviews":
                    import panel

                    panel.panel(plot_obj).save(html_filename, embed=True)  # type: ignore[attr-defined]
                elif plot_type == "bokeh":
                    from bokeh.plotting import output_file
                    from bokeh.io import save

                    output_file(html_filename)
                    save(plot_obj)
                self.logger.warning(f"PDF export not available, saved as HTML instead: {abs_html_filename}")
        else:
            # Default to HTML for unknown extensions
            if plot_type == "panel":
                plot_obj.save(filename, embed=True)  # type: ignore[attr-defined]
            elif plot_type == "holoviews":
                import panel

                panel.panel(plot_obj).save(filename, embed=True)  # type: ignore[attr-defined]
            elif plot_type == "bokeh":
                from bokeh.plotting import output_file
                from bokeh.io import save

                output_file(filename)
                save(plot_obj)
            self.logger.success(f"Plot saved to: {abs_filename}")
    else:
        # Show in notebook when no filename provided
        if plot_type == "panel":
            plot_obj.show()  # type: ignore[attr-defined]
        elif plot_type == "holoviews":
            import panel

            return panel.panel(plot_obj)
        elif plot_type == "bokeh":
            from bokeh.plotting import show

            show(plot_obj)


def plot_chrom(
    self,
    feature_uid=None,
    filename=None,
    rt_tol=10,
    rt_tol_factor_plot=1,
    mz_tol=0.0005,
    mz_tol_factor_plot=1,
    link_x=False,
):
    """
    Plot chromatograms for one or more features using MS1 data and feature metadata.

    This function filters MS1 data based on retention time (rt) and mass-to-charge ratio (mz) windows
    derived from feature information in `features_df`. It then generates interactive chromatogram plots using
    HoloViews, with feature retention time windows annotated. Plots can be displayed interactively or
    saved to a file.

    Parameters:
        feature_uid (int or list of int, optional):
            Feature identifier(s) for chromatogram generation. If None, chromatograms for all features in `features_df` are plotted.
        filename (str, optional):
            Output file path. If ending with `.html`, saves as interactive HTML; otherwise, saves as PNG.
            If not provided, displays the plot interactively.
        rt_tol (float, default=10):
            Retention time tolerance (in seconds) added to feature boundaries for MS1 data filtering.
        rt_tol_factor_plot (float, default=1):
            Retention time tolerance factor.
        mz_tol (float, default=0.0005):
            m/z tolerance added to feature boundaries for MS1 data filtering.
        mz_tol_factor_plot (float, default=1):
            m/z time tolerance factor.
        link_x (bool, default=True):
            If True, links the x-axes (retention time) across all chromatogram subplots.

    Returns:
        None

    Notes:
        - Uses `features_df` for feature metadata and `ms1_df` (Polars DataFrame) for MS1 data.
        - Aggregates MS1 intensities by retention time.
        - Utilizes HoloViews for visualization and Panel for layout/display.
    """
    # plots the chromatogram for a given feature id
    # If rt or mz are not provided, they are extracted from features_df using the supplied feature id (feature_uid)

    feature_uids = feature_uid
    # if feature_uids is None, plot all features
    if feature_uids is None:
        feats = self.features_df.clone()
    else:
        if isinstance(feature_uids, int):
            feature_uids = [feature_uids]
        # select only the features with feature_uid in feature_uids
        feats = self.features_df[self.features_df["feature_uid"].is_in(feature_uids)].clone()

    # make sure feature_uid is a list of integers

    chrom_plots = []
    feature_uids = feats["feature_uid"].values.tolist()
    mz_tol_plot = mz_tol * mz_tol_factor_plot
    rt_tol_plot = rt_tol * rt_tol_factor_plot
    # iterate over the list of feature_uid
    for feature_uid in feature_uids:
        # Retrieve the feature info
        feature_row = feats[feats["feature_uid"] == feature_uid]
        # rt = feature_row["rt"].values[0]
        rt_start = feature_row["rt_start"].values[0]
        rt_end = feature_row["rt_end"].values[0]
        mz = feature_row["mz"].values[0]
        mz_start = feature_row["mz_start"].values[0]
        mz_end = feature_row["mz_end"].values[0]

        # filter self.ms1_df with rt_start, rt_end, mz_start, mz_end
        chrom_df = self.ms1_df.filter(
            pl.col("rt") >= rt_start - rt_tol_plot,
            pl.col("rt") <= rt_end + rt_tol_plot,
        )
        chrom_df = chrom_df.filter(
            pl.col("mz") >= mz_start - mz_tol_plot,
            pl.col("mz") <= mz_end + mz_tol_plot,
        )

        if chrom_df.is_empty():
            print("No MS1 data found in the specified window.")
            continue

        # convert to pandas DataFrame
        chrom_df = chrom_df.to_pandas()
        # aggregate all points with the same rt using the sum of inty
        chrom_df = chrom_df.groupby("rt").agg({"inty": "sum"}).reset_index()
        yname = f"inty_{feature_uid}"
        chrom_df.rename(columns={"inty": yname}, inplace=True)

        # Plot the chromatogram using bokeh and ensure axes are independent by setting axiswise=True
        chrom = hv.Curve(chrom_df, kdims=["rt"], vdims=[yname]).opts(
            title=f"Chromatogram for feature {feature_uid}, mz = {mz:.4f}",
            xlabel="Retention time (s)",
            ylabel="Intensity",
            width=1000,
            tools=["hover"],
            height=250,
            axiswise=True,
            color="black",
        )

        # Add vertical lines at the start and end of the retention time
        chrom = chrom * hv.VLine(rt_start).opts(
            color="blue",
            line_width=1,
            line_dash="dashed",
            axiswise=True,
        )
        chrom = chrom * hv.VLine(rt_end).opts(
            color="blue",
            line_width=1,
            line_dash="dashed",
            axiswise=True,
        )

        # Append the subplot without linking axes
        chrom_plots.append(chrom)
    if link_x:
        # Create a layout with shared x-axis for all chromatogram plots
        layout = hv.Layout(chrom_plots).opts(shared_axes=True)
    else:
        layout = hv.Layout(chrom_plots).opts(shared_axes=False)

    layout = layout.cols(1)
    layout = panel.Column(layout)

    # Use consistent save/display behavior
    self._handle_sample_plot_output(layout, filename, "panel")


def _create_raster_plot(
    sample,
    mz_range=None,
    rt_range=None,
    raster_cmap="greys",
    raster_log=True,
    raster_min=1,
    raster_dynamic=True,
    raster_threshold=0.8,
    raster_max_px=8,
    width=750,
    height=600,
    filename=None,
):
    """Create the raster plot layer from MS1 data."""
    # Process colormap using the cmap package with proper error handling
    raster_cmap_processed = _process_cmap(
        raster_cmap if raster_cmap is not None else "greys", fallback="greys", logger=sample.logger
    )

    # get columns rt, mz, inty from sample.ms1_df, It's polars DataFrame
    spectradf = sample.ms1_df.to_pandas()

    # remove any inty<raster_min
    spectradf = spectradf[spectradf["inty"] >= raster_min]
    # keep only rt, mz, and inty
    spectradf = spectradf[["rt", "mz", "inty"]]
    if mz_range is not None:
        spectradf = spectradf[(spectradf["mz"] >= mz_range[0]) & (spectradf["mz"] <= mz_range[1])]
    if rt_range is not None:
        spectradf = spectradf[(spectradf["rt"] >= rt_range[0]) & (spectradf["rt"] <= rt_range[1])]

    maxrt = spectradf["rt"].max()
    minrt = spectradf["rt"].min()
    maxmz = spectradf["mz"].max()
    minmz = spectradf["mz"].min()

    def new_bounds_hook(plot, elem):
        x_range = plot.state.x_range
        y_range = plot.state.y_range
        x_range.bounds = minrt, maxrt
        y_range.bounds = minmz, maxmz

    points = hv.Points(
        spectradf,
        kdims=["rt", "mz"],
        vdims=["inty"],
        label="MS1 survey scans",
    ).opts(
        fontsize={"title": 16, "labels": 14, "xticks": 6, "yticks": 12},
        color=np.log(dim("inty")),
        colorbar=True,
        cmap="Magma",
        tools=["hover"],
    )

    if filename is not None:
        dyn = False
        if not filename.endswith(".html"):
            raster_dynamic = False

    dyn = raster_dynamic
    raster = hd.rasterize(
        points,
        aggregator=ds.max("inty"),
        interpolation="bilinear",
        dynamic=dyn,
    ).opts(
        active_tools=["box_zoom"],
        cmap=raster_cmap_processed,
        tools=["hover"],
        hooks=[new_bounds_hook],
        width=width,
        height=height,
        cnorm="log" if raster_log else "linear",
        xlabel="Retention time (s)",
        ylabel="m/z",
        colorbar=True,
        colorbar_position="right",
        axiswise=True,
    )
    raster = hd.dynspread(
        raster,
        threshold=raster_threshold,
        how="add",
        shape="square",
        max_px=raster_max_px,
    )

    return raster


def _load_and_merge_oracle_data(sample, oracle_folder, link_by_feature_uid, min_id_level, max_id_level, min_ms_level):
    """Load oracle data and merge with features."""
    if sample.features_df is None:
        sample.logger.error("Cannot plot 2D oracle: features_df is not available")
        return None

    feats = sample.features_df.clone()
    sample.logger.debug(f"Features data shape: {len(feats)} rows")

    # Convert to pandas for oracle operations that require pandas functionality
    if hasattr(feats, "to_pandas"):
        feats = feats.to_pandas()

    # check if annotationfile is not None
    if oracle_folder is None:
        sample.logger.info("No oracle folder provided, plotting features only")
        return None

    # try to read the annotationfile as a csv file and add it to feats
    oracle_file_path = os.path.join(oracle_folder, "diag", "summary_by_feature.csv")
    sample.logger.debug(f"Loading oracle data from: {oracle_file_path}")
    try:
        oracle_data = pd.read_csv(oracle_file_path)
        sample.logger.info(f"Oracle data loaded successfully with {len(oracle_data)} rows")
    except Exception as e:
        sample.logger.error(f"Could not read {oracle_file_path}: {e}")
        return None

    if link_by_feature_uid:
        cols_to_keep = [
            "title",
            "scan_idx",
            "mslevel",
            "hits",
            "id_level",
            "id_label",
            "id_ion",
            "id_class",
            "id_evidence",
            "score",
            "score2",
        ]
        oracle_data = oracle_data[cols_to_keep]

        # extract feature_uid from title. It begins with "uid:XYZ,"
        sample.logger.debug("Extracting feature UIDs from oracle titles using pattern 'uid:(\\d+)'")
        oracle_data["feature_uid"] = oracle_data["title"].str.extract(r"uid:(\d+)")
        oracle_data["feature_uid"] = oracle_data["feature_uid"].astype(int)

        # sort by id_level, remove duplicate feature_uid, keep the first one
        sample.logger.debug("Sorting by ID level and removing duplicates")
        oracle_data = oracle_data.sort_values(by=["id_level"], ascending=False)
        oracle_data = oracle_data.drop_duplicates(subset=["feature_uid"], keep="first")
        sample.logger.debug(f"After deduplication: {len(oracle_data)} unique oracle annotations")
    else:
        cols_to_keep = [
            "precursor",
            "rt",
            "title",
            "scan_idx",
            "mslevel",
            "hits",
            "id_level",
            "id_label",
            "id_ion",
            "id_class",
            "id_evidence",
            "score",
            "score2",
        ]
        oracle_data = oracle_data[cols_to_keep]
        oracle_data["feature_uid"] = None

        # iterate over the rows and find the feature_uid in feats by looking at the closest rt and mz
        for i, row in oracle_data.iterrows():
            candidates = feats[
                (abs(feats["rt"] - row["rt"]) < 1) & (abs(feats["mz"] - row["precursor"]) < 0.005)
            ].copy()
            if len(candidates) > 0:
                # sort by delta rt
                candidates["delta_rt"] = abs(candidates["rt"] - row["rt"])
                candidates = candidates.sort_values(by=["delta_rt"])
                oracle_data.at[i, "feature_uid"] = candidates["feature_uid"].values[0]
        # remove precursor and rt columns
        oracle_data = oracle_data.drop(columns=["precursor", "rt"])

    # Merge features with oracle data
    sample.logger.debug(f"Merging {len(feats)} features with oracle data")
    feats = feats.merge(oracle_data, how="left", on="feature_uid")
    sample.logger.debug(f"After merge: {len(feats)} total features")

    # filter feats by id_level
    initial_count = len(feats)
    if min_id_level is not None:
        feats = feats[(feats["id_level"] >= min_id_level)]
        sample.logger.debug(f"After min_id_level filter ({min_id_level}): {len(feats)} features")
    if max_id_level is not None:
        feats = feats[(feats["id_level"] <= max_id_level)]
        sample.logger.debug(f"After max_id_level filter ({max_id_level}): {len(feats)} features")
    if min_ms_level is not None:
        feats = feats[(feats["mslevel"] >= min_ms_level)]
        sample.logger.debug(f"After min_ms_level filter ({min_ms_level}): {len(feats)} features")

    sample.logger.info(f"Feature filtering complete: {initial_count} → {len(feats)} features remaining")
    return feats


def _setup_color_mapping(sample, feats, colorby, cmap, legend_groups=None):
    """Set up categorical color mapping for features."""
    import matplotlib.colors as mcolors

    feats["color"] = "black"  # Default fallback color
    cvalues = None
    color_column = "color"  # Default to fixed color
    colors = []

    # Determine which column to use for categorical coloring
    if colorby in ["class", "hg", "id_class", "id_hg"]:
        categorical_column = "id_class"
        # replace nans with 'mix'
        feats[categorical_column] = feats[categorical_column].fillna("mix")
    elif colorby in ["ion", "id_ion"]:
        categorical_column = "id_ion"
        feats[categorical_column] = feats[categorical_column].fillna("mix")
    elif colorby in ["evidence", "id_evidence"]:
        categorical_column = "id_evidence"
        feats[categorical_column] = feats[categorical_column].fillna("mix")
    elif colorby in ["level", "id_level"]:
        categorical_column = "id_level"
        feats[categorical_column] = feats[categorical_column].fillna("mix")
    else:
        categorical_column = None

    if categorical_column is not None:
        # Use provided legend_groups or derive from data
        if legend_groups is not None:
            # Use all specified groups to ensure consistent legend/coloring
            cvalues = legend_groups[:]  # Copy the list
            # Ensure 'mix' is always present as the last group if not already included
            if "mix" not in cvalues:
                cvalues.append("mix")
            sample.logger.info(f"Using provided legend_groups for legend: {cvalues}")

            # Check which provided groups actually have data
            present_groups = feats[categorical_column].unique()
            missing_groups = [grp for grp in cvalues if grp not in present_groups]
            if missing_groups:
                sample.logger.warning(f"Provided legend_groups not found in data: {missing_groups}")
            sample.logger.info(f"Groups present in data: {sorted(present_groups)}")

            # Assign any points not in legend_groups to 'mix'
            feats.loc[~feats[categorical_column].isin(cvalues[:-1]), categorical_column] = "mix"
        else:
            # Original behavior: use only groups present in data
            cvalues = feats[categorical_column].unique()
            # sort alphabetically
            cvalues = sorted(cvalues)
            # flip the strings left to right
            fcvalues = [cvalues[i][::-1] for i in range(len(cvalues))]
            # sort in alphabetical order the flipped strings and return the index
            idx = np.argsort(fcvalues)
            # apply to cvalues
            cvalues = [cvalues[i] for i in idx]
            sample.logger.info(f"Using groups derived from data: {cvalues}")

        color_column = categorical_column  # Use categorical coloring

    # Process colormap for categorical data
    if cvalues is not None:
        num_colors = len(cvalues)

        # Use colormap for categorical data - use _process_cmap for proper handling
        try:
            colormap = Colormap(cmap)
            colors = []
            for i in range(num_colors):
                # Generate evenly spaced colors across the colormap
                t = i / (num_colors - 1) if num_colors > 1 else 0.5
                color = colormap(t)
                # Convert to hex - handle different color formats
                if hasattr(color, "__len__") and len(color) >= 3:
                    # It's an array-like color (RGB or RGBA)
                    colors.append(mcolors.to_hex(color[:3]))
                else:
                    # It's a single value, convert to RGB
                    colors.append(mcolors.to_hex([color, color, color]))
        except (AttributeError, ValueError, TypeError):
            # Fallback to using _process_cmap if direct Colormap fails
            cmap_palette = _process_cmap(cmap, fallback="viridis", logger=sample.logger)
            # Sample colors from the palette
            colors = []
            for i in range(num_colors):
                idx = int(i * (len(cmap_palette) - 1) / (num_colors - 1)) if num_colors > 1 else len(cmap_palette) // 2
                colors.append(cmap_palette[idx])

        # Create a mapping from class name to color to ensure consistent color assignment
        # Each class gets the same color based on its position in the cvalues list
        class_to_color = {class_name: colors[i] for i, class_name in enumerate(cvalues)}

        # assign color to each row based on colorby category
        feats["color"] = "black"
        for class_name, color in class_to_color.items():
            if colorby in ["class", "hg", "id_class", "id_hg"]:
                feats.loc[feats["id_class"] == class_name, "color"] = color
            elif colorby in ["ion", "id_ion"]:
                feats.loc[feats["id_ion"] == class_name, "color"] = color
            elif colorby in ["id_evidence", "ms2_evidence"]:
                feats.loc[feats["id_evidence"] == class_name, "color"] = color

    return cvalues, color_column, colors


def _create_feature_overlay(sample, raster, feats, cvalues, color_column, colors, markersize, title, legend):
    """Create feature overlay with identified and unidentified features."""
    # replace NaN with 0 in id_level
    feats["id_level"] = feats["id_level"].fillna(0)

    # Create unified visualization with all features in single layer
    # This avoids the multiple layer legend conflicts that cause dark colors and shared toggling
    sample.logger.debug("Creating unified feature visualization with categorical coloring")

    # Prepare categorical coloring for identified features only (id_level >= 1)
    identified_feats = (
        feats[feats["id_level"] >= 1].copy() if len(feats[feats["id_level"] >= 1]) > 0 else pd.DataFrame()
    )
    unidentified_feats = (
        feats[feats["id_level"] < 1].copy() if len(feats[feats["id_level"] < 1]) > 0 else pd.DataFrame()
    )

    overlay = raster

    # Single layer for identified features with categorical coloring
    if len(identified_feats) > 0 and cvalues is not None:
        # Create proper confidence-based marker styling
        identified_feats["marker_style"] = identified_feats["id_level"].apply(
            lambda x: "circle" if x >= 2 else "circle_cross"
        )
        identified_feats["fill_alpha"] = identified_feats["id_level"].apply(
            lambda x: 1.0 if x >= 2 else 0.3  # Full opacity for high conf, transparent for medium
        )

        oracle_hover_identified = HoverTool(
            tooltips=[
                ("rt", "@rt"),
                ("m/z", "@mz{0.0000}"),
                ("feature_uid", "@feature_uid"),
                ("id_level", "@id_level"),
                ("id_class", "@id_class"),
                ("id_label", "@id_label"),
                ("id_ion", "@id_ion"),
                ("id_evidence", "@id_evidence"),
                ("score", "@score"),
                ("score2", "@score2"),
            ],
        )

        # Create completely separate overlay elements for each category
        overlays_to_combine = [raster]  # Start with raster base

        for i, category in enumerate(cvalues):
            category_data = identified_feats[identified_feats[color_column] == category].copy()
            if len(category_data) > 0:
                # Create a completely separate Points element for this category
                category_points = hv.Points(
                    category_data,
                    kdims=["rt", "mz"],
                    vdims=[
                        "inty",
                        "feature_uid",
                        "id_level",
                        "id_class",
                        "id_label",
                        "id_ion",
                        "id_evidence",
                        "score",
                        "score2",
                        "fill_alpha",
                    ],
                    label=str(category),  # This becomes the legend label
                ).options(
                    color=colors[i],  # Use pre-computed hex color for this category
                    marker="circle",
                    size=markersize,
                    alpha="fill_alpha",
                    tools=[oracle_hover_identified],
                    show_legend=True,
                )
                overlays_to_combine.append(category_points)
            else:
                # Create empty Points element for categories with no data to ensure they appear in legend
                empty_data = pd.DataFrame(
                    columns=[
                        "rt",
                        "mz",
                        "inty",
                        "feature_uid",
                        "id_level",
                        "id_class",
                        "id_label",
                        "id_ion",
                        "id_evidence",
                        "score",
                        "score2",
                        "fill_alpha",
                    ]
                )
                category_points = hv.Points(
                    empty_data,
                    kdims=["rt", "mz"],
                    vdims=[
                        "inty",
                        "feature_uid",
                        "id_level",
                        "id_class",
                        "id_label",
                        "id_ion",
                        "id_evidence",
                        "score",
                        "score2",
                        "fill_alpha",
                    ],
                    label=str(category),  # This becomes the legend label
                ).options(
                    color=colors[i],  # Use pre-computed hex color for this category
                    marker="circle",
                    size=markersize,
                    alpha=1.0,
                    tools=[oracle_hover_identified],
                    show_legend=True,
                )
                overlays_to_combine.append(category_points)

        # Combine all overlays
        overlay = overlays_to_combine[0]  # Start with raster
        for layer in overlays_to_combine[1:]:
            overlay = overlay * layer

    else:
        # No categorical data - just set overlay to raster
        overlay = raster

    # Separate layer for unidentified features (always black crosses)
    if len(unidentified_feats) > 0:
        oracle_hover_no_id = HoverTool(
            tooltips=[
                ("rt", "@rt"),
                ("m/z", "@mz{0.0000}"),
                ("feature_uid", "@feature_uid"),
                ("id_level", "@id_level"),
            ],
        )

        feature_points_no_id = hv.Points(
            unidentified_feats,
            kdims=["rt", "mz"],
            vdims=["inty", "feature_uid", "id_level"],
        ).options(
            color="black",
            marker="x",
            size=markersize,
            alpha=1.0,
            tools=[oracle_hover_no_id],
            show_legend=False,
        )

        overlay = overlay * feature_points_no_id

    if title is not None:
        sample.logger.debug(f"Setting plot title: {title}")
        overlay = overlay.opts(title=title)

    # Configure legend if requested and categorical coloring is available
    if legend is not None and cvalues is not None and len(cvalues) > 1:
        sample.logger.debug(
            f"Configuring integrated legend at '{legend}' position with {len(cvalues)} categories: {cvalues}"
        )

        # Map legend position parameter to HoloViews legend position
        legend_position_map = {
            "top_right": "top_right",
            "top_left": "top_left",
            "bottom_right": "bottom_right",
            "bottom_left": "bottom_left",
            "right": "right",
            "left": "left",
            "top": "top",
            "bottom": "bottom",
        }

        hv_legend_pos = legend_position_map.get(legend, "bottom_right")

        # Apply legend configuration to the overlay
        overlay = overlay.opts(legend_position=hv_legend_pos, legend_opts={"title": "", "padding": 2, "spacing": 2})

        sample.logger.debug(f"Applied integrated legend at position '{hv_legend_pos}'")
    elif legend is None:
        # Explicitly hide legend when legend=None
        overlay = overlay.opts(show_legend=False)
        sample.logger.debug("Legend hidden (legend=None)")

    return overlay


def _handle_output(sample, overlay, filename):
    """Handle plot export or display."""
    if filename is not None:
        # if filename includes .html, save the layout to an HTML file
        if filename.endswith(".html"):
            # For HoloViews overlay, we need to convert to Panel for saving
            panel.Column(overlay).save(filename, embed=True)
        elif filename.endswith(".svg"):
            success = _export_with_webdriver_manager(overlay, filename, "svg", sample.logger)
            if success:
                sample.logger.success(f"SVG exported: {os.path.abspath(filename)}")
            else:
                sample.logger.warning(f"SVG export failed: {os.path.abspath(filename)}")
        elif filename.endswith(".png"):
            success = _export_with_webdriver_manager(overlay, filename, "png", sample.logger)
            if success:
                sample.logger.success(f"PNG exported: {os.path.abspath(filename)}")
            else:
                sample.logger.warning(f"PNG export failed: {os.path.abspath(filename)}")
        else:
            # Default to PNG for any other format
            png_filename = filename + ".png" if not filename.endswith((".png", ".svg", ".html")) else filename
            success = _export_with_webdriver_manager(overlay, png_filename, "png", sample.logger)
            if success:
                sample.logger.success(f"PNG exported: {os.path.abspath(png_filename)}")
            else:
                sample.logger.warning(f"PNG export failed: {os.path.abspath(png_filename)}")
    else:
        # Create a Panel layout for consistent alignment with plot_2d()
        layout = panel.Column(overlay)
        # Return the Panel layout (consistent with plot_2d behavior)
        return layout


def plot_2d(
    self,
    filename=None,
    show_features=True,
    show_only_features_with_ms2=False,
    show_isotopes=False,
    show_ms2=False,
    show_in_browser=False,
    title=None,
    cmap="iridescent",
    marker="circle",
    markersize=5,
    size="static",
    raster_log=True,
    raster_min=1,
    raster_dynamic=True,
    raster_max_px=8,
    raster_threshold=0.8,
    height=600,
    width=750,
    mz_range=None,
    rt_range=None,
    legend=None,
    colorby=None,
):
    """
    Plot a two-dimensional visualization of MS1 survey scan data with optional overlays
    of feature and MS2 scan information.
    This method creates a plot from the internal MS1 data loaded into self.ms1_df
    and optionally overlays various feature and MS2 information depending on the provided
    parameters. The visualization is built using HoloViews and Holoviews dynamic rasterization,
    together with Panel for layout and exporting.
    Parameters:
        filename (str, optional):
            Path to save the plot. If provided and ends with ".html", the plot is saved as an
            interactive HTML file; otherwise, it is saved as a PNG image.
        show_features (bool, default True):
            Whether to overlay detected features on the plot.
        show_only_features_with_ms2 (bool, default False):
            If True, only display features that have associated MS2 scans. When False,
            features without MS2 data are also shown.
        show_isotopes (bool, default False):
            Whether to overlay isotope information on top of the features.
        show_ms2 (bool, default False):
            Whether to overlay MS2 scan information on the plot.
        title (str, optional):
            Title of the plot.
        cmap (str, optional):
            Colormap to use for the background rasterized data. Defaults to "iridescent_r" unless
            modified (e.g., if set to "grey", it is changed to "Greys256").
        marker (str, default 'circle'):
            Marker type to use for feature and MS2 points.
        markersize (int, default 10):
            Base size of the markers used for plotting points.
        size (str, default 'dynamic'):
            Controls marker sizing behavior. Options: 'dynamic', 'static', or 'slider'.
            - 'dynamic': Uses coordinate-based sizing that scales with zoom level (markers get larger when zooming in)
            - 'static': Uses screen-based sizing that remains constant regardless of zoom level
            - 'slider': Provides an interactive slider to dynamically adjust marker size
        raster_log (bool, default True):
            Use logarithmic scaling for raster intensity (True) or linear scaling (False).
        raster_min (float, default 1):
            Minimum intensity threshold for raster data filtering.
        raster_dynamic (bool, default True):
            Whether to use dynamic rasterization for the background point cloud.
        raster_max_px (int, default 8):
            Maximum pixel size for dynamic rasterization when using dynspread.
        raster_threshold (float, default 0.8):
            Threshold used for the dynspread process in dynamic rasterization.
        legend (str, optional):
            Legend position for categorical feature coloring ("top_right", "bottom_left", etc.) or None.
            Only applies when colorby is not None and contains categorical data.
        colorby (str, optional):
            Feature property to use for coloring. If None (default), uses current green/red scheme
            for features with/without MS2 data. If specified and contains categorical data, applies
            categorical coloring with legend support (similar to plot_2d_oracle).
    Behavior:
        - Checks for a loaded mzML file by verifying that self.file_obj is not None.
        - Converts internal MS1 data (a Polars DataFrame) to a Pandas DataFrame and filters out low-intensity
          points (inty < 1).
        - Sets up the plot bounds for retention time (rt) and mass-to-charge ratio (mz) using a hook function.
        - Renders the MS1 data as a background rasterized image with a logarithmic intensity normalization.
        - Conditionally overlays feature points (with and without MS2 information), isotopes (if requested),
          and MS2 scan points based on internal DataFrame data.
        - Depending on the filename parameter, either displays the plot interactively using Panel or
          saves it as an HTML or PNG file.
    Returns:
        None
    Side Effects:
        - May print a warning if no mzML file is loaded.
        - Either shows the plot interactively or writes the output to a file.
    """

    if self.ms1_df is None:
        self.logger.error("No MS1 data available.")
        return

    # Process colormap using the cmap package
    cmap_palette = _process_cmap(cmap, fallback="iridescent", logger=self.logger)

    # get columns rt, mz, inty from self.ms1_df, It's polars DataFrame
    spectradf = self.ms1_df.select(["rt", "mz", "inty"])
    # remove any inty<raster_min
    spectradf = spectradf.filter(pl.col("inty") >= raster_min)
    # keep only rt, mz, and inty
    spectradf = spectradf.select(["rt", "mz", "inty"])
    if mz_range is not None:
        spectradf = spectradf.filter((pl.col("mz") >= mz_range[0]) & (pl.col("mz") <= mz_range[1]))
    if rt_range is not None:
        spectradf = spectradf.filter((pl.col("rt") >= rt_range[0]) & (pl.col("rt") <= rt_range[1]))
    maxrt = spectradf["rt"].max()
    minrt = spectradf["rt"].min()
    maxmz = spectradf["mz"].max()
    minmz = spectradf["mz"].min()

    def new_bounds_hook(plot, elem):
        x_range = plot.state.x_range
        y_range = plot.state.y_range
        x_range.bounds = minrt, maxrt
        y_range.bounds = minmz, maxmz

    points = hv.Points(
        spectradf,
        kdims=["rt", "mz"],
        vdims=["inty"],
        label="MS1 survey scans",
    ).opts(
        fontsize={"title": 16, "labels": 14, "xticks": 6, "yticks": 12},
        color=np.log(dim("inty")),
        colorbar=True,
        cmap="Magma",
        tools=["hover"],
    )

    # Configure marker and size behavior based on size parameter
    use_dynamic_sizing = size.lower() in ["dyn", "dynamic"]
    use_slider_sizing = size.lower() == "slider"

    def dynamic_sizing_hook(plot, element):
        """Hook to convert size-based markers to radius-based for dynamic behavior"""
        try:
            if use_dynamic_sizing and hasattr(plot, "state") and hasattr(plot.state, "renderers"):
                from bokeh.models import Circle

                for renderer in plot.state.renderers:
                    if hasattr(renderer, "glyph"):
                        glyph = renderer.glyph
                        # Check if it's a circle/scatter glyph that we can convert
                        if hasattr(glyph, "size") and marker_type == "circle":
                            # Create a new Circle glyph with radius instead of size
                            new_glyph = Circle(
                                x=glyph.x,
                                y=glyph.y,
                                radius=base_radius,
                                fill_color=glyph.fill_color,
                                line_color=glyph.line_color,
                                fill_alpha=glyph.fill_alpha,
                                line_alpha=glyph.line_alpha,
                            )
                            renderer.glyph = new_glyph
        except Exception:
            # Silently fail and use regular sizing if hook doesn't work
            pass

    if use_dynamic_sizing:
        # Dynamic sizing: use coordinate-based sizing that scales with zoom
        marker_type = "circle"
        # Calculate radius based on data range for coordinate-based sizing
        rtrange = maxrt - minrt
        mzrange = maxmz - minmz
        # Use a fraction of the smaller dimension for radius
        base_radius = min(rtrange, mzrange) * 0.0005 * markersize
        size_1 = markersize  # Use regular size initially, hook will convert to radius
        size_2 = markersize
        hooks = [dynamic_sizing_hook]
    elif use_slider_sizing:
        # Slider sizing: create an interactive slider for marker size
        marker_type = marker  # Use the original marker parameter
        size_1 = markersize  # Use markersize initially, will be updated by slider
        size_2 = markersize
        base_radius = None  # Not used in slider mode
        hooks = []
    else:
        # Static sizing: use pixel-based sizing that stays fixed
        marker_type = marker  # Use the original marker parameter
        size_1 = markersize
        size_2 = markersize
        base_radius = None  # Not used in static mode
        hooks = []

    color_1 = "forestgreen"
    color_2 = "darkorange"

    # Handle colorby parameter for feature coloring
    use_categorical_coloring = False
    feature_colors = {}
    categorical_groups = []

    if filename is not None:
        dyn = False
        if not filename.endswith(".html"):
            if use_dynamic_sizing:
                # For exported files, use smaller coordinate-based size
                size_1 = 2
                size_2 = 2
            else:
                size_1 = 2
                size_2 = 2
            color_1 = "forestgreen"
            color_2 = "darkorange"
            raster_dynamic = False

    # For slider functionality, disable raster dynamic to avoid DynamicMap nesting
    if use_slider_sizing:
        raster_dynamic = False

    dyn = raster_dynamic
    raster = hd.rasterize(
        points,
        aggregator=ds.max("inty"),
        interpolation="bilinear",
        dynamic=dyn,  # alpha=10,                min_alpha=0,
    ).opts(
        active_tools=["box_zoom"],
        cmap=cmap_palette,
        tools=["hover"],
        hooks=[new_bounds_hook],
        width=width,
        height=height,
        cnorm="log" if raster_log else "linear",
        xlabel="Retention time (s)",
        ylabel="m/z",
        colorbar=True,
        colorbar_position="right",
        axiswise=True,
    )

    raster = hd.dynspread(
        raster,
        threshold=raster_threshold,
        how="add",
        shape="square",
        max_px=raster_max_px,
    )
    feature_points_1 = None
    feature_points_2 = None
    feature_points_3 = None
    feature_points_4 = None
    feature_points_iso = None
    # Plot features as red dots if features is True
    if self.features_df is not None and show_features:
        feats = self.features_df.clone()
        # Convert to pandas for operations that require pandas functionality
        if hasattr(feats, "to_pandas"):
            feats = feats.to_pandas()
        # if ms2_scans is not null, keep only the first element of the list
        feats["ms2_scans"] = feats["ms2_scans"].apply(
            lambda x: x[0] if isinstance(x, list) else x,
        )
        if mz_range is not None:
            feats = feats[(feats["mz"] >= mz_range[0]) & (feats["mz"] <= mz_range[1])]
        if rt_range is not None:
            feats = feats[(feats["rt"] >= rt_range[0]) & (feats["rt"] <= rt_range[1])]
        # keep only iso==0, i.e. the main
        feats = feats[feats["iso"] == 0]

        # Handle colorby parameter
        if colorby is not None and colorby in feats.columns:
            # Check if colorby data is categorical (string-like)
            colorby_values = feats[colorby].dropna()
            is_categorical = feats[colorby].dtype in ["object", "string", "category"] or (
                len(colorby_values) > 0 and isinstance(colorby_values.iloc[0], str)
            )

            if is_categorical:
                use_categorical_coloring = True
                # Get unique categories, sorted
                categorical_groups = sorted(feats[colorby].dropna().unique())

                # Set up colors for categorical data using matplotlib colormap
                from matplotlib.colors import to_hex

                try:
                    from matplotlib.cm import get_cmap

                    colormap_func = get_cmap(cmap if cmap != "iridescent" else "tab20")
                    feature_colors = {}
                    for i, group in enumerate(categorical_groups):
                        if len(categorical_groups) <= 20:
                            # Use qualitative colors for small number of categories
                            color_val = colormap_func(i / max(1, len(categorical_groups) - 1))
                        else:
                            # Use continuous colormap for many categories
                            color_val = colormap_func(i / max(1, len(categorical_groups) - 1))
                        feature_colors[group] = to_hex(color_val)
                except Exception as e:
                    self.logger.warning(f"Could not set up categorical coloring: {e}, using default colors")
                    use_categorical_coloring = False

        if use_categorical_coloring and colorby is not None:
            # Create separate feature points for each category
            for i, group in enumerate(categorical_groups):
                group_features = feats[feats[colorby] == group]
                if len(group_features) == 0:
                    continue

                # Split by MS2 status
                group_with_ms2 = group_features[group_features["ms2_scans"].notnull()]
                group_without_ms2 = group_features[group_features["ms2_scans"].isnull()]

                group_color = feature_colors.get(group, color_1)

                if len(group_with_ms2) > 0:
                    feature_hover = HoverTool(
                        tooltips=[
                            ("rt", "@rt"),
                            ("m/z", "@mz{0.0000}"),
                            ("feature_uid", "@feature_uid"),
                            ("inty", "@inty"),
                            ("iso", "@iso"),
                            ("adduct", "@adduct"),
                            ("chrom_coherence", "@chrom_coherence"),
                            ("chrom_prominence_scaled", "@chrom_prominence_scaled"),
                            (colorby, f"@{colorby}"),
                        ],
                    )
                    group_points_ms2 = hv.Points(
                        group_with_ms2,
                        kdims=["rt", "mz"],
                        vdims=[
                            "feature_uid",
                            "inty",
                            "iso",
                            "adduct",
                            "ms2_scans",
                            "chrom_coherence",
                            "chrom_prominence_scaled",
                            colorby,
                        ],
                        label=f"{group} (MS2)",
                    ).options(
                        color=group_color,
                        marker=marker_type,
                        size=size_1,
                        tools=[feature_hover],
                        hooks=hooks,
                    )
                    if feature_points_1 is None:
                        feature_points_1 = group_points_ms2
                    else:
                        feature_points_1 = feature_points_1 * group_points_ms2

                if len(group_without_ms2) > 0:
                    feature_hover = HoverTool(
                        tooltips=[
                            ("rt", "@rt"),
                            ("m/z", "@mz{0.0000}"),
                            ("feature_uid", "@feature_uid"),
                            ("inty", "@inty"),
                            ("iso", "@iso"),
                            ("adduct", "@adduct"),
                            ("chrom_coherence", "@chrom_coherence"),
                            ("chrom_prominence_scaled", "@chrom_prominence_scaled"),
                            (colorby, f"@{colorby}"),
                        ],
                    )
                    group_points_no_ms2 = hv.Points(
                        group_without_ms2,
                        kdims=["rt", "mz"],
                        vdims=[
                            "feature_uid",
                            "inty",
                            "iso",
                            "adduct",
                            "chrom_coherence",
                            "chrom_prominence_scaled",
                            colorby,
                        ],
                        label=f"{group} (no MS2)",
                    ).options(
                        color=group_color,
                        marker=marker_type,
                        size=size_2,
                        tools=[feature_hover],
                        hooks=hooks,
                    )
                    if feature_points_2 is None:
                        feature_points_2 = group_points_no_ms2
                    else:
                        feature_points_2 = feature_points_2 * group_points_no_ms2
        else:
            # Use original green/red coloring scheme for MS2 presence
            # find features with ms2_scans not None  and iso==0
            features_df = feats[feats["ms2_scans"].notnull()]
            # Create feature points with proper sizing method
            feature_hover_1 = HoverTool(
                tooltips=[
                    ("rt", "@rt"),
                    ("m/z", "@mz{0.0000}"),
                    ("feature_uid", "@feature_uid"),
                    ("inty", "@inty"),
                    ("iso", "@iso"),
                    ("adduct", "@adduct"),
                    ("chrom_coherence", "@chrom_coherence"),
                    ("chrom_prominence_scaled", "@chrom_prominence_scaled"),
                ],
            )
            if len(features_df) > 0:
                feature_points_1 = hv.Points(
                    features_df,
                    kdims=["rt", "mz"],
                    vdims=[
                        "feature_uid",
                        "inty",
                        "iso",
                        "adduct",
                        "ms2_scans",
                        "chrom_coherence",
                        "chrom_prominence_scaled",
                    ],
                    label="Features with MS2 data",
                ).options(
                    color=color_1,
                    marker=marker_type,
                    size=size_1,
                    tools=[feature_hover_1],
                    hooks=hooks,
                )

            # find features without MS2 data
            features_df = feats[feats["ms2_scans"].isnull()]
            feature_hover_2 = HoverTool(
                tooltips=[
                    ("rt", "@rt"),
                    ("m/z", "@mz{0.0000}"),
                    ("feature_uid", "@feature_uid"),
                    ("inty", "@inty"),
                    ("iso", "@iso"),
                    ("adduct", "@adduct"),
                    ("chrom_coherence", "@chrom_coherence"),
                    ("chrom_prominence_scaled", "@chrom_prominence_scaled"),
                ],
            )
            if len(features_df) > 0:
                feature_points_2 = hv.Points(
                    features_df,
                    kdims=["rt", "mz"],
                    vdims=[
                        "feature_uid",
                        "inty",
                        "iso",
                        "adduct",
                        "chrom_coherence",
                        "chrom_prominence_scaled",
                    ],
                    label="Features without MS2 data",
                ).options(
                    color="red",
                    marker=marker_type,
                    size=size_2,
                    tools=[feature_hover_2],
                    hooks=hooks,
                )

        if show_isotopes:
            # Use proper Polars filter syntax to avoid boolean indexing issues
            features_df = self.features_df.filter(pl.col("iso") > 0)
            # Convert to pandas for plotting compatibility
            if hasattr(features_df, "to_pandas"):
                features_df = features_df.to_pandas()
            feature_hover_iso = HoverTool(
                tooltips=[
                    ("rt", "@rt"),
                    ("m/z", "@mz{0.0000}"),
                    ("feature_uid", "@feature_uid"),
                    ("inty", "@inty"),
                    ("iso", "@iso"),
                    ("iso_of", "@iso_of"),
                    ("adduct", "@adduct"),
                    ("chrom_coherence", "@chrom_coherence"),
                    ("chrom_prominence_scaled", "@chrom_prominence_scaled"),
                ],
            )
            feature_points_iso = hv.Points(
                features_df,
                kdims=["rt", "mz"],
                vdims=[
                    "feature_uid",
                    "inty",
                    "iso",
                    "iso_of",
                    "adduct",
                    "chrom_coherence",
                    "chrom_prominence_scaled",
                ],
                label="Isotopes",
            ).options(
                color="violet",
                marker=marker_type,
                size=size_1,
                tools=[feature_hover_iso],
                hooks=hooks,
            )
    if show_ms2:
        # find all self.scans_df with mslevel 2 that are not linked to a feature
        ms2_orphan = self.scans_df.filter(pl.col("ms_level") == 2).filter(
            pl.col("feature_uid") < 0,
        )

        if len(ms2_orphan) > 0:
            # pandalize
            ms2 = ms2_orphan.to_pandas()
            ms2_hover_3 = HoverTool(
                tooltips=[
                    ("rt", "@rt"),
                    ("prec_mz", "@prec_mz{0.0000}"),
                    ("index", "@index"),
                    ("inty_tot", "@inty_tot"),
                    ("bl", "@bl"),
                ],
            )
            feature_points_3 = hv.Points(
                ms2,
                kdims=["rt", "prec_mz"],
                vdims=["index", "inty_tot", "bl"],
                label="Orphan MS2 scans",
            ).options(
                color=color_2,
                marker="x",
                size=size_2,
                tools=[ms2_hover_3],
            )

        ms2_linked = self.scans_df.filter(pl.col("ms_level") == 2).filter(
            pl.col("feature_uid") >= 0,
        )
        if len(ms2_linked) > 0:
            # pandalize
            ms2 = ms2_linked.to_pandas()
            ms2_hover_4 = HoverTool(
                tooltips=[
                    ("rt", "@rt"),
                    ("prec_mz", "@prec_mz{0.0000}"),
                    ("index", "@index"),
                    ("inty_tot", "@inty_tot"),
                    ("bl", "@bl"),
                ],
            )
            feature_points_4 = hv.Points(
                ms2,
                kdims=["rt", "prec_mz"],
                vdims=["index", "inty_tot", "bl"],
                label="Linked MS2 scans",
            ).options(
                color=color_1,
                marker="x",
                size=size_2,
                tools=[ms2_hover_4],
            )

    overlay = raster

    if feature_points_4 is not None:
        overlay = overlay * feature_points_4
    if feature_points_3 is not None:
        overlay = overlay * feature_points_3
    if feature_points_1 is not None:
        overlay = overlay * feature_points_1
    if not show_only_features_with_ms2 and feature_points_2 is not None:
        overlay = overlay * feature_points_2
    if feature_points_iso is not None:
        overlay = overlay * feature_points_iso

    if title is not None:
        overlay = overlay.opts(title=title)

    # Handle legend positioning for categorical coloring
    if legend is not None and use_categorical_coloring and len(categorical_groups) > 1:
        # Map legend position parameter to HoloViews legend position
        legend_position_map = {
            "top_right": "top_right",
            "top_left": "top_left",
            "bottom_right": "bottom_right",
            "bottom_left": "bottom_left",
            "right": "right",
            "left": "left",
            "top": "top",
            "bottom": "bottom",
        }

        hv_legend_pos = legend_position_map.get(legend, "bottom_right")

        # Apply legend configuration to the overlay
        overlay = overlay.opts(legend_position=hv_legend_pos, legend_opts={"title": "", "padding": 2, "spacing": 2})
    elif legend is None and use_categorical_coloring:
        # Explicitly hide legend when legend=None but categorical coloring is used
        overlay = overlay.opts(show_legend=False)

    # Handle slider functionality
    if use_slider_sizing:
        # For slider functionality, we need to work with the feature points directly
        # and not nest DynamicMaps. We'll create the slider using param and panel.
        import param
        import panel as on

        class MarkerSizeController(param.Parameterized):
            size_slider = param.Number(default=markersize, bounds=(1, 20), step=0.5)

        # Create a function that generates just the feature overlays with different sizes
        def create_feature_overlay(size_val):
            feature_overlay = None

            if feature_points_4 is not None:
                updated_points_4 = feature_points_4.opts(size=size_val)
                feature_overlay = updated_points_4 if feature_overlay is None else feature_overlay * updated_points_4
            if feature_points_3 is not None:
                updated_points_3 = feature_points_3.opts(size=size_val)
                feature_overlay = updated_points_3 if feature_overlay is None else feature_overlay * updated_points_3
            if feature_points_1 is not None:
                updated_points_1 = feature_points_1.opts(size=size_val)
                feature_overlay = updated_points_1 if feature_overlay is None else feature_overlay * updated_points_1
            if not show_only_features_with_ms2 and feature_points_2 is not None:
                updated_points_2 = feature_points_2.opts(size=size_val)
                feature_overlay = updated_points_2 if feature_overlay is None else feature_overlay * updated_points_2
            if feature_points_iso is not None:
                updated_points_iso = feature_points_iso.opts(size=size_val)
                feature_overlay = (
                    updated_points_iso if feature_overlay is None else feature_overlay * updated_points_iso
                )

            # Combine with the static raster background
            if feature_overlay is not None:
                combined_overlay = raster * feature_overlay
            else:
                combined_overlay = raster

            if title is not None:
                combined_overlay = combined_overlay.opts(title=title)

            return combined_overlay

        # Create a horizontal control widget on top of the plot
        # Create the slider widget with explicit visibility
        size_slider = on.widgets.FloatSlider(
            name="Marker Size",
            start=1.0,
            end=20.0,
            step=0.5,
            value=markersize,
            width=300,
            height=40,
            margin=(5, 5),
            show_value=True,
        )

        # Create the slider widget row with clear styling
        slider_widget = on.Row(
            on.pane.HTML("<b>Marker Size Control:</b>", width=150, height=40, margin=(5, 10)),
            size_slider,
            height=60,
            margin=10,
        )

        # Create slider widget
        size_slider = on.widgets.FloatSlider(
            name="Marker Size",
            start=1.0,
            end=20.0,
            step=0.5,
            value=markersize,
            width=300,
            height=40,
            margin=(5, 5),
            show_value=True,
        )

        slider_widget = on.Row(
            on.pane.HTML("<b>Marker Size:</b>", width=100, height=40, margin=(5, 10)),
            size_slider,
            height=60,
            margin=10,
        )

        # Simple reactive plot - slider mode doesn't use dynamic rasterization
        @on.depends(size_slider.param.value)
        def reactive_plot(size_val):
            overlay = create_feature_overlay(float(size_val))
            # Apply static rasterization for slider mode
            if raster_dynamic:
                return hd.rasterize(
                    overlay,
                    aggregator=ds.count(),
                    width=raster_max_px,
                    height=raster_max_px,
                    dynamic=False,  # Static raster for slider mode
                ).opts(
                    cnorm="eq_hist",
                    tools=["hover"],
                    width=width,
                    height=height,
                )
            else:
                return overlay

        # Create layout
        layout = on.Column(slider_widget, reactive_plot, sizing_mode="stretch_width")

        # Handle filename saving for slider mode
        if filename is not None:
            if filename.endswith(".html"):
                layout.save(filename, embed=True)
            else:
                # For slider plots, save the current state
                hv.save(create_feature_overlay(markersize), filename, fmt="png")
        else:
            # Use show() for display in notebook
            layout.show()
    else:
        # Create a panel layout without slider
        layout = panel.Column(overlay)

    # Handle display logic based on show_in_browser and raster_dynamic
    if filename is not None:
        # Use consistent save/display behavior
        self._handle_sample_plot_output(layout, filename, "panel")
    else:
        # Show in browser if both show_in_browser and raster_dynamic are True
        if show_in_browser and raster_dynamic:
            layout.show()
        else:
            # Return to notebook for inline display
            return layout


def plot_2d_oracle(
    self,
    oracle_folder=None,
    link_by_feature_uid=True,
    min_id_level=1,
    max_id_level=4,
    min_ms_level=2,
    colorby="hg",
    legend_groups=None,
    markersize=5,
    cmap="Turbo",
    raster_cmap="grey",
    raster_log=True,
    raster_min=1,
    raster_dynamic=True,
    raster_max_px=8,
    raster_threshold=0.8,
    mz_range=None,
    rt_range=None,
    width=750,
    height=600,
    filename=None,
    title=None,
    legend="bottom_right",
):
    """
    Plot a 2D visualization combining MS1 raster data and oracle-annotated features.

    Creates an interactive plot overlaying MS1 survey scan data with feature annotations
    from oracle files. Features are colored categorically based on identification class,
    ion type, or evidence level.

    Parameters:
        oracle_folder (str, optional): Path to oracle folder containing
            "diag/summary_by_feature.csv". Required for oracle annotations.
        link_by_feature_uid (bool): Whether to link features by UID (True) or by m/z/RT proximity.
        min_id_level (int): Minimum identification confidence level to include.
        max_id_level (int): Maximum identification confidence level to include.
        min_ms_level (int): Minimum MS level for features to include.
        colorby (str): Feature coloring scheme - "id_class", "id_ion", "id_evidence", etc.
        legend_groups (list, optional): List of groups to include in legend and coloring scheme.
            If provided, legend will show exactly these groups. 'mix' is automatically added
            as the last group to contain points not matching other groups. Works for all
            categorical coloring types (id_class, id_ion, id_evidence, etc.).
            If None (default), all groups present in the data will be shown without filtering.
            All specified classes will appear in the legend even if no features are present.
        markersize (int): Size of feature markers.
        cmap (str): Colormap name for categorical coloring.
        raster_cmap (str): Colormap for MS1 raster background.
        raster_log (bool): Use logarithmic scaling for raster intensity (True) or linear scaling (False).
        raster_min (float): Minimum intensity threshold for raster data filtering.
        raster_dynamic (bool): Enable dynamic rasterization.
        raster_threshold (float): Dynamic raster spread threshold.
        raster_max_px (int): Maximum pixel size for rasterization.
        mz_range (tuple, optional): m/z range filter (min, max).
        rt_range (tuple, optional): Retention time range filter (min, max).
        width/height (int): Plot dimensions in pixels.
        filename (str, optional): Export filename (.html/.svg/.png). If None, displays inline.
        title (str, optional): Plot title.
        legend (str, optional): Legend position ("top_right", "bottom_left", etc.) or None.

    Returns:
        HoloViews layout for display (if filename is None), otherwise None.
    """

    self.logger.info(f"Starting plot_2d_oracle with oracle_folder: {oracle_folder}")
    self.logger.debug(
        f"Parameters - link_by_feature_uid: {link_by_feature_uid}, min_id_level: {min_id_level}, max_id_level: {max_id_level}"
    )
    self.logger.debug(f"Plot parameters - colorby: {colorby}, markersize: {markersize}, filename: {filename}")

    # Early validation
    if self.features_df is None:
        self.logger.error("Cannot plot 2D oracle: features_df is not available")
        return

    if oracle_folder is None:
        self.logger.info("No oracle folder provided, plotting features only")
        return

    # Create raster plot layer
    raster = _create_raster_plot(
        self,
        mz_range=mz_range,
        rt_range=rt_range,
        raster_cmap=raster_cmap,
        raster_log=raster_log,
        raster_min=raster_min,
        raster_dynamic=raster_dynamic,
        raster_threshold=raster_threshold,
        raster_max_px=raster_max_px,
        width=width,
        height=height,
        filename=filename,
    )

    # Load and process oracle data
    feats = _load_and_merge_oracle_data(
        self,
        oracle_folder=oracle_folder,
        link_by_feature_uid=link_by_feature_uid,
        min_id_level=min_id_level,
        max_id_level=max_id_level,
        min_ms_level=min_ms_level,
    )

    if feats is None:
        return

    # Set up color scheme and categorical mapping
    cvalues, color_column, colors = _setup_color_mapping(self, feats, colorby, cmap, legend_groups)

    # Create feature overlay with all visualization elements
    overlay = _create_feature_overlay(
        self,
        raster=raster,
        feats=feats,
        cvalues=cvalues,
        color_column=color_column,
        colors=colors,
        markersize=markersize,
        title=title,
        legend=legend,
    )

    # Handle output: export or display
    return _handle_output(self, overlay, filename)


def plot_ms2_eic(
    self,
    feature_uid=None,
    rt_tol=5,
    mz_tol=0.05,
    link_x=True,
    n=20,
    deisotope=True,
    centroid=True,
    filename=None,
):
    """
    Plots the Extracted Ion Chromatograms (EIC) for the precursor and top n MS2 fragment ions of a given feature.
    Parameters:
        feature_uid: The feature unique identifier. Must be present in the features dataframe; if None, a message is printed.
        rt_tol (float, optional): The retention time tolerance (in seconds) to extend the feature's rt start and end values. Default is 5.
        mz_tol (float, optional): The m/z tolerance used when filtering the precursor and fragment ion intensities. Default is 0.05.
        link_x (bool, optional): If True, the x-axis (retention time) of all subplots is linked. Default is True.
        n (int, optional): The number of top MS2 fragment m/z values to consider for plotting. Default is 20.
        deisotope (bool, optional): Flag that determines whether deisotoping should be applied to the MS2 fragments. Default is True.
        centroid (bool, optional): Flag that controls whether centroiding is applied to the MS2 data. Default is True.
        filename (str, optional): If provided, the function saves the plot to the specified file. Supports .html for interactive plots or other formats (e.g., png).
                                  If None, the plot is displayed instead of being saved.
    Returns:
        None
    Notes:
        - The function first verifies the existence of the provided feature id and its associated MS2 spectrum.
        - It retrieves the top n fragments by intensity from the MS2 spectrum and computes the EIC for both the precursor ion and the fragments.
        - A helper method (_spec_to_mat) is used to convert spectral data into intensity matrices.
        - The resulting plots include hover tools to display the retention time and scan identifier.
        - The layout is arranged in a grid (4 columns by default) and may have linked x-axes based on the link_x parameter.
    """
    # plots the EIC for a given feature id inlcusind the EIC of the top n MS2 fragments

    if feature_uid is None:
        print("Please provide a feature id.")
        return
    # check if feature_uid is in features_df
    if feature_uid not in self.features_df["feature_uid"].values:
        print("Feature id not found in features_df.")

    feature = self.features_df[self.features_df["feature_uid"] == feature_uid]
    # get top n fragments
    ms2_specs = feature["ms2_specs"].values[0]
    if ms2_specs is None:
        print("No MS2 data found for this feature.")
        return

    if len(ms2_specs) == 0:
        print("No MS2 data found for this feature.")
        return
    # get the MS2 spectrum
    # get the mz of the top n fragments
    ms2_specs_df = ms2_specs[0].pandalize()
    ms2_specs_df = ms2_specs_df.sort_values(by="inty", ascending=False)
    ms2_specs_df = ms2_specs_df.head(n)
    top_mzs = ms2_specs_df["mz"].values.tolist()

    # find rt_start and rt_end of the feature_uid
    rt_start = feature["rt_start"].values[0] - rt_tol
    rt_end = feature["rt_end"].values[0] + rt_tol
    # get the cycle at rt_start and the cycle at rt_end from the closest scan with ms_level == 1
    scans = self.scans_df.filter(pl.col("ms_level") == 1)
    scans = scans.filter(pl.col("rt") > rt_start)
    scans = scans.filter(pl.col("rt") < rt_end)
    rts = scans["rt"].to_list()
    if len(scans) == 0:
        print(f"No scans found between {rt_start} and {rt_end}.")
        return
    scan_uids = scans["scan_uid"].to_list()
    eic_prec = self._spec_to_mat(
        scan_uids,
        mz_ref=feature["mz"].values.tolist(),
        mz_tol=mz_tol,
        deisotope=False,
        centroid=True,
    )
    # convert eic_prec from matrix to list
    eic_prec = eic_prec[0].tolist()

    # get all unique cycles from scans
    cycles = scans["cycle"].unique()
    scan_uids = []
    # iterate over all cycles and get the scan_uid of scan with ms_level == 2 and closest precursor_mz to spec.precursor_mz
    for cycle in cycles:
        scans = self.scans_df.filter(pl.col("cycle") == cycle)
        scans = scans.filter(pl.col("ms_level") == 2)
        scans = scans.filter(pl.col("prec_mz") > feature["mz"] - 5)
        scans = scans.filter(pl.col("prec_mz") < feature["mz"] + 5)
        if len(scans) == 0:
            print(
                f"No scans found for cycle {cycle} and mz {feature['mz']}. Increase mz_tol tolerance.",
            )
            return
        # get the scan with the closest precursor_mz to feature['mz']
        scan = scans[(scans["prec_mz"] - feature["mz"]).abs().arg_sort()[:1]]
        scan_uids.append(scan["scan_uid"][0])
    eic_prod = self._spec_to_mat(
        scan_uids,
        mz_ref=top_mzs,
        mz_tol=mz_tol,
        deisotope=deisotope,
        centroid=centroid,
    )

    prec_name = f"prec {feature['mz'].values[0]:.3f}"
    eic_df = pd.DataFrame({"rt": rts, prec_name: eic_prec})
    # add scan_uid to eic_df for the tooltips
    eic_df["scan_uid"] = scan_uids

    frag_names = [prec_name]
    for i, mz in enumerate(top_mzs):
        # add column to eic_df
        name = f"frag {mz:.3f}"
        frag_names.append(name)
        eic_df[name] = eic_prod[i]

    # create a plot for all columns in eic_df
    eic_plots: list[hv.Curve] = []
    for name in frag_names:
        eic = hv.Curve(eic_df, kdims=["rt"], vdims=[name, "scan_uid"]).opts(
            title=name,
            xlabel="RT (s)",
            ylabel=f"Inty_f{len(eic_plots)}",
            width=250,
            height=200,
            axiswise=True,
            color="black",
            tools=[HoverTool(tooltips=[("rt", "@rt"), ("scan_uid", "@scan_uid")])],
        )
        eic_plots.append(eic)

    # add as

    layout = hv.Layout(eic_plots).cols(4)
    if link_x:
        layout = layout.opts(shared_axes=True)

    if filename is not None:
        if filename.endswith(".html"):
            panel.panel(layout).save(filename, embed=True)  # type: ignore[attr-defined]
        else:
            hv.save(layout, filename, fmt="png")
    else:
        # Check if we're in a notebook environment and display appropriately
        layout_obj = panel.panel(layout)
        return _display_plot(layout, layout_obj)


def plot_ms2_cycle(
    self,
    cycle=None,
    filename=None,
    title=None,
    cmap=None,
    raster_dynamic=True,
    raster_max_px=8,
    raster_threshold=0.8,
    centroid=True,
    deisotope=True,
):
    if self.file_obj is None:
        print("Please load a mzML file first.")
        return

    if cycle is None:
        print("Please provide a cycle number.")
        return

    if cycle not in self.scans_df["cycle"].unique():
        print("Cycle number not found in scans_df.")
        return

    # Process colormap using the cmap package
    cmap_palette = _process_cmap(cmap, fallback="iridescent_r", logger=self.logger)

    # find all scans in cycle
    scans = self.scans_df.filter(pl.col("cycle") == cycle)
    scans = scans.filter(pl.col("ms_level") == 2)

    ms2data = []
    # iterate through all rows
    for scan in scans.iter_rows(named=True):
        scan_uid = scan["scan_uid"]
        # get spectrum
        spec = self.get_spectrum(
            scan_uid,
            precursor_trim=None,
            centroid=centroid,
            deisotope=deisotope,
        )
        if spec.mz.size == 0:
            continue
        d = {
            "prec_mz": [scan["prec_mz"]] * spec.mz.size,
            "mz": spec.mz,
            "inty": spec.inty,
        }
        ms2data.append(d)

    # convert to pandas DataFrame
    spectradf = pd.DataFrame(ms2data)

    # remove any inty<1
    spectradf = spectradf[spectradf["inty"] >= 1]
    # keep only rt, mz, and inty
    spectradf = spectradf[["prec_mz", "mz", "inty"]]
    maxrt = spectradf["prec_mz"].max()
    minrt = spectradf["prec_mz"].min()
    maxmz = spectradf["mz"].max()
    minmz = spectradf["mz"].min()

    # TODO elem not used
    def new_bounds_hook(plot, elem):
        x_range = plot.state.x_range
        y_range = plot.state.y_range
        x_range.bounds = minrt, maxrt
        y_range.bounds = minmz, maxmz

    points = hv.Points(
        spectradf,
        kdims=["prec_mz", "mz"],
        vdims=["inty"],
        label="MS1 survey scans",
    ).opts(
        fontsize={"title": 16, "labels": 14, "xticks": 6, "yticks": 12},
        color=np.log(dim("inty")),
        colorbar=True,
        cmap="Magma",
        tools=["hover"],
    )

    raster = hd.rasterize(
        points,
        aggregator=ds.max("inty"),
        interpolation="bilinear",
        dynamic=raster_dynamic,  # alpha=10,                min_alpha=0,
    ).opts(
        active_tools=["box_zoom"],
        cmap=cmap_palette,
        tools=["hover"],
        hooks=[new_bounds_hook],
        width=1000,
        height=1000,
        cnorm="log",
        xlabel="Q1 m/z",
        ylabel="m/z",
        colorbar=True,
        colorbar_position="right",
        axiswise=True,
    )

    overlay = hd.dynspread(
        raster,
        threshold=raster_threshold,
        how="add",
        shape="square",
        max_px=raster_max_px,
    )

    if title is not None:
        overlay = overlay.opts(title=title)

    # Create a panel layout
    layout = panel.Column(overlay)

    if filename is not None:
        # if filename includes .html, save the panel layout to an HTML file
        if filename.endswith(".html"):
            layout.save(filename, embed=True)
        else:
            # save the panel layout as a png
            hv.save(overlay, filename, fmt="png")
    else:
        # Check if we're in a notebook environment and display appropriately
        return _display_plot(overlay, layout)


def plot_ms2_q1(
    self,
    feature_uid=None,
    q1_width=10.0,
    mz_tol=0.01,
    link_x=True,
    n=20,
    deisotope=True,
    centroid=True,
    filename=None,
):
    # plots the EIC for a given feature id including the EIC of the top n MS2 fragments

    if feature_uid is None:
        print("Please provide a feature id.")
        return
    # check if feature_uid is in features_df
    if feature_uid not in self.features_df["feature_uid"].values:
        print("Feature id not found in features_df.")

    feature = self.features_df[self.features_df["feature_uid"] == feature_uid]
    # get top n fragments
    ms2_specs = feature["ms2_specs"].values[0]
    if ms2_specs is None:
        print("No MS2 data found for this feature.")
        return

    if len(ms2_specs) == 0:
        print("No MS2 data found for this feature.")
        return
    # get the MS2 spectrum
    # get the mz of the top n fragments
    ms2_specs_df = ms2_specs[0].pandalize()
    ms2_specs_df = ms2_specs_df.sort_values(by="inty", ascending=False)
    ms2_specs_df = ms2_specs_df.head(n)
    top_mzs = ms2_specs_df["mz"].values.tolist()

    # cycles is the cycle of the feature plus/minus q1_width
    feature_scan = self.select_closest_scan(feature["rt"].values[0])
    cycle = feature_scan["cycle"][0]
    scans = self.scans_df.filter(pl.col("cycle") == cycle)
    scans = scans.filter(pl.col("ms_level") == 2)
    # find the scan in cycle whose 'prec_mz' is the closest to the feature['mz']
    scan_uid = scans[(scans["prec_mz"] - feature["mz"]).abs().arg_sort()[:1]]["scan_uid"][0]
    # get q1_width scans before and after the scan_uid
    scans = self.scans_df.filter(pl.col("scan_uid") >= scan_uid - q1_width)
    scans = scans.filter(pl.col("scan_uid") <= scan_uid + q1_width)
    scan_uids = scans["scan_uid"].to_list()
    q1s = scans["prec_mz"].to_list()

    q1_prod = self._spec_to_mat(
        scan_uids,
        mz_ref=top_mzs,
        mz_tol=mz_tol,
        deisotope=deisotope,
        centroid=centroid,
    )
    q1_df = pd.DataFrame({"q1": q1s})

    frag_names = []
    for i, mz in enumerate(top_mzs):
        # add column to q1_df
        name = f"frag {mz:.3f}"
        # if q1_ratio exists, add it to the name
        if "q1_ratio" in ms2_specs_df.columns:
            q1_ratio = ms2_specs_df["q1_ratio"].values[i]
            name += f" q1r: {q1_ratio:.2f}"
        frag_names.append(name)
        q1_df[name] = q1_prod[i]
    # add scan_uid to q1_df for the tooltips
    q1_df["scan_uid"] = scan_uids

    # create a plot for all columns in eic_df
    eic_plots: list[hv.Curve] = []
    for name in frag_names:
        eic = hv.Curve(q1_df, kdims=["q1"], vdims=[name, "scan_uid"]).opts(
            title=name,
            xlabel="Q1 (m/z)",
            ylabel=f"Inty_f{len(eic_plots)}",
            width=250,
            height=200,
            axiswise=True,
            color="black",
            tools=[HoverTool(tooltips=[("Q1", "@q1"), ("scan_uid", "@scan_uid")])],
        )
        eic_plots.append(eic)

    # add as

    layout = hv.Layout(eic_plots).cols(4)
    if link_x:
        layout = layout.opts(shared_axes=True)

    if filename is not None:
        if filename.endswith(".html"):
            panel.panel(layout).save(filename, embed=True)  # type: ignore[attr-defined]
        else:
            hv.save(layout, filename, fmt="png")
    else:
        # Check if we're in a notebook environment and display appropriately
        layout_obj = panel.panel(layout)
        return _display_plot(layout, layout_obj)


def plot_dda_stats(
    self,
    filename=None,
):
    """
    Generates scatter plots for DDA statistics.
    This method retrieves statistical data using the `get_dda_stats` method, filters relevant
    columns, and preprocesses the data by replacing any values below 0 with None. It then creates
    a scatter plot for each metric specified in the `cols_to_plot` list. Each scatter plot uses "cycle"
    as the x-axis, and the corresponding metric as the y-axis. In addition, common hover tooltips are
    configured to display auxiliary data including "index", "cycle", "rt", and all other metric values.
    If the `filename` parameter is provided:
        - If it ends with ".html", the layout is saved as an interactive HTML file using Panel.
        - Otherwise, the layout is saved as a PNG image using HoloViews.
    If no filename is provided, the interactive panel is displayed.
    Parameters:
        filename (str, optional): The path and filename where the plot should be saved. If the filename
            ends with ".html", the plot is saved as an HTML file; otherwise, it is saved as a PNG image.
            If not provided, the plot is displayed interactively.
    Notes:
        - The method requires the holoviews, panel, and bokeh libraries for visualization.
        - The data is expected to include the columns 'index', 'cycle', 'rt', and the metrics listed in
            `cols_to_plot`.
    """
    stats = self.get_dda_stats()
    cols_to_plot = [
        "inty_tot",
        "bl",
        "ms2_n",
        "time_cycle",
        "time_ms1_to_ms1",
        "time_ms1_to_ms2",
        "time_ms2_to_ms2",
        "time_ms2_to_ms1",
    ]
    # Ensure that 'index' and 'rt' are kept for hover along with the columns to plot
    stats = stats[["scan_uid", "cycle", "rt", *cols_to_plot]]
    # set any value < 0 to None
    stats[stats < 0] = None

    # Create a Scatter for each column in cols_to_plot stacked vertically, with hover enabled
    scatter_plots = []
    # Define common hover tooltips for all plots including all cols_to_plot
    common_tooltips = [
        ("scan_uid", "@scan_uid"),
        ("cycle", "@cycle"),
        ("rt", "@rt"),
    ] + [(c, f"@{c}") for c in cols_to_plot]
    for col in cols_to_plot:
        hover = HoverTool(tooltips=common_tooltips)
        scatter = hv.Scatter(
            stats,
            kdims="cycle",
            vdims=[col, "scan_uid", "rt"] + [c for c in cols_to_plot if c != col],
        ).opts(
            title=col,
            xlabel="Cycle",
            ylabel=col,
            height=250,
            width=800,
            tools=[hover],
            size=3,
        )
        scatter_plots.append(scatter)

    layout = hv.Layout(scatter_plots).cols(1)
    if filename is not None:
        if filename.endswith(".html"):
            panel.panel(layout).save(filename, embed=True)  # type: ignore[attr-defined]
        else:
            hv.save(layout, filename, fmt="png")
    else:
        # Check if we're in a notebook environment and display appropriately
        layout_obj = panel.panel(layout)
        return _display_plot(layout, layout_obj)


def plot_features_stats(
    self,
    filename=None,
):
    """
    Generates vertically stacked density plots for selected feature metrics.
    The distributions are created separately for features with and without MS2 data.
    Metrics include mz, rt, log10(inty), chrom_coherence, chrom_prominence, and chrom_prominence_scaled.
    The plots help to visualize the distribution differences between features that are linked to MS2 spectra and those that are not.

    Parameters:
        filename (str, optional): The output filename. If the filename ends with ".html",
                                    the plot is saved as an interactive HTML file; otherwise,
                                    if provided, the plot is saved as a PNG image. If not provided,
                                    the interactive plot is displayed.

    Returns:
        None
    """
    # Work on a copy of features_df
    feats = self.features_df.clone()
    # Convert to pandas for operations that require pandas functionality
    if hasattr(feats, "to_pandas"):
        feats = feats.to_pandas()

    # Apply log10 transformation to intensity (handling non-positive values)
    feats["inty"] = np.where(feats["inty"] <= 0, np.nan, np.log10(feats["inty"]))

    # Apply log10 transformation to quality (handling non-positive values)
    feats["quality"] = np.where(feats["quality"] <= 0, np.nan, np.log10(feats["quality"]))

    # Separate features based on presence of MS2 data
    feats_with_MS2 = feats[feats["ms2_scans"].notnull()]
    feats_without_MS2 = feats[feats["ms2_scans"].isnull()]

    # Define the specific metrics to plot
    cols_to_plot = [
        "mz",
        "rt",
        "inty",  # Already log10 transformed above
        "rt_delta",
        "quality",  # Already log10 transformed above
        "chrom_coherence",
        "chrom_prominence",
        "chrom_prominence_scaled",
        "chrom_height_scaled",
    ]

    # Ensure an index column is available for plotting
    feats["index"] = feats.index

    density_plots = []
    # Create overlaid distribution plots for each metric
    for col in cols_to_plot:
        # Extract non-null values from both groups
        data_with = feats_with_MS2[col].dropna().values
        data_without = feats_without_MS2[col].dropna().values

        # Create distribution elements - Green for WITH MS2, Red for WITHOUT MS2
        dist_with = hv.Distribution(data_with, label="With MS2").opts(
            color="green",
            alpha=0.6,
        )
        dist_without = hv.Distribution(data_without, label="Without MS2").opts(
            color="red",
            alpha=0.6,
        )

        # Overlay the distributions with a legend and hover tool enabled
        title = col
        if col == "inty":
            title = "log10(inty)"
        elif col == "quality":
            title = "log10(quality)"

        overlay = (dist_with * dist_without).opts(
            title=title,
            show_legend=True,
            tools=["hover"],
        )
        density_plots.append(overlay)

    # Arrange the plots in a grid layout (3 columns for 7 plots)
    layout = hv.Layout(density_plots).cols(3).opts(shared_axes=False)

    # Use consistent save/display behavior
    if filename is not None:
        self._handle_sample_plot_output(layout, filename, "holoviews")
    else:
        # Return the layout directly for notebook display
        return layout


def plot_tic(
    self,
    title=None,
    filename=None,
):
    """
    Plot Total Ion Chromatogram (TIC) by summing MS1 peak intensities at each retention time.

    Uses `self.ms1_df` (Polars DataFrame) and aggregates intensities by `rt` (sum).
    Creates a `Chromatogram` object and uses its `plot()` method to display the result.
    """
    if self.ms1_df is None:
        self.logger.error("No MS1 data available.")
        return

    # Import helper locally to avoid circular imports
    from masster.study.helpers import get_tic

    # Delegate TIC computation to study helper which handles ms1_df and scans_df fallbacks
    try:
        chrom = get_tic(self, label=title)
    except Exception as e:
        self.logger.exception("Failed to compute TIC via helper: %s", e)
        return

    if filename is not None:
        try:
            chrom.plot(width=1000, height=250)
        except Exception:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 3))
            plt.plot(chrom.rt, chrom.inty, color="black")
            plt.xlabel("Retention time (s)")
            plt.ylabel("Intensity")
            if title:
                plt.title(title)
            plt.tight_layout()
            plt.savefig(filename)
        return None

    chrom.plot(width=1000, height=250)
    return None


def plot_bpc(
    self,
    title=None,
    filename=None,
    rt_unit="s",
):
    """
    Plot Base Peak Chromatogram (BPC) using MS1 data.

    Aggregates MS1 points by retention time and selects the maximum intensity (base peak)
    at each time point. Uses `self.ms1_df` (Polars DataFrame) as the source of MS1 peaks.

    Parameters:
        title (str, optional): Plot title.
        filename (str, optional): If provided and ends with `.html` saves an interactive html,
            otherwise saves a png. If None, returns a displayable object for notebooks.
        rt_unit (str, optional): Unit label for the x-axis, default 's' (seconds).

    Returns:
        None or notebook display object (via _display_plot)
    """
    if self.ms1_df is None:
        self.logger.error("No MS1 data available.")
        return

    # Import helper locally to avoid circular imports
    from masster.study.helpers import get_bpc

    # Delegate BPC computation to study helper
    try:
        chrom = get_bpc(self, rt_unit=rt_unit, label=title)
    except Exception as e:
        self.logger.exception("Failed to compute BPC via helper: %s", e)
        return

    # If filename was requested, save a static png using bokeh export via the chromatogram plotting
    if filename is not None:
        # chromatogram.plot() uses bokeh to show the figure; to save as png we rely on holoviews/hv.save
        # Create a bokeh figure by plotting to an offscreen axis
        try:
            # Use Chromatogram.plot to generate and show the figure (will open in notebook/browser)
            chrom.plot(width=1000, height=250)
        except Exception:
            # Last-resort: create a simple matplotlib plot and save
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 3))
            plt.plot(chrom.rt, chrom.inty, color="black")
            plt.xlabel(f"Retention time ({rt_unit})")
            plt.ylabel("Intensity")
            if title:
                plt.title(title)
            plt.tight_layout()
            plt.savefig(filename)
        return None

    # No filename: display using the chromatogram's built-in plotting (bokeh)
    chrom.plot(width=1000, height=250)
    return None
