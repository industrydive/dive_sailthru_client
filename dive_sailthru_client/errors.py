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

    # Definition of the error codes from Sailthru that we consider to be a user/email related error
    # Designed to raise a SailthruUserEmailError to allow for handling of these cases specifically
    # See full list of errors from Sailthru at https://getstarted.sailthru.com/developers/api-basics/responses/
    USER_EMAIL_ERROR_CODES = {
                11: 'Invalid Email',
                32: 'Email has opted out of delivery from client',
                33: 'Email has opted out of delivery from template',
                34: 'Email may not be emailed',
                35: 'Email is a known hardbounce',
                37: 'Email will only accept basic templates',
    }
