"""
Wizard module for automated processing of mass spectrometry studies.

This module provides the Wizard class for fully automated processing of MS data
from raw files to final study results, including batch conversion, assembly,
alignment, merging, plotting, and export.

The create_analysis() function allows immediate generation of standalone analysis
scripts without creating a Wizard instance first.

The analyze() function combines create_analysis() with immediate execution of the
generated script for fully automated processing.
"""

from .wizard import Wizard, wizard_def, create_scripts

__all__ = ["Wizard", "wizard_def", "create_scripts"]
