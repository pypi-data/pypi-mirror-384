"""
Core client for the Zoho Creator SDK.
"""

import logging
import time
from collections.abc import Generator, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, NoReturn, Optional, cast

import httpx
from pydantic import ValidationError as PydanticValidationError

from .auth import BaseAuthHandler, get_auth_handler
from .config import ConfigManager
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    ResourceNotFoundError,
    ServerError,
    ZohoPermissionError,
    ZohoTimeoutError,
)
from .models import (
    APIConfig,
    Application,
    Connection,
    CustomAction,
    Page,
    Permission,
    Record,
    Section,
    Workflow,
)

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client wrapper for making API requests."""

    def __init__(self, auth_handler: BaseAuthHandler, config: APIConfig) -> None:
        self.auth_handler = auth_handler
        self.config = config
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.config.timeout),
            follow_redirects=True,
        )
        self.client.headers.update(
            {"User-Agent": "zoho-creator-sdk/0.1.0", "Content-Type": "application/json"}
        )

    def get(
        self, url: str, params: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform a GET request."""
        return self._make_request("GET", url, params=params)

    def post(
        self, url: str, json: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform a POST request."""
        return self._make_request("POST", url, json=json)

    def patch(
        self, url: str, json: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Perform a PATCH request."""
        return self._make_request("PATCH", url, json=json)

    def delete(self, url: str) -> Mapping[str, Any]:
        """Perform a DELETE request."""
        return self._make_request("DELETE", url)

    def _make_request(self, method: str, url: str, **kwargs: Any) -> Mapping[str, Any]:
        """Make an HTTP request with authentication, retries, and error handling."""
        # Get authentication headers
        headers = self.auth_handler.get_auth_headers()
        existing_headers = kwargs.get("headers", {})
        kwargs["headers"] = {**existing_headers, **headers}

        # Log the request
        logger.debug("Making %s request to %s", method, url)
        if kwargs.get("params"):
            logger.debug("Request params: %s", kwargs["params"])
        if kwargs.get("json"):
            logger.debug("Request body: %s", kwargs["json"])

        # Try the request with automatic token refresh on 401 errors
        try:
            response = self._make_request_with_retry(method, url, **kwargs)
            result = self._process_response(response)

            # Log the response
            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response body: %s", result)

            return result
        except AuthenticationError:
            # If we get an authentication error, try refreshing the token once
            logger.info("Authentication error. Attempting token refresh and retry.")
            try:
                self.auth_handler.refresh_auth()
                # Update headers with new token
                headers = self.auth_handler.get_auth_headers()
                existing_headers = kwargs.get("headers", {})
                kwargs["headers"] = {**existing_headers, **headers}
                # Retry the request
                response = self._make_request_with_retry(method, url, **kwargs)
                result = self._process_response(response)

                # Log the response
                logger.debug("Response status after retry: %s", response.status_code)
                logger.debug("Response body after retry: %s", result)

                return result
            except AuthenticationError as e:
                logger.error("Failed to refresh authentication token: %s", e)
                raise

    def _make_request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        """Make an HTTP request with retry logic for server errors."""
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)

                # Handle rate limiting (429 errors)
                if response.status_code == 429:
                    retry_after = self._get_retry_after(response)
                    logger.warning(
                        "Rate limit hit (429). Retrying after %s seconds.", retry_after
                    )
                    if attempt < self.config.max_retries:
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError("Rate limit exceeded after retry.")

                # Handle server errors (5xx)
                if response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (2**attempt)
                        logger.warning(
                            "Server error (%s). Retrying in %.2f seconds.",
                            response.status_code,
                            delay,
                        )
                        time.sleep(delay)
                        continue
                    # If we've exhausted retries, raise ServerError
                    try:
                        data = response.json()
                        error_message = data.get("message", "Server error")
                        error_code = data.get("code")
                    except ValueError:
                        error_message = f"Server error: {response.status_code}"
                        error_code = None
                    raise ServerError(error_message, response.status_code, error_code)

                return response

            except (httpx.TimeoutException, httpx.ConnectError, NetworkError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning("Network error. Retrying in %.2f seconds.", delay)
                    time.sleep(delay)
                    continue
                if isinstance(e, httpx.TimeoutException):
                    raise TimeoutError(
                        f"Request timed out after {self.config.timeout} seconds."
                    ) from e
                if isinstance(e, httpx.ConnectError):
                    raise NetworkError(f"Connection error: {e}") from e
                raise NetworkError(
                    f"Network error after {self.config.max_retries} retries."
                ) from e

        raise last_exception or APIError("Request failed after retries.")

    def _get_retry_after(self, response: httpx.Response) -> float:
        """Extract the Retry-After value from response headers."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                # Try to parse as HTTP date format
                try:
                    retry_date = datetime.strptime(
                        retry_after, "%a, %d %b %Y %H:%M:%S GMT"
                    ).replace(tzinfo=timezone.utc)
                    return (retry_date - datetime.now(timezone.utc)).total_seconds()
                except ValueError:
                    pass
        return self.config.retry_delay

    def _process_response(self, response: httpx.Response) -> Mapping[str, Any]:
        """Process the HTTP response and handle errors."""
        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.text.strip():
                return {}
            try:
                data = response.json()
                return cast(Mapping[str, Any], data)
            except ValueError as exc:
                raise APIError(
                    f"Invalid JSON response: {response.text}",
                    status_code=response.status_code,
                ) from exc
        else:
            try:
                data = response.json()
            except ValueError as exc:
                raise APIError(
                    f"Invalid JSON response: {response.text}",
                    status_code=response.status_code,
                ) from exc
            self._handle_error_response(response, data)

    def _handle_error_response(
        self, response: httpx.Response, data: Mapping[str, Any]
    ) -> NoReturn:
        """Handle API error responses."""
        status_code = response.status_code
        error_message = data.get("message", "Unknown error")
        error_code = data.get("code")

        if status_code == 400:
            raise BadRequestError(error_message, status_code, error_code)
        if status_code == 401:
            raise AuthenticationError(message=error_message, error_code=error_code)
        if status_code == 403:
            raise ZohoPermissionError(error_message, status_code, error_code)
        if status_code == 404:
            raise ResourceNotFoundError(error_message, status_code, error_code)
        if status_code == 408:
            raise ZohoTimeoutError(error_message, status_code, error_code)
        if status_code == 429:
            raise QuotaExceededError(error_message, status_code, error_code)
        if status_code >= 500:
            raise ServerError(error_message, status_code, error_code)

        raise APIError(error_message, status_code, error_code)


class AppContext:
    """Fluent interface helper for application-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        owner_name: str,
        app_name: Optional[str] = None,
    ) -> None:
        self.http_client = http_client
        self.app_link_name: str = app_link_name or app_name or ""
        self.owner_name = owner_name

    def form(
        self, form_link_name: str, form_name: Optional[str] = None
    ) -> "FormContext":
        """Get a form instance for this application."""
        form_name_to_use = form_link_name or form_name
        if not form_name_to_use:
            raise ValueError("Either form_link_name or form_name must be provided")
        return FormContext(
            self.http_client,
            self.app_link_name,
            form_name_to_use,
            self.owner_name,
        )

    def report(
        self, report_link_name: str, report_name: Optional[str] = None
    ) -> "ReportContext":
        """Get a report instance for this application."""
        report_name_to_use = report_link_name or report_name
        if not report_name_to_use:
            raise ValueError("Either report_link_name or report_name must be provided")
        return ReportContext(
            self.http_client,
            self.app_link_name,
            report_name_to_use,
            self.owner_name,
        )

    def workflow(
        self, workflow_link_name: str, workflow_name: Optional[str] = None
    ) -> "WorkflowContext":
        """Get a workflow instance for this application."""
        workflow_name_to_use = workflow_link_name or workflow_name
        if not workflow_name_to_use:
            raise ValueError(
                "Either workflow_link_name or workflow_name must be provided"
            )
        return WorkflowContext(
            self.http_client,
            self.app_link_name,
            workflow_name_to_use,
            self.owner_name,
        )

    def permission(self, permission_id: str) -> "PermissionContext":
        """Get a permission instance for this application."""
        return PermissionContext(
            self.http_client,
            self.app_link_name,
            permission_id,
            self.owner_name,
        )

    def connection(self, connection_id: str) -> "ConnectionContext":
        """Get a connection instance for this application."""
        return ConnectionContext(
            self.http_client,
            self.app_link_name,
            connection_id,
            self.owner_name,
        )

    def custom_action(
        self, custom_action_link_name: str, custom_action_name: Optional[str] = None
    ) -> "CustomActionContext":
        """Get a custom action instance for this application."""
        custom_action_name_to_use = custom_action_link_name or custom_action_name
        if not custom_action_name_to_use:
            raise ValueError(
                "Either custom_action_link_name or custom_action_name must be provided"
            )
        return CustomActionContext(
            self.http_client,
            self.app_link_name,
            custom_action_name_to_use,
            self.owner_name,
        )


