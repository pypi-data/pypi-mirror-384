"""
Internal module for managing global state.
"""

# Global state
_current_run = None
_token = None
_api_base_url = "https://digilog-server.vercel.app/api/v1"
# _api_base_url = "http://localhost:3000/api/v1" ## For my local testers :)

def get_current_run():
    """Get the currently active run."""
    return _current_run

def set_api_base_url(url):
    """Set the API base URL."""
    global _api_base_url
    _api_base_url = url

def get_api_base_url():
    """Get the current API base URL."""
    return _api_base_url 