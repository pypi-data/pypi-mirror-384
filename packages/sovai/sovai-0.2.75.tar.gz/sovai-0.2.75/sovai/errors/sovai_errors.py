class InvalidCredentialsError(Exception):
    """
    Raise exception if credentional data invalid status code: 401

    :param Exception: Base class exception
    """

    def __init__(self, message: str):
        super().__init__(message)


class ServiceUnavailableError(Exception):
    """
    Raise exception if server unavailable status code: 503

    :param Exception: Base class exception
    """

    def __init__(self, message: str):
        super().__init__(message)


class InvalidInputData(Exception):
    """
    Raise exception when you incorrent tap input data such email or password

    :param Exception: Base class exception
    """

    def __init__(self, message: str):
        super().__init__(message)
