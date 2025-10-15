class CentralReachException(Exception):
    """
    The class is deprecated, don't use it!
    """

    pass


class ScheduledMaintenance(CentralReachException):
    """
    The class is deprecated, don't use it!
    """

    pass


class EmptyPage(CentralReachException):
    """
    The class is deprecated, don't use it!
    """

    pass


class BadRequest(CentralReachException):
    """
    The class is deprecated, don't use it!
    """

    pass


class CentralReachError(CentralReachException):
    pass


class ScheduledMaintenanceError(ScheduledMaintenance, CentralReachError):
    pass


class EmptyPageError(EmptyPage, CentralReachError):
    pass


class BadRequestError(BadRequest, CentralReachError):
    pass


class PasswordExpiredException(CentralReachException):
    """
    This exception is raised when a password is expired
    """

    pass
