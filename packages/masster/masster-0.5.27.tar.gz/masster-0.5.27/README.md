# MASSter
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/masster)](https://badge.fury.io/py/masster)
[![PyPI version](https://badge.fury.io/py/masster.svg)](https://badge.fury.io/py/masster)

**MASSter** is a Python package for the analysis of mass spectrometry data, tailored for the purpose of metabolomics and LC-MS data processing. It is designed to deal with DDA, and hides functionalities for DIA and ZTScan DIA data. The sample-centric feature detection uses OpenMS. All other functionalities for e.g. centroiding, RT alignment, adduct and isotopomer detection, merging of multiple samples, gap-filling, quantification, etc. were redesigned and engineered to maximize scalability (tested with 3000 LC-MS), speed, quality, and results.

This is a poorly documented, stable branch of the development codebase in use in the Zamboni lab. 

## Prerequisites

**MASSter** reads raw (Thermo), wiff (SCIEX), or mzML data. It's recommended to provide raw, profile data.

## Installation

```bash
pip install masster
```

## Basic usage
### Quick start: use the wizard

```python
import masster
wiz = masster.wizard.create_scripts(
    source=r'..\..\folder_with_raw_data',
    folder=r'..\..folder_to_store_results'
    )
wiz.run()
```

This will run a wizard that should perform all key steps and save the results to the `folder`.

### Basic workflow for analyzing a single sample
```python
import masster
sample = masster.Sample(filename='...') # full path to a *.raw, *.wiff, or *.mzML file
# process
sample.find_features(chrom_fwhm=0.5, noise=50) # for orbitrap data, set noise to 1e5
sample.find_adducts()
sample.find_ms2()

# access data
sample.features_df

# save results
sample.save() # stores to *.sample5, our custom hdf5 format
sample.export_mgf()

# some plots
sample.plot_bpc()
sample.plot_tic()
sample.plot_2d()
sample.plot_features_stats()

# explore methods
dir(study)
```

### Basic Workflow for analyzing LC-MS study with 2-... samples

```python
import masster
# Initialize the Study object with the default folder
study = masster.Study(folder=r'D:\...\mylcms')

# Load data from folder with raw data, here: WIFF
study.add(r'D:\...\...\...\*.wiff')

# Perform retention time correction
study.align(rt_tol=2.0)
study.plot_alignment()
study.plot_bpc()
study.plot_rt_correction()

# Find consensus features
study.merge(min_samples=3)
study.plot_consensus_2d()

# Retrieve missing data for quantification
study.fill()

# Integrate according to consensus metadata
study.integrate()

# export results
study.export_mgf()
study.export_mztab()
study.export_xlsx()
study.export_parquet()

# Save the study to .study5
study.save()

# Some of the plots...
study.plot_samples_pca()
study.plot_samples_umap()
study.plot_samples_2d()
```

### Quick Start with Wizard
MASSter includes a Wizard to automatically process everything:

```python
from masster import Wizard

# Create wizard instance
wiz = Wizard(source="./raw_data", 
             folder="./output", 
             num_cores=8)

# Generate analysis scripts
wiz.create_scripts()

# Test with single file, then run full batch
wiz.test_and_run()
```

### One-Line Command Processing
Or, from the command-line:
```bash
python -c "from masster import Wizard; wiz = Wizard(source='D:/Data/studies/my_study/raw', folder='D:/Data/studies/my_study/masster'); wiz.create_scripts(); wiz.test_and_run()"
```

## License
GNU Affero General Public License v3

See the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
This project uses several third-party libraries, including pyOpenMS which is licensed under the BSD 3-Clause License. For complete information about third-party dependencies and their licenses, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Citation
If you use Masster in your research, please cite this repository.
