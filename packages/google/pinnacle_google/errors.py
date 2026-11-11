class ConnectorError(Exception):
    """Base error for the Google connector."""


class GoogleNotConfigured(ConnectorError):
    """OAuth client id/secret missing."""


class Phase3ReadOnly(ConnectorError):
    """Send and calendar mutation are forbidden until later phases."""
