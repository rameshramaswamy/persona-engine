from fastapi import Depends, HTTPException, status, Header
from src.auth.jwt_validator import KeycloakValidator

oauth2_scheme = KeycloakValidator()

async def get_current_user(authorization: str = Header(...)):
    """
    Extracts Bearer token, validates it, and returns User context.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    
    token = authorization.split(" ")[1]
    payload = oauth2_scheme.decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Construct user context object
    # In real world, we might query DB here to ensure user wasn't banned recently
    return {
        "user_id": payload.get("sub"),
        "tenant_id": payload.get("tenant_id", "default_tenant"), # Custom claim mapped in Keycloak
        "roles": payload.get("realm_access", {}).get("roles", []),
        "tier": payload.get("tier", "free")
    }