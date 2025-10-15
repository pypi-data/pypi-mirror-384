class VersantError(Exception):
    pass


class BadRequestError(VersantError):
    pass


class WrongPasswordError(VersantError):
    pass


class WrongCredentialsError(VersantError):
    pass


class BrowserError(VersantError):
    pass
