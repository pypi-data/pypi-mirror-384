
#!/usr/bin/env python3
"""
This module handles configuration management for the EPUB reader.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import psutil

# Set up logging
logger = logging.getLogger(__name__)

# Define the path for the configuration file
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "speakub")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Define default configuration settings
DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "en",
    "voice_rate": "+20%",
    "pitch": "default",
    "volume": "default",
    "tts_enabled": True,
    "reading_speed": 200,  # Words per minute
    "theme": "default",
    "font_size": 12,
    # TTS settings for centralized configuration
    "tts": {
        "rate": 0,  # TTS rate adjustment (-100 to +100)
        "volume": 100,  # TTS volume (0-100)
        "pitch": "+0Hz",  # TTS pitch adjustment
        "smooth_mode": False,  # Smooth TTS mode enabled/disabled
    },
    # Hardware-aware cache configuration
    "cache": {
        "auto_detect_hardware": True,
        "chapter_cache_size": 50,  # Default fallback
        "width_cache_size": 1000,  # Default fallback
        "hardware_profile": "auto",  # auto, low_end, mid_range, high_end
    },
    # Network configuration
    "network": {
        "recovery_timeout_minutes": 30,  # Network recovery monitoring timeout
        "recovery_check_interval": 10,  # Seconds between connectivity checks
        "connectivity_test_host": "8.8.8.8",  # Host for connectivity testing
        "connectivity_test_port": 53,  # Port for connectivity testing
        "connectivity_test_timeout": 5,  # Timeout for connectivity test
    },
    # Performance monitoring configuration
    "performance": {
        "enable_monitoring": False,  # Enable performance monitoring
        "log_slow_operations": True,  # Log operations exceeding thresholds
        # Threshold for slow operations (ms)
        "slow_operation_threshold_ms": 100,
        "memory_usage_tracking": True,  # Track memory usage
        "cpu_usage_tracking": True,  # Track CPU usage
        "benchmark_enabled": False,  # Enable benchmarking mode
        "benchmark_output_file": "performance_benchmark.json",  # Benchmark output file
    },
}


_hardware_profile: Optional[str] = None


def detect_hardware_profile() -> str:
    """
    Detect hardware profile based on system resources.
    Uses lazy initialization to avoid running on every import.

    Returns:
        str: Hardware profile ('low_end', 'mid_range', 'high_end')
    """
    global _hardware_profile
    if _hardware_profile is None:
        _hardware_profile = _do_detect_hardware()
    return _hardware_profile


def _do_detect_hardware() -> str:
    """
    Internal function to perform actual hardware detection.
    """
    try:
        # Get system memory in GB
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Get CPU core count
        cpu_count = psutil.cpu_count(logical=True)

        # Get CPU frequency if available
        try:
            cpu_freq_info = psutil.cpu_freq()
            cpu_freq = cpu_freq_info.max if cpu_freq_info else 0
        except Exception:
            cpu_freq = 0

        logger.debug(
            f"Hardware detection: {cpu_count} cores, "
            f"{memory_gb:.1f}GB RAM, {cpu_freq:.0f}MHz CPU"
        )

        # Classification logic
        if (memory_gb is not None and memory_gb <= 4) or (
            cpu_count is not None and cpu_count <= 2
        ):
            return "low_end"
        elif (memory_gb is not None and memory_gb <= 8) or (
            cpu_count is not None and cpu_count <= 4
        ):
            return "mid_range"
        else:
            return "high_end"

    except Exception as e:
        logger.warning(f"Hardware detection failed: {e}, using mid_range as fallback")
        return "mid_range"


def get_cache_sizes_for_profile(profile: str) -> Dict[str, int]:
    """
    Get recommended cache sizes for a hardware profile.

    Args:
        profile: Hardware profile ('low_end', 'mid_range', 'high_end')

    Returns:
        Dict with chapter_cache_size and width_cache_size
    """
    profiles = {
        "low_end": {
            "chapter_cache_size": 10,  # Minimal cache for low memory
            "width_cache_size": 200,
        },
        "mid_range": {
            "chapter_cache_size": 25,  # Balanced cache
            "width_cache_size": 500,
        },
        "high_end": {
            "chapter_cache_size": 50,  # Maximum cache for performance
            "width_cache_size": 1000,
        },
    }

    return profiles.get(profile, profiles["mid_range"])


def get_adaptive_cache_config() -> Dict[str, int]:
    """
    Get adaptive cache configuration based on detected hardware.

    Returns:
        Dict with chapter_cache_size and width_cache_size
    """
    try:
        profile = detect_hardware_profile()
        cache_sizes = get_cache_sizes_for_profile(profile)
        logger.debug(f"Adaptive cache config for {profile} hardware: {cache_sizes}")
        return cache_sizes
    except Exception as e:
        logger.warning(f"Failed to get adaptive cache config: {e}, using defaults")
        return {"chapter_cache_size": 50, "width_cache_size": 1000}


def get_cache_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Get cache configuration, either from config file or auto-detected.

    Args:
        config: Configuration dictionary (if None, loads from file)

    Returns:
        Dict with chapter_cache_size and width_cache_size
    """
    if config is None:
        config = load_config()

    cache_config = config.get("cache", {})

    # Check if auto-detection is enabled
    if cache_config.get("auto_detect_hardware", True):
        # Use hardware detection
        adaptive_config = get_adaptive_cache_config()

        # Allow manual override
        chapter_size = cache_config.get(
            "chapter_cache_size", adaptive_config["chapter_cache_size"]
        )
        width_size = cache_config.get(
            "width_cache_size", adaptive_config["width_cache_size"]
        )

        return {"chapter_cache_size": chapter_size, "width_cache_size": width_size}
    else:
        # Use manual configuration
        return {
            "chapter_cache_size": cache_config.get("chapter_cache_size", 50),
            "width_cache_size": cache_config.get("width_cache_size", 1000),
        }


