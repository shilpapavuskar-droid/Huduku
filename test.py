import requests

url = "http://localhost:8001/api/v1/users/verify-token"
headers = {
 "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJleHAiOjE3NjY3MjE0MjV9.zV-cdXU7llVqoT5vUp70OvJGSw6wEssUEgtZyUg4LK8"
}
response = requests.get(url, headers=headers)
print(response.json())
