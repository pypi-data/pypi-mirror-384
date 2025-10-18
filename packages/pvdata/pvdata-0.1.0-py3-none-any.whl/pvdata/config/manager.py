"""
Global configuration management
"""

from typing import Any, Dict, Union
from pathlib import Path
from contextlib import contextmanager
import json
import copy


class ConfigManager:
    """
    Global configuration manager with support for file-based configuration

    Features:
        - Hierarchical configuration with defaults
        - File-based configuration (JSON/YAML)
        - Temporary configuration contexts
        - Thread-safe operations

    Examples:
        >>> config = ConfigManager()
        >>> config.set('compression', 'zstd')
        >>> config.get('compression')
        'zstd'

        >>> # Temporary configuration
        >>> with config.temporary(compression='snappy'):
        ...     print(config.get('compression'))  # 'snappy'
        >>> print(config.get('compression'))  # 'zstd'
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default configuration values"""
        self._config = {
            # Parquet settings
            "parquet_preset": "optimized",
            "compression": "zstd",
            "compression_level": 3,
            "row_group_size": 100000,
            # Performance settings
            "n_jobs": -1,  # Use all CPUs
            "chunk_size": 100000,
            "memory_map": True,
            "use_threads": True,
            # Data optimization
            "optimize_dtypes": True,
            "force_downcast": True,
            # Logging
            "log_level": "INFO",
            "show_progress": True,
            # Cache
            "enable_cache": True,
            "cache_size_mb": 512,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config = ConfigManager()
            >>> config.get('compression')
            'zstd'
            >>> config.get('nonexistent', 'default_value')
            'default_value'
        """
        # Support dot notation for nested keys
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value

        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set

        Examples:
            >>> config = ConfigManager()
            >>> config.set('compression', 'snappy')
            >>> config.get('compression')
            'snappy'
        """
        # Support dot notation for nested keys
        keys = key.split(".")

        if len(keys) == 1:
            self._config[key] = value
        else:
            # Navigate to the parent dict
            current = self._config
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update multiple configuration values

        Args:
            config_dict: Dictionary of configuration values

        Examples:
            >>> config = ConfigManager()
            >>> config.update({'compression': 'snappy', 'n_jobs': 4})
            >>> config.get('compression')
            'snappy'
        """
        for key, value in config_dict.items():
            self.set(key, value)

    def load_from_file(self, path: Union[str, Path]) -> None:
        """
        Load configuration from JSON or YAML file

        Args:
            path: Path to configuration file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported

        Examples:
            >>> config = ConfigManager()
            >>> config.load_from_file('config.json')  # doctest: +SKIP
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Determine file format
        if path.suffix == ".json":
            with open(path, "r") as f:
                config_dict = json.load(f)
        elif path.suffix in [".yaml", ".yml"]:
            try:
                import yaml

                with open(path, "r") as f:
                    config_dict = yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML configuration files. "
                    "Install it with: pip install pyyaml"
                )
        else:
            raise ValueError(
                f"Unsupported configuration file format: {path.suffix}. "
                "Supported formats: .json, .yaml, .yml"
            )

        self.update(config_dict)

    def save_to_file(self, path: Union[str, Path]) -> None:
        """
        Save current configuration to JSON or YAML file

        Args:
            path: Path to save configuration

        Examples:
            >>> config = ConfigManager()
            >>> config.save_to_file('config.json')  # doctest: +SKIP
        """
        path = Path(path)

        if path.suffix == ".json":
            with open(path, "w") as f:
                json.dump(self._config, f, indent=2)
        elif path.suffix in [".yaml", ".yml"]:
            try:
                import yaml

                with open(path, "w") as f:
                    yaml.dump(self._config, f, default_flow_style=False)
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML configuration files. "
                    "Install it with: pip install pyyaml"
                )
        else:
            raise ValueError(
                f"Unsupported configuration file format: {path.suffix}. "
                "Supported formats: .json, .yaml, .yml"
            )

    def reset(self) -> None:
        """
        Reset configuration to defaults

        Examples:
            >>> config = ConfigManager()
            >>> config.set('compression', 'snappy')
            >>> config.reset()
            >>> config.get('compression')
            'zstd'
        """
        self._load_defaults()

    def to_dict(self) -> Dict[str, Any]:
        """
        Get all configuration as dictionary

        Returns:
            Copy of configuration dictionary

        Examples:
            >>> config = ConfigManager()
            >>> config_dict = config.to_dict()
            >>> 'compression' in config_dict
            True
        """
        return copy.deepcopy(self._config)

    @contextmanager
    def temporary(self, **kwargs: Any):
        """
        Temporary configuration context manager

        Args:
            **kwargs: Temporary configuration values

        Yields:
            None

        Examples:
            >>> config = ConfigManager()
            >>> config.set('compression', 'zstd')
            >>> with config.temporary(compression='snappy'):
            ...     print(config.get('compression'))  # 'snappy'
            snappy
            >>> config.get('compression')  # Back to 'zstd'
            'zstd'
        """
        # Save old values
        old_values = {}
        for key in kwargs:
            old_values[key] = self.get(key)

        # Set new values
        try:
            for key, value in kwargs.items():
                self.set(key, value)
            yield
        finally:
            # Restore old values
            for key, value in old_values.items():
                if value is None:
                    # If the key didn't exist before, remove it
                    keys = key.split(".")
                    if len(keys) == 1 and key in self._config:
                        del self._config[key]
                else:
                    self.set(key, value)

    def __repr__(self) -> str:
        """String representation"""
        return f"ConfigManager({len(self._config)} settings)"

    def __str__(self) -> str:
        """Human-readable string representation"""
        return json.dumps(self._config, indent=2)


# Global singleton instance
config = ConfigManager()
