import collections
import functools
from typing import Optional

import flask

from . import api_version_request
from . import exceptions
from . import utils
from . import versioned_method


class CustomDict(collections.UserDict):

    def __getitem__(self, endpoint):

        def version_select(*args, **kwargs):
            """Select and call the matching version of the specified method.

            Look for the method which matches the name supplied and version
            constraints and calls it with the supplied arguments.
            :returns: Returns the result of the method called
            :raises: VersionNotFoundForAPIMethod if there is no method which
                 matches the name and version constraints
            """

            # Version of the API that is requested by the client
            version_request = flask.g.api_version_request

            versioned_methods = flask.current_app.versioned_endpoints[endpoint]
            for func in versioned_methods:
                if version_request.matches_versioned_method(func):
                    # Update the version_select wrapper function so
                    # other decorator attributes like wsgi.response
                    # are still respected.
                    functools.update_wrapper(version_select, func.func)
                    return func.func(*args, **kwargs)

            # No version match
            raise exceptions.VersionNotFoundForAPIMethod(
                version=version_request.get_string())

        if flask.current_app and endpoint in flask.current_app.versioned_endpoints:  # noqa
            return version_select
        else:
            return super().__getitem__(endpoint)


class Flask(flask.Flask):
    versioned_endpoints = collections.defaultdict(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the `view_functions` defined in `flask.Flask` with a
        # custom dict-like data structure.
        self.view_functions = CustomDict()

    @classmethod
    def api_version(cls, min_ver: str, max_ver: Optional[str]=None):
        """Decorator for versioning API methods.

        :param min_ver: string representing minimum version
        :param max_ver: optional string representing maximum version
        """

        def decorator(f):
            obj_min_ver = api_version_request.APIVersionRequest(min_ver)
            obj_max_ver = api_version_request.APIVersionRequest(max_ver)

            func_name = f.__name__

            new_func = versioned_method.VersionedMethod(
                func_name, obj_min_ver, obj_max_ver, f)

            # Add to list of versioned endpoints registered
            cls.versioned_endpoints[func_name].append(new_func)

            # Ensure the list is sorted by minimum version (reversed)
            # so later when we work through the list in order we find
            # the method which has the latest version which supports
            # the version requested.
            # TODO(jordanP): Add check to ensure that there are no overlapping
            # ranges of valid versions as that is ambiguous
            cls.versioned_endpoints[func_name].sort(reverse=True)

            return f

        return decorator


# create our little application :)
app = Flask(__name__)
app.response_class = utils.Response
app.test_client_class = utils.FlaskClient


@app.before_request
def only_json():
    """Check that if the client sent some data, it's JSON formatted."""
    if flask.request.data and not flask.request.is_json:
        flask.abort(415)


@app.before_request
def set_api_version_request():
    """Set API version request based on the request header information."""

    # If the client didn't explicitly tell which version it supports,
    # assume it supports the oldest (minimum) version, just to be safe.
    if api_version_request.HEADER_NAME not in flask.request.headers:
        flask.g.api_version_request = api_version_request.min_api_version()
    else:
        hdr_string = flask.request.headers[api_version_request.HEADER_NAME]

        # Special value, useful for testing or client leaving on the bleeding
        # edge who always want the latest and greatest version of our API.
        if hdr_string == 'latest':
            flask.g.api_version_request = api_version_request.max_api_version()
        else:
            flask.g.api_version_request = \
                api_version_request.APIVersionRequest(hdr_string)

            # Check that the version requested is within the global
            # minimum/maximum of supported API versions
            if not flask.g.api_version_request.matches(
                    api_version_request.min_api_version(),
                    api_version_request.max_api_version()
            ):
                raise exceptions.InvalidGlobalAPIVersion(
                    req_ver=flask.g.api_version_request.get_string(),
                    min_ver=api_version_request.min_api_version().get_string(),
                    max_ver=api_version_request.max_api_version().get_string()
                )


@app.after_request
def add_api_version_header(response: utils.Response):
    # We should always tell the client which version of the API we delivered.
    if hasattr(flask.g, 'api_version_request'):
        requested_version = flask.g.api_version_request
        response.headers.add(
            api_version_request.HEADER_NAME,
            requested_version.get_string()
        )
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
        data = flask.request.get_json()
        return flask.jsonify(data)
    else:
        return b''


@app.api_version("1.1")
@app.route('/min_version')
def index2():
    return flask.jsonify(['/min_version'])


@app.api_version(
    min_ver=api_version_request.min_api_version().get_string(),
    max_ver="1.1"
)
@app.route('/max_version')
def index3():
    return flask.jsonify(['/max_version'])


@app.api_version(
    api_version_request.min_api_version().get_string(),
    api_version_request.min_api_version().get_string()
)
@app.api_version(
    api_version_request.max_api_version().get_string(),
    api_version_request.max_api_version().get_string(),
)
@app.route('/double_decorator')
def index4():
    return flask.jsonify(['/double_decorator'])


@app.route('/versioned_view')
def index5():
    requested_version = flask.g.api_version_request
    if requested_version.matches("1.2"):
        return b'1.2'
    elif requested_version.matches("1.1"):
        return b'1.1'
    else:
        return b'1.0'

