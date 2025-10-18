"""
Parquet configuration presets and utilities
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ParquetConfigPreset:
    """Parquet configuration preset"""

    compression: str
    compression_level: Optional[int]
    row_group_size: int
    use_dictionary: bool
    write_statistics: bool
    optimize_dtypes: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ParquetConfig:
    """
    Parquet configuration presets for different use cases

    Presets:
        - STANDARD: Balanced configuration with snappy compression
        - OPTIMIZED: Maximum compression and optimization (46x ratio)
        - FAST: Fast write with minimal compression
    """

    STANDARD = ParquetConfigPreset(
        compression="snappy",
        compression_level=None,
        row_group_size=100000,
        use_dictionary=True,
        write_statistics=True,
        optimize_dtypes=False,
    )

    OPTIMIZED = ParquetConfigPreset(
        compression="zstd",
        compression_level=3,
        row_group_size=100000,
        use_dictionary=True,
        write_statistics=True,
        optimize_dtypes=True,
    )

    FAST = ParquetConfigPreset(
        compression="snappy",
        compression_level=None,
        row_group_size=500000,
        use_dictionary=False,
        write_statistics=True,
        optimize_dtypes=False,
    )

    MAXIMUM_COMPRESSION = ParquetConfigPreset(
        compression="zstd",
        compression_level=22,  # Max zstd compression
        row_group_size=100000,
        use_dictionary=True,
        write_statistics=True,
        optimize_dtypes=True,
    )

    @classmethod
    def get_preset(cls, name: str) -> ParquetConfigPreset:
        """
        Get a configuration preset by name

        Args:
            name: Preset name ('standard', 'optimized', 'fast', 'maximum_compression')

        Returns:
            ParquetConfigPreset instance

        Raises:
            ValueError: If preset name is not recognized

        Examples:
            >>> config = ParquetConfig.get_preset('optimized')
            >>> config.compression
            'zstd'
        """
        name = name.upper()
        if not hasattr(cls, name):
            available = [
                attr
                for attr in dir(cls)
                if not attr.startswith("_") and isinstance(getattr(cls, attr), ParquetConfigPreset)
            ]
            raise ValueError(
                f"Unknown preset '{name}'. " f"Available presets: {', '.join(available)}"
            )
        return getattr(cls, name)

    @classmethod
    def create_custom(
        cls,
        compression: str = "zstd",
        compression_level: Optional[int] = 3,
        row_group_size: int = 100000,
        use_dictionary: bool = True,
        write_statistics: bool = True,
        optimize_dtypes: bool = True,
    ) -> ParquetConfigPreset:
        """
        Create a custom configuration preset

        Args:
            compression: Compression algorithm ('snappy', 'gzip', 'zstd', 'lz4', 'brotli')
            compression_level: Compression level (algorithm-specific)
            row_group_size: Number of rows per row group
            use_dictionary: Enable dictionary encoding
            write_statistics: Write column statistics
            optimize_dtypes: Optimize data types before writing

        Returns:
            ParquetConfigPreset instance

        Examples:
            >>> config = ParquetConfig.create_custom(
            ...     compression='gzip',
            ...     compression_level=6,
            ...     row_group_size=50000
            ... )
        """
        return ParquetConfigPreset(
            compression=compression,
            compression_level=compression_level,
            row_group_size=row_group_size,
            use_dictionary=use_dictionary,
            write_statistics=write_statistics,
            optimize_dtypes=optimize_dtypes,
        )
