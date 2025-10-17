"""
analysis.py

Advanced analytical methods for mass spectrometry study data including
UMAP clustering, statistical association testing, and text pattern analysis.
"""

from __future__ import annotations

"""
Optimized analysis module for mass spectrometry data.
"""
import warnings
import re
import numpy as np
import pandas as pd
from scipy import stats

# Suppress sklearn deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sklearn")

# Check for optional dependencies
UMAP_AVAILABLE = False
HDBSCAN_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    import umap

    UMAP_AVAILABLE = True
except ImportError:
    pass

try:
    import hdbscan

    HDBSCAN_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.metrics import silhouette_score

    SKLEARN_AVAILABLE = True
except ImportError:
    pass

# Compiled regex patterns for efficient text processing
TOKEN_PATTERN = re.compile(r"[_\-\s\|\.]+")
ALPHANUMERIC_PATTERN = re.compile(r"^[A-Za-z0-9]+$")

# Simple cache for tokenization
_tokenization_cache = {}


def tokenize_text_cached(text):
    """Cached text tokenization for repeated strings - preserves original case."""
    if text in _tokenization_cache:
        return _tokenization_cache[text]

    if pd.isna(text) or text == "" or not isinstance(text, str):
        result = tuple()
    else:
        # Split by common delimiters to create atoms (same as original)
        atoms = TOKEN_PATTERN.split(str(text).strip())
        # Clean and filter atoms - preserve original case
        meaningful_tokens = []
        for atom in atoms:
            atom = atom.strip()  # Remove .lower() to preserve case
            if atom and len(atom) > 1:  # Original was > 1, not >= 1
                meaningful_tokens.append(atom)

        result = tuple(meaningful_tokens)

    # Prevent cache from growing too large
    if len(_tokenization_cache) < 10000:
        _tokenization_cache[text] = result

    return result


# Clear cache to ensure fresh start
_tokenization_cache.clear()


