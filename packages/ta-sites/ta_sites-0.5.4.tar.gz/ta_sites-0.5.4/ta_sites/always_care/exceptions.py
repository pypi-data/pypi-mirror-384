class AlwaysCareError(Exception):
    pass


class AlwaysCareOtpCodeError(AlwaysCareError):
    pass


class BadRequestError(AlwaysCareError):
    pass