class FormContext:
    """Fluent interface helper for form-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        form_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.form_link_name = form_link_name
        self.owner_name = owner_name

    def add_record(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Add a new record to this form.

        Args:
            data: The record data to add

        Returns:
            Dict containing the created record information
        """
        url = (
            f"{self.http_client.config.base_url}/data/{self.owner_name}/"
            f"{self.app_link_name}/form/{self.form_link_name}"
        )
        payload = {"data": data}
        return self.http_client.post(url, json=payload)

    def get_records(self, **kwargs: Any) -> Generator[Record, None, None]:
        """Get records from this form with automatic pagination.

        Returns a generator that yields records one by one, automatically
        fetching subsequent pages as needed.

        Args:
            **kwargs: Additional query parameters for the API request

        Yields:
            Record: Individual records from the form
        """
        base_url = self.http_client.config.base_url
        url = (
            f"{base_url}/data/{self.owner_name}/{self.app_link_name}/"
            f"form/{self.form_link_name}"
        )

        # Continue fetching pages until no more records are available
        while True:
            response_data = self.http_client.get(url, params=kwargs)

            # Extract records from the current page
            records_data = response_data.get("data", [])
            if not records_data:
                break

            # Yield each record individually
            for record_data in records_data:
                try:
                    yield Record(**record_data)
                except PydanticValidationError as e:
                    raise APIError(f"Failed to parse record data: {e}") from e

            # Check for pagination indicators in the response meta
            meta = response_data.get("meta", {})
            more_records = meta.get("more_records", False)
            next_page_token = meta.get("next_page_token")

            # If there's no more_records, we're done
            if not more_records:
                break

            # If there's a next_page_token, use it for pagination
            if next_page_token:
                kwargs["next_page_token"] = next_page_token
            else:
                # If no token but more_records is True, this shouldn't happen
                # but we'll break to avoid infinite loops
                logger.warning("more_records is True but no next_page_token provided")
                break


