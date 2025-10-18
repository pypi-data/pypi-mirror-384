"""
pvdata.processing - Data processing operations

This module provides time-series and spatial data processing capabilities.
"""

# Time series processing (TASK_07)
from pvdata.processing.timeseries import (
    TimeSeriesResampler,
    TimeSeriesAggregator,
    TimeSeriesAnalyzer,
)

# To be implemented in TASK_08, TASK_09
# from pvdata.processing.spatial import aggregate_spatial
# from pvdata.processing.quality import check_quality

__all__ = [
    # Time series
    "TimeSeriesResampler",
    "TimeSeriesAggregator",
    "TimeSeriesAnalyzer",
    # To be added
    # 'aggregate_spatial',
    # 'check_quality',
]