_tts_config_cache: Optional[Dict[str, Any]] = None
_config_mtime: Optional[float] = None


def get_tts_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get TTS configuration from config file.

    Args:
        config: Configuration dictionary (if None, loads from file)

    Returns:
        Dict with TTS settings (rate, volume, pitch, smooth_mode)
    """
    global _tts_config_cache, _config_mtime

    if config is None:
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            current_mtime = config_path.stat().st_mtime
            if _tts_config_cache is None or current_mtime != _config_mtime:
                config = load_config()
                _config_mtime = current_mtime
                _tts_config_cache = config.get("tts", {})
            else:
                config = {"tts": _tts_config_cache}
        else:
            config = load_config()

    tts_config = config.get("tts", {})
    default_tts = DEFAULT_CONFIG["tts"]

    # Merge with defaults to ensure all keys are present
    merged_tts = default_tts.copy()
    merged_tts.update(tts_config)

    return merged_tts


def save_tts_config(tts_config: Dict[str, Any]) -> None:
    """
    Save TTS configuration to config file.

    Args:
        tts_config: TTS configuration dictionary to save
    """
    try:
        config = load_config()
        config["tts"] = tts_config
        save_config(config)
        logger.debug("TTS configuration saved")
    except Exception as e:
        logger.error(f"Error saving TTS configuration: {e}")


def validate_tts_config(tts_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize TTS configuration values.

    Args:
        tts_config: TTS configuration to validate

    Returns:
        Validated TTS configuration with sanitized values
    """
    validated = {}

    # Validate rate (-100 to +100)
    rate = tts_config.get("rate", 0)
    validated["rate"] = max(-100, min(100, rate))

    # Validate volume (0 to 100)
    volume = tts_config.get("volume", 100)
    validated["volume"] = max(0, min(100, volume))

    # Validate pitch (string format like "+0Hz", "-10Hz", etc.)
    pitch = tts_config.get("pitch", "+0Hz")
    if isinstance(pitch, str) and pitch.endswith("Hz"):
        try:
            # Extract numeric part
            pitch_value = int(pitch[:-2])
            # Clamp to reasonable range (-50 to +50)
            pitch_value = max(-50, min(50, pitch_value))
            validated["pitch"] = f"{pitch_value:+}Hz"
        except ValueError:
            validated["pitch"] = "+0Hz"
    else:
        validated["pitch"] = "+0Hz"

    # Validate smooth_mode (boolean)
    validated["smooth_mode"] = bool(tts_config.get("smooth_mode", False))

    return validated


