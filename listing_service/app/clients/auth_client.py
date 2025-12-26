# python
import requests

AUTH_SERVICE_URL = "http://auth-srv:8000/api/v1/users/verify-token"

def verify_user(request):
    #token = request.headers.get("Authorization")
    token ="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJleHAiOjE3NjY3MjkzODd9.oqkXnJDy0PU-2A62CT0P94OmyPEeivsohDmUu5v7TgY"
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
