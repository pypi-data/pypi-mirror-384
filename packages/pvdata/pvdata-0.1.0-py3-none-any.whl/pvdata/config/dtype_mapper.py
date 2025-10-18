"""
Data type optimization and mapping utilities
"""

from typing import Dict, Optional, Any
import pandas as pd


class DTypeMapper:
    """
    Data type optimization mapper for photovoltaic data

    Provides intelligent data type selection to minimize memory usage
    while maintaining data integrity.
    """

    # Default mapping for common PV data columns
    DEFAULT_MAP: Dict[str, str] = {
        "index_tri": "int32",
        "eff": "float32",
        "Year": "int16",
        "Month": "int8",
        "Day": "int8",
        "Hour": "int8",
        "Minute": "int8",
        "Second": "int8",
    }

    # Integer ranges for different types
    INT_RANGES = {
        "int8": (-128, 127),
        "uint8": (0, 255),
        "int16": (-32768, 32767),
        "uint16": (0, 65535),
        "int32": (-2147483648, 2147483647),
        "uint32": (0, 4294967295),
        "int64": (-9223372036854775808, 9223372036854775807),
    }

    @classmethod
    def optimize_dtype(cls, series: pd.Series, force_downcast: bool = True) -> str:
        """
        Automatically select the optimal data type for a series

        Args:
            series: Input pandas Series
            force_downcast: If True, use smallest possible type

        Returns:
            Optimal dtype as string

        Examples:
            >>> s = pd.Series([1, 2, 3, 4, 5])
            >>> DTypeMapper.optimize_dtype(s)
            'int8'

            >>> s = pd.Series([0.1, 0.2, 0.3])
            >>> DTypeMapper.optimize_dtype(s)
            'float32'
        """
        # Handle null series
        if series.isnull().all():
            return str(series.dtype)

        # Get current dtype
        current_dtype = series.dtype

        # Handle integer types
        if pd.api.types.is_integer_dtype(current_dtype):
            return cls._optimize_integer_dtype(series, force_downcast)

        # Handle float types
        elif pd.api.types.is_float_dtype(current_dtype):
            return cls._optimize_float_dtype(series, force_downcast)

        # Handle string/object types
        elif pd.api.types.is_object_dtype(current_dtype):
            # Try to convert to numeric
            try:
                numeric = pd.to_numeric(series, errors="coerce")
                if not numeric.isnull().all():
                    if (numeric == numeric.astype(int)).all():
                        return cls._optimize_integer_dtype(numeric.astype(int), force_downcast)
                    else:
                        return cls._optimize_float_dtype(numeric, force_downcast)
            except (ValueError, TypeError):
                pass

            # Check if categorical would be beneficial
            n_unique = series.nunique()
            n_total = len(series)
            if n_unique / n_total < 0.5 and n_unique < 1000:
                return "category"

            return "string"

        # Keep datetime, timedelta, bool as is
        return str(current_dtype)

    @classmethod
    def _optimize_integer_dtype(cls, series: pd.Series, force_downcast: bool) -> str:
        """Optimize integer dtype"""
        min_val = series.min()
        max_val = series.max()

        # Check if unsigned is possible
        if min_val >= 0:
            if max_val <= cls.INT_RANGES["uint8"][1]:
                return "uint8" if force_downcast else "uint16"
            elif max_val <= cls.INT_RANGES["uint16"][1]:
                return "uint16" if force_downcast else "uint32"
            elif max_val <= cls.INT_RANGES["uint32"][1]:
                return "uint32" if force_downcast else "uint32"
            else:
                return "int64"
        else:
            # Signed integer
            if min_val >= cls.INT_RANGES["int8"][0] and max_val <= cls.INT_RANGES["int8"][1]:
                return "int8" if force_downcast else "int16"
            elif min_val >= cls.INT_RANGES["int16"][0] and max_val <= cls.INT_RANGES["int16"][1]:
                return "int16" if force_downcast else "int32"
            elif min_val >= cls.INT_RANGES["int32"][0] and max_val <= cls.INT_RANGES["int32"][1]:
                return "int32" if force_downcast else "int32"
            else:
                return "int64"

    @classmethod
    def _optimize_float_dtype(cls, series: pd.Series, force_downcast: bool) -> str:
        """Optimize float dtype"""
        if force_downcast:
            # Check if float32 is sufficient
            try:
                as_float32 = series.astype("float32")
                # Check for precision loss
                max_diff = (series - as_float32).abs().max()
                if max_diff < 1e-6 or pd.isna(max_diff):
                    return "float32"
            except (ValueError, OverflowError):
                pass

        return "float64"

    @classmethod
    def apply_mapping(
        cls,
        df: pd.DataFrame,
        custom_map: Optional[Dict[str, str]] = None,
        auto_optimize: bool = False,
    ) -> pd.DataFrame:
        """
        Apply dtype mapping to DataFrame

        Args:
            df: Input DataFrame
            custom_map: Custom column -> dtype mapping (overrides defaults)
            auto_optimize: If True, auto-optimize columns not in mapping

        Returns:
            DataFrame with optimized dtypes

        Examples:
            >>> df = pd.DataFrame({'Year': [2020, 2021], 'eff': [85.5, 90.2]})
            >>> df_opt = DTypeMapper.apply_mapping(df)
            >>> df_opt['Year'].dtype
            dtype('int16')
        """
        df = df.copy()

        # Merge default and custom mappings
        mapping = cls.DEFAULT_MAP.copy()
        if custom_map:
            mapping.update(custom_map)

        # Apply explicit mapping
        for col, dtype in mapping.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except (ValueError, TypeError) as e:
                    # Skip columns that can't be converted
                    print(f"Warning: Could not convert {col} to {dtype}: {e}")

        # Auto-optimize remaining columns
        if auto_optimize:
            for col in df.columns:
                if col not in mapping:
                    try:
                        optimal_dtype = cls.optimize_dtype(df[col])
                        if optimal_dtype != str(df[col].dtype):
                            df[col] = df[col].astype(optimal_dtype)
                    except Exception:
                        # Skip if optimization fails
                        pass

        return df

    @classmethod
    def get_memory_savings(cls, df_before: pd.DataFrame, df_after: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate memory savings from dtype optimization

        Args:
            df_before: DataFrame before optimization
            df_after: DataFrame after optimization

        Returns:
            Dict with memory statistics

        Examples:
            >>> df = pd.DataFrame({'a': [1, 2, 3]})
            >>> df_opt = DTypeMapper.apply_mapping(df, auto_optimize=True)
            >>> stats = DTypeMapper.get_memory_savings(df, df_opt)
            >>> stats['savings_percent']  # doctest: +SKIP
            75.0
        """
        mem_before = df_before.memory_usage(deep=True).sum()
        mem_after = df_after.memory_usage(deep=True).sum()
        savings = mem_before - mem_after
        savings_percent = (savings / mem_before * 100) if mem_before > 0 else 0

        return {
            "memory_before_mb": mem_before / 1024 / 1024,
            "memory_after_mb": mem_after / 1024 / 1024,
            "savings_mb": savings / 1024 / 1024,
            "savings_percent": savings_percent,
        }
