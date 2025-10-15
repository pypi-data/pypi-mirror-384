"""Statistical tensorization techniques.

Tensorization techniques map lower-order data such as matrices to higher-order arrays,
which enables the exploitation of underlying tensor structure. Several statistical
tensorization methods are defined here.
"""

from .statistics import cum3 as cum3
from .statistics import cum4 as cum4
from .statistics import dcov as dcov
from .statistics import scov as scov
from .statistics import stcum4 as stcum4
from .statistics import xcum4 as xcum4
