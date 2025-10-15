"""
Main client interface for Digilog.

This module provides the wandb-like interface for initializing runs,
logging metrics, and managing experiment tracking.
"""

import os
from typing import Any, Dict, Optional
from .api import APIClient
from .run import Run
from .config import config as global_config
from .exceptions import (
    AuthenticationError, ConfigurationError, ValidationError
)
from ._state import get_current_run, _current_run, _token, get_api_base_url


def set_token(token: str) -> None:
    """
    Set the authentication token for API requests.
    
    Args:
        token: Authentication token
    """
    global _token
    _token = token


def init(
    project: str,
    name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    group: Optional[str] = None,
    tags: Optional[list] = None,
    notes: Optional[str] = None,
    **kwargs
) -> Run:
    """
    Initialize a new experiment run.
    
    Args:
        project: Project name
        name: Run name (optional)
        config: Configuration parameters (optional)
        group: Group name for related runs (optional)
        tags: Tags for organization (optional, not yet implemented)
        notes: Description/notes (optional)
        **kwargs: Additional configuration parameters
        
    Returns:
        Run object for the new experiment
        
    Raises:
        AuthenticationError: If no valid token is provided
        ValidationError: If required parameters are invalid
    """
    global _current_run
    
    # Check if there's already an active run
    if _current_run is not None:
        raise ValidationError("A run is already active. Call finish() first.")
    
    # Validate required parameters
    if not project or not isinstance(project, str):
        raise ValidationError("Project name is required and must be a string")
    
    # Get authentication token
    token = _token or os.environ.get('DIGILOG_API_KEY')
    if not token:
        raise AuthenticationError(
            "No authentication token found. Set DIGILOG_API_KEY environment variable "
            "or call set_token()"
        )
    
    # Create API client
    api_client = APIClient(get_api_base_url(), token)
    
    # Merge config from kwargs
    if config is None:
        config_dict = {}
    else:
        config_dict = config.copy()
    if kwargs:
        config_dict.update(kwargs)
    
    try:
        # Create or get project
        try:
            print(f"Creating project: {project}")
            project_data = api_client.create_project(project, notes)
        except Exception as e:
            # Project might already exist, try to get it
            projects = api_client.get_projects()
            project_data = None
            for p in projects:
                if p['name'] == project:
                    project_data = p
                    break
            
            if not project_data:
                raise e
        
        # Create run
        print(f"Creating run: {name} from project data: {project_data}")
        run_data = api_client.create_run(
            project_id=project_data['id'],
            name=name,
            description=notes,
            group_id=group
        )
        
        # Create Run object
        _current_run = Run(
            api_client=api_client,
            run_id=run_data['id'],
            project_id=project_data['id'],
            name=name,
            description=notes,
            group_id=group,
            config=config_dict
        )
        
        # Update global config
        global_config.update(config_dict)
        global_config.freeze()
        
        return _current_run
        
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize run: {e}")


def log(data: Dict[str, Any], step: Optional[int] = None) -> None:
    """
    Log metrics and other data to the current run.
    
    Args:
        data: Dictionary of metrics to log
        step: Step number (optional)
        
    Raises:
        ValidationError: If no active run or invalid data
    """
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log(data, step)


def finish() -> None:
    """
    Finish the current run.
    
    Raises:
        ValidationError: If no active run
    """
    global _current_run
    
    if _current_run is None:
        raise ValidationError("No active run to finish.")
    
    _current_run.finish()
    _current_run = None
    
    # Unfreeze global config
    global_config.unfreeze()


# Convenience functions for direct access to current run
def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """Log a single metric to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    if isinstance(value, (int, float)):
        run.log_metric(key, value, step)
    else:
        run.log_config(key, value)


def log_config(key: str, value: Any) -> None:
    """Log a configuration parameter to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log_config(key, value)


def log_configs(configs: Dict[str, Any]) -> None:
    """Log multiple configuration parameters to the current run."""
    run = get_current_run()
    if run is None:
        raise ValidationError("No active run. Call init() first.")
    
    run.log_configs(configs)


# Context manager support
class run:
    """
    Context manager for automatic run management.
    
    Usage:
        with digilog.run(project="my-project") as run:
            run.log({"loss": 0.1})
    """
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._run = None
    
    def __enter__(self):
        self._run = init(**self.kwargs)
        return self._run
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._run:
            status = "FAILED" if exc_type else "FINISHED"
            self._run.finish(status) 