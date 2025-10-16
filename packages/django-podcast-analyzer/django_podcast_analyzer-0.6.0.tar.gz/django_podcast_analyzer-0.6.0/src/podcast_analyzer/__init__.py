# __init__.py
#
# Copyright (c) 2024 - 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Django Podcast Analyzer"""

__version__ = "0.6.0"

from podcast_analyzer.exceptions import (
    FeedFetchError,
    FeedParseError,
    ImageRetrievalError,
)

__all__ = ["FeedFetchError", "FeedParseError", "ImageRetrievalError"]
