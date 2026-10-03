from urllib.request import HTTPRedirectHandler, build_opener


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # Credentials must never be forwarded to a redirected origin.
        return None


def urlopen(request, *, timeout):
    return build_opener(RejectRedirect()).open(request, timeout=timeout)
