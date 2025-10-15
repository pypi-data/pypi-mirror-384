from revproxy.views import ProxyView
from django.conf import settings
from django.shortcuts import redirect
from revproxy.response import get_django_response


def get_request_headers(self):
    """Return request headers that will be sent to upstream.

    The header REMOTE_USER is set to the current user
    if AuthenticationMiddleware is enabled and
    the view's add_remote_user property is True.

    .. versionadded:: 0.9.8

    If the view's add_x_forwarded property is True, the
    headers X-Forwarded-For and X-Forwarded-Proto are set to the
    IP address of the requestor and the request's protocol (http or https),
    respectively.

    .. versionadded:: TODO

    """
    request_headers = self.get_proxy_request_headers(self.request)

    if (
        self.add_remote_user
        and hasattr(self.request, "user")
        and self.request.user.is_active
    ):
        request_headers["REMOTE_USER"] = self.request.user.get_username()
        self.log.info("REMOTE_USER set")

    if self.add_x_forwarded:
        request_ip = self.request.META.get("REMOTE_ADDR")
        self.log.debug("Proxy request IP: %s", request_ip)
        request_headers["X-Forwarded-For"] = request_ip
        if settings.DEBUG:
            http_port = self.request.META["SERVER_PORT"]
            request_headers["X-Forwarded-Port"] = http_port
        request_proto = "https" if self.request.is_secure() else "http"
        self.log.debug("Proxy request using %s", request_proto)
        request_headers["X-Forwarded-Proto"] = request_proto
    return request_headers


ProxyView.get_request_headers = get_request_headers


class IIIFProxyView(ProxyView):
    upstream = settings.JAMA_IIIF_UPSTREAM_URL
    add_x_forwarded = True

    def dispatch(self, request, path):
        # print(f"### Upstream in setting: {settings.JAMA_IIIF_UPSTREAM_URL}")
        # print(f"### Upstream in class: {self.upstream}")
        # print(request.path)
        self.request_headers = self.get_request_headers()

        redirect_to = self._format_path_to_redirect(request)
        if redirect_to:
            return redirect(redirect_to)

        proxy_response = self._created_proxy_response(request, path)

        # print(proxy_response.headers)

        self._replace_host_on_redirect_location(request, proxy_response)
        self._set_content_type(request, proxy_response)

        response = get_django_response(
            proxy_response,
            strict_cookies=self.strict_cookies,
            streaming_amount=self.streaming_amount,
        )

        self.log.debug("RESPONSE RETURNED: %s", response)
        return response