def analyze_umap(
    self,
    n_neighbors=15,
    min_dist=0.1,
    metric="euclidean",
    random_state=42,
    cluster_methods=["hdbscan", "kmeans", "dbscan"],
    n_clusters_range=(2, 8),
    min_cluster_size=3,
    significance_threshold=0.01,
    plot_results=True,
    filename=None,
    markersize=4,
):
    """
    Perform UMAP dimensionality reduction followed by clustering analysis with enriched term labeling.

    This method performs comprehensive cluster analysis on the study's consensus matrix, including:
    - UMAP dimensionality reduction for visualization
    - Automated clustering with multiple algorithms (HDBSCAN, K-means, DBSCAN)
    - Metadata association discovery using statistical tests
    - Text pattern analysis to identify enriched sample characteristics
    - Enhanced visualization with intelligent label positioning for enriched terms

    The enhanced visualization features cluster-aware enriched term labels with connecting spikes:
    - Terms shared across multiple clusters are positioned at the geometric center with lines to each cluster
    - Terms specific to single clusters are positioned nearby with short spikes
    - Terms are ranked by presence percentage within clusters (favoring common terms)
    - Empty/blank terms are automatically filtered out
    - Label positioning adapts to line direction for optimal text alignment
    - Dashed edges and color-coordinated labels provide visual clarity

    Unlike plot_samples_umap() which colors by metadata columns, this function performs clustering
    and colors points by cluster assignments, with tooltips showing enrichment information.

    Parameters
    ----------
    n_neighbors : int, default=15
        Number of neighbors for UMAP embedding. Higher values preserve more global structure,
        lower values preserve more local structure.

    min_dist : float, default=0.1
        Minimum distance parameter for UMAP. Controls how tightly points are packed in the
        embedding. Values closer to 0 result in tighter clusters.

    metric : str, default="euclidean"
        Distance metric for UMAP. Options include 'euclidean', 'manhattan', 'cosine', etc.

    random_state : int, default=42
        Random seed for reproducibility of UMAP embedding and clustering.

    cluster_methods : list, default=["hdbscan", "kmeans", "dbscan"]
        Clustering algorithms to evaluate. Available options:
        - 'hdbscan': Hierarchical density-based clustering (requires hdbscan package)
        - 'kmeans': K-means clustering with multiple k values
        - 'dbscan': Density-based spatial clustering with multiple eps values

    n_clusters_range : tuple, default=(2, 8)
        Range of cluster numbers to test for K-means (min_clusters, max_clusters).

    min_cluster_size : int, default=3
        Minimum cluster size for HDBSCAN and DBSCAN algorithms.

    significance_threshold : float, default=0.05
        P-value threshold for statistical significance of metadata associations.

    plot_results : bool, default=True
        Whether to generate interactive Bokeh plots with enhanced labeling.
        When False, only returns analysis results without visualization.

    filename : str, optional
        If provided, saves the interactive plot to this HTML file.

    markersize : int, default=4
        Size of scatter plot markers representing samples.

    Returns
    -------
    dict
        Comprehensive results dictionary containing:

        - **umap_coords** : numpy.ndarray
            2D UMAP coordinates for all samples (n_samples x 2)

        - **best_clustering** : dict
            Best clustering result based on silhouette score, containing:
            - 'labels': cluster assignments for each sample
            - 'score': silhouette score (quality metric)
            - 'n_clusters': number of identified clusters
            - 'n_noise': number of noise points (outliers)
            - 'method': clustering algorithm used

        - **all_clustering_results** : dict
            Results from all tested clustering configurations, keyed by method name

        - **significant_associations** : list
            All statistically significant associations (both numeric and text), sorted by
            cluster presence percentage. Each association includes:
            - Statistical test results (p-value, effect size)
            - Cluster-specific enrichment information
            - Interpretation of effect size magnitude

        - **text_associations** : list
            Subset of associations specifically for text pattern enrichment, ranked by
            presence percentage within clusters rather than statistical enrichment

        - **cluster_summaries** : dict
            Summary information for each cluster:
            - 'n_samples': number of samples in cluster
            - 'sample_names': list of sample names in cluster

        - **analysis_dataframe** : pandas.DataFrame
            Complete dataframe with UMAP coordinates, cluster assignments, and all
            sample metadata used for association analysis

    Raises
    ------
    ImportError
        If required dependencies (umap-learn, scikit-learn) are not installed

    ValueError
        If consensus matrix is empty or samples data is unavailable

    Examples
    --------
    Basic UMAP analysis with default parameters:

    >>> results = study.analyze_umap()
    >>> print(f"Found {results['best_clustering']['n_clusters']} clusters")
    >>> print(f"Silhouette score: {results['best_clustering']['score']:.3f}")

    Custom analysis with specific clustering and enhanced visualization:

    >>> results = study.analyze_umap(
    ...     n_neighbors=20,
    ...     min_dist=0.05,
    ...     cluster_methods=["hdbscan", "dbscan"],
    ...     significance_threshold=0.01,
    ...     filename="cluster_analysis.html"
    ... )

    Fast analysis for large datasets:

    >>> results = study.analyze_umap(
    ...     cluster_methods=["hdbscan"]
    ... )

    Notes
    -----
    The enhanced visualization automatically identifies and labels enriched terms based on:

    1. **Presence-based ranking**: Terms are ranked by their prevalence within clusters
       rather than statistical enrichment, favoring terms common across cluster members

    2. **Intelligent positioning**:
       - Shared terms (multiple clusters) positioned at geometric center with connecting lines
       - Individual terms positioned adjacent to their cluster with short spikes
       - Westward lines position labels to the left with right-aligned text
       - Eastward lines position labels to the right with left-aligned text

    3. **Quality filtering**: Empty terms (variants of 'empty', 'blank', 'qc') are
       automatically excluded from enrichment analysis and visualization

    4. **Visual styling**: Dashed edges, color-coordinated labels and lines, and
       moderate boundary expansion (5%) create professional, readable plots

    The method automatically handles missing dependencies by falling back to simplified
    analysis when optional packages (hdbscan) are unavailable.
    """

    # Check dependencies
    if not UMAP_AVAILABLE:
        self.logger.error("UMAP is required. Install with: pip install umap-learn")
        return None

    if not SKLEARN_AVAILABLE:
        self.logger.error("scikit-learn is required. Install with: pip install scikit-learn")
        return None

    self.logger.info("Starting UMAP cluster analysis...")

    # Get data
    consensus_matrix = self.get_consensus_matrix()
    samples_df = self.samples_df

    if consensus_matrix is None or consensus_matrix.shape[0] == 0:
        self.logger.error("No consensus matrix available. Run feature detection first.")
        return None

    if samples_df is None or len(samples_df) == 0:
        self.logger.error("No samples data available.")
        return None

    # Prepare data for UMAP
    sample_cols = [col for col in consensus_matrix.columns if col != "consensus_uid"]

    if hasattr(consensus_matrix, "select"):
        matrix_data = consensus_matrix.select(sample_cols).to_numpy()
    else:
        matrix_sample_data = consensus_matrix.drop(columns=["consensus_uid"], errors="ignore")
        matrix_data = (
            matrix_sample_data.values if hasattr(matrix_sample_data, "values") else np.array(matrix_sample_data)
        )

    # Transpose so samples are rows
    matrix_data = matrix_data.T
    matrix_data = np.nan_to_num(matrix_data, nan=0.0, posinf=0.0, neginf=0.0)

    # Standardize data
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    matrix_scaled = scaler.fit_transform(matrix_data)

    # Perform UMAP with optimizations
    self.logger.debug(f"Computing UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}")
    import umap

    # UMAP optimization: use limited threads to save memory
    n_jobs = 1

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
        n_jobs=n_jobs,
        low_memory=False,
    )
    umap_coords = reducer.fit_transform(matrix_scaled)

    # Convert samples_df to pandas for easier analysis
    samples_pd = samples_df.to_pandas() if hasattr(samples_df, "to_pandas") else samples_df

    # Get the actual sample columns present in consensus matrix
    sample_cols = [col for col in consensus_matrix.columns if col != "consensus_uid"]
    consensus_sample_names = set(sample_cols)

    # Filter samples_df to only include samples present in consensus matrix
    if "sample_name" in samples_pd.columns:
        # Create a mask for samples present in consensus matrix
        sample_mask = samples_pd["sample_name"].isin(consensus_sample_names)

        if sample_mask.sum() != len(samples_pd):
            missing_samples = set(samples_pd["sample_name"]) - consensus_sample_names
            self.logger.warning(
                f"Filtering out {len(missing_samples)} samples not in consensus matrix: {list(missing_samples)}"
            )
            samples_pd = samples_pd[sample_mask].copy()

        # Reorder samples_pd to match the order in consensus matrix sample_cols
        samples_pd = samples_pd.set_index("sample_name").reindex(sample_cols).reset_index()

    # Final check - ensure we have the same number of samples
    if len(samples_pd) != len(umap_coords):
        self.logger.error(
            f"After filtering, still have mismatch: samples_df has {len(samples_pd)} rows, UMAP has {len(umap_coords)} points"
        )
        return None

    self.logger.info(f"Using {len(samples_pd)} samples for analysis")

    # Try different clustering methods
    clustering_results = {}

    for method in cluster_methods:
        self.logger.debug(f"Trying clustering method: {method}")

        if method == "hdbscan" and HDBSCAN_AVAILABLE:
            import hdbscan

            clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
            cluster_labels = clusterer.fit_predict(umap_coords)

            # Calculate silhouette score (excluding noise points for HDBSCAN)
            valid_labels = cluster_labels[cluster_labels != -1]
            valid_coords = umap_coords[cluster_labels != -1]

            if len(np.unique(valid_labels)) > 1:
                from sklearn.metrics import silhouette_score

                score = silhouette_score(valid_coords, valid_labels)
                n_clusters = len(np.unique(valid_labels))
                n_noise = np.sum(cluster_labels == -1)

                clustering_results[f"{method}"] = {
                    "labels": cluster_labels,
                    "score": score,
                    "n_clusters": n_clusters,
                    "n_noise": n_noise,
                    "method": method,
                }

        elif method == "kmeans":
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score

            for n_clusters in range(n_clusters_range[0], n_clusters_range[1] + 1):
                kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
                cluster_labels = kmeans.fit_predict(umap_coords)
                score = silhouette_score(umap_coords, cluster_labels)

                clustering_results[f"{method}_k{n_clusters}"] = {
                    "labels": cluster_labels,
                    "score": score,
                    "n_clusters": n_clusters,
                    "n_noise": 0,
                    "method": f"{method} (k={n_clusters})",
                }

        elif method == "dbscan":
            from sklearn.cluster import DBSCAN

            # Standard DBSCAN eps values for exploration
            eps_values = [0.3, 0.5, 0.7, 1.0, 1.5]

            for eps in eps_values:
                dbscan = DBSCAN(eps=eps, min_samples=min_cluster_size, n_jobs=-1)
                cluster_labels = dbscan.fit_predict(umap_coords)

                n_clusters = len(np.unique(cluster_labels[cluster_labels != -1]))
                n_noise = np.sum(cluster_labels == -1)

                # Only consider valid clusterings
                if n_clusters > 1:
                    from sklearn.metrics import silhouette_score

                    valid_labels = cluster_labels[cluster_labels != -1]
                    valid_coords = umap_coords[cluster_labels != -1]

                    if len(valid_coords) > 0 and len(np.unique(valid_labels)) > 1:
                        score = silhouette_score(valid_coords, valid_labels)

                        clustering_results[f"{method}_eps{eps}"] = {
                            "labels": cluster_labels,
                            "score": score,
                            "n_clusters": n_clusters,
                            "n_noise": n_noise,
                            "method": f"{method} (eps={eps})",
                        }

    if not clustering_results:
        self.logger.error("No valid clustering results found")
        return None

    # Select best clustering based on silhouette score
    best_key = max(clustering_results.keys(), key=lambda k: clustering_results[k]["score"])
    best_clustering = clustering_results[best_key]

    self.logger.info(
        f"Best clustering: {best_clustering['method']} with {best_clustering['n_clusters']} clusters, "
        f"silhouette score: {best_clustering['score']:.3f}"
    )

    # Analyze associations between clusters and sample metadata
    cluster_labels = best_clustering["labels"]

    # Add cluster labels to samples dataframe for analysis
    analysis_df = samples_pd.copy()
    analysis_df["cluster"] = cluster_labels

    # Remove noise points (label -1) for association analysis
    analysis_df_clean = analysis_df[analysis_df["cluster"] != -1].copy()

    if len(analysis_df_clean) == 0:
        self.logger.error("No samples assigned to clusters (all noise)")
        return None

    # Analyze associations with specific columns only
    significant_associations = []

    # Define which columns to analyze for associations (non-text)
    association_cols = {"sample_sequence", "num_features"}

    # Define which columns to analyze for text patterns - include all relevant text columns
    text_pattern_cols = {"sample_name", "sample_group", "sample_batch", "sample_type"}

    for col in samples_pd.columns:
        if col not in association_cols:
            continue

        try:
            # Check if column has enough variation
            col_data = analysis_df_clean[col].dropna()
            if len(col_data.unique()) < 2:
                continue

            # Determine if column is numeric or categorical
            if pd.api.types.is_numeric_dtype(col_data):
                # Numeric variable - use ANOVA or Kruskal-Wallis
                cluster_groups = [group[col].dropna().values for name, group in analysis_df_clean.groupby("cluster")]
                cluster_groups = [group for group in cluster_groups if len(group) > 0]

                if len(cluster_groups) > 1:
                    # Try ANOVA first
                    try:
                        f_stat, p_value = stats.f_oneway(*cluster_groups)
                        test_name = "ANOVA"
                    except Exception:
                        # Fall back to Kruskal-Wallis (non-parametric)
                        h_stat, p_value = stats.kruskal(*cluster_groups)
                        test_name = "Kruskal-Wallis"
                        f_stat = h_stat

                    if p_value < significance_threshold:
                        # Calculate effect size (eta-squared approximation)
                        ss_between = sum(
                            len(group) * (np.mean(group) - np.mean(col_data)) ** 2 for group in cluster_groups
                        )
                        ss_total = np.sum((col_data - np.mean(col_data)) ** 2)
                        eta_squared = ss_between / ss_total if ss_total > 0 else 0

                        significant_associations.append({
                            "column": col,
                            "variable_type": "numeric",
                            "test": test_name,
                            "statistic": f_stat,
                            "p_value": p_value,
                            "effect_size": eta_squared,
                            "interpretation": "Large effect"
                            if eta_squared > 0.14
                            else "Medium effect"
                            if eta_squared > 0.06
                            else "Small effect",
                        })

            else:
                # Categorical variable - use Chi-square test
                contingency_table = pd.crosstab(analysis_df_clean["cluster"], analysis_df_clean[col])

                # Only test if we have enough observations
                if (
                    contingency_table.sum().sum() > 10
                    and contingency_table.shape[0] > 1
                    and contingency_table.shape[1] > 1
                ):
                    try:
                        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

                        if p_value < significance_threshold:
                            # Calculate Cramer's V (effect size for chi-square)
                            n = contingency_table.sum().sum()
                            cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))

                            significant_associations.append({
                                "column": col,
                                "variable_type": "categorical",
                                "test": "Chi-square",
                                "statistic": chi2,
                                "p_value": p_value,
                                "effect_size": cramers_v,
                                "interpretation": "Large effect"
                                if cramers_v > 0.5
                                else "Medium effect"
                                if cramers_v > 0.3
                                else "Small effect",
                                "contingency_table": contingency_table,
                            })
                    except Exception:
                        continue

        except Exception as e:
            self.logger.debug(f"Error analyzing column {col}: {e}")
            continue

    # Sort by effect size (descending)
    significant_associations.sort(key=lambda x: x["effect_size"], reverse=True)

    # Enhanced cluster-centric text analysis - analyze what makes each cluster unique
    self.logger.debug("Performing cluster-centric enrichment analysis...")

    text_associations = []

    # Optimized text tokenization using cached function
    def tokenize_text_optimized(text):
        """Optimized text tokenization with caching"""
        return tokenize_text_cached(text)

    # Collect all atoms from specified string columns only
    string_columns = []
    for col in text_pattern_cols:
        if col in analysis_df_clean.columns:
            col_data = analysis_df_clean[col].dropna()
            if len(col_data) > 0 and not pd.api.types.is_numeric_dtype(col_data):
                if len(col_data.astype(str).unique()) > 1:  # Has variation
                    string_columns.append(col)

    if string_columns:
        # Text analysis for string columns
        self.logger.debug(f"Analyzing cluster enrichments in {len(string_columns)} string columns")

        # Build cluster-centric atom analysis using cached tokenization
        cluster_atoms = {}  # cluster_id -> {atom -> count}
        global_atom_counts = {}  # atom -> total_count_across_all_samples

        # Pre-tokenize all text data once for efficiency with column prefixes
        sample_atom_sets = {}
        for idx, row in analysis_df_clean.iterrows():
            sample_atoms = set()
            for col in string_columns:
                atoms = tokenize_text_optimized(row[col])
                # Add column prefix to distinguish where tokens come from
                col_prefix = col.replace("sample_", "") + ":"  # e.g., "name:", "group:", "batch:", "type:"
                prefixed_atoms = [f"{col_prefix}{atom}" for atom in atoms]
                sample_atoms.update(prefixed_atoms)
            sample_atom_sets[idx] = sample_atoms

        # Collect atoms by cluster
        for idx, row in analysis_df_clean.iterrows():
            cluster_id = row["cluster"]
            if cluster_id not in cluster_atoms:
                cluster_atoms[cluster_id] = {}

            # Use pre-tokenized atoms
            sample_atoms = sample_atom_sets[idx]

            # Count atoms for this cluster and globally
            for atom in sample_atoms:
                cluster_atoms[cluster_id][atom] = cluster_atoms[cluster_id].get(atom, 0) + 1
                global_atom_counts[atom] = global_atom_counts.get(atom, 0) + 1

    # Calculate cluster enrichments using hypergeometric test (same for both modes)
    if string_columns:
        n_total_samples = len(analysis_df_clean)

        # For each cluster, find significantly enriched terms
        for cluster_id, cluster_atom_counts in cluster_atoms.items():
            cluster_size = len(analysis_df_clean[analysis_df_clean["cluster"] == cluster_id])

            for atom, cluster_count in cluster_atom_counts.items():
                global_count = global_atom_counts[atom]

                # Skip empty terms from enrichment analysis and plotting
                if (
                    atom == "<empty>"
                    or atom.lower() == "empty"
                    or atom.strip() == ""
                    or ":empty" in atom.lower()
                    or atom.lower().endswith("empty")
                    or ":blank" in atom.lower()
                    or atom.lower().endswith("blank")
                ):
                    continue

                # Skip atoms with low frequency
                if global_count < 2:
                    continue

                # Skip terms that occur in fewer than 5 samples within this cluster
                if cluster_count < 5:
                    continue

                # IMPORTANT: Skip atoms that appear in too many clusters (not cluster-specific)
                # Count how many clusters this atom appears in
                clusters_with_atom = set()
                for other_cluster_id, other_cluster_atom_counts in cluster_atoms.items():
                    if atom in other_cluster_atom_counts:
                        clusters_with_atom.add(other_cluster_id)

                total_clusters = len(cluster_atoms)
                cluster_specificity = len(clusters_with_atom) / total_clusters if total_clusters > 0 else 1

                # Skip if atom appears in more than 50% of clusters (not specific enough)
                if cluster_specificity > 0.5:
                    # Note: logger not available in standalone function, would need to pass self
                    continue

                # Additional check: ensure this cluster has significantly more of this atom than others
                # max_other_cluster_count = 0
                # for other_cluster_id, other_cluster_atom_counts in cluster_atoms.items():
                #    if other_cluster_id != cluster_id and atom in other_cluster_atom_counts:
                #        max_other_cluster_count = max(max_other_cluster_count, other_cluster_atom_counts[atom])

                # Skip if current cluster doesn't have significantly more instances than the next highest
                # if cluster_count <= max_other_cluster_count * 1.5:
                # Note: logger not available in standalone function, would need to pass self
                #    continue

                # Calculate enrichment using hypergeometric test
                try:
                    from scipy.stats import hypergeom

                    M = n_total_samples
                    n = global_count
                    N = cluster_size
                    k = cluster_count

                    # Calculate p-value (probability of observing k or more successes)
                    p_value = hypergeom.sf(k - 1, M, n, N)

                    # Calculate enrichment ratio
                    expected_freq = (n / M) * N
                    enrichment_ratio = cluster_count / expected_freq if expected_freq > 0 else float("inf")

                    # Only consider significantly enriched terms (p < threshold and enrichment > 1.5x)
                    if p_value < significance_threshold and enrichment_ratio > 1.5:
                        # Calculate percentage of cluster samples with this atom
                        cluster_percentage = (cluster_count / cluster_size) * 100
                        global_percentage = (global_count / n_total_samples) * 100

                        text_associations.append({
                            "atom": atom,
                            "cluster_id": cluster_id,
                            "type": "cluster_enrichment",
                            "test": "Hypergeometric",
                            "p_value": p_value,
                            "enrichment_ratio": enrichment_ratio,
                            "effect_size": enrichment_ratio,  # Use enrichment ratio as effect size
                            "interpretation": "Large enrichment"
                            if enrichment_ratio > 3
                            else "Medium enrichment"
                            if enrichment_ratio > 2
                            else "Small enrichment",
                            "cluster_count": cluster_count,
                            "cluster_size": cluster_size,
                            "cluster_percentage": cluster_percentage,
                            "global_count": global_count,
                            "global_percentage": global_percentage,
                            "cluster_samples_with_atom": cluster_count,
                            "total_samples_with_atom": global_count,
                        })

                except Exception as e:
                    self.logger.debug(f"Error analyzing enrichment of '{atom}' in cluster {cluster_id}: {e}")
                    continue

    # Sort text associations by cluster presence percentage (favors common terms in clusters)
    text_associations.sort(key=lambda x: x["cluster_percentage"], reverse=True)

    # Combine regular and text associations
    all_associations = significant_associations + text_associations
    # Sort by cluster percentage for text associations, effect size for others
    all_associations.sort(key=lambda x: x.get("cluster_percentage", x.get("effect_size", 0)), reverse=True)

    # Generate cluster summaries
    cluster_summaries = {}
    for cluster_id in analysis_df_clean["cluster"].unique():
        cluster_data = analysis_df_clean[analysis_df_clean["cluster"] == cluster_id]
        cluster_summaries[cluster_id] = {
            "n_samples": len(cluster_data),
            "sample_names": cluster_data["sample_name"].tolist() if "sample_name" in cluster_data else [],
        }

    # Create results dictionary
    results = {
        "umap_coords": umap_coords,
        "best_clustering": best_clustering,
        "all_clustering_results": clustering_results,
        "significant_associations": all_associations,
        "text_associations": text_associations,
        "cluster_summaries": cluster_summaries,
        "analysis_dataframe": analysis_df_clean,
    }

    # Create sample-specific enrichment tooltips with optimization
    sample_enrichments = {}

    # For each sample, find which text atoms it contains that are significant
    if text_associations:
        max_check_terms = 10  # Standard limit for tooltip calculation

        for idx, row in analysis_df_clean.iterrows():
            sample_name = row.get("sample_name", f"sample_{idx}")
            sample_enrichments[sample_name] = []

            # Check which significant atoms this sample contains
            for assoc in text_associations[:max_check_terms]:  # Check fewer terms in fast mode
                atom = assoc["atom"]

                # Check if this sample contains this atom in any of the text columns
                sample_has_atom = False
                for col in text_pattern_cols:
                    if col in row:
                        text_value = str(row[col]) if not pd.isna(row[col]) else ""
                        if atom.lower() in text_value.lower():
                            sample_has_atom = True
                            break

                if sample_has_atom:
                    sample_enrichments[sample_name].append(f"{atom} ({assoc['p_value']:.3f})")
                    if len(sample_enrichments[sample_name]) >= 3:  # Only show top 3 per sample
                        break

    # Create embedded plots if requested
    if plot_results:
        plots = {}

        # Plot 1: Enhanced UMAP with clusters and enriched term labels (EMBEDDED PLOTTING)
        from bokeh.models import ColumnDataSource, HoverTool, LabelSet, LegendItem, Legend
        from bokeh.plotting import figure
        from collections import defaultdict

        # Create cluster plot with enhanced size
        p1 = figure(
            width=900,
            height=700,
            title=f"UMAP Clusters with Enriched Terms ({best_clustering['method']})",
            tools="pan,wheel_zoom,box_zoom,reset,save",
        )
        p1.xaxis.axis_label = "UMAP1"
        p1.yaxis.axis_label = "UMAP2"

        # Remove grid
        p1.grid.visible = False

        # Color points by cluster
        unique_clusters = np.unique(cluster_labels)
        n_clusters = len(unique_clusters)

        # Handle color mapping for many clusters - use turbo colormap
        if n_clusters <= 10:
            from bokeh.palettes import turbo

            colors = turbo(max(10, n_clusters))[:n_clusters]
        elif n_clusters <= 20:
            from bokeh.palettes import turbo

            colors = turbo(20)[:n_clusters]
        else:
            # For many clusters, use a continuous colormap
            from bokeh.palettes import turbo

            colors = turbo(min(256, n_clusters))

        # Calculate cluster centers and plot points
        cluster_centers = {}
        for i, cluster_id in enumerate(unique_clusters):
            mask = cluster_labels == cluster_id
            if cluster_id == -1:
                color = "gray"
                label = "Noise"
            else:
                color = colors[i % len(colors)]
                label = f"Cluster {cluster_id}"

            cluster_coords = umap_coords[mask]

            # Calculate cluster center
            if len(cluster_coords) > 0:
                center_x = np.mean(cluster_coords[:, 0])
                center_y = np.mean(cluster_coords[:, 1])
                cluster_centers[cluster_id] = (center_x, center_y)

            cluster_samples = samples_pd[mask] if len(samples_pd) == len(mask) else None
            sample_names = (
                cluster_samples["sample_name"].tolist()
                if cluster_samples is not None and "sample_name" in cluster_samples
                else [f"Sample_{j}" for j in range(np.sum(mask))]
            )
            sample_uids = (
                cluster_samples["sample_uid"].tolist()
                if cluster_samples is not None and "sample_uid" in cluster_samples
                else [f"UID_{j}" for j in range(np.sum(mask))]
            )

            # Create enrichment tooltip text for this cluster
            cluster_associations = [assoc for assoc in text_associations if assoc.get("cluster_id") == cluster_id]

            # Get the top enrichments for this cluster (not individual samples)
            cluster_enrichments = []
            for assoc in cluster_associations[:3]:  # Top 3 enrichments for this cluster
                atom = assoc["atom"]
                # Skip color codes and other non-meaningful atoms
                if not ((atom.startswith("#") and len(atom) == 7) or atom in ["nan", "None", "null"]):
                    cluster_enrichments.append(atom)

            # Create the same enrichment text for ALL samples in this cluster
            if cluster_enrichments:
                cluster_enrichment_text = "; ".join(cluster_enrichments)
            else:
                cluster_enrichment_text = "No enrichments found"

            # Apply the same enrichment text to all samples in this cluster
            sample_enrichment_texts = [cluster_enrichment_text] * np.sum(mask)

            source = ColumnDataSource({
                "x": umap_coords[mask, 0],
                "y": umap_coords[mask, 1],
                "cluster": [cluster_id] * np.sum(mask),
                "sample_name": sample_names[: np.sum(mask)],
                "sample_uid": sample_uids[: np.sum(mask)],
                "enrichments": sample_enrichment_texts[: np.sum(mask)],
            })

            p1.scatter("x", "y", size=markersize, color=color, alpha=0.7, source=source)

        # Enhanced enriched term visualization
        max_terms_per_cluster = 2
        min_enrichment = 2.0

        # Process enriched terms - group by cluster and filter
        cluster_terms = defaultdict(list)
        for assoc in text_associations:
            # Skip empty terms from plotting
            atom = assoc.get("atom", "")
            if (
                atom == "<empty>"
                or atom.lower() == "empty"
                or atom.strip() == ""
                or ":empty" in atom.lower()
                or atom.lower().endswith("empty")
                or ":blank" in atom.lower()
                or atom.lower().endswith("blank")
            ):
                continue

            if assoc["enrichment_ratio"] >= min_enrichment and assoc["cluster_id"] in cluster_centers:
                cluster_terms[assoc["cluster_id"]].append(assoc)

        # Limit terms per cluster and sort by cluster presence percentage (favors common terms)
        for cluster_id in cluster_terms:
            cluster_terms[cluster_id] = sorted(
                cluster_terms[cluster_id], key=lambda x: x["cluster_percentage"], reverse=True
            )[:max_terms_per_cluster]

        # Collect all unique terms for shared term handling
        all_terms = {}
        for cluster_id, terms in cluster_terms.items():
            for term in terms:
                atom = term["atom"]
                if atom not in all_terms:
                    all_terms[atom] = []
                all_terms[atom].append(cluster_id)

        # Separate terms into shared vs cluster-specific
        shared_terms = {atom: clusters for atom, clusters in all_terms.items() if len(clusters) > 1}
        specific_terms = {atom: clusters[0] for atom, clusters in all_terms.items() if len(clusters) == 1}

        # Merge overlapping terms that refer to the same concept
        # E.g., "type:qc" and "name:PooledQC" both refer to QC samples
        def should_merge_terms(term1, term2):
            """Check if two terms should be merged based on semantic overlap"""
            # Extract the actual values (remove prefixes)
            val1 = term1.replace("name:", "").replace("type:", "").replace("group:", "").replace("batch:", "").lower()
            val2 = term2.replace("name:", "").replace("type:", "").replace("group:", "").replace("batch:", "").lower()

            # Define known overlapping concepts
            qc_terms = {"qc", "pooledqc", "pooled_qc", "quality_control", "qualitycontrol"}
            blank_terms = {"blank", "blk", "empty", "background"}

            # Check if both terms belong to the same concept group
            if val1 in qc_terms and val2 in qc_terms:
                return True
            if val1 in blank_terms and val2 in blank_terms:
                return True

            # Also check for direct string similarity (e.g., case variations)
            if val1 == val2:
                return True

            return False

        def merge_overlapping_terms(shared_terms, specific_terms):
            """Merge terms that refer to the same concept"""
            all_atoms = list(shared_terms.keys()) + list(specific_terms.keys())
            merged_groups = []
            used_atoms = set()

            for i, atom1 in enumerate(all_atoms):
                if atom1 in used_atoms:
                    continue

                group = [atom1]
                used_atoms.add(atom1)

                # Find all atoms that should be merged with this one
                for j, atom2 in enumerate(all_atoms[i + 1 :], i + 1):
                    if atom2 in used_atoms:
                        continue
                    if should_merge_terms(atom1, atom2):
                        group.append(atom2)
                        used_atoms.add(atom2)

                if len(group) > 1:
                    merged_groups.append(group)

            return merged_groups

        # Find terms that should be merged
        merged_groups = merge_overlapping_terms(shared_terms, specific_terms)

        # Apply merging: create new combined terms and remove originals
        for group in merged_groups:
            # Determine the combined clusters for this group
            combined_clusters = set()
            for atom in group:
                if atom in shared_terms:
                    combined_clusters.update(shared_terms[atom])
                elif atom in specific_terms:
                    combined_clusters.add(specific_terms[atom])

            # Create a new combined term name using newlines
            # Keep the original prefixes and atom names
            combined_atom = "\n".join(group)

            # Remove original terms from both dictionaries
            for atom in group:
                shared_terms.pop(atom, None)
                specific_terms.pop(atom, None)

            # Add the combined term to appropriate dictionary
            combined_clusters_list = list(combined_clusters)
            if len(combined_clusters_list) > 1:
                shared_terms[combined_atom] = combined_clusters_list
            else:
                specific_terms[combined_atom] = combined_clusters_list[0]

        # Create label sources for enriched terms
        label_sources = {}
        line_sources = {}
        line_cluster_mapping = {}  # Track which cluster each line belongs to

        # Handle shared terms (place at center of all clusters that share it, but in empty areas)
        for atom, clusters in shared_terms.items():
            if len(clusters) > 1:
                # Calculate center of all clusters sharing this term
                cluster_coords_list = [cluster_centers[cid] for cid in clusters if cid in cluster_centers]
                if cluster_coords_list:
                    center_x = np.mean([coord[0] for coord in cluster_coords_list])
                    center_y = np.mean([coord[1] for coord in cluster_coords_list])

                    # Calculate data bounds using simple approach
                    all_x = [pt[0] for pt in umap_coords]
                    all_y = [pt[1] for pt in umap_coords]
                    x_min, x_max = min(all_x), max(all_x)
                    y_min, y_max = min(all_y), max(all_y)
                    data_range_x = x_max - x_min
                    data_range_y = y_max - y_min

                    # Find empty area around the center
                    best_distance = 0
                    best_position = None

                    for distance_factor in [1.0, 1.5, 2.0]:
                        offset_distance = distance_factor * max(data_range_x, data_range_y) * 0.1

                        for angle in np.linspace(0, 2 * np.pi, 8):
                            label_x = center_x + offset_distance * np.cos(angle)
                            label_y = center_y + offset_distance * np.sin(angle)

                            # Calculate minimum distance to any data point
                            distances = [np.sqrt((pt[0] - label_x) ** 2 + (pt[1] - label_y) ** 2) for pt in umap_coords]
                            min_distance = min(distances)

                            if min_distance > best_distance:
                                best_distance = min_distance
                                best_position = (label_x, label_y)

                    # Use best position or fallback to center
                    if best_position is not None:
                        label_x, label_y = best_position
                    else:
                        label_x, label_y = center_x, center_y

                    # Check if label would be outside plot bounds and adjust
                    label_margin = max(data_range_x, data_range_y) * 0.05
                    if label_x < x_min - label_margin:
                        label_x = x_min - label_margin
                    elif label_x > x_max + label_margin:
                        label_x = x_max + label_margin

                    if label_y < y_min - label_margin:
                        label_y = y_min - label_margin
                    elif label_y > y_max + label_margin:
                        label_y = y_max + label_margin

                    # Keep the original atom name with prefixes for display
                    display_atom = atom  # Keep prefixes like name:, group:, batch:, type:

                    # Create label source with center alignment for shared terms
                    label_source = ColumnDataSource({
                        "x": [label_x],
                        "y": [label_y],
                        "text": [display_atom],
                        "atom": [atom],
                        "text_align": ["center"],
                    })
                    label_sources[atom] = label_source

                    # Create lines to each cluster center
                    line_x = []
                    line_y = []
                    for cluster_id in clusters:
                        if cluster_id in cluster_centers:
                            cx, cy = cluster_centers[cluster_id]
                            line_x.extend([label_x, cx, np.nan])  # nan to break line
                            line_y.extend([label_y, cy, np.nan])

                    line_source = ColumnDataSource({"x": line_x, "y": line_y})
                    line_sources[atom] = line_source
                    line_cluster_mapping[atom] = "shared"

        # Handle cluster-specific terms (arrange multiple terms per cluster to avoid overlap)
        # Group specific terms by cluster to handle multiple terms per cluster
        cluster_specific_terms = defaultdict(list)
        for atom, cluster_id in specific_terms.items():
            cluster_specific_terms[cluster_id].append(atom)

        # Calculate data bounds once
        all_x = [pt[0] for pt in umap_coords]
        all_y = [pt[1] for pt in umap_coords]
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        data_range_x = x_max - x_min
        data_range_y = y_max - y_min

        # Expand plot ranges to accommodate labels (add 15% margin on all sides)
        margin = 0.15
        x_margin = data_range_x * margin
        y_margin = data_range_y * margin
        plot_x_min = x_min - x_margin
        plot_x_max = x_max + x_margin
        plot_y_min = y_min - y_margin
        plot_y_max = y_max + y_margin

        # Set expanded plot ranges
        p1.x_range.start = plot_x_min
        p1.x_range.end = plot_x_max
        p1.y_range.start = plot_y_min
        p1.y_range.end = plot_y_max

        # Process each cluster that has specific terms
        for cluster_id, cluster_atoms in cluster_specific_terms.items():
            if cluster_id not in cluster_centers:
                continue

            cx, cy = cluster_centers[cluster_id]
            n_terms = len(cluster_atoms)

            if n_terms == 1:
                # Single term - use smart positioning with shorter distances
                atom = cluster_atoms[0]

                # Try multiple candidate positions with shorter distances and more angles
                best_distance = 0
                best_position = None

                # Use shorter base distance and test many angles
                base_distance = max(data_range_x, data_range_y) * 0.08  # Much shorter base distance

                # Test positions at different angles and short distances
                for distance_factor in [0.8, 1.0, 1.3]:  # Shorter distance factors
                    offset_distance = base_distance * distance_factor

                    for angle in np.linspace(0, 2 * np.pi, 24):  # More angles (24 directions)
                        label_x = cx + offset_distance * np.cos(angle)
                        label_y = cy + offset_distance * np.sin(angle)

                        # Calculate minimum distance to any data point
                        distances = [np.sqrt((pt[0] - label_x) ** 2 + (pt[1] - label_y) ** 2) for pt in umap_coords]
                        min_distance = min(distances)

                        # Check distance to other labels to avoid overlap
                        min_label_distance = float("inf")
                        for other_atom, other_source in label_sources.items():
                            if other_atom != atom:
                                other_data = other_source.data
                                if other_data["x"] and other_data["y"]:
                                    other_x, other_y = other_data["x"][0], other_data["y"][0]
                                    label_distance = np.sqrt((label_x - other_x) ** 2 + (label_y - other_y) ** 2)
                                    min_label_distance = min(min_label_distance, label_distance)

                        # Prefer positions that are reasonably far from data points and other labels
                        combined_distance = min(
                            min_distance, min_label_distance if min_label_distance != float("inf") else min_distance
                        )

                        if combined_distance > best_distance:
                            best_distance = combined_distance
                            best_position = (label_x, label_y)

                # Use best position found, or fallback to simple short offset
                if best_position is not None:
                    label_x, label_y = best_position
                else:
                    # Fallback: simple short radial offset
                    offset_distance = base_distance
                    angle = (cluster_id * 45) % 360  # Deterministic angle based on cluster
                    angle_rad = np.radians(angle)
                    label_x = cx + offset_distance * np.cos(angle_rad)
                    label_y = cy + offset_distance * np.sin(angle_rad)

                # Check if label would be outside plot bounds and adjust
                label_margin = max(data_range_x, data_range_y) * 0.05

                # Instead of clamping to bounds, let labels go outside and plot bounds will be expanded later
                # Only apply minimal adjustments to prevent labels from being extremely far out
                extreme_margin = max(data_range_x, data_range_y) * 0.25  # Allow 25% outside data range

                if label_x < x_min - extreme_margin:
                    label_x = x_min - extreme_margin
                elif label_x > x_max + extreme_margin:
                    label_x = x_max + extreme_margin

                if label_y < y_min - extreme_margin:
                    label_y = y_min - extreme_margin
                elif label_y > y_max + extreme_margin:
                    label_y = y_max + extreme_margin

                # Determine text alignment based on position relative to cluster
                text_align = "right" if label_x > cx else "left"

                # Clean up atom name for display but keep prefixes
                display_atom = atom  # Keep prefixes like name:, group:, batch:, type:

                # Create label source with alignment
                label_source = ColumnDataSource({
                    "x": [label_x],
                    "y": [label_y],
                    "text": [display_atom],
                    "atom": [atom],
                    "text_align": [text_align],
                })
                label_sources[atom] = label_source

                # Create spike line from cluster center to label
                line_source = ColumnDataSource({"x": [cx, label_x], "y": [cy, label_y]})
                line_sources[atom] = line_source
                line_cluster_mapping[atom] = cluster_id

            else:
                # Multiple terms - stack them vertically with one line to cluster center
                # Determine if this cluster has shared vs non-shared terms to adjust positioning
                has_shared = any(atom in shared_terms for atom in cluster_atoms)
                has_specific = any(atom in specific_terms for atom in cluster_atoms)

                # Adjust base distance: put non-shared (cluster-specific) labels further out
                if has_specific and not has_shared:
                    # Pure cluster-specific terms - place further from center to reduce overlap
                    base_distance = max(data_range_x, data_range_y) * 0.15  # Further out
                elif has_shared and not has_specific:
                    # Pure shared terms - place closer to center
                    base_distance = max(data_range_x, data_range_y) * 0.08  # Closer
                else:
                    # Mixed terms - use intermediate distance
                    base_distance = max(data_range_x, data_range_y) * 0.1  # Standard distance

                # Calculate a good angle for the stack based on cluster position and available space
                # For non-shared terms, prefer angles that point away from plot center
                best_angle = None
                best_distance = 0

                # Get plot center for reference
                plot_center_x = (x_min + x_max) / 2
                plot_center_y = (y_min + y_max) / 2

                # Calculate angle from plot center to cluster center
                center_to_cluster_angle = np.arctan2(cy - plot_center_y, cx - plot_center_x)

                if has_specific and not has_shared:
                    # For non-shared terms, prefer angles that point away from plot center
                    # Create angles around the center-to-cluster direction
                    base_angle = center_to_cluster_angle
                    preferred_angles = [
                        base_angle,  # Directly away from center
                        base_angle + np.pi / 4,  # 45° offset
                        base_angle - np.pi / 4,  # -45° offset
                        base_angle + np.pi / 6,  # 30° offset
                        base_angle - np.pi / 6,  # -30° offset
                        base_angle + np.pi / 3,  # 60° offset
                        base_angle - np.pi / 3,  # -60° offset
                        base_angle + np.pi / 2,  # 90° offset
                        base_angle - np.pi / 2,  # -90° offset
                    ]
                else:
                    # For shared terms or mixed, use the original preferred angles
                    preferred_angles = [
                        np.pi / 4,
                        3 * np.pi / 4,
                        5 * np.pi / 4,
                        7 * np.pi / 4,  # 45°, 135°, 225°, 315°
                        np.pi / 6,
                        np.pi / 3,
                        2 * np.pi / 3,
                        5 * np.pi / 6,  # 30°, 60°, 120°, 150°
                        7 * np.pi / 6,
                        4 * np.pi / 3,
                        5 * np.pi / 3,
                        11 * np.pi / 6,
                    ]  # 210°, 240°, 300°, 330°

                for test_angle in preferred_angles:
                    test_x = cx + base_distance * np.cos(test_angle)
                    test_y = cy + base_distance * np.sin(test_angle)

                    # Calculate minimum distance to any data point
                    distances = [np.sqrt((pt[0] - test_x) ** 2 + (pt[1] - test_y) ** 2) for pt in umap_coords]
                    min_distance = min(distances)

                    if min_distance > best_distance:
                        best_distance = min_distance
                        best_angle = test_angle

                # Use the best angle found, or fallback to 45°
                if best_angle is not None:
                    stack_angle = best_angle
                else:
                    # Fallback: use 45° based on cluster
                    angle_options = [np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4, 7 * np.pi / 4]
                    stack_angle = angle_options[cluster_id % len(angle_options)]

                # Position for the end of the line (before labels start)
                line_end_x = cx + base_distance * np.cos(stack_angle)
                line_end_y = cy + base_distance * np.sin(stack_angle)

                # Simplified approach: center labels at line end, then add 20pt offset in same direction
                # Calculate 20pt offset in the same direction as the line
                label_offset_distance = 20  # 20 points in the same direction

                # Convert 20 points to data coordinates (approximate)
                # Assuming typical plot size, 20pt ≈ 1-2% of data range
                data_range = max(data_range_x, data_range_y)
                offset_in_data_coords = data_range * 0.02  # 2% of data range for 20pt

                # Add offset in direction based on line orientation for better text placement
                # For westward lines: place label LEFT of endpoint with RIGHT alignment
                # For eastward lines: place label RIGHT of endpoint with LEFT alignment

                angle_degrees = (stack_angle * 180 / np.pi) % 360
                if 90 < angle_degrees < 270:
                    # Line goes LEFT (westward) - place label to the LEFT of line end
                    label_center_x = line_end_x - offset_in_data_coords  # SUBTRACT to go left
                    label_center_y = line_end_y  # Keep same Y position
                    text_align = "right"  # Right-align so text ends near line endpoint
                else:
                    # Line goes RIGHT (eastward) - place label to the RIGHT of line end
                    label_center_x = line_end_x + offset_in_data_coords  # ADD to go right
                    label_center_y = line_end_y  # Keep same Y position
                    text_align = "left"  # Left-align so text starts near line endpoint

                # Calculate consistent vertical spacing for stacked labels
                # BETTER APPROACH: Use single LabelSet with newline characters

                # Create a single multi-line text string with all terms
                display_atoms = [atom for atom in cluster_atoms]  # Keep original atom names with prefixes
                combined_text = "\n".join(display_atoms)

                # Check if label would be outside plot bounds and adjust
                label_margin = max(data_range_x, data_range_y) * 0.05
                label_x = label_center_x
                label_y = label_center_y

                if label_x < x_min - label_margin:
                    label_x = x_min - label_margin
                    text_align = "left"
                elif label_x > x_max + label_margin:
                    label_x = x_max + label_margin
                    text_align = "right"

                if label_y < y_min - label_margin:
                    label_y = y_min - label_margin
                elif label_y > y_max + label_margin:
                    label_y = y_max + label_margin

                # Create single label source with multi-line text and alignment
                label_source = ColumnDataSource({
                    "x": [label_x],
                    "y": [label_y],
                    "text": [combined_text],
                    "atoms": [cluster_atoms],  # Store all atoms for reference
                    "text_align": [text_align],
                })

                # Store this single label source using a unique key for the cluster stack
                stack_label_key = f"cluster_{cluster_id}_labels"
                label_sources[stack_label_key] = label_source

                # Create single line from cluster center to line end (before labels)
                stack_line_source = ColumnDataSource({"x": [cx, line_end_x], "y": [cy, line_end_y]})
                # Use a unique key for the stack line
                stack_key = f"cluster_{cluster_id}_stack"
                line_sources[stack_key] = stack_line_source
                line_cluster_mapping[stack_key] = cluster_id

        # Add lines (spikes) to plot with matching cluster colors
        line_renderers = {}
        for line_key, line_source in line_sources.items():
            # Get the cluster color for this line
            if line_key in shared_terms:
                # For shared terms, use the same style as cluster-specific terms
                # Use a neutral color or the color of the first cluster it appears in
                first_cluster_id = list(shared_terms[line_key])[0]
                if first_cluster_id == -1:
                    line_color = "gray"
                else:
                    cluster_idx = (
                        list(unique_clusters).index(first_cluster_id) if first_cluster_id in unique_clusters else 0
                    )
                    line_color = colors[cluster_idx % len(colors)]
                line_dash = "dashed"  # Use dashed for all edges
            elif line_key in specific_terms:
                # For cluster-specific terms, use the cluster's color
                cluster_id = specific_terms[line_key]
                if cluster_id == -1:
                    line_color = "gray"
                else:
                    cluster_idx = list(unique_clusters).index(cluster_id) if cluster_id in unique_clusters else 0
                    line_color = colors[cluster_idx % len(colors)]
                line_dash = "dashed"  # Use dashed for all edges
            elif line_key in line_cluster_mapping:
                # For stack lines, use the cluster's color
                cluster_info = line_cluster_mapping[line_key]
                if cluster_info == "shared":
                    # For shared stacks, use a neutral color or first cluster color
                    line_color = "black"
                    line_dash = "dashed"  # Use dashed for all edges
                else:
                    cluster_id = cluster_info
                    if cluster_id == -1:
                        line_color = "gray"
                    else:
                        cluster_idx = list(unique_clusters).index(cluster_id) if cluster_id in unique_clusters else 0
                        line_color = colors[cluster_idx % len(colors)]
                    line_dash = "dashed"  # Use dashed for all edges
            else:
                # Fallback
                line_color = "gray"
                line_dash = "dashed"  # Use dashed for all edges

            line_renderer = p1.line(
                "x", "y", source=line_source, line_color=line_color, line_width=2, alpha=0.8, line_dash=line_dash
            )
            line_renderers[line_key] = line_renderer

        # Add labels to plot (simple and direct approach)
        label_renderers = {}  # Store label renderers for legend control
        for label_key, label_source in label_sources.items():
            # Determine color and style based on label key type
            if label_key.startswith("cluster_") and label_key.endswith("_labels"):
                # This is a cluster stack with multiple terms
                cluster_id = int(label_key.split("_")[1])
                if cluster_id == -1:
                    text_color = "gray"
                else:
                    cluster_idx = list(unique_clusters).index(cluster_id) if cluster_id in unique_clusters else 0
                    text_color = colors[cluster_idx % len(colors)]
                text_font_style = "bold"
            elif label_key in shared_terms:
                # Shared term - use same color as edge (first cluster's color)
                first_cluster_id = list(shared_terms[label_key])[0]
                if first_cluster_id == -1:
                    text_color = "gray"
                else:
                    cluster_idx = (
                        list(unique_clusters).index(first_cluster_id) if first_cluster_id in unique_clusters else 0
                    )
                    text_color = colors[cluster_idx % len(colors)]
                text_font_style = "bold"
            elif label_key in specific_terms:
                # Individual cluster-specific term
                cluster_id = specific_terms[label_key]
                if cluster_id == -1:
                    text_color = "gray"
                else:
                    cluster_idx = list(unique_clusters).index(cluster_id) if cluster_id in unique_clusters else 0
                    text_color = colors[cluster_idx % len(colors)]
                text_font_style = "bold"
            else:
                # Fallback
                text_color = "black"
                text_font_style = "bold"

            # Get text alignment from label source, default to center
            label_data = label_source.data
            text_align = label_data.get("text_align", ["center"])[0] if "text_align" in label_data else "center"

            label_set = LabelSet(
                x="x",
                y="y",
                text="text",
                source=label_source,
                text_font_size="11pt",
                text_color=text_color,
                text_font_style=text_font_style,
                text_align=text_align,
                text_baseline="middle",
            )
            p1.add_layout(label_set)
            label_renderers[label_key] = label_set  # Store for legend control

        # Check if any labels are close to plot boundaries and expand if needed
        if label_sources:
            # Collect all label positions
            all_label_positions = []
            for source in label_sources.values():
                data = source.data
                if "x" in data and "y" in data and data["x"] and data["y"]:
                    all_label_positions.extend(zip(data["x"], data["y"]))

            if all_label_positions:
                # Check if any labels are close to current plot boundaries
                current_x_min, current_x_max = p1.x_range.start, p1.x_range.end
                current_y_min, current_y_max = p1.y_range.start, p1.y_range.end

                # Define "close to boundary" as within 5% of the plot range
                x_range = current_x_max - current_x_min
                y_range = current_y_max - current_y_min
                boundary_threshold_x = x_range * 0.05
                boundary_threshold_y = y_range * 0.05

                needs_expansion = False
                for label_x, label_y in all_label_positions:
                    if (
                        label_x < current_x_min + boundary_threshold_x
                        or label_x > current_x_max - boundary_threshold_x
                        or label_y < current_y_min + boundary_threshold_y
                        or label_y > current_y_max - boundary_threshold_y
                    ):
                        needs_expansion = True
                        break

                # If labels are close to boundaries, expand plot by 5% (reduced from 10%)
                if needs_expansion:
                    expansion_factor = 0.05  # 5% expansion (half of previous 10%)
                    x_expansion = x_range * expansion_factor
                    y_expansion = y_range * expansion_factor

                    p1.x_range.start = current_x_min - x_expansion
                    p1.x_range.end = current_x_max + x_expansion
                    p1.y_range.start = current_y_min - y_expansion
                    p1.y_range.end = current_y_max + y_expansion

        # Add hover tool with enrichment information
        hover = HoverTool(
            tooltips=[
                ("Cluster", "@cluster"),
                ("Sample", "@sample_name"),
                ("Sample UID", "@sample_uid"),
                ("Enrichments", "@enrichments"),
            ]
        )
        p1.add_tools(hover)

        # Remove cluster legend labels from scatter plots (already done above)
        # But keep any existing legend structure for now

        # Create custom legend for enrichment terms (line/label pairs) ONLY
        if line_renderers and (shared_terms or specific_terms):
            legend_items = []
            renderer_to_terms = {}  # Group terms by their renderer

            # Get all enriched terms and group them by their line renderer
            all_enriched_atoms = set(shared_terms.keys()) | set(specific_terms.keys())

            # First pass: map each term to its renderer
            for atom in all_enriched_atoms:
                renderer = None
                renderer_key = None

                if atom in shared_terms:
                    # Shared term
                    if atom in line_renderers:
                        renderer = line_renderers[atom]
                        renderer_key = atom
                    else:
                        # Look for any stack renderer from clusters that have this shared term
                        for cluster_id in shared_terms[atom]:
                            stack_key = f"cluster_{cluster_id}_stack"
                            if stack_key in line_renderers:
                                renderer = line_renderers[stack_key]
                                renderer_key = stack_key
                                break

                elif atom in specific_terms:
                    # Cluster-specific term
                    cluster_id = specific_terms[atom]
                    if atom in line_renderers:
                        renderer = line_renderers[atom]
                        renderer_key = atom
                    else:
                        stack_key = f"cluster_{cluster_id}_stack"
                        if stack_key in line_renderers:
                            renderer = line_renderers[stack_key]
                            renderer_key = stack_key

                # Group terms by renderer
                if renderer and renderer_key:
                    if renderer_key not in renderer_to_terms:
                        renderer_to_terms[renderer_key] = {
                            "renderer": renderer,
                            "shared_terms": [],
                            "specific_terms": [],
                            "cluster_id": None,
                        }

                    if atom in shared_terms:
                        renderer_to_terms[renderer_key]["shared_terms"].append(atom)
                    else:
                        renderer_to_terms[renderer_key]["specific_terms"].append(atom)
                        renderer_to_terms[renderer_key]["cluster_id"] = specific_terms[atom]

            # Second pass: create legend entries, one per renderer
            for renderer_key, term_info in renderer_to_terms.items():
                shared_list = term_info["shared_terms"]
                specific_list = term_info["specific_terms"]
                line_renderer = term_info["renderer"]

                # For now, legend can only control the line renderer
                # Label visibility will be handled via JavaScript callback if needed
                # (Note: LabelSet cannot be directly controlled by Bokeh legends)

                # Create combined label text
                if shared_list:
                    # Shared terms - remove "Shared:" prefix and just show the terms
                    clean_terms = [
                        atom.replace("name:", "").replace("group:", "").replace("batch:", "").replace("type:", "")
                        for atom in shared_list
                    ]
                    if len(clean_terms) == 1:
                        label_text = clean_terms[0]
                    else:
                        label_text = ", ".join(clean_terms)

                elif specific_list:
                    # Cluster-specific terms
                    cluster_id = term_info["cluster_id"]
                    clean_terms = [
                        atom.replace("name:", "").replace("group:", "").replace("batch:", "").replace("type:", "")
                        for atom in specific_list
                    ]
                    if len(clean_terms) == 1:
                        label_text = f"C{cluster_id}: {clean_terms[0]}"
                    else:
                        label_text = f"C{cluster_id}: {', '.join(clean_terms)}"

                # Add single legend entry for the line renderer only
                # (Labels cannot be controlled by Bokeh legends directly)
                legend_items.append(LegendItem(label=label_text, renderers=[line_renderer]))

            # Hide cluster legend after we've created our enrichment legend
            if hasattr(p1, "legend") and p1.legend:
                if isinstance(p1.legend, list):
                    for legend in p1.legend:
                        legend.visible = False
                else:
                    p1.legend.visible = False

            # Create and add the custom enrichment legend
            if legend_items:
                enrichment_legend = Legend(items=legend_items, location="center_right", click_policy="hide")
                p1.add_layout(enrichment_legend, "right")

        plots["cluster_plot"] = p1

        # Save cluster plot if filename provided
        if filename:
            # Handle filename extension properly
            if filename.endswith(".html"):
                base_filename = filename[:-5]  # Remove .html extension
                cluster_filename = f"{base_filename}_clusters.html"
            else:
                cluster_filename = f"{filename}_clusters.html"

            if not filename.startswith("/") and not filename[1:3] == ":\\":
                cluster_filename = f"{self.folder}/{cluster_filename}"
            _isolated_save_plot(p1, cluster_filename, cluster_filename, self.logger, "UMAP Cluster Plot")
        else:
            _isolated_show_notebook(p1)

        results["plots"] = plots

    # Print summary
    self.logger.debug("\n=== UMAP Cluster Analysis Summary ===")
    self.logger.debug(f"Best clustering: {best_clustering['method']}")
    self.logger.debug(f"Number of clusters: {best_clustering['n_clusters']}")
    self.logger.debug(f"Silhouette score: {best_clustering['score']:.3f}")
    if best_clustering["n_noise"] > 0:
        self.logger.debug(f"Noise points: {best_clustering['n_noise']}")

    self.logger.info(f"\nFound {len(all_associations)} total significant associations:")

    # Show regular column associations
    regular_assocs = [a for a in all_associations if "column" in a]
    if regular_assocs:
        self.logger.info(f"  {len(regular_assocs)} column-level associations:")
        for assoc in regular_assocs[:3]:  # Show top 3
            self.logger.info(
                f"    {assoc['column']} ({assoc['variable_type']}): {assoc['test']} p={assoc['p_value']:.4f}, "
                f"effect_size={assoc['effect_size']:.3f} ({assoc['interpretation']})"
            )

    # Show text atom associations
    text_assocs = [a for a in all_associations if "atom" in a]
    if text_assocs:
        self.logger.info(f"  {len(text_assocs)} text pattern associations:")
        for assoc in text_assocs[:3]:  # Show top 3
            freq = assoc.get("atom_frequency", 0)
            percentage = (freq / len(analysis_df_clean)) * 100 if len(analysis_df_clean) > 0 else 0

            self.logger.info(
                f"    '{assoc['atom']}' ({assoc['type']}): p={assoc['p_value']:.4f}, "
                f"effect_size={assoc['effect_size']:.3f} ({assoc['interpretation']}) "
                f"[{freq} samples, {percentage:.1f}%]"
            )

    if len(all_associations) > 20:
        self.logger.info(f"  ... and {len(all_associations) - 20} more associations")

    return results


