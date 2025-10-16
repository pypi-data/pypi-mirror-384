import os
import requests
import platform

# Try to load .env if python-dotenv is installed. Be robust: search upward from
# both the package location and the current working directory so editable installs
# and different working directories still pick up the project's .env.
try:
    from dotenv import load_dotenv
    def _find_and_load_dotenv(max_levels=6):
        # candidate directories: cwd, then package parent and upward
        candidates = []

        # start from current working directory
        cwd = os.path.abspath(os.getcwd())
        candidates.append(cwd)

        # also start from package directory (sdk/debug_helper)
        pkg_dir = os.path.abspath(os.path.dirname(__file__))
        candidates.append(pkg_dir)

        seen = set()
        for start in candidates:
            path = start
            for _ in range(max_levels):
                if path in seen:
                    break
                seen.add(path)
                dotenv_file = os.path.join(path, '.env')
                if os.path.isfile(dotenv_file):
                    load_dotenv(dotenv_file)
                    return dotenv_file
                parent = os.path.dirname(path)
                if parent == path:
                    break
                path = parent
        # Finally, try default load (lets python-dotenv search in cwd)
        load_dotenv()
        return None
    # If caller explicitly points to a dotenv file, prefer that (helps when
    # the package is installed non-editably in site-packages and the package
    # directory isn't inside the repository tree).
    explicit = os.environ.get('DEBUG_HELPER_DOTENV')
    if explicit:
        try:
            if os.path.isfile(explicit):
                load_dotenv(explicit)
            else:
                # Try to expand relative paths from CWD
                expanded = os.path.abspath(explicit)
                if os.path.isfile(expanded):
                    load_dotenv(expanded)
                else:
                    # Fall back to the search routine if the explicit path
                    # doesn't resolve to a file.
                    _find_and_load_dotenv()
        except Exception:
            # If explicit load fails for any reason, fall back to search.
            _find_and_load_dotenv()
    else:
        _find_and_load_dotenv()
except Exception:
    # If python-dotenv isn't available, provide a tiny fallback loader so the
    # SDK can still discover a nearby .env file when the package is installed
    # into site-packages (common when installed non-editably).
    def _parse_and_load_dotenv_file(dotenv_path):
        try:
            with open(dotenv_path, 'r', encoding='utf-8') as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    # remove surrounding single/double quotes
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    # Only set if not already present in the environment
                    if key and key not in os.environ:
                        os.environ[key] = val
            return True
        except Exception:
            return False

    def _find_and_load_dotenv_fallback(max_levels=6):
        candidates = []
        cwd = os.path.abspath(os.getcwd())
        candidates.append(cwd)
        pkg_dir = os.path.abspath(os.path.dirname(__file__))
        candidates.append(pkg_dir)
        seen = set()
        for start in candidates:
            path = start
            for _ in range(max_levels):
                if path in seen:
                    break
                seen.add(path)
                dotenv_file = os.path.join(path, '.env')
                if os.path.isfile(dotenv_file):
                    if _parse_and_load_dotenv_file(dotenv_file):
                        return dotenv_file
                parent = os.path.dirname(path)
                if parent == path:
                    break
                path = parent
        # no file found
        return None

    # prefer explicit env file path if provided
    explicit = os.environ.get('DEBUG_HELPER_DOTENV')
    if explicit:
        expanded = os.path.abspath(explicit)
        if os.path.isfile(expanded):
            _parse_and_load_dotenv_file(expanded)
        else:
            _find_and_load_dotenv_fallback()
    else:
        _find_and_load_dotenv_fallback()


