"""
Tests for time series processing module
"""

import pytest
import pandas as pd
import numpy as np

from pvdata.processing import (
    TimeSeriesResampler,
    TimeSeriesAggregator,
    TimeSeriesAnalyzer,
)
from pvdata.utils.exceptions import ValidationError


@pytest.fixture
def sample_timeseries_df():
    """Create sample time series data for testing"""
    start_time = pd.Timestamp("2024-01-01 00:00:00")
    timestamps = pd.date_range(start_time, periods=288, freq="5min")

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "power": np.random.randint(0, 5000, 288),
            "voltage": np.random.uniform(220, 240, 288),
            "temperature": np.random.uniform(15, 35, 288),
        }
    )

    # Add some missing values
    df.loc[50:52, "power"] = np.nan
    df.loc[100, "voltage"] = np.nan

    return df


@pytest.fixture
def hourly_timeseries_df():
    """Create hourly time series data"""
    timestamps = pd.date_range("2024-01-01", periods=24, freq="1H")

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "power": np.random.randint(1000, 5000, 24),
            "voltage": np.random.uniform(220, 240, 24),
        }
    )

    return df


class TestTimeSeriesResampler:
    """Tests for TimeSeriesResampler"""

    def test_resampler_initialization(self):
        """Test resampler initialization"""
        resampler = TimeSeriesResampler()
        assert resampler.timestamp_column == "timestamp"

        resampler = TimeSeriesResampler(timestamp_column="time")
        assert resampler.timestamp_column == "time"

    def test_resample_to_hourly(self, sample_timeseries_df):
        """Test resampling to hourly frequency"""
        resampler = TimeSeriesResampler()
        df_hourly = resampler.resample(sample_timeseries_df, freq="1H", method="mean")

        # 288 5-min intervals = 24 hours
        assert len(df_hourly) == 24
        assert "timestamp" in df_hourly.columns
        assert all(col in df_hourly.columns for col in ["power", "voltage", "temperature"])

    def test_resample_with_sum(self, sample_timeseries_df):
        """Test resampling with sum aggregation"""
        resampler = TimeSeriesResampler()
        df_hourly = resampler.resample(sample_timeseries_df, freq="1H", method="sum")

        assert len(df_hourly) == 24
        # Sum should be larger than mean
        assert df_hourly["power"].iloc[0] > 0

    def test_resample_custom_aggregation(self, sample_timeseries_df):
        """Test resampling with custom aggregation methods"""
        resampler = TimeSeriesResampler()
        df_resampled = resampler.resample(
            sample_timeseries_df,
            freq="15min",
            agg_methods={"power": "sum", "voltage": "mean", "temperature": "max"},
        )

        # 288 / 3 = 96 15-minute intervals
        assert len(df_resampled) == 96

    def test_resample_with_fill(self, sample_timeseries_df):
        """Test resampling with missing value filling"""
        resampler = TimeSeriesResampler()
        df_filled = resampler.resample(
            sample_timeseries_df, freq="1H", method="mean", fill_method="ffill"
        )

        # Check that result has no NaN (or fewer)
        assert df_filled["power"].isna().sum() <= sample_timeseries_df["power"].isna().sum()

    def test_resample_empty_dataframe(self):
        """Test resampling empty DataFrame"""
        resampler = TimeSeriesResampler()
        df_empty = pd.DataFrame(columns=["timestamp", "value"])

        with pytest.raises(ValidationError, match="empty"):
            resampler.resample(df_empty, freq="1H")

    def test_resample_missing_timestamp(self):
        """Test resampling with missing timestamp column"""
        resampler = TimeSeriesResampler()
        df = pd.DataFrame({"value": [1, 2, 3]})

        with pytest.raises(ValidationError, match="not found"):
            resampler.resample(df, freq="1H")

    def test_resample_multiple(self, sample_timeseries_df):
        """Test resampling to multiple frequencies"""
        resampler = TimeSeriesResampler()
        results = resampler.resample_multiple(
            sample_timeseries_df, frequencies=["15min", "1H", "2H"]
        )

        assert len(results) == 3
        assert "15min" in results
        assert "1H" in results
        assert "2H" in results

        # Check row counts
        assert len(results["15min"]) == 96  # 288 / 3
        assert len(results["1H"]) == 24  # 288 / 12
        assert len(results["2H"]) == 12  # 288 / 24


