import os
import json
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import sys


def load_env_file(env_file='.env'):
    """Load environment variables from .env file."""
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


load_env_file()


class BasePortManager:
    """Base class for all Port.io managers with shared functionality."""

    def __init__(self, client_id: str, client_secret: str, port_host: str = "api.port.io",
                 manager_name: str = "BasePortManager"):
        """
        Initialize the base Port manager.

        Args:
            client_id: Port.io client ID for authentication
            client_secret: Port.io client secret for authentication
            port_host: Port.io API host (default: api.port.io)
            manager_name: Name of the manager for logging
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.port_host = port_host
        self.access_token = None
        self.logger = self._setup_logger(manager_name)

    def _setup_logger(self, manager_name: str) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(manager_name)

        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_access_token(self) -> Optional[str]:
        """
        Get access token using client ID and client secret.

        Returns:
            Access token string or None if failed
        """
        if self.access_token:
            return self.access_token

        try:
            url = f"https://{self.port_host}/v1/auth/access_token"
            payload = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            }

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('accessToken')

                if self.access_token:
                    return self.access_token
                else:
                    self.logger.error("No access token in response")
                    return None
            else:
                self.logger.error(f"Authentication failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during authentication: {e}")
            return None

    def make_api_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
                         params: Optional[Dict[str, Any]] = None, silent_404: bool = False) -> Optional[Dict[str, Any]]:
        """
        Make an authenticated API request to Port.io.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            silent_404: If True, don't log 404 errors (useful for existence checks)

        Returns:
            Response data as dictionary or None if failed
        """
        access_token = self.get_access_token()
        if not access_token:
            self.logger.error("Failed to get access token")
            return None

        try:
            url = f"https://{self.port_host}{endpoint}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 404 and silent_404:
                # Don't log 404 as error when doing existence checks
                return None
            else:
                self.logger.error(f"Request failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making {method} request to {endpoint}: {e}")
            return None

    def discover_json_files(self, directory: str, file_type: str = "files") -> list:
        """
        Discover all JSON files in the specified directory.
        Files are processed in priority order: .blueprint.json files before .extra.json files.

        Args:
            directory: Path to the directory
            file_type: Type of files for logging (e.g., "blueprints", "mappings")

        Returns:
            List of file information dictionaries
        """
        files = []
        directory_path = Path(directory)

        if not directory_path.exists():
            self.logger.error(f"{file_type.title()} directory not found: {directory}")
            return files

        json_files = list(directory_path.glob("*.json"))

        if not json_files:
            self.logger.warning(f"No JSON files found in {directory}")
            return files

        # Since all files now use .json extension, sort alphabetically
        json_files.sort(key=lambda x: x.name)

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                files.append({
                    'file_path': str(json_file),
                    'filename': json_file.name,
                    'data': file_data
                })

            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {json_file.name}: {e}")
            except Exception as e:
                self.logger.error(f"Error loading {json_file.name}: {e}")

        return files

    def get_strategy(self, manager_type: str) -> str:
        """
        Get the merge strategy for a specific manager type.

        Args:
            manager_type: Type of manager ('blueprints', 'actions', 'mappings', 'widgets')

        Returns:
            Strategy string (defaults to 'merge')
        """
        return 'merge'  # Always use merge strategy

    def should_continue_on_error(self) -> bool:
        """Check if should continue processing when errors occur."""
        return False  # Always stop on error for safety
