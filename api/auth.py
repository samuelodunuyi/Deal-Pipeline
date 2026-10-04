from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView


class LoginIPThrottle(AnonRateThrottle):
    """Caps login attempts per client IP."""

    scope = 'login'


class LoginUsernameThrottle(SimpleRateThrottle):
    """
    Caps login attempts per target username, so rotating IPs (or spoofing X-Forwarded-For)
    does not bypass the limit when guessing one account's password.
    """

    scope = 'login_user'

    def get_cache_key(self, request, view):
        username = str(request.data.get('username', '')).strip().lower()
        if not username:
            return None
        return self.cache_format % {'scope': self.scope, 'ident': username}


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginIPThrottle, LoginUsernameThrottle]
