"""Main Voltarium client for CCEE API."""

import time
from collections.abc import AsyncGenerator
from types import TracebackType
from typing import Any, Self

import httpx
from httpx import Response
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from voltarium.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    VoltariumError,
)
from voltarium.models import (
    ApiHeaders,
    Contract,
    ContractFile,
    CreateContractRequest,
    CreateMigrationRequest,
    ListContractsParams,
    ListMigrationsParams,
    MigrationItem,
    MigrationListItem,
    Token,
    UpdateMigrationRequest,
)

PRODUCTION_BASE_URL = "https://api-abm.ccee.org.br"
SANDBOX_BASE_URL = "https://sandbox-api-abm.ccee.org.br"


class VoltariumClient:
    """Asynchronous client for CCEE API."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        base_url: str = PRODUCTION_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL for the API
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        # Remove trailing slashes
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries

        # Internal state
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        self._token: Token | None = None

    async def _refresh_token(self) -> None:
        """Get access token, refreshing if needed."""
        try:
            response = await self._http_client.post(
                "/sso/oauth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid credentials") from e
            raise

        token_data = response.json()
        self._token = Token.model_validate(token_data)

    async def _get_access_token(self) -> str:
        # Check if we have a valid cached token
        if self._token and time.time() < self._token.expires_at - 30:  # 30s buffer
            return self._token.access_token
        # If no valid token, refresh it
        await self._refresh_token()
        assert self._token is not None  # refresh_token sets this
        return self._token.access_token

    async def _get_auth_header(self) -> dict[str, str]:
        """Get authorization header."""
        token = await self._get_access_token()
        return {"Authorization": f"Bearer {token}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Response:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method
            path: API path
            headers: Additional headers
            params: Query parameters
            json: JSON body

        Returns:
            Response object

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If request validation fails
            NotFoundError: If resource not found
            RateLimitError: If rate limit exceeded
            ServerError: If server error occurs
            VoltariumError: For other API errors
        """
        # Get auth headers
        auth_headers = await self._get_auth_header()

        # Merge headers - start with standard headers
        request_headers = {
            "Accept": "application/json",
            **auth_headers,
        }

        # Add Content-Type header for JSON requests
        if json is not None:
            request_headers["Content-Type"] = "application/json"

        if headers:
            request_headers.update(headers)

        async def _reauthenticate(*args: Any, **kwargs: Any) -> None:
            """Reauthenticate the client to refresh the access token."""
            try:
                await self._get_access_token()  # Fetch new token
            except VoltariumError as e:
                raise AuthenticationError(f"Reauthentication failed: {e}") from e

        retry_strategy = AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type(AuthenticationError),
            after=_reauthenticate,
        )
        async for attempt in retry_strategy:
            with attempt:
                response = await self._http_client.request(
                    method=method,
                    url=path,
                    headers=request_headers,
                    params=params,
                    json=json,
                )
                self._raise_for_status(response=response)
        return response

    def _raise_for_status(self, response: Response) -> None:
        """Handle API response and raise appropriate exceptions."""

        if response.status_code < 400:
            response.raise_for_status()
            return

        try:
            content = response.json()
        except ValueError:
            content = {}

        if response.status_code == 401:
            raise AuthenticationError("???")
        if response.status_code == 403:
            if "ERR_CREDENCIAL_INVALID" in content.get("error", ""):
                raise AuthenticationError("Invalid credentials")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code == 400:
            raise ValidationError(code=content.get("error"), message=content.get("message"))
        response.raise_for_status()

    # Migration endpoints

    async def list_migrations(
        self,
        initial_reference_month: str,
        final_reference_month: str,
        agent_code: str | int,
        profile_code: str | int,
        consumer_unit_code: str | None = None,
        migration_status: str | None = None,
    ) -> AsyncGenerator[MigrationListItem]:
        """List migrations for a retailer.

        Args:
            initial_reference_month: Start reference month (YYYY-MM)
            final_reference_month: End reference month (YYYY-MM)
            agent_code: Agent code
            profile_code: Profile code
            consumer_unit_code: Optional consumer unit code filter
            migration_status: Optional migration status filter

        Returns:
            AsyncGenerator of migrations
        """
        # Create headers model
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        # Create parameters model
        params_model = ListMigrationsParams(
            initial_reference_month=initial_reference_month,
            final_reference_month=final_reference_month,
            retailer_profile_code=str(profile_code),
            consumer_unit_code=consumer_unit_code,
            migration_status=migration_status,
        )

        async def _get_page(page_index: str | None = None) -> Response:
            # Update the page index if provided
            if page_index is not None:
                params_model.next_page_index = page_index
            else:
                params_model.next_page_index = None

            return await self._request(
                method="GET",
                path="/v1/varejista/migracoes",
                headers=headers_model.model_dump(by_alias=True),
                params=params_model.model_dump(by_alias=True, exclude_none=True),
            )

        # Handle pagination
        page_index = None
        while True:
            response = await _get_page(page_index)
            data = response.json()

            # Yield migrations from current page
            for migration_data in data.get("migracao", []):
                yield MigrationListItem.model_validate(migration_data)

            # Check if there are more pages
            page_index = data.get("indexProximaPagina")
            if page_index is None:
                break

    async def create_migration(
        self,
        migration_data: CreateMigrationRequest,
        agent_code: str | int,
        profile_code: str | int,
    ) -> MigrationItem:
        """Create a new migration.

        Args:
            migration_data: Migration data
            agent_code: Agent code
            profile_code: Profile code

        Returns:
            Created migration
        """
        # Create headers model
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        # Use model_dump with by_alias=True to get Portuguese field names for the API
        json_data = migration_data.model_dump(by_alias=True, exclude_none=True)

        response = await self._request(
            method="POST",
            path="/v1/varejista/migracoes",
            headers=headers_model.model_dump(by_alias=True),
            json=json_data,
        )

        return MigrationItem.model_validate(response.json())

    async def get_migration(
        self,
        agent_code: str | int,
        profile_code: str | int,
        migration_id: str,
    ) -> MigrationItem:
        """Get a migration by ID.

        Args:
            agent_code: Agent code
            profile_code: Profile code
            migration_id: Migration ID

        Returns:
            Migration details
        """
        # Create headers model
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        response = await self._request(
            method="GET",
            path=f"/v1/varejista/migracoes/{migration_id}",
            headers=headers_model.model_dump(by_alias=True),
        )

        data = response.json()
        if isinstance(data, list) and data:
            return MigrationItem.model_validate(data[0])
        return MigrationItem.model_validate(data)

    async def update_migration(
        self,
        migration_id: str,
        migration_data: UpdateMigrationRequest,
        agent_code: str | int,
        profile_code: str | int,
    ) -> MigrationItem:
        """Update a migration.

        Args:
            migration_id: Migration ID
            migration_data: Updated migration data
            agent_code: Agent code
            profile_code: Profile code

        Returns:
            Updated migration
        """
        # Create headers model
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        # Use model_dump with by_alias=True to get Portuguese field names for the API
        json_data = migration_data.model_dump(by_alias=True, exclude_none=True)

        response = await self._request(
            method="PUT",
            path=f"/v1/varejista/migracoes/{migration_id}",
            headers=headers_model.model_dump(by_alias=True),
            json=json_data,
        )

        return MigrationItem.model_validate(response.json())

    async def delete_migration(
        self,
        migration_id: str,
        agent_code: str | int,
        profile_code: str | int,
    ) -> None:
        """Delete a migration.

        Args:
            migration_id: Migration ID
            agent_code: Agent code
            profile_code: Profile code
        """
        # Create headers model
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        await self._request(
            method="DELETE",
            path=f"/v1/varejista/migracoes/{migration_id}",
            headers=headers_model.model_dump(by_alias=True),
        )

    # Contracts endpoints

    async def list_contracts(
        self,
        initial_reference_month: str,
        final_reference_month: str,
        agent_code: str | int,
        profile_code: str | int,
        utility_agent_code: str | int | None = None,
        consumer_unit_code: str | None = None,
        contract_status: str | None = None,
    ) -> AsyncGenerator[Contract]:
        """List retailer contracts with filtering and pagination.

        Mirrors list_migrations pattern.
        """
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        params_model = ListContractsParams(
            initial_reference_month=initial_reference_month,
            final_reference_month=final_reference_month,
            retailer_profile_code=str(profile_code),
            utility_agent_code=str(utility_agent_code) if utility_agent_code is not None else None,
            consumer_unit_code=consumer_unit_code,
            contract_status=contract_status,
        )

        async def _get_page(page_index: str | None = None) -> Response:
            if page_index is not None:
                params_model.next_page_index = page_index
            else:
                params_model.next_page_index = None

            return await self._request(
                method="GET",
                path="/v1/varejista/contratos",
                headers=headers_model.model_dump(by_alias=True),
                params=params_model.model_dump(by_alias=True, exclude_none=True),
            )

        page_index = None
        while True:
            response = await _get_page(page_index)
            data = response.json()

            for contract_data in data.get("contratos", data.get("contrato", [])):
                yield Contract.model_validate(contract_data)

            page_index = data.get("indexProximaPagina")
            if page_index is None:
                break

    async def get_contract(
        self,
        contract_id: str,
        agent_code: str | int,
        profile_code: str | int,
    ) -> Contract:
        """Get a contract by ID."""
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        response = await self._request(
            method="GET",
            path=f"/v1/varejista/contratos/{contract_id}",
            headers=headers_model.model_dump(by_alias=True),
        )

        body = response.json()
        # Some endpoints return array for single item; support both
        if isinstance(body, list) and body:
            return Contract.model_validate(body[0])
        return Contract.model_validate(body)

    async def create_contract(
        self,
        contract_data: CreateContractRequest,
        agent_code: str | int,
        profile_code: str | int,
    ) -> Contract:
        """Create a retailer contract (POST /v1/varejista/contratos)."""
        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        # Use model_dump with by_alias=True to match Portuguese field names
        json_data = contract_data.model_dump(by_alias=True, exclude_none=True)

        response = await self._request(
            method="POST",
            path="/v1/varejista/contratos",
            headers=headers_model.model_dump(by_alias=True),
            json=json_data,
        )

        body = response.json()
        if isinstance(body, list) and body:
            return Contract.model_validate(body[0])
        return Contract.model_validate(body)

    async def download_contract_file(
        self,
        contract_id: str,
        agent_code: str | int,
        profile_code: str | int,
    ) -> ContractFile:
        """Download the binary file for a concluded contract.

        Returns metadata and base64-encoded payload compatible with tests and
        callers that need to persist the document locally.
        """

        headers_model = ApiHeaders(
            agent_code=str(agent_code),
            profile_code=str(profile_code),
        )

        response = await self._request(
            method="GET",
            path=f"/v1/varejista/contratos/{contract_id}/arquivo",
            headers=headers_model.model_dump(by_alias=True),
        )

        content_disposition = response.headers.get("content-disposition", "")
        filename = contract_id
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')

        return ContractFile(
            contract_id=contract_id,
            filename=filename,
            content_type=response.headers.get("content-type", "application/octet-stream"),
            content_base64=response.text,
            content_length=int(response.headers.get("content-length", len(response.content))),
        )

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self._http_client.aclose()
