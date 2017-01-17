Traditional API versioning
==========================
Most APIs are versioned using a version prefix like ``/v1.0/``, ``/v2/`` etc.
In theory, every major API change should increase the major version number,
to maintain backward compatibility with clients consuming the API. This
quickly becomes problematic if the API wants to evolve quickly, the URLs
would have to be updated often.


Microversioning and content negotiation
=======================================
A more elegant solution to solve the backward compatibility issue is to tell
a client to send, in a HTTP header with each request, the maximum version
of the API it supports. The server is in charge of returning a response
that is valid with respect to what the client understands. That technique
is called ``content negotiation``.


Microversioning and Flask
=========================
The basic idea is to decorate each ``view function`` (i.e the function in
charge of a Flask endpoint) with a decorator that tells for which version of
the API a ``view function`` is available.

To indicate that an endpoint is only available to clients which send a
``X-Version`` HTTP header between 1.0 and 1.1, do::

 @app.api_version(
     min_ver="1.0,
     max_ver="1.1"
 )
 @app.route('/ep1')
 def index():
     return b'ep1'


To deprecate an endpoint, just decorate it with ``api_version`` and a
``max_ver`` argument. To introduce an endpoint, hidden to old client, just
decorate it with ``api_version`` and a ``min_ver`` argument. Finally, to serve
different content based on which version a client understands, do::

 @app.route('/versioned_view')
 def index():
     requested_version = flask.g.api_version_request
     if requested_version.matches("1.2"):
         return b'1.2'
     elif requested_version.matches("1.1"):
         return b'1.1'
     else:
         return b'1.0'

Note
====
The code, especially the ``api_version_request`` and ``versioned_method``
modules, is heavily borrowed from the OpenStack project.
