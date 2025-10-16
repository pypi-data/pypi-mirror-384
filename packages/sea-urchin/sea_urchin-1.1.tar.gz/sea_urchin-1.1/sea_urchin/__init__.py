"""
Sea Urchin is a set of Python tools to post-process trajectories from AIMD, MD and metadynamics simulations. The pycolvars module easily reads and analyze metadynamics runs. The Sea Urchin module can extract and analyze local structure around atomic species. The outcome of the algorithm is a quantitative mapping of the multiple coordination environments present in the MD data.

Details on the Sea Urchin algorithm are presented in the paper:
Roncoroni, F., Sanz-Matias, A., Sundararaman, S., & Prendergast, D. Unsupervised learning of representative local atomic arrangements in molecular dynamics data. Phys. Chem. Chem. Phys.,25, 13741-13754 (2023) (https://doi.org/10.1039/D3CP00525A);
arXiv preprint arXiv:2302.01465.

Applications of the Sea Urchin algorithm:
Sanz-Matias, A., Roncoroni, F., Sundararaman, S., & Prendergast, D. Ca-dimers, solvent layering, and dominant electrochemically active species in Ca(BH4_44​)2_22​ in THF Nature Communications 15, 1397 (2024) (https://doi.org/10.1038/s41467-024-45672-7)
arXiv preprint [https://arxiv.org/pdf/2303.08261]

"""

import sys
import os
import warnings

# Check for Python version
if sys.version_info[0] == 2:
    raise ImportError('Please run with Python3. This is Python2.')

# Package info
__version__ = '1.1'
__date__ = "15 Oct. 2025"
__author__ = "Materials Theory Group"

# Check for optional dependencies
def _check_optional_dependencies():
    """Check availability of optional dependencies."""
    # Check for IRA availability
    _IRA_AVAILABLE = False
    try:
        # First try direct import
        import ira_mod
        _IRA_AVAILABLE = True
    except ImportError:
        # Try to find IRA in common locations
        ira_path = os.environ.get('IRA_PATH')

        if not ira_path:
            from os.path import expanduser
            home = expanduser("~")

            default_locations = [
                home + '/Software/IterativeRotationsAssignments/interface',
                '/usr/local/IterativeRotationsAssignments/interface',
                './IterativeRotationsAssignments/interface',
            ]

            for location in default_locations:
                if os.path.exists(location):
                    ira_path = location
                    break

        # If IRA path is found, add it to sys.path and try importing
        if ira_path and os.path.exists(ira_path):
            if ira_path not in sys.path:
                sys.path.insert(0, ira_path)
            try:
                import ira_mod
                _IRA_AVAILABLE = True
            except ImportError:
                pass

    return _IRA_AVAILABLE

# Initialize optional dependency flags
_IRA_AVAILABLE = _check_optional_dependencies()

# Optional: Inform users about missing optional dependencies
if not _IRA_AVAILABLE:
    warnings.warn(
        "IRA (Iterative Rotations Assignments) not found. "
        "Some advanced alignment features may not be available. "
        "See installation documentation for setup instructions.",
        UserWarning,
        stacklevel=2
    )

# Import and expose the SeaUrchin class
from .core import SeaUrchin

__all__ = ["SeaUrchin"]
