import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('scale_core.security')


def get_client_ip(request) -> str:
    """Extract real client IP address from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Monitors authenticated sessions, records client IP, and enforces session security.
    """
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            ip = get_client_ip(request)
            # Update last_login_ip if changed
            if request.user.last_login_ip != ip:
                request.user.last_login_ip = ip
                request.user.save(update_fields=['last_login_ip'])
        return None