class ReportContext:
    """Fluent interface helper for report-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        report_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.report_link_name = report_link_name
        self.owner_name = owner_name

    def get_records(self, **kwargs: Any) -> Generator[Record, None, None]:
        """Get records from this report with automatic pagination.

        Returns a generator that yields records one by one, automatically
        fetching subsequent pages as needed.

        Args:
            **kwargs: Additional query parameters for the API request

        Yields:
            Record: Individual records from the report
        """
        base_url = self.http_client.config.base_url
        url = (
            f"{base_url}/data/{self.owner_name}/{self.app_link_name}/report/"
            f"{self.report_link_name}"
        )

        # Continue fetching pages until no more records are available
        while True:
            response_data = self.http_client.get(url, params=kwargs)

            # Extract records from the current page
            records_data = response_data.get("data", [])
            if not records_data:
                break

            # Yield each record individually
            for record_data in records_data:
                try:
                    yield Record(**record_data)
                except PydanticValidationError as e:
                    raise APIError(f"Failed to parse record data: {e}") from e

            # Check for pagination indicators in the response meta
            meta = response_data.get("meta", {})
            more_records = meta.get("more_records", False)
            next_page_token = meta.get("next_page_token")

            # If there's no more_records, we're done
            if not more_records:
                break

            # If there's a next_page_token, use it for pagination
            if next_page_token:
                kwargs["next_page_token"] = next_page_token
            else:
                # If no token but more_records is True, this shouldn't happen
                # but we'll break to avoid infinite loops
                logger.warning("more_records is True but no next_page_token provided")
                break


class WorkflowContext:
    """Fluent interface helper for workflow-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        workflow_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.workflow_link_name = workflow_link_name
        self.owner_name = owner_name

    def get_workflow(self) -> Workflow:
        """Get the workflow details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/workflow/{self.workflow_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Workflow(**response_data.get("workflow", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse workflow data: {e}") from e

    def execute_workflow(self, record_id: str, **kwargs: Any) -> Mapping[str, Any]:
        """Execute the workflow on a specific record."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/workflow/{self.workflow_link_name}/"
            f"{record_id}/execute"
        )
        payload = {"data": kwargs}
        return self.http_client.post(url, json=payload)


