"""
ECLSS reference values from NASA/TP-2015-218570/REV2
(Life Support Baseline Values and Assumptions Document)

82 kg reference crewmember, 90 min/day exercise assumption.
All values from specific BVAD tables.

Sub-modules:
    crew          - Metabolic rates and reference CM demographics
    atmosphere    - Cabin atmosphere parameters and safe ranges
    contaminants  - Trace contaminant generation rates
    gas           - Molar masses and gas constant
    recovery      - Water recovery and equipment assumptions
"""

from eclss.constants.crew import *           # noqa: F401,F403
from eclss.constants.atmosphere import *     # noqa: F401,F403
from eclss.constants.contaminants import *   # noqa: F401,F403
from eclss.constants.gas import *            # noqa: F401,F403
from eclss.constants.recovery import *       # noqa: F401,F403
