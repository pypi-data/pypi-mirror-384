import time
import requests
import threading
import logging
from typing import Any, Dict, Optional
import jwt

class TokenManager:
    _instances = {}
    _lock = threading.Lock()  # Add a lock for thread safety

    @classmethod
    def reset_instances(cls):
        """Reset all token manager instances - useful for testing"""
        with cls._lock:
            cls._instances = {}

    def __new__(cls, user_id, *args, **kwargs):
        """
        Ensure only one instance per user.
        """
        with cls._lock:
            if user_id not in cls._instances:
                cls._instances[user_id] = super(TokenManager, cls).__new__(cls)
                cls._instances[user_id].__init__(user_id, *args, **kwargs)
            return cls._instances[user_id]

    def __init__(self, user_id, client_id, client_secret, token_url):
        if hasattr(self, "initialized"):  # Prevent re-initialization
            return
        self.user_id = user_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.tokens = {}  # Store tokens (access/refresh)
        self.lock = threading.Lock()  # Add a lock for thread safety
        self.redirect_uri = None  # Initialize the redirect_uri attribute
        self.force_api = False  # Initialize force_api setting
        self.initialized = True

    def set_force_api(self, force_api: bool):
        """Set the force_api setting for this token manager."""
        self.force_api = force_api

    def get_force_api(self) -> bool:
        """Get the force_api setting for this token manager."""
        return self.force_api

    def set_tokens(self, token_data: Dict[str, Any]):
        """ Store tokens with expiration. """
        with self.lock:
            # Update existing tokens instead of creating new dict
            self.tokens.update({
                "access_token": token_data.get("access_token"),
                "expires_at": time.time() + token_data.get("expires_in", 3600),
            })
            
            # Store refresh token if available
            if "refresh_token" in token_data:
                self.tokens["refresh_token"] = token_data["refresh_token"]
            
            # Decode access token claims
            if "access_token" in token_data:
                try:
                    access_token_payload = jwt.decode(
                        token_data["access_token"],
                        options={"verify_signature": False}
                    )
                    self.tokens["access_token_claims"] = access_token_payload
                except Exception as e:
                    logging.error(f"Failed to decode access token claims: {str(e)}")
                    self.tokens["access_token_claims"] = {}
                
            # Store ID token if available
            if "id_token" in token_data:
                self.tokens["id_token"] = token_data["id_token"]
                
                # Parse claims from ID token
                try:
                    id_token_payload = jwt.decode(
                        token_data["id_token"],
                        options={"verify_signature": False}
                    )
                    self.tokens["id_token_claims"] = id_token_payload
                except Exception as e:
                    logging.error(f"Failed to decode ID token claims: {str(e)}")
                    self.tokens["id_token_claims"] = {}

    def set_redirect_uri(self, redirect_uri: str):
        """Set the redirect URI for token exchange."""
        self.redirect_uri = redirect_uri

    async def exchange_code_for_token(self, code: str, code_verifier: Optional[str] = None):
        """
        Exchange an authorization code for an access token.
        """
        if not self.redirect_uri:
            raise ValueError("Redirect URI is not set")
            
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
        }
        
        # Add client secret if available (for non-PKCE flow)
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        # Add code verifier for PKCE flow
        if code_verifier:
            data["code_verifier"] = code_verifier
            
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        self.set_tokens(token_data)
        return self.tokens["access_token"]
    
    def get_access_token(self):
        """ Get a valid access token. Refresh if expired. """
        with self.lock:
            if not self.tokens or "access_token" not in self.tokens:
                raise ValueError("No access token available")
                
            # Check if token is expired
            # if time.time() >= self.tokens["expires_at"]:
            if time.time() >= self.tokens.get("expires_at", 0):
                # Try to refresh token if available
                if "refresh_token" in self.tokens:
                    return self.refresh_access_token()
                else:
                    raise ValueError("Access token expired and no refresh token available")
                
            return self.tokens["access_token"]

    def refresh_access_token(self):
        """ Use the refresh token to get a new access token. """
        if "refresh_token" not in self.tokens:
            raise ValueError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
        }
        
        # Add client secret if available
        if self.client_secret:
            data["client_secret"] = self.client_secret
            
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        self.set_tokens(token_data)
        return self.tokens["access_token"]

    def get_id_token(self):
        """Get the ID token if available."""
        return self.tokens.get("id_token")
        
    def get_claims(self, token_type: str = "access_token"):
        """Get the claims from the specified token type.
        
        Args:
            token_type (str): The type of token to get claims from. 
                            Valid values are "access_token" or "id_token".
                            
        Returns:
            dict: The claims from the specified token, or empty dict if not available.
        """
        # Validate token type
        valid_token_types = ["access_token", "id_token"]
        if token_type not in valid_token_types:
            logging.warning(f"Invalid token_type '{token_type}'. Valid types are: {valid_token_types}")
            return {}
        
        # Use f-string for safer string formatting
        claims_key = f"{token_type}_claims"
        claims = self.tokens.get(claims_key, {})
        
        if not claims:
            logging.warning(f"No claims available for token type: {token_type}")
            
        return claims
    
    def get_claim(self, key: str, token_type: str = "access_token"):
        """Get a specific claim from the specified token type.
        
        Args:
            key (str): The claim key to retrieve
            token_type (str): The type of token to get the claim from.
                            Valid values are "access_token" or "id_token".
                            
        Returns:
            dict: Dictionary containing the claim name and value, or empty dict if not found.
        """
        claims = self.get_claims(token_type)
        value = claims.get(key)
        return {"name": key, "value": value}
    
    def revoke_token(self):
        """ Revoke the current access token. """
        if "access_token" not in self.tokens:
            return  # No token to revoke
            
        revoke_url = f"{self.token_url.replace('/token', '/revoke')}"
        data = {
            "token": self.tokens["access_token"],
            "client_id": self.client_id,
        }
        
        # Add client secret if available
        if self.client_secret:
            data["client_secret"] = self.client_secret
            
        try:
            response = requests.post(revoke_url, data=data)
            response.raise_for_status()
        except Exception:
            pass  # Best effort revocation
            
        self.tokens = {}  # Clear stored tokens
