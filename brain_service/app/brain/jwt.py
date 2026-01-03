from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
import jwt

class JWTAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Read token from cookie (set by UI login) or Authorization header
        auth = request.COOKIES.get("auth_token") or request.headers.get("Authorization")
        if not auth:
            # unauthenticated; let views decide
            return None

        token = auth
        if auth.startswith("Bearer "):
            token = auth[len("Bearer "):].strip()

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            # Only block API paths; allow UI pages like `/`
            if request.path.startswith("/api/"):
                return JsonResponse({"detail": "Token expired"}, status=401)
            return None
        except jwt.InvalidTokenError:
            if request.path.startswith("/api/"):
                return JsonResponse({"detail": "Invalid token"}, status=401)
            return None

        # Attach info for later use
        request.user_id = payload.get("user_id")
        request.is_staff = payload.get("is_staff", False)
        return None
