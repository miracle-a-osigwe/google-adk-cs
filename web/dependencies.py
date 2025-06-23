import os
from typing import Dict, Optional
from fastapi import Depends, Request, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(".env.example")

# --- Configuration ---
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET is not set in the environment variables.")

ALGORITHM = "HS256"
# Supabase JWTs have a specific 'aud' (audience) claim.
# This is an extra layer of security.
JWT_AUDIENCE = "authenticated"

# This is a FastAPI utility that automatically looks for the
# "Authorization: Bearer <token>" header in the request.
bearer_scheme = HTTPBearer(auto_error=False)


class RedirectToLoginException(Exception):
    def __init__(self, redirect_to: str = "/"):
        self.redirect_to = redirect_to

# --- The Dependency Function ---
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    supabase_auth_token: Optional[str] = Cookie(None)
) -> Dict:
    """
    A dependency that validates a Supabase JWT and returns the user's data (payload).

    1. Extracts the token from the "Authorization: Bearer" header.
    2. Decodes and validates the JWT's signature and claims.
    3. If valid, returns the token payload (a dictionary with user info).
    4. If invalid, raises an HTTPException(401) which stops the request.
    """
    # Check for token in Authorization header
    if credentials:
        token = credentials.credentials
    elif supabase_auth_token:
        token = supabase_auth_token
    # Check for token in localStorage via custom header
    elif request.headers.get("X-Supabase-Auth"):
        token = request.headers.get("X-Supabase-Auth")
    # Check for token in localStorage via query param (fallback)
    elif request.query_params.get("token"):
        token = request.query_params.get("token")
    # Check for token in cookies
    elif request.headers.get('cookie'):
        token = request.headers.get('cookie').split('=')[-1]
    # No token found
    else:
        # This would require client-side code to send the token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # The `jwt.decode` function is where the magic happens.
        # It verifies the signature against the secret, checks for expiration,
        # and validates the audience claim.
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE
        )

        # The 'sub' (subject) claim in a Supabase JWT is the user's unique ID.
        user_id: str = payload.get("sub")
        if user_id is None:
            # This case is unlikely if the token is otherwise valid, but it's good practice.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identification in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # If everything is fine, return the entire payload.
        # The route function can now trust this data.
        return payload

    except JWTError as e:
        # This block catches any error from jwt.decode, like:
        # - Signature has expired.
        # - Invalid signature.
        # - Invalid audience.
        raise RedirectToLoginException(str(request.url))