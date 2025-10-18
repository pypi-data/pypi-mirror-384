# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

import requests

from .token import attempt_refresh

# =============================================================================
# There are two sets of functions here. The old ones called send_*_request
# expect an authentication token. If the token is invalid, the request fails.
# The new ones in CallWithToken take the token from a project handle.
# If the token is invalid, they may try to refresh it, if the required
# information is available in the environment.


# The decision whether a token is expired and should be refreshed is left
# to a callback function. By default, refresh is never attempted.
def never_refresh(r):
    """Decide whether the token needs refresh.
    Argument: r - response from an HTTP call with the requests module
    Returns:  True if the token is expired and should be refreshed,
              False otherwise.
    This default implementation always returns False.
    """
    return False


class CallWithToken(object):
    def __init__(
        self,
        handle,
        is_token_expired_callback=never_refresh,
        session=requests.Session(),
    ):
        self._project_handle = handle
        self._is_token_expired = is_token_expired_callback
        self._session = session
        return

    def GET(self, url, headers):
        r = send_get_request(self._session, url, self._project_handle.token, headers)
        if self._is_token_expired(r) and attempt_refresh(self._project_handle):
            r = send_get_request(
                self._session, url, self._project_handle.token, headers
            )
        return r

    def POST(self, url, headers, data):
        r = send_post_request(
            self._session, url, self._project_handle.token, headers, data
        )
        if self._is_token_expired(r) and attempt_refresh(self._project_handle):
            r = send_post_request(
                self._session, url, self._project_handle.token, headers, data
            )
        return r

    def PUT(self, url, headers, data, allow_redirects=True):
        r = send_put_multipart_request(
            self._session,
            url,
            self._project_handle.token,
            headers,
            data,
            allow_redirects,
        )
        if self._is_token_expired(r) and attempt_refresh(self._project_handle):
            # @@@ if files contained streaming data, can't read that on retry
            r = send_put_multipart_request(
                self._session,
                url,
                self._project_handle.token,
                headers,
                data,
                allow_redirects,
            )
        return r

    def DELETE(self, url, headers):
        r = send_delete_request(self._session, url, self._project_handle.token, headers)
        if self._is_token_expired(r) and attempt_refresh(self._project_handle):
            r = send_delete_request(
                self._session, url, self._project_handle.token, headers
            )
        return r


# -----------------------------------------------------------------------------


def send_get_request(session, url, token, headers):
    headers["Authorization"] = _append_bearer(token)

    rsp = session.get(url, headers=headers)
    return rsp


def send_post_request(session, url, token, headers, payload):
    headers["Authorization"] = _append_bearer(token)

    rsp = session.post(url, headers=headers, data=payload)
    return rsp


def send_put_multipart_request(
    session, url, token, headers, data, allow_redirects=True
):
    headers["Authorization"] = _append_bearer(token)

    rsp = session.put(url, headers=headers, data=data, allow_redirects=allow_redirects)
    return rsp


def send_delete_request(session, url, token, headers):
    headers["Authorization"] = _append_bearer(token)

    rsp = session.delete(url, headers=headers)
    return rsp


# =============================================================================
# private functions


def _append_bearer(access_token):
    if "Bearer" in access_token:
        return access_token
    return "Bearer " + access_token