class PermissionContext:
    """Fluent interface helper for permission-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        permission_id: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.permission_id = permission_id
        self.owner_name = owner_name

    def get_permission(self) -> Permission:
        """Get the permission details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/permission/{self.permission_id}"
        )
        response_data = self.http_client.get(url)
        try:
            return Permission(**response_data.get("permission", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse permission data: {e}") from e

    def update_permission(self, data: Mapping[str, Any]) -> Mapping[str, Any]:
        """Update the permission."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/permission/{self.permission_id}"
        )
        payload = {"data": data}
        return self.http_client.patch(url, json=payload)


class ConnectionContext:
    """Fluent interface helper for connection-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        connection_id: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.connection_id = connection_id
        self.owner_name = owner_name

    def get_connection(self) -> Connection:
        """Get the connection details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/connection/{self.connection_id}"
        )
        response_data = self.http_client.get(url)
        try:
            return Connection(**response_data.get("connection", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse connection data: {e}") from e

    def test_connection(self) -> Mapping[str, Any]:
        """Test the connection."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/connection/{self.connection_id}/test"
        )
        return self.http_client.get(url)


class CustomActionContext:
    """Fluent interface helper for custom action-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        custom_action_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.custom_action_link_name = custom_action_link_name
        self.owner_name = owner_name

    def get_custom_action(self) -> CustomAction:
        """Get the custom action details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/customaction/{self.custom_action_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return CustomAction(**response_data.get("customaction", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse custom action data: {e}") from e

    def execute_custom_action(self, record_id: str, **kwargs: Any) -> Mapping[str, Any]:
        """Execute the custom action on a specific record."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/customaction/{self.custom_action_link_name}/"
            f"{record_id}/execute"
        )
        payload = {"data": kwargs}
        return self.http_client.post(url, json=payload)


class PageContext:
    """Fluent interface helper for page-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        page_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.page_link_name = page_link_name
        self.owner_name = owner_name

    def get_page(self) -> Page:
        """Get the page details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/page/{self.page_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Page(**response_data.get("page", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse page data: {e}") from e


class SectionContext:
    """Fluent interface helper for section-specific operations."""

    def __init__(
        self,
        http_client: HTTPClient,
        app_link_name: str,
        section_link_name: str,
        owner_name: str,
    ) -> None:
        self.http_client = http_client
        self.app_link_name = app_link_name
        self.section_link_name = section_link_name
        self.owner_name = owner_name

    def get_section(self) -> Section:
        """Get the section details."""
        url = (
            f"{self.http_client.config.base_url}/settings/{self.owner_name}/"
            f"{self.app_link_name}/section/{self.section_link_name}"
        )
        response_data = self.http_client.get(url)
        try:
            return Section(**response_data.get("section", {}))
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse section data: {e}") from e


class ZohoCreatorClient:
    """The main client for interacting with the Zoho Creator API."""

    def __init__(self) -> None:
        """Initialize the Zoho Creator client with zero-config setup."""
        # Create a ConfigManager which will automatically load from env vars and files
        self.config_manager = ConfigManager()

        # Use the loaded config to create the AuthHandler and HTTPClient internally
        self.auth_config = self.config_manager.get_auth_config()
        self.api_config = self.config_manager.get_api_config()

        # Create the auth handler
        self.auth_handler = get_auth_handler(self.auth_config, self.api_config)

        # Create the HTTP client
        self.http_client = HTTPClient(self.auth_handler, self.api_config)

    def workflow(
        self, app_link_name: str, owner_name: str, workflow_link_name: str
    ) -> WorkflowContext:
        """Get a workflow context for fluent interface operations."""
        return WorkflowContext(
            self.http_client, app_link_name, workflow_link_name, owner_name
        )

    def permission(
        self, app_link_name: str, owner_name: str, permission_id: str
    ) -> PermissionContext:
        """Get a permission context for fluent interface operations."""
        return PermissionContext(
            self.http_client, app_link_name, permission_id, owner_name
        )

    def connection(
        self, app_link_name: str, owner_name: str, connection_id: str
    ) -> ConnectionContext:
        """Get a connection context for fluent interface operations."""
        return ConnectionContext(
            self.http_client, app_link_name, connection_id, owner_name
        )

    def custom_action(
        self, app_link_name: str, owner_name: str, custom_action_link_name: str
    ) -> CustomActionContext:
        """Get a custom action context for fluent interface operations."""
        return CustomActionContext(
            self.http_client, app_link_name, custom_action_link_name, owner_name
        )

    def form(
        self, app_link_name: str, owner_name: str, form_link_name: str
    ) -> FormContext:
        """Get a form context for fluent interface operations."""
        return FormContext(self.http_client, app_link_name, form_link_name, owner_name)

    def report(
        self, app_link_name: str, owner_name: str, report_link_name: str
    ) -> ReportContext:
        """Get a report context for fluent interface operations."""
        return ReportContext(
            self.http_client, app_link_name, report_link_name, owner_name
        )

    def page(
        self, app_link_name: str, owner_name: str, page_link_name: str
    ) -> PageContext:
        """Get a page context for fluent interface operations."""
        return PageContext(self.http_client, app_link_name, page_link_name, owner_name)

    def section(
        self, app_link_name: str, owner_name: str, section_link_name: str
    ) -> SectionContext:
        """Get a section context for fluent interface operations."""
        return SectionContext(
            self.http_client, app_link_name, section_link_name, owner_name
        )

    def application(
        self, app_link_name: str, owner_name: str, app_name: Optional[str] = None
    ) -> AppContext:
        """Get an application context for fluent interface operations."""
        return AppContext(self.http_client, app_link_name, owner_name, app_name)

    def get_applications(self, owner_name: str) -> Sequence[Application]:
        """Get all applications."""
        url = f"{self.api_config.base_url}/meta/{owner_name}/applications"
        response_data = self.http_client.get(url)
        try:
            return [Application(**app) for app in response_data.get("applications", [])]
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse application data: {e}") from e

    def get_permissions(
        self, owner_name: str, app_link_name: str
    ) -> Sequence[Permission]:
        """Get all permissions for an application."""
        url = (
            f"{self.api_config.base_url}/settings/{owner_name}/{app_link_name}/"
            "permissions"
        )
        response_data = self.http_client.get(url)
        try:
            return [Permission(**perm) for perm in response_data.get("permissions", [])]
        except PydanticValidationError as e:
            raise APIError(f"Failed to parse permission data: {e}") from e

    def update_record(
        self,
        owner_name: str,
        app_link_name: str,
        report_link_name: str,
        record_id: str,
        *,
        data: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Update an existing record."""
        url = (
            f"{self.api_config.base_url}/data/{owner_name}/{app_link_name}/"
            f"report/{report_link_name}/{record_id}"
        )
        payload = {"data": data}
        return self.http_client.patch(url, json=payload)

    def delete_record(
        self, owner_name: str, app_link_name: str, report_link_name: str, record_id: str
    ) -> Mapping[str, Any]:
        """Delete a record."""
        url = (
            f"{self.api_config.base_url}/data/{owner_name}/{app_link_name}/"
            f"report/{report_link_name}/{record_id}"
        )
        return self.http_client.delete(url)
