import time
from typing import Optional, cast

from .exceptions import KonigleError


def _get_client_ip(request):
    """
    Get the real client IP address, accounting for proxies.

    Checks headers in order of preference:
    1. X-Forwarded-For (if request already went through a proxy such as load balancer)
    2. X-Real-IP
    3. REMOTE_ADDR (direct connection)
    """
    # Check if already behind a proxy
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, )
        # The first one is the original client
        ip = x_forwarded_for.split(",")[0].strip()
        return ip

    # Check X-Real-IP header
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip

    # Fall back to direct connection IP
    return request.META.get("REMOTE_ADDR", "")


def relay(request, path: Optional[str] = None):
    """
    Proxy a Django request to another server and return the response.

    Handles:
    - Both GET and POST requests
    - Normal cookies (persistent with expiration)
    - Session cookies (no expiration)
    - Request headers
    - Query parameters

    Args:
        request: Django HttpRequest object
        path: Path to append to WWW_SERVER_URL (optional, defaults to
        request.path)

    Returns:
        Django HttpResponse object with content and cookies from
        original server

    Settings required:
        WWW_SERVER_URL: Base URL of the original server
        normally *.konigle.net when using the Konigle website CMS.
    """
    try:
        import requests
        from django.conf import settings
        from django.http import HttpResponse
    except ImportError:
        raise ImportError(
            "Only Django server can relay the requests to .konigle.net "
        )
    # Get original server URL from settings
    original_server: str | None = getattr(settings, "WWW_SERVER_URL", None)

    if not original_server:
        raise KonigleError(
            "Configuration error: WWW_SERVER_URL not set in settings",
        )

    original_server = original_server.rstrip("/")

    # Use request.path if no path provided
    if path is None:
        path = cast(str, request.path)

    # Build target URL
    target_url = f'{original_server}/{path.lstrip("/")}'

    # Add query parameters
    if request.GET:
        target_url += "?" + request.GET.urlencode()

    client_ip = _get_client_ip(request)
    original_host = request.get_host()

    # Prepare headers to forward
    headers = {
        "User-Agent": request.META.get("HTTP_USER_AGENT", ""),
        "Accept": request.META.get("HTTP_ACCEPT", "*/*"),
        "Accept-Language": request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
        "Accept-Encoding": request.META.get("HTTP_ACCEPT_ENCODING", ""),
        "X-Forwarded-For": client_ip,
        "X-Real-IP": client_ip,
        "X-Forwarded-Proto": ("https" if request.is_secure() else "http"),
        "X-Forwarded-Host": original_host,
        "X-Proxied-Request": "true",
        # "Host": original_host,
    }

    # Forward Referer if present
    if "HTTP_REFERER" in request.META:
        headers["Referer"] = request.META["HTTP_REFERER"]

    # Forward CSRF token if present
    if "csrftoken" in request.COOKIES:
        headers["X-CSRFToken"] = request.COOKIES["csrftoken"]

    # Create requests session to maintain cookies
    session = requests.Session()

    # Forward ALL cookies from browser to original server
    for cookie_name, cookie_value in request.COOKIES.items():
        session.cookies.set(cookie_name, cookie_value)

    try:
        # Make request based on method
        if request.method == "POST":
            response = session.post(
                target_url,
                data=request.POST,
                files=request.FILES,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=True,  # Verify SSL certificates
            )
        elif request.method == "PUT":
            response = session.put(
                target_url,
                data=request.body,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=True,
            )
        elif request.method == "DELETE":
            response = session.delete(
                target_url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=True,
            )
        else:  # GET, HEAD, OPTIONS, etc.
            response = session.request(
                request.method,
                target_url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=True,
            )

        # Create Django response
        django_response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("content-type", "text/html"),
        )

        # Forward important response headers
        headers_to_forward = [
            "cache-control",
            "content-encoding",
            "content-language",
            "etag",
            "last-modified",
            "vary",
        ]

        for header in headers_to_forward:
            if header in response.headers:
                django_response[header] = response.headers[header]

        # Forward ALL cookies from original server back to browser
        current_time = int(time.time())

        for cookie in session.cookies:
            # Determine if this is a session cookie or persistent cookie
            if cookie.expires:
                # Persistent cookie - has expiration time
                max_age = cookie.expires - current_time
                if max_age < 0:
                    # Cookie already expired, set to 0 to delete it
                    max_age = 0
            else:
                # Session cookie - no expiration (deleted when browser closes)
                max_age = None

            # Set cookie on relay server's response

            django_response.set_cookie(
                key=cookie.name,
                value=cookie.value,  # type: ignore[attr-defined]
                max_age=max_age,  # None = session cookie, int = persistent cookie
                path=cookie.path or "/",
                domain=None,  # Use current domain (relay server)
                secure=True,  # Both servers use HTTPS
                httponly=cookie.has_nonstandard_attr("HttpOnly"),
                samesite=cookie.get_nonstandard_attr("SameSite", "Lax"),
            )

        return django_response

    except requests.Timeout:
        return HttpResponse(
            "Error: Request to server timed out",
            status=504,  # Gateway Timeout
        )
    except requests.ConnectionError:
        return HttpResponse(
            "Error: Could not connect to server",
            status=502,  # Bad Gateway
        )
    except requests.RequestException as e:
        return HttpResponse(f"Error: Request failed - {str(e)}", status=502)
    except Exception as e:
        return HttpResponse(f"Error: Unexpected error - {str(e)}", status=500)