class DebugHelperSDK:
    """
    Debug Helper SDK for creating issues using API Key or JWT authentication.
    Automatically handles environment info and project association.
    """

    def __init__(self, api_key: str, base_url: str = "http://194.242.33.189/api/v1"):
        self.base_url = base_url.rstrip("/")
        self.access_token = None
        self.refresh_token = None
        self.api_key = api_key

    # ---------------------
    # JWT Authentication
    # ---------------------
    def login(self, email: str, password: str):
        """Login user and store JWT tokens."""
        url = f"{self.base_url}/auth/login/"
        response = requests.post(url, json={"email": email, "password": password})
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.json()}")
        data = response.json()
        self.access_token = data['access']
        self.refresh_token = data.get('refresh')
        return data

    def refresh(self):
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        url = f"{self.base_url}/auth/refresh/"
        response = requests.post(url, json={"refresh": self.refresh_token})
        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.json()}")
        self.access_token = response.json()['access']
        return self.access_token

    # ---------------------
    # API Key
    # ---------------------
    def use_api_key(self, api_key: str):
        """Use API key authentication instead of JWT."""
        self.api_key = api_key

    @classmethod
    def from_env(cls, api_key: str):
        """Create SDK instance using base URL from environment and provided API key."""
        base = os.environ.get('DEBUG_HELPER_BASE_URL', 'http://194.242.33.189/api/v1')
        return cls(api_key=api_key, base_url=base)

    def _ensure_auth(self):
        if not self.access_token and not self.api_key:
            raise Exception("You must login or set an API key first")

    # ---------------------
    # Projects (JWT only)
    # ---------------------
    def get_projects(self):
        """Fetch all projects available for the authenticated user (JWT only)."""
        self._ensure_auth()
        if self.api_key:
            raise Exception("Project list not available using API key")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.base_url}/projects/"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch projects: {response.json()}")
        return response.json()

    def get_project_id_by_name(self, name: str):
        """Get project ID by name (JWT only)."""
        projects = self.get_projects()
        for proj in projects:
            if proj['name'].lower() == name.lower():
                return proj['id']
        return None

    def create_project(self, name: str, slug: str = None, description: str = ""):
        """Create a new project (superadmin only, JWT required)."""
        self._ensure_auth()
        if self.api_key:
            raise Exception("Cannot create project using API key")
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        if not slug:
            slug = name.lower().replace(" ", "-")
        payload = {"name": name, "slug": slug, "description": description}
        url = f"{self.base_url}/projects/"
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code not in [200, 201]:
            raise Exception(f"Project creation failed: {response.json()}")
        return response.json()['id']

    # ---------------------
    # Issues
    # ---------------------
    def create_issue(
        self,
        title: str,
        description: str = "",
        severity: str = "medium",
        file_name: str = "",
        line_number: int = None,
        function_name: str = "",
        stack_trace: str = "",
        error_type: str = "",
        environment_info: dict = None,
        project_name: str = None,
        project_id: str = None,
        # Optional external API logging
        api_url: str = None,
        api_headers: dict = None,
        api_request_body: any = None,
        api_response: any = None,
        api_response_headers: dict = None,
        api_status_code: int = None
    ):
        """
        Create an issue using API Key or JWT authentication.
        API Key: automatically associates the project.
        JWT: project_name or project_id must be provided.
        """
        self._ensure_auth()

        # Build headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        else:
            headers["Authorization"] = f"Bearer {self.access_token}"

        # Prepare environment info
        if environment_info is None:
            environment_info = self._default_environment_info()

        # Add external API logging if provided
        external_api = {}
        if api_url:
            external_api['url'] = api_url
        if api_headers:
            external_api['request_headers'] = api_headers
        if api_request_body is not None:
            external_api['request_body'] = api_request_body
        if api_status_code:
            external_api['status_code'] = api_status_code
        if api_response_headers:
            external_api['response_headers'] = api_response_headers
        if api_response is not None:
            external_api['response'] = self._parse_api_response(api_response)

        if external_api:
            environment_info['external_api'] = external_api

        # Resolve project_id for JWT auth
        if not self.api_key:
            if not project_id:
                if not project_name:
                    raise Exception("You must provide project_name or project_id when using JWT")
                project_id = self.get_project_id_by_name(project_name)
                if not project_id:
                    project_id = self.create_project(project_name)

        # Build payload
        payload = {
            "title": title,
            "description": description,
            "severity": severity,
            "file_name": file_name,
            "line_number": line_number,
            "function_name": function_name,
            "stack_trace": stack_trace,
            "error_type": error_type,
            "environment_info": environment_info,
        }

        # Add project info
        if self.api_key:
            payload["project_api_key"] = self.api_key
        else:
            payload["project_id"] = project_id

        # Remove None or empty values
        payload = {k: v for k, v in payload.items() if v not in [None, ""]}

        # Print request for debugging
        print("=== DEBUG ===")
        print("URL:", f"{self.base_url}/issues/")
        print("Headers:", headers)
        print("Payload:", payload)
        print("=============")

        # Send POST request
        response = requests.post(f"{self.base_url}/issues/", json=payload, headers=headers)

        try:
            data = response.json()
        except Exception:
            data = response.text

        if response.status_code not in [200, 201]:
            raise Exception(f"Issue creation failed: {data}")

        # Return minimal response like Postman
        minimal_response = {
            "title": data.get("title"),
            "description": data.get("description"),
            "severity": data.get("severity"),
            "assigned_to": data.get("assigned_to"),
        }

        return minimal_response

    def _parse_api_response(self, response):
        """Parse API response robustly, handling different types."""
        try:
            # If it's a requests.Response object
            if hasattr(response, 'text') and hasattr(response, 'json'):
                try:
                    return response.json()  # Try JSON first
                except Exception:
                    return response.text  # Fall back to text
            # If it's already a dict (parsed JSON)
            elif isinstance(response, dict):
                return response
            # If it's a list
            elif isinstance(response, list):
                return response
            # If it's a string
            elif isinstance(response, str):
                # Try to parse as JSON
                try:
                    import json
                    return json.loads(response)
                except Exception:
                    return response  # Keep as string
            # For other types, convert to string
            else:
                return str(response)
        except Exception:
            # If anything fails, just return as string
            return str(response)


# ---------------------
# Example Usage
# ---------------------
if __name__ == "__main__":
    # Example usage
    sdk = DebugHelperSDK(api_key="dh_I9yXl0tby4hPgtaviYU9b9dgH-dH01ekmD5E_WPJQF0")

    issue = sdk.create_issue(
        title="Unhandled NullReference in worker",
        description="NullRef in worker.process_job when input is missing key",
        file_name="worker.py",
        line_number=123,
        function_name="process_job",
        stack_trace="""Traceback (most recent call last):
        File "/app/worker.py", line 123, in process_job
            x.y()
        AttributeError: 'NoneType' object has no attribute 'y'""",
        error_type="AttributeError",
        severity="critical",
        environment_info={
            "python": "3.11.4",
            "platform": "linux",
            "app_version": "1.2.3",
            "hostname": "worker-02"
        },
        # Example external API logging
        api_url="https://api.example.com/data",
        api_headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
        api_request_body={"query": "test"},
        api_response={"data": "example response"},
        api_response_headers={"Content-Type": "application/json"},
        api_status_code=200
    )

    print("Issue created:", issue)