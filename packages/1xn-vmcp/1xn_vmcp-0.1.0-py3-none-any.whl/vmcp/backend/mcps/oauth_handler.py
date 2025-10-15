"""
OAuth handler for MCP server authentication.

Handles OAuth 2.0 flow for MCP servers that require OAuth authentication.
Manages callback, token exchange, and token persistence.
"""

import secrets
import hashlib
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse

from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_async
from vmcp.backend.mcps.models import MCPAuthConfig
from vmcp.backend.storage.models import ThirdPartyOAuthState
from vmcp.backend.storage.database import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/mcps/oauth", tags=["MCP OAuth"])


class OAuthManager:
    """Manages OAuth flow for MCP servers."""

    @staticmethod
    def generate_pkce_pair() -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (random string)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

        # Generate code challenge (SHA256 of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        return code_verifier, code_challenge

    @staticmethod
    @trace_async("oauth.save_state")
    def save_oauth_state(state: str, state_data: Dict[str, Any], expires_minutes: int = 10) -> bool:
        """
        Save OAuth state to database.

        Args:
            state: OAuth state parameter
            state_data: State data to store
            expires_minutes: Expiration time in minutes

        Returns:
            True if successful
        """
        db = next(get_db())
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

            oauth_state = ThirdPartyOAuthState(
                state=state,
                state_data=state_data,
                expires_at=expires_at
            )

            db.add(oauth_state)
            db.commit()

            logger.info(f"Saved OAuth state: {state[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to save OAuth state: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    @trace_async("oauth.get_state")
    def get_oauth_state(state: str) -> Optional[Dict[str, Any]]:
        """
        Get OAuth state from database.

        Args:
            state: OAuth state parameter

        Returns:
            State data or None if not found
        """
        db = next(get_db())
        try:
            oauth_state = db.query(ThirdPartyOAuthState).filter(
                ThirdPartyOAuthState.state == state,
                ThirdPartyOAuthState.expires_at > datetime.utcnow()
            ).first()

            if oauth_state:
                logger.info(f"Retrieved OAuth state: {state[:8]}...")
                return oauth_state.state_data
            else:
                logger.warning(f"OAuth state not found or expired: {state[:8]}...")
                return None

        except Exception as e:
            logger.error(f"Failed to get OAuth state: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    @trace_async("oauth.delete_state")
    def cleanup_oauth_state(state: str) -> bool:
        """
        Delete OAuth state after use.

        Args:
            state: OAuth state parameter

        Returns:
            True if successful
        """
        db = next(get_db())
        try:
            db.query(ThirdPartyOAuthState).filter(
                ThirdPartyOAuthState.state == state
            ).delete()
            db.commit()

            logger.info(f"Cleaned up OAuth state: {state[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup OAuth state: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    @trace_async("oauth.exchange_code")
    async def exchange_code_for_token(
        code: str,
        token_url: str,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code
            token_url: Token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret (optional for PKCE)
            redirect_uri: Redirect URI
            code_verifier: PKCE code verifier (optional)

        Returns:
            Token response dictionary
        """
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
        }

        # Add client secret if provided
        if client_secret:
            payload['client_secret'] = client_secret

        # Add PKCE code verifier if provided
        if code_verifier:
            payload['code_verifier'] = code_verifier

        logger.info(f"Exchanging code for token at: {token_url}")
        logger.debug(f"Token request payload keys: {list(payload.keys())}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=payload,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )

                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("✅ Successfully exchanged code for token")
                    return token_data
                else:
                    error_msg = f"Token exchange failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {'error': error_msg}

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return {'error': str(e)}


@router.get("/authorize")
@trace_async("oauth.authorize")
async def oauth_authorize(
    server_id: str = Query(..., description="MCP server ID"),
    auth_url: str = Query(..., description="Authorization URL"),
    token_url: str = Query(..., description="Token URL"),
    client_id: str = Query(..., description="Client ID"),
    client_secret: Optional[str] = Query(None, description="Client secret"),
    scope: Optional[str] = Query(None, description="OAuth scope"),
    redirect_uri: str = Query(..., description="Redirect URI"),
):
    """
    Initiate OAuth flow for an MCP server.

    This endpoint generates the OAuth authorization URL and redirects the user.
    """
    # Generate state parameter
    state = secrets.token_urlsafe(32)

    # Generate PKCE pair
    code_verifier, code_challenge = OAuthManager.generate_pkce_pair()

    # Save state data
    state_data = {
        'server_id': server_id,
        'token_url': token_url,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier,
        'timestamp': datetime.utcnow().isoformat()
    }

    if not OAuthManager.save_oauth_state(state, state_data):
        raise HTTPException(status_code=500, detail="Failed to save OAuth state")

    # Build authorization URL
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }

    if scope:
        params['scope'] = scope

    auth_redirect_url = f"{auth_url}?{urlencode(params)}"

    logger.info(f"Starting OAuth flow for server: {server_id}")
    logger.info(f"Redirecting to: {auth_url}")

    # Return redirect HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Authorization</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
            }}
            h1 {{ color: #333; }}
            p {{ color: #666; }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Authorizing MCP Server</h1>
            <div class="spinner"></div>
            <p>Redirecting to authorization page...</p>
            <p><small>Server: {server_id}</small></p>
        </div>
        <script>
            window.location.href = {repr(auth_redirect_url)};
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/callback")
@trace_async("oauth.callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
):
    """
    Handle OAuth callback from MCP server.

    This endpoint receives the authorization code and exchanges it for tokens.
    """
    logger.info(f"OAuth callback received - state: {state[:8]}...")

    # Get state data
    state_data = OAuthManager.get_oauth_state(state)
    if not state_data:
        error_html = render_error_page("Invalid or expired OAuth state. Please try again.")
        return HTMLResponse(content=error_html, status_code=400)

    # Extract OAuth configuration
    server_id = state_data.get('server_id')
    token_url = state_data.get('token_url')
    client_id = state_data.get('client_id')
    client_secret = state_data.get('client_secret')
    redirect_uri = state_data.get('redirect_uri')
    code_verifier = state_data.get('code_verifier')

    logger.info(f"Processing OAuth callback for server: {server_id}")

    # Exchange code for token
    token_response = await OAuthManager.exchange_code_for_token(
        code=code,
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier
    )

    # Cleanup state
    OAuthManager.cleanup_oauth_state(state)

    # Check for errors
    if 'error' in token_response:
        error_html = render_error_page(f"OAuth failed: {token_response['error']}")
        return HTMLResponse(content=error_html, status_code=400)

    # Save tokens to database
    from vmcp.backend.mcps.mcp_config_manager import MCPConfigManager
    config_manager = MCPConfigManager(user_id=1)

    server_config = config_manager.get_server(server_id)
    if not server_config:
        error_html = render_error_page(f"Server {server_id} not found")
        return HTMLResponse(content=error_html, status_code=404)

    # Update OAuth tokens
    oauth_state = {
        'access_token': token_response.get('access_token'),
        'refresh_token': token_response.get('refresh_token'),
        'expires_in': token_response.get('expires_in'),
        'token_type': token_response.get('token_type', 'Bearer'),
        'updated_at': datetime.utcnow().isoformat()
    }

    if config_manager.update_server_oauth(server_id, oauth_state):
        logger.info(f"✅ OAuth successful for server: {server_id}")
        success_html = render_success_page(server_config.name)
        return HTMLResponse(content=success_html)
    else:
        error_html = render_error_page("Failed to save OAuth tokens")
        return HTMLResponse(content=error_html, status_code=500)


def render_success_page(server_name: str) -> str:
    """Render OAuth success page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Success</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 3rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .success-icon {{
                font-size: 4rem;
                margin-bottom: 1rem;
            }}
            h1 {{ color: #10b981; margin: 0; }}
            p {{ color: #666; margin: 1rem 0; }}
            .close-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 5px;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 1rem;
            }}
            .close-btn:hover {{ background: #5568d3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Authorization Successful!</h1>
            <p>Successfully authorized MCP server:</p>
            <p><strong>{server_name}</strong></p>
            <p>You can now close this window and return to vMCP.</p>
            <button class="close-btn" onclick="window.close()">Close Window</button>
        </div>
    </body>
    </html>
    """


def render_error_page(error_message: str) -> str:
    """Render OAuth error page."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Error</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}
            .container {{
                background: white;
                padding: 3rem;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }}
            .error-icon {{
                font-size: 4rem;
                margin-bottom: 1rem;
            }}
            h1 {{ color: #ef4444; margin: 0; }}
            p {{ color: #666; margin: 1rem 0; }}
            .error-detail {{
                background: #fee2e2;
                padding: 1rem;
                border-radius: 5px;
                color: #991b1b;
                margin: 1rem 0;
            }}
            .close-btn {{
                background: #ef4444;
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 5px;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 1rem;
            }}
            .close-btn:hover {{ background: #dc2626; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="error-icon">❌</div>
            <h1>Authorization Failed</h1>
            <div class="error-detail">{error_message}</div>
            <p>Please try again or contact support if the problem persists.</p>
            <button class="close-btn" onclick="window.close()">Close Window</button>
        </div>
    </body>
    </html>
    """
