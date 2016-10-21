from sailthru.sailthru_error import SailthruClientError


class SailthruApiError(SailthruClientError):
    """
        Custom Exception class for errors at the API level. In other words
        when response.is_ok() is False. Since this is a subclass of
        SailthruClientError, any handlers already set up for that will
        catch this too.
    """
    # TODO: add accessor for response_error object

    def __init__(self, *args, **kwargs):
        self.api_error_code = kwargs.pop('api_error_code', 0)
        self.api_error_message = kwargs.pop('api_error_message', '')

        super(SailthruApiError, self).__init__(*args, **kwargs)


