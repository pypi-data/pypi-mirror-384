from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import aiohttp

from naylence.fame.security.credential import CredentialProvider
from naylence.fame.util.logging import getLogger

from .token import Token
from .token_provider import TokenProvider

logger = getLogger(__name__)


class OAuth2ClientCredentialsTokenProvider(TokenProvider):
    """
    Token provider that implements OAuth2 client credentials flow.
    Caches tokens until they expire and automatically refreshes them.
    """

    def __init__(
        self,
        token_url: str,
        client_id_provider: CredentialProvider,
        client_secret_provider: CredentialProvider,
        scopes: Optional[list[str]] = None,
        audience: Optional[str] = None,
    ):
        self._token_url = token_url
        self._client_id_provider = client_id_provider
        self._client_secret_provider = client_secret_provider
        self._scopes = scopes or []
        self._audience = audience

        # Token cache
        self._cached_token: Optional[Token] = None

    async def get_token(self) -> Token:
        """Get a valid OAuth2 access token, refreshing if necessary."""
        # Check if we have a valid cached token
        if self._cached_token and self._cached_token.is_valid:
            # Refresh 30 seconds early
            current_time = datetime.now(timezone.utc)
            if (
                self._cached_token.expires_at is None
                or current_time < self._cached_token.expires_at - timedelta(seconds=30)
            ):
                logger.debug("using_cached_oauth2_token", token_url=self._token_url)
                return self._cached_token

        # Fetch a new token
        return await self._fetch_new_token()

    async def _fetch_new_token(self) -> Token:
        """Fetch a new OAuth2 access token using client credentials flow."""
        client_id = await self._client_id_provider.get()
        if not client_id:
            raise ValueError("Client ID not available from credential provider")

        client_secret = await self._client_secret_provider.get()
        if not client_secret:
            raise ValueError("Client secret not available from credential provider")

        # Prepare the token request
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        if self._scopes:
            data["scope"] = " ".join(self._scopes)

        if self._audience:
            data["audience"] = self._audience

        # Make the token request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"OAuth2 token request failed: {response.status} - {error_text}")

                token_data = await response.json()

        # Extract and cache the token
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("No access_token in OAuth2 response")

        # Cache the token with expiration
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        token = Token(value=access_token, expires_at=expires_at)
        self._cached_token = token

        logger.debug(
            "oath2_token_fetched",
            token_url=self._token_url,
            client_id=client_id,
            scopes=self._scopes,
            audience=self._audience,
            expires_in=expires_in,
        )

        return token
