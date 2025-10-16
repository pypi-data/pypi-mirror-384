"""
Main client for the Debug Helper SDK.
"""

import os
import sys
import json
import traceback
import platform
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path


class DebugHelperException(Exception):
    """Custom exception for Debug Helper SDK errors."""
    pass


class DebugLogger:
    """
    Debug Helper SDK client for reporting issues programmatically.
    
    Usage:
        logger = DebugLogger(api_key="your_project_api_key")
        logger.issue(
            title="Payment API error",
            file_name="payments.py",
            line_number=101,
            log_path="/var/logs/error.log"
        )
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "http://127.0.0.1:8000",
        timeout: int = 30,
        retries: int = 3,
        auto_logging: bool = True
    ):
        """
        Initialize the Debug Helper client.
        
        Args:
            api_key: Project API key from Debug Helper dashboard
            api_url: Base URL of the Debug Helper API
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
            auto_logging: Whether to automatically capture environment info
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.auto_logging = auto_logging
        
        # Setup session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'debug-helper-sdk/1.0.0 (Python {sys.version.split()[0]})'
        })
        
        # Setup logging
        self.logger = logging.getLogger('debug_helper_sdk')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def issue(
        self,
        title: str,
        description: str = "",
        file_name: str = "",
        line_number: Optional[int] = None,
        function_name: str = "",
        log_path: Optional[Union[str, Path]] = None,
        severity: str = "medium",
        exception: Optional[Exception] = None,
        environment_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Report an issue to the Debug Helper service.
        
        Args:
            title: Short summary of the issue
            description: Detailed description of the issue
            file_name: Name of the file where the issue occurred
            line_number: Line number where the issue occurred
            function_name: Name of the function where the issue occurred
            log_path: Path to log file (local path or cloud URL)
            severity: Issue severity (low, medium, high, critical)
            exception: Python exception object to extract stack trace
            environment_info: Additional environment information
            
        Returns:
            Dictionary containing the created issue data
            
        Raises:
            DebugHelperException: If the API request fails
        """
        try:
            # Prepare issue data
            issue_data = {
                'title': title,
                'description': description,
                'file_name': file_name,
                'severity': severity
            }
            
            if line_number is not None:
                issue_data['line_number'] = line_number
            
            if function_name:
                issue_data['function_name'] = function_name
            
            # Extract stack trace from exception
            if exception:
                issue_data['stack_trace'] = ''.join(
                    traceback.format_exception(type(exception), exception, exception.__traceback__)
                )
                issue_data['error_type'] = type(exception).__name__
            
            # Collect environment information
            if self.auto_logging:
                env_info = self._collect_environment_info()
                if environment_info:
                    env_info.update(environment_info)
                issue_data['environment_info'] = env_info
            elif environment_info:
                issue_data['environment_info'] = environment_info
            
            # Create the issue
            response = self._make_request('POST', '/api/v1/issues/', data=issue_data)
            issue = response.json()
            
            self.logger.info(f"Issue created successfully: {issue.get('id')}")
            
            # Upload log file if provided
            if log_path:
                try:
                    self._upload_log_file(issue['id'], log_path)
                except Exception as e:
                    self.logger.warning(f"Failed to upload log file: {str(e)}")
            
            return issue
            
        except Exception as e:
            self.logger.error(f"Failed to create issue: {str(e)}")
            raise DebugHelperException(f"Failed to create issue: {str(e)}")
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect system and environment information."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'platform': sys.platform,
            },
            'environment_variables': {
                key: value for key, value in os.environ.items()
                if not key.lower().startswith(('password', 'secret', 'key', 'token'))
            },
            'working_directory': os.getcwd(),
            'process_id': os.getpid(),
        }
    
    def _upload_log_file(self, issue_id: str, log_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Upload a log file associated with an issue.
        
        Args:
            issue_id: ID of the issue to associate the log with
            log_path: Path to the log file (local path or URL)
            
        Returns:
            Dictionary containing the uploaded log file data
        """
        log_path = Path(log_path) if isinstance(log_path, str) else log_path
        
        if log_path.exists() and log_path.is_file():
            # Upload local file
            return self._upload_local_file(issue_id, log_path)
        elif str(log_path).startswith(('http://', 'https://', 's3://')):
            # Handle remote file reference
            return self._upload_remote_file_reference(issue_id, str(log_path))
        else:
            raise DebugHelperException(f"Log file not found: {log_path}")
    
    def _upload_local_file(self, issue_id: str, file_path: Path) -> Dict[str, Any]:
        """Upload a local file to the Debug Helper service."""
        try:
            # Prepare multipart form data
            files_data = {
                'file': (file_path.name, open(file_path, 'rb'), 'text/plain'),
                'issue_id': (None, str(issue_id)),
                'original_path': (None, str(file_path))
            }
            
            # Make request without JSON content-type for file upload
            session = requests.Session()
            session.headers.update({
                'Authorization': f'ApiKey {self.api_key}',
                'User-Agent': self.session.headers['User-Agent']
            })
            
            response = session.post(
                f"{self.api_url}/api/v1/logs/upload-sdk/",
                files=files_data,
                timeout=self.timeout
            )
            
            if response.status_code not in (200, 201):
                raise DebugHelperException(f"Upload failed: {response.text}")
            
            self.logger.info(f"Log file uploaded successfully: {file_path.name}")
            return response.json()
            
        except Exception as e:
            raise DebugHelperException(f"Failed to upload log file: {str(e)}")
        finally:
            # Ensure file is closed
            if 'file' in locals():
                files_data['file'][1].close()
    
    def _upload_remote_file_reference(self, issue_id: str, file_url: str) -> Dict[str, Any]:
        """Create a reference to a remote file (S3, HTTP, etc.)."""
        log_data = {
            'issue_id': issue_id,
            'original_path': file_url,
            'storage_type': 'url',
            'storage_url': file_url,
            'file_name': file_url.split('/')[-1]
        }
        
        response = self._make_request('POST', '/api/v1/logs/', data=log_data)
        return response.json()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an HTTP request to the Debug Helper API with retries.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            DebugHelperException: If all retry attempts fail
        """
        url = f"{self.api_url}{endpoint}"
        
        for attempt in range(self.retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, params=params, timeout=self.timeout)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=data, params=params, timeout=self.timeout)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, params=params, timeout=self.timeout)
                else:
                    raise DebugHelperException(f"Unsupported HTTP method: {method}")
                
                if response.status_code in (200, 201):
                    return response
                elif response.status_code == 401:
                    raise DebugHelperException("Invalid API key")
                elif response.status_code == 403:
                    raise DebugHelperException("Access denied")
                elif response.status_code == 404:
                    raise DebugHelperException("Resource not found")
                else:
                    error_msg = f"API request failed: {response.status_code} - {response.text}"
                    if attempt < self.retries:
                        self.logger.warning(f"Attempt {attempt + 1} failed, retrying... {error_msg}")
                        continue
                    else:
                        raise DebugHelperException(error_msg)
                        
            except requests.exceptions.Timeout:
                if attempt < self.retries:
                    self.logger.warning(f"Request timeout on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    raise DebugHelperException("Request timeout after all retries")
            except requests.exceptions.ConnectionError:
                if attempt < self.retries:
                    self.logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    raise DebugHelperException("Connection error after all retries")
    
    def test_connection(self) -> bool:
        """
        Test the connection to the Debug Helper API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self._make_request('GET', '/health/')
            return response.status_code == 200
        except:
            return False
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the current project.
        
        Returns:
            Dictionary containing project information
        """
        try:
            # This would require a project info endpoint
            # For now, return basic info
            return {
                'api_key': self.api_key[:8] + '...',
                'api_url': self.api_url,
                'connection_test': self.test_connection()
            }
        except Exception as e:
            raise DebugHelperException(f"Failed to get project info: {str(e)}")


# Convenience function for quick issue reporting
def report_issue(
    api_key: str,
    title: str,
    description: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Quick function to report an issue without creating a DebugLogger instance.
    
    Args:
        api_key: Project API key
        title: Issue title
        description: Issue description
        **kwargs: Additional arguments passed to DebugLogger.issue()
        
    Returns:
        Dictionary containing the created issue data
    """
    logger = DebugLogger(api_key)
    return logger.issue(title, description, **kwargs)