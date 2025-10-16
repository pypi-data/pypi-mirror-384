"""Bitbucket API client for pull request operations."""

import base64
from typing import Any, Optional

import requests

from ..core.config import get_app_config, get_cache_manager
from ..core.models import FileChange, PullRequestDiff, PullRequestInfo


class BitbucketClient:
    """Client for interacting with Bitbucket API."""

    BASE_URL = "https://api.bitbucket.org/2.0"

    def __init__(
        self,
        workspace: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
    ):
        """Initialize Bitbucket client.

        Args:
            workspace: Bitbucket workspace name
            token: Bitbucket API token (App Password or Repository Access Token)
            username: Bitbucket username (required for App Password authentication)
        """
        self.workspace = workspace
        self.app_config = get_app_config()
        self.token = token or self.app_config.bitbucket_token
        self.username = username or self.app_config.bitbucket_auth_username
        self.cache_manager = get_cache_manager()

        if not self.token:
            raise ValueError(
                "Bitbucket API token is required. "
                "Set BITBUCKET_TOKEN environment variable."
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Debug ALL environment variables
        import os

        print("🔍 ALL ENV VARS containing 'AUTH' or 'TOKEN' or 'BITBUCKET':")
        for key, value in os.environ.items():
            if "AUTH" in key or "TOKEN" in key or "BITBUCKET" in key:
                print(f"   {key} = '{value[:20]}...' ({len(value)} chars)")

        # Try to get values directly from environment
        direct_username = os.environ.get("BB_AUTH_USERNAME")
        direct_token = os.environ.get("BITBUCKET_TOKEN")

        print(f"🔍 DIRECT: BB_AUTH_USERNAME from os.environ = '{direct_username}'")
        token_part = direct_token[:10] if direct_token else None
        print(f"🔍 DIRECT: BITBUCKET_TOKEN from os.environ = '{token_part}...'")

        # Override with direct environment values if available
        if direct_username:
            self.username = direct_username
            print(f"✅ OVERRIDE: Using direct BB_AUTH_USERNAME = '{self.username}'")

        if direct_token:
            self.token = direct_token
            print(f"✅ OVERRIDE: Using direct BITBUCKET_TOKEN = '{self.token[:10]}...'")

        # Debug Pydantic config loading
        raw_config = self.app_config
        auth_val = raw_config.bitbucket_auth_username
        token_val = (
            raw_config.bitbucket_token[:10] + "..."
            if raw_config.bitbucket_token
            else None
        )
        print(f"🔍 Pydantic config: bitbucket_auth_username = '{auth_val}'")
        print(f"🔍 Pydantic config: bitbucket_token = '{token_val}'")

        print(f"🔍 Client init: self.username = '{self.username}'")
        token_status = "***" if self.token else "None"
        print(f"🔍 Client init: self.token = '{token_status}'")

        # Set up authentication based on token type
        self._setup_authentication()

    def validate_token(self) -> bool:
        """Validate that the token works for basic API access.

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Test with a simple repository info call (doesn't require PR permissions)
            test_url = f"{self.BASE_URL}/repositories/{self.workspace}"
            self._make_request("GET", test_url)
            print("✅ Token validation successful")
            return True
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            return False

    def _setup_authentication(self) -> None:
        """Set up authentication based on token type.

        Uses Basic Auth for App Passwords (when username is provided)
        Uses Bearer Auth for Repository Access Tokens (when no username provided)
        """
        print(f"🔐 Setting up auth - username: '{self.username}', token length: {len(self.token) if self.token else 0}")

        if self.username:
            # App Password: Use Basic Auth
            credentials = f"{self.username}:{self.token}"
            print(f"🔐 Credentials string: {self.username}:***")
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            print(f"🔐 Base64 encoded: {encoded_credentials[:20]}...")
            self.session.headers["Authorization"] = f"Basic {encoded_credentials}"
            print("🔐 Using Basic Auth (App Password)")
            print(f"🔐 Final auth header: Basic {encoded_credentials[:20]}...")
        else:
            # Repository Access Token: Use Bearer Auth
            self.session.headers["Authorization"] = f"Bearer {self.token}"
            print("🔐 Using Bearer Auth (Repository Access Token)")
            print(f"🔐 Final auth header: Bearer {self.token[:20]}...")

    def get_pull_request(self, repo_slug: str, pr_id: int) -> PullRequestInfo:
        """Get pull request information.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID

        Returns:
            PullRequestInfo object
        """
        url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}"
        )
        response = self._make_request("GET", url)

        pr_data = response.json()

        return PullRequestInfo(
            id=pr_data["id"],
            title=pr_data["title"],
            description=pr_data.get("description", ""),
            source_branch=pr_data["source"]["branch"]["name"],
            target_branch=pr_data["destination"]["branch"]["name"],
            author=pr_data["author"]["display_name"],
            state=pr_data["state"],
        )

    def get_pull_request_diff(self, repo_slug: str, pr_id: int) -> PullRequestDiff:
        """Get the diff for a pull request.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID

        Returns:
            PullRequestDiff object with diff content and file changes
        """
        cache_key = f"pr_diff_{self.workspace}_{repo_slug}_{pr_id}"

        # Try to get from cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            return PullRequestDiff(**cached_data)

        # Get PR info
        pr_info = self.get_pull_request(repo_slug, pr_id)

        # Get diff content
        diff_url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/diff"
        )
        response = self._make_request("GET", diff_url)
        diff_content = response.text

        # Get file changes from diffstat
        diffstat_url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/diffstat"
        )
        response = self._make_request("GET", diffstat_url)
        diffstat_data = response.json()

        files = []
        for file_data in diffstat_data.get("values", []):
            files.append(
                FileChange(
                    filename=file_data["new"]["path"],
                    status=file_data["status"],
                    additions=file_data.get("lines_added", 0),
                    deletions=file_data.get("lines_removed", 0),
                )
            )

        result = PullRequestDiff(
            pull_request=pr_info,
            files=files,
            diff_content=diff_content,
        )

        # Cache the result
        self.cache_manager.set(cache_key, result.model_dump())

        return result

    def add_pull_request_comment(
        self,
        repo_slug: str,
        pr_id: int,
        content: str,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        from_line: Optional[int] = None,
        to_line: Optional[int] = None,
    ) -> dict[str, Any]:
        """Add a comment to a pull request.

        Args:
            repo_slug: Repository slug
            pr_id: Pull request ID
            content: Comment content
            file_path: Optional file path for inline comment
            line: Optional line number for inline comment

        Returns:
            Comment data from API
        """
        url = (
            f"{self.BASE_URL}/repositories/{self.workspace}/"
            f"{repo_slug}/pullrequests/{pr_id}/comments"
        )

        comment_data = {"content": {"raw": content}}

        # Add inline comment data if provided
        if file_path and (line is not None or to_line is not None or from_line is not None):
            inline: dict[str, Any] = {"path": file_path}
            if from_line is not None and to_line is not None:
                inline["from"] = from_line
                inline["to"] = to_line
            elif to_line is not None:
                inline["to"] = to_line
            else:
                inline["to"] = line
            comment_data["inline"] = inline

        response = self._make_request("POST", url, json=comment_data)
        return response.json()

    def get_repository_info(self, repo_slug: str) -> dict[str, Any]:
        """Get repository information.

        Args:
            repo_slug: Repository slug

        Returns:
            Repository data from API
        """
        url = f"{self.BASE_URL}/repositories/{self.workspace}/{repo_slug}"
        response = self._make_request("GET", url)
        return response.json()

    def _make_request(
        self,
        method: str,
        url: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        """Make an HTTP request to Bitbucket API.

        Args:
            method: HTTP method
            url: Request URL
            json: JSON payload
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails
        """
        print(f"🔍 Making {method} request to: {url}")
        print(f"📂 Repository: {self.workspace}")
        auth_header = self.session.headers.get("Authorization", "None")
        if auth_header != "None":
            auth_type = auth_header.split()[0] if len(auth_header.split()) > 0 else "Unknown"
            auth_value = auth_header.split()[1][:20] + "..." if len(auth_header.split()) > 1 else "No value"
            print(f"🔐 Auth header: {auth_type} {auth_value}")
        else:
            print(f"🔐 Auth header: None")

        response = self.session.request(method, url, json=json, params=params)

        if not response.ok:
            print(f"❌ Request failed: {response.status_code}")
            print(f"❌ Response headers: {dict(response.headers)}")
            error_data = response.json() if response.content else {}
            print(f"❌ Error data: {error_data}")
            raise requests.HTTPError(
                f"Bitbucket API error {response.status_code}: "
                f"{error_data.get('error', {}).get('message', 'Unknown error')}"
            )

        print(f"✅ Request successful: {response.status_code}")
        return response


def create_bitbucket_client(
    workspace: str, token: Optional[str] = None, username: Optional[str] = None
) -> BitbucketClient:
    """Create a Bitbucket client instance.

    Args:
        workspace: Bitbucket workspace
        token: Optional API token
        username: Optional username for App Password authentication

    Returns:
        Configured Bitbucket client
    """
    return BitbucketClient(workspace, token, username)
