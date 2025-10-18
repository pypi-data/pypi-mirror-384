# --------------------------------------------------------------------------
# Source file provided under Apache License, Version 2.0, January 2004,
# http://www.apache.org/licenses/
# (c) Copyright IBM Corp. 2017, 2025
# --------------------------------------------------------------------------

from os import environ

import requests


class Token(object):

    def __init__(self, token, refresh_token=None, iam_url=None, wslib=None):
        self.token = token
        self.wslib = wslib
        self.refresh_token = refresh_token
        self.refreshable = (iam_url != None and refresh_token != None) or wslib != None
        self.iam_url = iam_url


class TokenRefresher(object):

    def __init__(self, oauth_url, refresh_token, wslib):
        self.oauth_url = oauth_url
        self.refresh_token = refresh_token
        self.wslib = wslib
        return

    @classmethod
    def create(cls, token=None):
        """Attempts to create a token refresher.
        Returns None if required environment variables are missing.
        """
        params = {
            "oauth_url": (token.iam_url if token.iam_url != None else None),
            "refresh_token": (
                token.refresh_token if token.refresh_token != None else None
            ),
            "wslib": token.wslib,
        }
        return cls(**params)

    def get_fresh_token_from_wslib(self):
        return [self.wslib.auth.get_current_token(), None]

    def get_fresh_token(self):
        if self.oauth_url != None:
            return self.get_fresh_token_from_iam()
        elif self.wslib != None:
            return self.get_fresh_token_from_wslib()
        else:
            return None

    def get_fresh_token_from_iam(self):
        """Obtain a fresh user token.
        Returns the new token on success, None on failure.
        """
        try:
            r = requests.post(
                self.oauth_url,
                auth=("bx", "bx"),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "expiry": "600",
                },
            )
        except Exception as e:
            return None

        if r.status_code != requests.codes["ok"]:
            try:
                r = requests.post(
                    self.oauth_url,
                    auth=("jupyter-notebook", "jupyter-notebook"),
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "expiry": "600",
                    },
                )
            except Exception as e:
                return None
            if r.status_code != requests.codes["ok"]:
                return None

        try:
            data = r.json()
        except Exception as e:
            return None

        if not "access_token" in data:
            return None

        return [data["access_token"], data["refresh_token"]]


def attempt_refresh(handle):
    """Attempts to refresh the token in the argument handle.
    Returns True if the token was refreshed, False otherwise.
    The reason for failed refresh is not exposed to the caller.
    """

    if not handle.refreshable:
        return False

    if hasattr(handle, "_refresher_") and handle._refresher_:
        refresher = handle._refresher_
    else:
        refresher = TokenRefresher.create(handle)
        if not refresher:
            return False
        handle._refresher_ = refresher

    token = refresher.get_fresh_token()
    if not token:
        return False

    # pylogger.warning('@@@ token refreshed')
    handle.token = token[0]
    handle.refresh_token = token[1]
    return True
