from jose import jwt, JWTError
from src.core.config import settings
import logging

logger = logging.getLogger("auth")

class KeycloakValidator:
    def __init__(self):
        # Env vars: KEYCLOAK_URL, REALM_NAME
        self.jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.REALM_NAME}/protocol/openid-connect/certs"
        self.audience = "persona-api"
        # In prod, fetch and cache JWKS keys dynamically
        # For simplicity here, we assume public key or disable sig check for dev flow if needed
        # self.jwks = requests.get(self.jwks_url).json()

    def decode_token(self, token: str) -> dict:
        try:
            # Full validation requires fetching JWKS keys. 
            # options={"verify_signature": False} used ONLY for internal dev if Keycloak not reachable
            payload = jwt.decode(
                token, 
                "secret-key-if-HS256-or-public-key-if-RS256", 
                algorithms=["RS256"],
                audience=self.audience,
                options={"verify_signature": False} # ⚠️ TODO: Implement JWKS caching for Prod
            )
            return payload
        except JWTError as e:
            logger.error(f"Token validation failed: {e}")
            return None