class TestTimeSeriesAggregator:
    """Tests for TimeSeriesAggregator"""

    def test_aggregator_initialization(self):
        """Test aggregator initialization"""
        aggregator = TimeSeriesAggregator()
        assert aggregator.timestamp_column == "timestamp"

    def test_aggregate_daily(self, sample_timeseries_df):
        """Test daily aggregation"""
        aggregator = TimeSeriesAggregator()
        daily = aggregator.aggregate_daily(sample_timeseries_df)

        # 288 5-min intervals = 1 day
        assert len(daily) == 1
        assert "date" in daily.columns

    def test_aggregate_daily_custom(self, sample_timeseries_df):
        """Test daily aggregation with custom methods"""
        aggregator = TimeSeriesAggregator()
        daily = aggregator.aggregate_daily(
            sample_timeseries_df,
            agg_methods={"power": ["sum", "mean", "max"], "voltage": "mean"},
        )

        assert len(daily) == 1
        # Check multi-level columns exist
        assert "power" in daily.columns or ("power", "sum") in daily.columns

    def test_aggregate_monthly(self):
        """Test monthly aggregation"""
        # Create 2 months of data
        timestamps = pd.date_range("2024-01-01", "2024-02-29", freq="1D")
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "power": np.random.randint(1000, 5000, len(timestamps)),
            }
        )

        aggregator = TimeSeriesAggregator()
        monthly = aggregator.aggregate_monthly(df)

        # Should have 2 months
        assert len(monthly) == 2
        assert "year_month" in monthly.columns

    def test_rolling_aggregate_time_based(self, hourly_timeseries_df):
        """Test rolling aggregation with time-based window"""
        aggregator = TimeSeriesAggregator()
        rolling = aggregator.rolling_aggregate(hourly_timeseries_df, window="3H", method="mean")

        assert len(rolling) == 24
        assert "power" in rolling.columns

    def test_rolling_aggregate_count_based(self, hourly_timeseries_df):
        """Test rolling aggregation with count-based window"""
        aggregator = TimeSeriesAggregator()
        rolling = aggregator.rolling_aggregate(hourly_timeseries_df, window=5, method="max")

        assert len(rolling) == 24

    def test_rolling_aggregate_methods(self, hourly_timeseries_df):
        """Test different rolling aggregation methods"""
        aggregator = TimeSeriesAggregator()

        for method in ["mean", "sum", "min", "max", "std"]:
            rolling = aggregator.rolling_aggregate(hourly_timeseries_df, window=3, method=method)
            assert len(rolling) == 24


class TestTimeSeriesAnalyzer:
    """Tests for TimeSeriesAnalyzer"""

    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        analyzer = TimeSeriesAnalyzer()
        assert analyzer.timestamp_column == "timestamp"

    def test_analyze_basic(self, sample_timeseries_df):
        """Test basic time series analysis"""
        analyzer = TimeSeriesAnalyzer()
        stats = analyzer.analyze(sample_timeseries_df)

        assert "total_rows" in stats
        assert "time_range" in stats
        assert "duration_days" in stats
        assert "detected_frequency" in stats
        assert "missing_rate" in stats

        assert stats["total_rows"] == 288
        assert stats["detected_frequency"] == "5min"

    def test_analyze_missing_data(self, sample_timeseries_df):
        """Test missing data detection"""
        analyzer = TimeSeriesAnalyzer()
        stats = analyzer.analyze(sample_timeseries_df)

        # We added 4 missing values in fixture
        assert stats["missing_values"] >= 3
        assert stats["missing_rate"] > 0

    def test_analyze_missing_timestamp(self):
        """Test analysis with missing timestamp column"""
        analyzer = TimeSeriesAnalyzer()
        df = pd.DataFrame({"value": [1, 2, 3]})

        with pytest.raises(ValidationError, match="not found"):
            analyzer.analyze(df)

    def test_find_gaps(self, sample_timeseries_df):
        """Test gap detection"""
        # Add a gap by removing some rows
        df_with_gaps = sample_timeseries_df.drop(sample_timeseries_df.index[100:110])

        analyzer = TimeSeriesAnalyzer()
        gaps = analyzer.find_gaps(df_with_gaps, expected_freq="5min", min_gap_size=1)

        # Should find at least the gap we created
        assert len(gaps) >= 1
        assert "gap_start" in gaps.columns
        assert "gap_end" in gaps.columns
        assert "gap_duration" in gaps.columns

    def test_find_gaps_no_gaps(self, sample_timeseries_df):
        """Test gap detection when no gaps exist"""
        analyzer = TimeSeriesAnalyzer()
        gaps = analyzer.find_gaps(sample_timeseries_df, expected_freq="5min")

        # Should find no gaps in continuous data
        assert len(gaps) == 0


class TestIntegration:
    """Integration tests for time series processing"""

    def test_resample_and_aggregate(self, sample_timeseries_df):
        """Test resampling followed by aggregation"""
        # Resample to hourly
        resampler = TimeSeriesResampler()
        df_hourly = resampler.resample(sample_timeseries_df, freq="1H", method="mean")

        # Aggregate daily
        aggregator = TimeSeriesAggregator()
        daily = aggregator.aggregate_daily(df_hourly)

        assert len(daily) == 1
        assert "date" in daily.columns

    def test_analyze_resampled_data(self, sample_timeseries_df):
        """Test analyzing resampled data"""
        # Resample
        resampler = TimeSeriesResampler()
        df_hourly = resampler.resample(sample_timeseries_df, freq="1H", method="mean")

        # Analyze
        analyzer = TimeSeriesAnalyzer()
        stats = analyzer.analyze(df_hourly)

        assert stats["total_rows"] == 24
        assert stats["detected_frequency"] == "1H"

    def test_full_pipeline(self):
        """Test complete time series processing pipeline"""
        # Create data with irregular intervals and gaps
        timestamps = pd.date_range("2024-01-01", periods=100, freq="5min")
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "power": np.random.randint(0, 5000, 100),
                "voltage": np.random.uniform(220, 240, 100),
            }
        )

        # Add gap
        df = df.drop(df.index[50:55])

        # 1. Analyze original data
        analyzer = TimeSeriesAnalyzer()
        analyzer.analyze(df)

        # 2. Find gaps
        gaps = analyzer.find_gaps(df, expected_freq="5min")
        assert len(gaps) >= 1

        # 3. Resample to regular intervals
        resampler = TimeSeriesResampler()
        df_resampled = resampler.resample(df, freq="15min", method="mean", fill_method="ffill")

        # 4. Aggregate
        aggregator = TimeSeriesAggregator()
        hourly = aggregator.aggregate_daily(df_resampled)

        assert len(hourly) >= 1
