"""
arthub_api.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of exceptions.
"""


class Error(Exception):
    """There was an ambiguous exception that occurred while call each interface.
    """

    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return str(self.value)


class ErrorNotLogin(Error):
    """arthub_api.OpenAPI instance not logged in
    """

    def __init__(self):
        Error.__init__(self, value="failed to login in")
