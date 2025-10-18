"""
Time series processing module for photovoltaic data

Provides utilities for resampling, aggregating, and analyzing time series data:
- TimeSeriesResampler: Resample time series to different frequencies
- TimeSeriesAggregator: Aggregate time series data with various methods
- TimeSeriesAnalyzer: Analyze time series patterns and statistics
"""

from typing import Optional, Union, List, Dict, Any

import pandas as pd
import numpy as np

from pvdata.utils.exceptions import ValidationError
from pvdata.utils.decorators import handle_errors, log_execution, measure_time
from pvdata.utils.logger import get_logger

logger = get_logger(__name__)


class TimeSeriesResampler:
    """
    Resample time series data to different frequencies

    Features:
    - Flexible frequency resampling (1min, 5min, 1H, 1D, etc.)
    - Multiple aggregation methods (mean, sum, min, max, first, last)
    - Missing data handling
    - Timezone support

    Examples:
        >>> resampler = TimeSeriesResampler()
        >>> df_hourly = resampler.resample(df, freq="1H", method="mean")

        >>> # Resample to daily with custom aggregation
        >>> df_daily = resampler.resample(
        ...     df,
        ...     freq="1D",
        ...     agg_methods={"power": "sum", "voltage": "mean"}
        ... )
    """

    def __init__(self, timestamp_column: str = "timestamp"):
        """
        Initialize TimeSeriesResampler

        Args:
            timestamp_column: Name of timestamp column (default: "timestamp")
        """
        self.timestamp_column = timestamp_column

    @measure_time()
    @log_execution(level="DEBUG")
    @handle_errors(ValidationError, reraise=True)
    def resample(
        self,
        df: pd.DataFrame,
        freq: str,
        method: str = "mean",
        agg_methods: Optional[Dict[str, Union[str, List[str]]]] = None,
        fill_method: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Resample time series to specified frequency

        Args:
            df: Input DataFrame with timestamp column
            freq: Target frequency (e.g., "1min", "5min", "1H", "1D")
            method: Default aggregation method ("mean", "sum", "min", "max", "first", "last")
            agg_methods: Custom aggregation methods per column
            fill_method: Method to fill missing values ("ffill", "bfill", "interpolate")

        Returns:
            Resampled DataFrame

        Examples:
            >>> resampler = TimeSeriesResampler()
            >>> df_hourly = resampler.resample(df, "1H", method="mean")

            >>> # Custom aggregation per column
            >>> df_resampled = resampler.resample(
            ...     df,
            ...     "15min",
            ...     agg_methods={"power": "sum", "temperature": "mean"}
            ... )
        """
        # Validate input
        if self.timestamp_column not in df.columns:
            raise ValidationError(
                f"Timestamp column '{self.timestamp_column}' not found in DataFrame"
            )

        if df.empty:
            raise ValidationError("Cannot resample empty DataFrame")

        logger.info(
            f"Resampling from {len(df)} rows to frequency '{freq}' " f"using method '{method}'"
        )

        # Create a copy and set timestamp as index
        df_resampled = df.copy()
        df_resampled[self.timestamp_column] = pd.to_datetime(df_resampled[self.timestamp_column])
        df_resampled = df_resampled.set_index(self.timestamp_column)

        # Perform resampling
        if agg_methods:
            # Custom aggregation per column
            result = df_resampled.resample(freq).agg(agg_methods)
        else:
            # Default aggregation for all columns
            result = df_resampled.resample(freq).agg(method)

        # Handle missing values
        if fill_method:
            if fill_method == "ffill":
                result = result.fillna(method="ffill")
            elif fill_method == "bfill":
                result = result.fillna(method="bfill")
            elif fill_method == "interpolate":
                result = result.interpolate(method="linear")
            else:
                logger.warning(f"Unknown fill_method: {fill_method}, skipping fill")

        # Reset index to convert timestamp back to column
        result = result.reset_index()

        logger.info(f"Resampled to {len(result)} rows")

        return result

    def resample_multiple(
        self,
        df: pd.DataFrame,
        frequencies: List[str],
        method: str = "mean",
    ) -> Dict[str, pd.DataFrame]:
        """
        Resample to multiple frequencies at once

        Args:
            df: Input DataFrame
            frequencies: List of target frequencies
            method: Aggregation method

        Returns:
            Dictionary mapping frequency to resampled DataFrame

        Examples:
            >>> resampler = TimeSeriesResampler()
            >>> results = resampler.resample_multiple(
            ...     df,
            ...     ["5min", "15min", "1H", "1D"]
            ... )
            >>> df_hourly = results["1H"]
        """
        results = {}

        for freq in frequencies:
            logger.info(f"Resampling to {freq}")
            results[freq] = self.resample(df, freq, method=method)

        return results


class TimeSeriesAggregator:
    """
    Aggregate time series data with various methods

    Features:
    - Time-based aggregation (hourly, daily, monthly)
    - Custom time windows
    - Rolling aggregations
    - Group-by aggregations

    Examples:
        >>> aggregator = TimeSeriesAggregator()
        >>> daily_stats = aggregator.aggregate_daily(df)

        >>> # Rolling window aggregation
        >>> rolling = aggregator.rolling_aggregate(df, window="1H", method="mean")
    """

    def __init__(self, timestamp_column: str = "timestamp"):
        """
        Initialize TimeSeriesAggregator

        Args:
            timestamp_column: Name of timestamp column
        """
        self.timestamp_column = timestamp_column

    @measure_time()
    @log_execution(level="DEBUG")
    def aggregate_daily(
        self,
        df: pd.DataFrame,
        agg_methods: Optional[Dict[str, Union[str, List[str]]]] = None,
    ) -> pd.DataFrame:
        """
        Aggregate data by day

        Args:
            df: Input DataFrame with timestamp
            agg_methods: Aggregation methods per column

        Returns:
            Daily aggregated DataFrame

        Examples:
            >>> aggregator = TimeSeriesAggregator()
            >>> daily = aggregator.aggregate_daily(df)

            >>> # Custom aggregation
            >>> daily = aggregator.aggregate_daily(
            ...     df,
            ...     agg_methods={"power": ["sum", "mean", "max"]}
            ... )
        """
        df_copy = df.copy()
        df_copy[self.timestamp_column] = pd.to_datetime(df_copy[self.timestamp_column])
        df_copy["date"] = df_copy[self.timestamp_column].dt.date

        if agg_methods:
            result = df_copy.groupby("date").agg(agg_methods)
        else:
            # Default: mean for numeric columns
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            result = df_copy.groupby("date")[numeric_cols].mean()

        result = result.reset_index()
        logger.info(f"Aggregated to {len(result)} daily records")

        return result

    @measure_time()
    @log_execution(level="DEBUG")
    def aggregate_monthly(
        self,
        df: pd.DataFrame,
        agg_methods: Optional[Dict[str, Union[str, List[str]]]] = None,
    ) -> pd.DataFrame:
        """
        Aggregate data by month

        Args:
            df: Input DataFrame
            agg_methods: Aggregation methods per column

        Returns:
            Monthly aggregated DataFrame
        """
        df_copy = df.copy()
        df_copy[self.timestamp_column] = pd.to_datetime(df_copy[self.timestamp_column])
        df_copy["year_month"] = df_copy[self.timestamp_column].dt.to_period("M")

        if agg_methods:
            result = df_copy.groupby("year_month").agg(agg_methods)
        else:
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            result = df_copy.groupby("year_month")[numeric_cols].mean()

        result = result.reset_index()
        result["year_month"] = result["year_month"].astype(str)
        logger.info(f"Aggregated to {len(result)} monthly records")

        return result

    @measure_time()
    @log_execution(level="DEBUG")
    def rolling_aggregate(
        self,
        df: pd.DataFrame,
        window: Union[str, int],
        method: str = "mean",
        min_periods: Optional[int] = None,
        center: bool = False,
    ) -> pd.DataFrame:
        """
        Apply rolling window aggregation

        Args:
            df: Input DataFrame
            window: Window size (e.g., "1H" for time-based, 10 for count-based)
            method: Aggregation method
            min_periods: Minimum periods required
            center: Whether to center the window

        Returns:
            DataFrame with rolling aggregation

        Examples:
            >>> aggregator = TimeSeriesAggregator()
            >>> # 1-hour rolling mean
            >>> rolling = aggregator.rolling_aggregate(df, "1H", "mean")

            >>> # 10-point rolling max
            >>> rolling = aggregator.rolling_aggregate(df, 10, "max")
        """
        df_copy = df.copy()
        df_copy[self.timestamp_column] = pd.to_datetime(df_copy[self.timestamp_column])
        df_copy = df_copy.set_index(self.timestamp_column)

        # Get numeric columns
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns

        # Apply rolling aggregation
        if isinstance(window, str):
            # Time-based window
            rolling = df_copy[numeric_cols].rolling(
                window=window, min_periods=min_periods, center=center
            )
        else:
            # Count-based window
            rolling = df_copy[numeric_cols].rolling(
                window=window, min_periods=min_periods, center=center
            )

        # Apply aggregation method
        if method == "mean":
            result = rolling.mean()
        elif method == "sum":
            result = rolling.sum()
        elif method == "min":
            result = rolling.min()
        elif method == "max":
            result = rolling.max()
        elif method == "std":
            result = rolling.std()
        else:
            raise ValueError(f"Unknown aggregation method: {method}")

        result = result.reset_index()
        logger.info(f"Applied rolling {method} with window {window}")

        return result


class TimeSeriesAnalyzer:
    """
    Analyze time series patterns and statistics

    Features:
    - Missing data detection
    - Data quality checks
    - Frequency detection
    - Gap analysis
    - Pattern detection

    Examples:
        >>> analyzer = TimeSeriesAnalyzer()
        >>> stats = analyzer.analyze(df)
        >>> print(f"Missing: {stats['missing_rate']:.1f}%")

        >>> # Detect gaps
        >>> gaps = analyzer.find_gaps(df, expected_freq="5min")
    """

    def __init__(self, timestamp_column: str = "timestamp"):
        """
        Initialize TimeSeriesAnalyzer

        Args:
            timestamp_column: Name of timestamp column
        """
        self.timestamp_column = timestamp_column

    @measure_time()
    @log_execution(level="DEBUG")
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive time series analysis

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with analysis results

        Examples:
            >>> analyzer = TimeSeriesAnalyzer()
            >>> stats = analyzer.analyze(df)
            >>> print(stats)
            {
                'total_rows': 10000,
                'time_range': ('2024-01-01', '2024-01-31'),
                'duration_days': 30,
                'missing_rate': 5.2,
                'detected_frequency': '5min',
                ...
            }
        """
        if self.timestamp_column not in df.columns:
            raise ValidationError(f"Timestamp column '{self.timestamp_column}' not found")

        df_copy = df.copy()
        df_copy[self.timestamp_column] = pd.to_datetime(df_copy[self.timestamp_column])

        # Basic statistics
        total_rows = len(df_copy)
        time_min = df_copy[self.timestamp_column].min()
        time_max = df_copy[self.timestamp_column].max()
        duration = time_max - time_min

        # Detect frequency
        time_diffs = df_copy[self.timestamp_column].diff().dropna()
        most_common_diff = time_diffs.mode()[0] if len(time_diffs) > 0 else None
        detected_freq = self._timedelta_to_freq_string(most_common_diff)

        # Missing data analysis
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
        total_missing = df_copy[numeric_cols].isna().sum().sum()
        total_values = len(df_copy) * len(numeric_cols)
        missing_rate = (total_missing / total_values * 100) if total_values > 0 else 0

        result = {
            "total_rows": total_rows,
            "time_range": (str(time_min), str(time_max)),
            "duration_days": duration.days + duration.seconds / 86400,
            "detected_frequency": detected_freq,
            "missing_values": int(total_missing),
            "missing_rate": float(missing_rate),
            "numeric_columns": len(numeric_cols),
        }

        logger.info(f"Analysis complete: {total_rows} rows, {missing_rate:.1f}% missing")

        return result

    def find_gaps(
        self,
        df: pd.DataFrame,
        expected_freq: str,
        min_gap_size: int = 1,
    ) -> pd.DataFrame:
        """
        Find gaps in time series data

        Args:
            df: Input DataFrame
            expected_freq: Expected frequency (e.g., "5min", "1H")
            min_gap_size: Minimum gap size to report (in multiples of expected_freq)

        Returns:
            DataFrame with gap information

        Examples:
            >>> analyzer = TimeSeriesAnalyzer()
            >>> gaps = analyzer.find_gaps(df, expected_freq="5min")
            >>> print(f"Found {len(gaps)} gaps")
        """
        df_copy = df.copy()
        df_copy[self.timestamp_column] = pd.to_datetime(df_copy[self.timestamp_column])
        df_sorted = df_copy.sort_values(self.timestamp_column)

        # Calculate time differences
        time_diffs = df_sorted[self.timestamp_column].diff()

        # Convert expected frequency to timedelta
        expected_delta = pd.Timedelta(expected_freq)

        # Find gaps larger than expected
        gap_threshold = expected_delta * (1 + min_gap_size)
        gaps_mask = time_diffs > gap_threshold

        # Extract gap information
        gaps = []
        for idx in df_sorted[gaps_mask].index:
            prev_idx = df_sorted.index.get_loc(idx) - 1
            if prev_idx >= 0:
                prev_time = df_sorted.iloc[prev_idx][self.timestamp_column]
                curr_time = df_sorted.loc[idx, self.timestamp_column]
                gap_size = (curr_time - prev_time) / expected_delta

                gaps.append(
                    {
                        "gap_start": prev_time,
                        "gap_end": curr_time,
                        "gap_duration": curr_time - prev_time,
                        "gap_size_intervals": gap_size,
                    }
                )

        result = pd.DataFrame(gaps)
        logger.info(f"Found {len(result)} gaps larger than {min_gap_size} intervals")

        return result

    def _timedelta_to_freq_string(self, td: Optional[pd.Timedelta]) -> Optional[str]:
        """Convert timedelta to frequency string"""
        if td is None or pd.isna(td):
            return None

        total_seconds = td.total_seconds()

        if total_seconds < 60:
            return f"{int(total_seconds)}s"
        elif total_seconds < 3600:
            return f"{int(total_seconds / 60)}min"
        elif total_seconds < 86400:
            return f"{int(total_seconds / 3600)}H"
        else:
            return f"{int(total_seconds / 86400)}D"
