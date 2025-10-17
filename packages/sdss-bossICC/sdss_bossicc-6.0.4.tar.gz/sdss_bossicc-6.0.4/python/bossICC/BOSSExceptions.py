from actorcore.ICCExceptions import *  # noqa


class PhaseMicroBusy(Exception):
    """Thrown by the cam forth controller when the CamForth is busy."""


class UndefinedCommand(Exception):
    """Thrown when an unkown command is issued to the camForth."""


class TimeOutError(Exception):
    """Thrown whenever a command times out."""
