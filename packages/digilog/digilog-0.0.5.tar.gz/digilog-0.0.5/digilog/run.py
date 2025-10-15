"""
Run object for managing experiment runs.
"""

import time
from typing import Any, Dict, List, Optional, Union
from .api import APIClient
from .config import Config
from .exceptions import ValidationError, RunNotFoundError


class Run:
    """
    Represents an active experiment run.
    
    Similar to wandb.run, this object provides methods for logging
    metrics, configurations, and managing the run lifecycle.
    """
    
    def __init__(
        self,
        api_client: APIClient,
        run_id: str,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        group_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.api_client = api_client
        self.run_id = run_id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.group_id = group_id
        self.config = Config(config or {})
        self._finished = False
        self._start_time = time.time()
        
        # Log initial configuration if provided
        if config:
            self._log_configs(config)
    
    def log(
        self, 
        data: Dict[str, Any], 
        step: Optional[int] = None
    ) -> None:
        """
        Log metrics and other data.
        
        Args:
            data: Dictionary of metrics to log
            step: Step number (optional)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        # Convert data to metrics format
        metrics = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                metric = {"key": key, "value": value}
                if step is not None:
                    metric["step"] = step
                metrics.append(metric)
            else:
                # For non-numeric values, convert to string and log as config
                self.config[key] = str(value)
        
        if metrics:
            self.api_client.log_metrics(self.run_id, metrics)
    
    def log_metric(
        self, 
        key: str, 
        value: Union[int, float], 
        step: Optional[int] = None
    ) -> None:
        """
        Log a single metric.
        
        Args:
            key: Metric name
            value: Metric value
            step: Step number (optional)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.api_client.log_metric(self.run_id, key, value, step)
    
    def log_metrics(
        self, 
        metrics: List[Dict[str, Any]]
    ) -> None:
        """
        Log multiple metrics.
        
        Args:
            metrics: List of metric dictionaries with 'key' and 'value' fields
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.api_client.log_metrics(self.run_id, metrics)
    
    def log_config(self, key: str, value: Any) -> None:
        """
        Log a configuration parameter.
        
        Args:
            key: Configuration key
            value: Configuration value (will be converted to string)
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        self.config[key] = str(value)
        self.api_client.log_config(self.run_id, key, str(value))
    
    def log_configs(self, configs: Dict[str, Any]) -> None:
        """
        Log multiple configuration parameters.
        
        Args:
            configs: Dictionary of configuration parameters
        """
        if self._finished:
            raise ValidationError("Cannot log to finished run")
        
        # Update local config
        self.config.update(configs)
        
        # Convert all values to strings for API
        string_configs = {k: str(v) for k, v in configs.items()}
        self.api_client.log_configs(self.run_id, string_configs)
    
    def finish(self, status: str = "FINISHED") -> None:
        """
        Finish the run.
        
        Args:
            status: Run status ("FINISHED", "FAILED", or "CANCELLED")
        """
        if self._finished:
            return
        
        self._finished = True
        self.api_client.finish_run(self.run_id, status)
    
    def get_metrics(
        self, 
        metric_key: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get metrics for this run.
        
        Args:
            metric_key: Filter by specific metric key
            limit: Number of metrics to return
            offset: Number of metrics to skip
            
        Returns:
            List of metric dictionaries
        """
        return self.api_client.get_metrics(
            self.run_id, metric_key, limit, offset
        )
    
    def get_run_data(self) -> Dict[str, Any]:
        """
        Get the full run data including metrics and configurations.
        
        Returns:
            Dictionary containing run information
        """
        return self.api_client.get_run(self.run_id)
    
    def _log_configs(self, configs: Dict[str, Any]) -> None:
        """Internal method to log initial configurations."""
        string_configs = {k: str(v) for k, v in configs.items()}
        self.api_client.log_configs(self.run_id, string_configs)
    
    @property
    def id(self) -> str:
        """Get the run ID."""
        return self.run_id
    
    @property
    def project(self) -> str:
        """Get the project ID."""
        return self.project_id
    
    @property
    def is_finished(self) -> bool:
        """Check if the run is finished."""
        return self._finished
    
    @property
    def duration(self) -> float:
        """Get the run duration in seconds."""
        if self._finished:
            return time.time() - self._start_time
        return time.time() - self._start_time
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically finish the run."""
        if not self._finished:
            status = "FAILED" if exc_type else "FINISHED"
            self.finish(status)
    
    def __repr__(self) -> str:
        status = "finished" if self._finished else "running"
        return f"Run(id='{self.run_id}', name='{self.name}', status='{status}')" 