def get_network_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get network configuration from config file.

    Args:
        config: Configuration dictionary (if None, loads from file)

    Returns:
        Dict with network settings
    """
    if config is None:
        config = load_config()

    network_config = config.get("network", {})
    default_network = DEFAULT_CONFIG["network"]

    # Merge with defaults to ensure all keys are present
    merged_network = default_network.copy()
    merged_network.update(network_config)

    return merged_network


# Define the path for the pronunciation corrections file
CORRECTIONS_FILE = os.path.join(CONFIG_DIR, "corrections.json")


def save_pronunciation_corrections(corrections: Dict[str, str]) -> None:
    """
    Save pronunciation corrections to JSON file.

    Args:
        corrections: Corrections dictionary to save
    """
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # If corrections is empty, create file with instructions and examples
        if not corrections:
            instructions_content = {
                "_comment": "Chinese Pronunciation Corrections Configuration",
                "_instructions": (
                    "Add your correction rules below in format: "
                    "'original': 'corrected'"
                ),
                "_examples": {"生長": "生掌", "長": "常"},
            }
            with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(instructions_content, f, indent=4, ensure_ascii=False)
        else:
            with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(corrections, f, indent=4, ensure_ascii=False)

        logger.debug(f"Pronunciation corrections saved to {CORRECTIONS_FILE}")
    except IOError as e:
        logger.error(f"Error saving pronunciation corrections file: {e}")


def load_pronunciation_corrections() -> Dict[str, str]:
    """
    Load pronunciation corrections from external JSON file.
    The file should be a JSON object (dictionary) with "original": "correction" format.
    If the file doesn't exist, creates an empty one for user customization.

    Returns:
        Dict[str, str]: Corrections dictionary.
    """
    if not os.path.exists(CORRECTIONS_FILE):
        logger.debug("Corrections file not found. Skipping pronunciation corrections.")
        return {}

    try:
        with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
            corrections = json.load(f)
            if not isinstance(corrections, dict):
                logger.warning(
                    f"'{CORRECTIONS_FILE}' root element is not a JSON object (dict), "
                    "ignored."
                )
                return {}

            # Validate content is string: string, exclude instruction keys
            validated_corrections = {
                k: v
                for k, v in corrections.items()
                if isinstance(k, str) and isinstance(v, str) and not k.startswith("_")
            }

            logger.debug(
                "Successfully loaded "
                f"{len(validated_corrections)} pronunciation correction "
                f"rules from '{CORRECTIONS_FILE}'."
            )
            return validated_corrections

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error reading or parsing '{CORRECTIONS_FILE}': {e}")
        return {}


class ConfigManager:
    """
    Centralized configuration manager with hierarchical override system.

    Override priority (highest to lowest):
    1. Runtime overrides (set via set_override())
    2. Environment variables (SPEAKUB_*)
    3. Configuration file (~/.config/speakub/config.json)
    4. Default values
    """

    def __init__(self):
        self._overrides: Dict[str, Any] = {}
        self._config_cache: Optional[Dict[str, Any]] = None
        self._config_mtime: Optional[float] = None

    def _load_config_with_hierarchy(self) -> Dict[str, Any]:
        """
        Load configuration with hierarchical override system.

        Returns:
            Dict[str, Any]: Merged configuration dictionary
        """
        # Start with defaults
        config = DEFAULT_CONFIG.copy()

        # Load from file if exists
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            try:
                current_mtime = config_path.stat().st_mtime
                if self._config_cache is None or self._config_mtime != current_mtime:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        file_config = json.load(f)
                    self._config_cache = file_config
                    self._config_mtime = current_mtime
                else:
                    file_config = self._config_cache

                # Deep merge file config into defaults
                self._deep_update(config, file_config)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load config file: {e}")

        # Apply environment variable overrides
        self._apply_env_overrides(config)

        # Apply runtime overrides (highest priority)
        self._deep_update(config, self._overrides)

        return config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """
        Apply environment variable overrides to configuration.

        Environment variables should be prefixed with SPEAKUB_ and use
        dot notation for nested keys, e.g.:
        SPEAKUB_TTS_RATE=10
        SPEAKUB_TTS_VOLUME=80
        SPEAKUB_FONT_SIZE=14

        Args:
            config: Configuration dictionary to update
        """
        prefix = "SPEAKUB_"

        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            # Remove prefix and convert to lowercase with underscores
            config_key = env_key[len(prefix):].lower()

            # Convert underscores to dots for nested access
            config_key = config_key.replace("_", ".")

            # Parse value (try int, float, bool, otherwise string)
            parsed_value = self._parse_env_value(env_value)

            # Set nested value
            self._set_nested_value(config, config_key, parsed_value)

    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """
        Parse environment variable value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Parsed value
        """
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Try int
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _set_nested_value(
        self, config: Dict[str, Any], key_path: str, value: Any
    ) -> None:
        """
        Set a value in nested dictionary using dot notation.

        Args:
            config: Configuration dictionary
            key_path: Dot-separated path (e.g., "tts.rate")
            value: Value to set
        """
        keys = key_path.split(".")
        current = config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary.

        Args:
            base: Base dictionary to update
            update: Dictionary with updates
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Dot-separated key path (e.g., "tts.rate"). If None, return full config.
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self._load_config_with_hierarchy()

        if key is None:
            return config

        # Navigate nested dictionary
        keys = key.split(".")
        current = config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set_override(self, key: str, value: Any) -> None:
        """
        Set a runtime override (highest priority).

        Args:
            key: Dot-separated key path
            value: Value to set
        """
        self._set_nested_value(self._overrides, key, value)
        logger.debug(f"Runtime override set: {key} = {value}")

    def clear_override(self, key: str) -> None:
        """
        Clear a runtime override.

        Args:
            key: Dot-separated key path
        """
        keys = key.split(".")
        current = self._overrides

        try:
            for k in keys[:-1]:
                current = current[k]
            del current[keys[-1]]
            logger.debug(f"Runtime override cleared: {key}")
        except KeyError:
            pass

    def save_to_file(self) -> None:
        """
        Save current configuration (without runtime overrides) to file.
        """
        config = self._load_config_with_hierarchy()

        # Remove runtime overrides for saving
        file_config = {}

        # Extract file-level config (remove defaults and env vars)
        for key, value in config.items():
            if key not in self._overrides:
                # Check if it's different from defaults
                if key not in DEFAULT_CONFIG or DEFAULT_CONFIG[key] != value:
                    file_config[key] = value

        save_config(file_config)

    def reload(self) -> None:
        """
        Force reload configuration from disk.
        """
        self._config_cache = None
        self._config_mtime = None
        logger.debug("Configuration reloaded from disk")


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration value using the global ConfigManager.

    Args:
        key: Dot-separated key path (e.g., "tts.rate"). If None, return full config.
        default: Default value if key not found

    Returns:
        Configuration value
    """
    return _config_manager.get(key, default)


