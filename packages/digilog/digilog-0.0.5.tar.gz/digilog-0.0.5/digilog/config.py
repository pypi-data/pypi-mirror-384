"""
Configuration management for Digilog runs.
"""

import os
from typing import Any, Dict, Optional
from .exceptions import ValidationError


class Config:
    """
    Configuration object for managing run parameters.
    
    Similar to wandb.config, this allows setting and accessing
    configuration parameters for the current run.
    """
    
    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        self._config = initial_config or {}
        self._frozen = False
    
    def update(self, config: Dict[str, Any], allow_val_change: bool = False) -> None:
        """
        Update configuration parameters.
        
        Args:
            config: Dictionary of configuration parameters
            allow_val_change: Whether to allow changing existing values
        """
        if self._frozen and not allow_val_change:
            raise ValidationError("Cannot update config after run has started")
        
        for key, value in config.items():
            if key in self._config and not allow_val_change:
                raise ValidationError(f"Config key '{key}' already exists")
            self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to config values."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"Config has no attribute '{name}'")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to config values."""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting of config values."""
        if self._frozen:
            raise ValidationError("Cannot modify config after run has started")
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the config."""
        return key in self._config
    
    def __iter__(self):
        """Iterate over config keys."""
        return iter(self._config)
    
    def __len__(self) -> int:
        """Get the number of config parameters."""
        return len(self._config)
    
    def items(self):
        """Get config items."""
        return self._config.items()
    
    def keys(self):
        """Get config keys."""
        return self._config.keys()
    
    def values(self):
        """Get config values."""
        return self._config.values()
    
    def freeze(self) -> None:
        """Freeze the config to prevent further modifications."""
        self._frozen = True
    
    def unfreeze(self) -> None:
        """Unfreeze the config to allow modifications."""
        self._frozen = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"Config({self._config})"
    
    def __str__(self) -> str:
        return str(self._config)


# Global config instance
config = Config() 