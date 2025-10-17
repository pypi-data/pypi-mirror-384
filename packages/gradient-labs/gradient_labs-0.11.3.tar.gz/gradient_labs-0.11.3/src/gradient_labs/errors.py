from requests.exceptions import JSONDecodeError


class ResponseError(Exception):
    """
    Exeception representing an unexpected HTTP response status from the API.
    """

    def __init__(self, response):
        super().__init__()

        self.status_code = response.status_code
        try:
            self.message = response.json().get("message")
        except JSONDecodeError:
            self.message = response.text

    def __str__(self):
        return f"HTTP {self.status_code}: {self.message}"


class SignatureVerificationError(Exception):
    """
    Exception representing the webhook signature was invalid or too old.
    """
