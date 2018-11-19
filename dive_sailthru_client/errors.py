from sailthru.sailthru_error import SailthruClientError


class SailthruApiError(SailthruClientError):
    """
        Custom Exception class for errors at the API level. In other words
        when response.is_ok() is False. Since this is a subclass of
        SailthruClientError, any handlers already set up for that will
        catch this too.
    """
    # TODO: add accessor for response_error object
    pass

class SailthruUserEmailError(SailthruClientError):
    """
    Custom Exception class for errors related to user email being invalid or
    otherwise not being able to be emailed. A common usage is that the user
    will stop trying to email when the API returns an error of this class.
    """
    pass