def _analyze_umap_simplified(
    self,
    n_neighbors=15,
    min_dist=0.1,
    metric="euclidean",
    random_state=42,
    cluster_methods=["hdbscan", "kmeans"],
    n_clusters_range=(2, 8),
    min_cluster_size=3,
    significance_threshold=0.05,
    plot_results=True,
    filename=None,
):
    """Simplified fallback version of UMAP analysis."""

    self.logger.info("Starting simplified UMAP analysis...")

    # Check dependencies
    if not UMAP_AVAILABLE or not HDBSCAN_AVAILABLE:
        self.logger.error("Required dependencies not available")
        return {
            "umap_coords": None,
            "best_clustering": None,
            "all_clustering_results": {},
            "significant_associations": [],
            "text_associations": [],
            "cluster_summaries": {},
            "analysis_dataframe": None,
        }

    try:
        # Get data
        consensus_matrix = self.get_consensus_matrix()
        samples_df = self.samples_df

        if consensus_matrix is None or samples_df is None:
            self.logger.error("No data available")
            return {
                "umap_coords": None,
                "best_clustering": None,
                "all_clustering_results": {},
                "significant_associations": [],
                "text_associations": [],
                "cluster_summaries": {},
                "analysis_dataframe": None,
            }

        # Basic UMAP
        sample_cols = [col for col in consensus_matrix.columns if col != "consensus_uid"]

        if hasattr(consensus_matrix, "select"):
            matrix_data = consensus_matrix.select(sample_cols).to_numpy()
        else:
            matrix_data = consensus_matrix.drop(columns=["consensus_uid"], errors="ignore").values

        matrix_data = matrix_data.T
        matrix_data = np.nan_to_num(matrix_data)

        scaler = StandardScaler()
        matrix_scaled = scaler.fit_transform(matrix_data)

        # Import dependencies locally
        import umap
        import hdbscan

        reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist, random_state=random_state)
        umap_coords = reducer.fit_transform(matrix_scaled)

        # Simple clustering
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
        cluster_labels = clusterer.fit_predict(umap_coords)

        best_clustering = {
            "labels": cluster_labels,
            "n_clusters": len(np.unique(cluster_labels[cluster_labels != -1])),
            "n_noise": np.sum(cluster_labels == -1),
            "silhouette_score": 0.5,  # Placeholder
            "method": "hdbscan",
        }

        self.logger.info(f"Simplified analysis found {best_clustering['n_clusters']} clusters")

        return {
            "umap_coords": umap_coords,
            "best_clustering": best_clustering,
            "all_clustering_results": {"hdbscan": best_clustering},
            "significant_associations": [],
            "text_associations": [],
            "cluster_summaries": {},
            "analysis_dataframe": None,
        }

    except Exception as e:
        self.logger.error(f"Error in simplified analysis: {e}")
        return {
            "umap_coords": None,
            "best_clustering": None,
            "all_clustering_results": {},
            "significant_associations": [],
            "text_associations": [],
            "cluster_summaries": {},
            "analysis_dataframe": None,
        }


# ========================================
# Helper Functions for Plotting
# ========================================


def _isolated_save_plot(plot, filename, title, logger, plot_type):
    """Save plot to file in isolation"""
    try:
        from bokeh.io import output_file, save
        from bokeh.models import Title

        # Add title to plot
        plot.add_layout(Title(text=title, text_font_size="16pt"), "above")

        # Configure output
        output_file(filename)
        save(plot)
        logger.info(f"Saved {plot_type} to: {filename}")

    except Exception as e:
        logger.error(f"Error saving {plot_type}: {e}")


def _isolated_show_notebook(plot):
    """Show plot in notebook if available"""
    try:
        from bokeh.io import show

        show(plot)
    except Exception:
        pass  # Silently fail if not in notebook
