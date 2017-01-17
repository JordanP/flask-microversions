from werkzeug.exceptions import BadRequest, NotAcceptable, NotFound


class InvalidAPIVersionString(BadRequest):
    def __init__(self, response=None, **kwargs):
        msg = ("API Version String %(version)s is of invalid format. Must "
               "be of format MajorNum.MinorNum.") % {**kwargs}
        super().__init__(msg, response)


class InvalidGlobalAPIVersion(NotAcceptable):
    def __init__(self, response=None, **kwargs):
        msg = ("Version %(req_ver)s is not supported by the API. Minimum "
               "is %(min_ver)s and maximum is %(max_ver)s.") % {**kwargs}
        super().__init__(msg, response)


class VersionNotFoundForAPIMethod(NotFound):
    def __init__(self, response=None, **kwargs):
        msg = ("API version %(version)s is not supported on this "
               "method.") % {**kwargs}
        super().__init__(msg, response)
