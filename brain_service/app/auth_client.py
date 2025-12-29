# python
import requests

AUTH_SERVICE_URL = "http://auth-srv:8000/api/v1/users/verify-token"

def verify_user(request):
    #token = request.headers.get("Authorization")
    token ="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJleHAiOjE3NjY4NDQ1Mzd9.wRqgkQHUqEnOzMh1abEZLp8y7CwFMJtJeJGKJMEydKA"
    if not token:
        return None

    response = requests.get(
        AUTH_SERVICE_URL,
        headers={"Authorization": token},
        timeout=5
    )

    if response.status_code != 200:
        return None

    return response.json()   # {user_id, email}
