import httpx
AUTH_SERVICE_URL = "http://auth-srv:8000/api/v1/users/verify-token"


def verify_user(request):
    """
    Extract Bearer token from the DRF/Django request's Authorization header
    and verify the user with auth_service.

    Returns:
        dict user payload on success, or None on failure.
    """
    auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")


    if not auth_header:
        return None

    token = auth_header.strip()
    if not token.startswith("Bearer "):
        return None

    jwt = token[len("Bearer ") :].strip()
    if not jwt:
        return None

    try:
        with httpx.Client() as client:
            resp = client.get(
                AUTH_SERVICE_URL,
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=5.0,
            )
    except httpx.RequestError:
        return None

    if resp.status_code != 200:
        return None

    # Expected to contain at least user_id, maybe more
    return resp.json()
