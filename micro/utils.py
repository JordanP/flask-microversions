import functools

import flask
import flask.json
import flask.testing


class JSONResponseMixin():
    def json(self):
        return flask.json.loads(self.data)


class Response(JSONResponseMixin, flask.Response):
    pass


def add_json_kwarg(f):
    """Fill the headers and the body of an HTTP request for a JSON request."""

    @functools.wraps(f)
    def decorated(*args, json=None, **kwargs):
        if not json:
            return f(*args, **kwargs)

        if 'headers' not in kwargs or 'Content-Type' not in kwargs['headers']:
            headers = kwargs.setdefault('headers', {})
            headers['Content-Type'] = 'application/json'
        if 'data' not in kwargs or kwargs['data'] is None:
            kwargs['data'] = flask.json.dumps(json)
        return f(*args, **kwargs)

    return decorated


class FlaskClient(flask.testing.FlaskClient):
    post = add_json_kwarg(flask.testing.FlaskClient.post)


class ComparableMixin(object):  # pragma: no cover
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)
