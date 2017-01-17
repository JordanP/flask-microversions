import re

from . import exceptions
from . import utils
from . import versioned_method

# Define the minimum and maximum version of the API across all of the
# REST API. The format of the version is:
# X.Y where:
#
# - X will only be changed if a significant backwards incompatible API
# change is made which affects the API as whole. That is, something
# that is only very very rarely incremented.
#
# - Y when you make any change to the API. Note that this includes
# semantic changes which may not affect the input or output formats or
# even originate in the API code layer. We are not distinguishing
# between backwards compatible and backwards incompatible changes in
# the versioning system. It must be made clear in the documentation as
# to what is a backwards compatible change and what is a backwards
# incompatible one.

#
# You must update the API version history string below with a one or
# two line description as well as update rest_api_version_history.rst
REST_API_VERSION_HISTORY = """

    REST API Version History:

    * 1.0 - Initial Version.
"""

# The minimum and maximum versions of the API supported
# The default api version request is defined to be the
# the minimum version of the API supported.
MIN_API_VERSION = (1, 0)
MAX_API_VERSION = (1, 2)

HEADER_NAME = "X-Version"


# NOTE(jordanP): min and max versions declared as functions so we can
# mock them for unittests.
def min_api_version():
    return APIVersionRequest('.'.join(map(str, MIN_API_VERSION)))


def max_api_version():
    return APIVersionRequest('.'.join(map(str, MAX_API_VERSION)))


class APIVersionRequest(utils.ComparableMixin):
    """This class represents an API Version Request.

    This class includes convenience methods for manipulation
    and comparison of version numbers as needed to implement
    API microversions.
    """

    def __init__(self, version_string=None):
        """Create an API version request object."""
        self._ver_major = None
        self._ver_minor = None

        if version_string is not None:
            match = re.match(r"^([0-9]\d*)\.([0-9]\d*)$", version_string)
            if match:
                self._ver_major = int(match.group(1))
                self._ver_minor = int(match.group(2))
            else:
                raise exceptions.InvalidAPIVersionString(
                    version=version_string)

    def __bool__(self):
        return (self._ver_major or self._ver_minor) is not None

    __nonzero__ = __bool__

    def _cmpkey(self):
        """Return the value used by ComparableMixin for rich comparisons."""
        return self._ver_major, self._ver_minor

    def matches_versioned_method(self, method):
        """Compares this version to that of a versioned method."""

        if not isinstance(method, versioned_method.VersionedMethod):
            msg = ('An API version request must be compared '
                   'to a VersionedMethod object.')
            raise ValueError(msg)

        return self.matches(method.start_version, method.end_version)

    def matches(self, min_version, max_version=None):
        """Compares this version to the specified min/max range.

        Returns whether the version object represents a version
        greater than or equal to the minimum version and less than
        or equal to the maximum version.

        If min_version is null then there is no minimum limit.
        If max_version is null then there is no maximum limit.
        If self is null then raise ValueError.

        :param min_version: Minimum acceptable version.
        :param max_version: Maximum acceptable version.
        :returns: boolean
        """

        if not self:
            raise ValueError

        if isinstance(min_version, str):
            min_version = APIVersionRequest(version_string=min_version)
        if isinstance(max_version, str):
            max_version = APIVersionRequest(version_string=max_version)

        if not min_version and not max_version:
            return True

        if not max_version:
            return min_version <= self
        if not min_version:
            return self <= max_version
        return min_version <= self <= max_version

    def get_string(self):
        """Returns a string representation of this object.

        If this method is used to create an APIVersionRequest,
        the resulting object will be an equivalent request.
        """
        if not self:
            raise ValueError
        return "%s.%s" % (self._ver_major, self._ver_minor)
