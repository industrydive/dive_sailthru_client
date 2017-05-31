from sailthru.sailthru_error import SailthruClientError


def is_sailthru_client_timeout_error(error):
    ''' Returns True if given error is an instance of SailthruClientError and
        it looks like a ConnectTimeout error
    '''
    return (isinstance(error, SailthruClientError) and 'ConnectTimeout' in
            str(error))
