class DBException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.error_code = None


class DBConnectionError(DBException):
    def __init__(self, error_code, message):
        self.message = message
        self.error_code = error_code


class DBQueryError(DBException):
    def __init__(self, error_code, message):
        self.message = message
        self.error_code = error_code


class DBIntegrityError(DBException):
    def __init__(self, error_code, message):
        self.message = message
        self.error_code = error_code