def set_config_override(key: str, value: Any) -> None:
    """
    Set a runtime configuration override.

    Args:
        key: Dot-separated key path
        value: Value to set
    """
    _config_manager.set_override(key, value)


def save_config_to_file() -> None:
    """
    Save current configuration to file.
    """
    _config_manager.save_to_file()


# Backward compatibility functions
def load_config() -> Dict[str, Any]:
    """Backward compatibility wrapper."""
    return get_config()


def save_config(config: Dict[str, Any]) -> None:
    """Backward compatibility wrapper."""
    # This is a simplified version - for full compatibility,
    # we'd need to merge with existing config
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.debug(f"Configuration saved to {CONFIG_FILE}")
        # Invalidate cache
        _config_manager.reload()
    except IOError as e:
        logger.error(f"Error saving configuration file: {e}")


# Example usage (for testing)
if __name__ == "__main__":
    # Test loading config
    print("Loading configuration...")
    my_config = load_config()
    print("Current config:", my_config)

    # Test modifying and saving config
    print("\nModifying configuration...")
    my_config["language"] = "fr"
    my_config["font_size"] = 14
    save_config(my_config)

    # Test reloading config
    print("\nReloading configuration...")
    reloaded_config = load_config()
    print("Reloaded config:", reloaded_config)
    assert reloaded_config["language"] == "fr"
    assert reloaded_config["font_size"] == 14

    # Restore default settings
    print("\nRestoring default configuration...")
    save_config(DEFAULT_CONFIG)
    final_config = load_config()
    print("Final config:", final_config)
    assert final_config["language"] == "en"

    print("\nConfiguration management test complete.")
