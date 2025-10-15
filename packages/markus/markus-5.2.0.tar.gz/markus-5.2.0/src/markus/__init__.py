# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from importlib.metadata import (
    version as importlib_version,
    PackageNotFoundError,
)

from markus.main import configure, get_metrics  # noqa

try:
    __version__ = importlib_version("markus")
except PackageNotFoundError:
    __version__ = "unknown"


INCR = "incr"
GAUGE = "gauge"
TIMING = "timing"
HISTOGRAM = "histogram"

__all__ = ["configure", "get_metrics", "INCR", "GAUGE", "TIMING", "HISTOGRAM"]
