"""
API client for communicating with the Digilog backend.
"""

import json
import os
import requests
from typing import Any, Dict, List, Optional, Union
from .exceptions import (
    APIError, AuthenticationError, NetworkError, 
    ProjectNotFoundError, RunNotFoundError, ValidationError
)

VERBOSE = False 


class APIClient:
    """Client for communicating with the Digilog REST API."""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token or os.environ.get('DIGILOG_API_KEY')
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                'X-API-Key': f'{self.token}',
                'Content-Type': 'application/json'
            })
    
    def _make_rest_request(
        self, 
        endpoint: str, 
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """Make a REST request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if VERBOSE:
                print(f"Making {method} request to {url}")
                if data:
                    print(f"Request body: {data}")
                if params:
                    print(f"Query params: {params}")
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Parse REST response
            response_data = response.json()
            if VERBOSE:
                print(f"REST response: {response_data}")
            
            # REST response structure: { "data": ..., "meta": ... }
            if "data" in response_data:
                return response_data["data"]
            else:
                return response_data
            
        except requests.exceptions.RequestException as e:
            if VERBOSE:
                print(f"REST request failed: {e}")
            if isinstance(e, requests.exceptions.ConnectionError):
                raise NetworkError(f"Failed to connect to {self.base_url}: {e}")
            elif isinstance(e, requests.exceptions.Timeout):
                raise NetworkError(f"Request timeout: {e}")
            elif hasattr(e, 'response') and e.response is not None:
                response = e.response
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or missing authentication token")
                elif response.status_code == 404:
                    raise ProjectNotFoundError("Project or run not found")
                elif response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown API error')
                        raise APIError(error_msg, response.status_code, response)
                    except json.JSONDecodeError:
                        raise APIError(f"HTTP {response.status_code}: {response.text}", response.status_code, response)
            else:
                raise NetworkError(f"Request failed: {e}")
        
        return {}
    
    def create_project(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project."""
        data = {"name": name}
        if description:
            data["description"] = description
        
        result = self._make_rest_request('/projects', method='POST', data=data)
        return result if isinstance(result, dict) else {}
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects for the authenticated user."""
        result = self._make_rest_request('/projects', method='GET')
        return result if isinstance(result, list) else []
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a specific project."""
        result = self._make_rest_request(f'/projects/{project_id}', method='GET')
        return result if isinstance(result, dict) else {}
    
    def create_run(
        self, 
        project_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new run."""
        data = {"projectId": project_id}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if group_id:
            data["groupId"] = group_id
        
        result = self._make_rest_request('/runs', method='POST', data=data)
        if VERBOSE:
            print(f"create_run result: {result}")
        return result if isinstance(result, dict) else {}
    
    def get_runs(
        self, 
        project_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get runs for a project."""
        params = {
            "limit": limit,
            "offset": offset
        }
        result = self._make_rest_request(f'/projects/{project_id}/runs', method='GET', params=params)
        return result if isinstance(result, list) else []
    
    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get a specific run."""
        result = self._make_rest_request(f'/runs/{run_id}', method='GET')
        return result if isinstance(result, dict) else {}
    
    def finish_run(self, run_id: str, status: str = "FINISHED") -> Dict[str, Any]:
        """Finish a run."""
        data = {"status": status}
        result = self._make_rest_request(f'/runs/{run_id}/finish', method='PATCH', data=data)
        return result if isinstance(result, dict) else {}
    
    def log_metric(
        self, 
        run_id: str, 
        key: str, 
        value: Union[int, float], 
        step: Optional[int] = None
    ) -> Dict[str, Any]:
        """Log a single metric."""
        data = {"key": key, "value": value}
        if step is not None:
            data["step"] = step
        
        result = self._make_rest_request(f'/runs/{run_id}/metrics', method='POST', data=data)
        return result if isinstance(result, dict) else {}
    
    def log_metrics(
        self, 
        run_id: str, 
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Log multiple metrics."""
        data = {"metrics": metrics}
        result = self._make_rest_request(f'/runs/{run_id}/metrics', method='POST', data=data)
        return result if isinstance(result, dict) else {}
    
    def get_metrics(
        self, 
        run_id: str, 
        metric_key: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get metrics for a run."""
        params = {
            "limit": limit,
            "offset": offset
        }
        if metric_key:
            params["metricKey"] = metric_key
        
        result = self._make_rest_request(f'/runs/{run_id}/metrics', method='GET', params=params)
        return result if isinstance(result, list) else []
    
    def log_config(self, run_id: str, key: str, value: str) -> Dict[str, Any]:
        """Log a single configuration parameter."""
        data = {"key": key, "value": value}
        result = self._make_rest_request(f'/runs/{run_id}/configs', method='POST', data=data)
        return result if isinstance(result, dict) else {}
    
    def log_configs(self, run_id: str, configs: Dict[str, str]) -> Dict[str, Any]:
        """Log multiple configuration parameters."""
        data = {"configs": configs}
        result = self._make_rest_request(f'/runs/{run_id}/configs', method='POST', data=data)
        return result if isinstance(result, dict) else {}
    
    def compare_runs(
        self, 
        run_ids: List[str], 
        metric_keys: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Compare multiple runs."""
        params = {"runIds": ",".join(run_ids)}
        if metric_keys:
            params["metricKeys"] = ",".join(metric_keys)
        
        result = self._make_rest_request('/runs/compare', method='GET', params=params)
        return result if isinstance(result, list) else []
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get project summary statistics."""
        result = self._make_rest_request(f'/projects/{project_id}/summary', method='GET')
        return result if isinstance(result, dict) else {}
    
    def get_metric_keys(self, run_id: str) -> List[str]:
        """Get available metric keys for a run."""
        result = self._make_rest_request(f'/runs/{run_id}/metric-keys', method='GET')
        if isinstance(result, list):
            return [str(item) for item in result]
        return [] 