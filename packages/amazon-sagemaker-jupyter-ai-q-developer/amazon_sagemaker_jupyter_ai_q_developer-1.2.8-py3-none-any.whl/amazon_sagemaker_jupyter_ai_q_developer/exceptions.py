class ClientExtensionException(Exception):
    """
    Exception raised for client-side errors.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"ClientException: {self.message}"


class ServerExtensionException(Exception):
    """
    Exception raised for server-side errors.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"ServerException: {self.message}"
