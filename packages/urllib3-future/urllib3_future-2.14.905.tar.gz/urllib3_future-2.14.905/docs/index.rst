urllib3.future
==============

.. toctree::
   :hidden:
   :maxdepth: 3

   v2-migration-guide
   user-guide
   async
   advanced-usage
   reference/index
   contributing
   changelog

- ⚡ urllib3.future is a powerful, *user-friendly* HTTP client for Python.
- ⚡ urllib3.future goes beyond supported features while remaining compatible.
- ⚡ urllib3.future brings many critical features that are missing from both the Python standard libraries and **urllib3**!


- Async.
- Task safety.
- Thread safety.
- Happy Eyeballs.
- Connection pooling.
- Unopinionated about OpenSSL.
- Client-side SSL/TLS verification.
- Highly customizable DNS resolution.
- File uploads with multipart encoding.
- DNS over UDP, TLS, QUIC, or HTTPS. DNSSEC protected.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, brotli, and zstd encoding.
- Support for Python/PyPy 3.7+, no compromise.
- Automatic Connection Upgrade / Downgrade.
- Early (Informational) Responses / Hints.
- HTTP/1.1, HTTP/2 and HTTP/3 support.
- WebSocket over HTTP/2+ (RFC8441).
- Proxy support for HTTP and SOCKS.
- Post-Quantum Security with QUIC.
- Detailed connection inspection.
- HTTP/2 with prior knowledge.
- Multiplexed connection.
- Mirrored Sync & Async.
- Trailer Headers.
- Amazingly Fast.
- WebSocket.

urllib3 is powerful and easy to use:

.. code-block:: pycon

   >>> import urllib3
   >>> resp = urllib3.request("GET", "https://httpbin.org/robots.txt")
   >>> resp.status
   200
   >>> resp.data
   b"User-agent: *\nDisallow: /deny\n"
   >>> resp.version
   20

Installing
----------

urllib3.future can be installed with `pip <https://pip.pypa.io>`_

.. code-block:: bash

  $ python -m pip install urllib3.future

Usage
-----

The :doc:`user-guide` is the place to go to learn how to use the library and
accomplish common tasks. The more in-depth :doc:`advanced-usage` guide is the place to go for lower-level tweaking.

The :doc:`reference/index` documentation provides API-level documentation.

License
-------

urllib3.future is made available under the MIT License. For more details, see `LICENSE.txt <https://github.com/jawah/urllib3.future/blob/master/LICENSE.txt>`_.

Contributing
------------

We happily welcome contributions, please see :doc:`contributing` for details.
