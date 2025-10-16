from __future__ import annotations

import asyncio
import contextlib
import threading
import typing
from os import environ, path

import pytest
from tornado import httpserver, ioloop, web

from dummyserver.server import DEFAULT_CERTS, run_loop_in_thread, run_tornado_app
from dummyserver.testcase import ProxyHandler  # type: ignore[attr-defined]
from urllib3 import AsyncResolverDescription, ResolverDescription

CA_PATH = path.join(path.dirname(__file__), *[".." for i in range(2)])
TRAEFIK_HTTPBIN_IPV4: str = environ.get("TRAEFIK_HTTPBIN_IPV4", "127.0.0.1")


@pytest.mark.usefixtures("requires_traefik")
class TraefikTestCase:
    host: str = "httpbin.local"
    alt_host: str = "alt.httpbin.local"

    http_port: int = 8888
    https_port: int = 4443

    http_alt_port: int = 9999
    https_alt_port: int = 8754

    https_haproxy_port: int = 9443

    http_url: str = f"http://{host}:{http_port}"
    https_url: str = f"https://{host}:{https_port}"

    http_alt_url: str = f"http://{host}:{http_alt_port}"
    https_alt_url: str = f"https://{host}:{https_alt_port}"

    https_haproxy_url: str = f"https://{host}:{https_haproxy_port}"

    test_resolver_raw: str = f"in-memory://default?hosts={host}:{TRAEFIK_HTTPBIN_IPV4}&hosts={alt_host}:{TRAEFIK_HTTPBIN_IPV4}"

    test_resolver: ResolverDescription = ResolverDescription.from_url(test_resolver_raw)

    test_async_resolver: AsyncResolverDescription = AsyncResolverDescription.from_url(
        test_resolver_raw
    )

    ca_authority: str | None = None

    @classmethod
    def setup_class(cls) -> None:
        expected_ca_path = path.join(CA_PATH, "rootCA.pem")

        if path.exists(expected_ca_path):
            cls.ca_authority = expected_ca_path


class TraefikWithProxyTestCase(TraefikTestCase):
    io_loop: typing.ClassVar[ioloop.IOLoop]

    https_certs: typing.ClassVar[dict[str, typing.Any]] = DEFAULT_CERTS

    proxy_host: typing.ClassVar[str] = "localhost"
    proxy_host_alt: typing.ClassVar[str] = "127.0.0.1"
    proxy_server: typing.ClassVar[httpserver.HTTPServer]
    proxy_port: typing.ClassVar[int]
    proxy_url: typing.ClassVar[str]

    https_proxy_server: typing.ClassVar[httpserver.HTTPServer]
    https_proxy_port: typing.ClassVar[int]
    https_proxy_url: typing.ClassVar[str]

    server_thread: typing.ClassVar[threading.Thread]
    _stack: typing.ClassVar[contextlib.ExitStack]

    @classmethod
    def setup_class(cls) -> None:
        super().setup_class()

        with contextlib.ExitStack() as stack:
            io_loop = stack.enter_context(run_loop_in_thread())

            async def run_app() -> None:
                app = web.Application([(r".*", ProxyHandler)])
                cls.proxy_server, cls.proxy_port = run_tornado_app(
                    app, None, "http", cls.proxy_host
                )

                upstream_ca_certs = cls.https_certs.get("ca_certs")

                app = web.Application(
                    [(r".*", ProxyHandler)], upstream_ca_certs=upstream_ca_certs
                )
                cls.https_proxy_server, cls.https_proxy_port = run_tornado_app(
                    app, cls.https_certs, "https", cls.proxy_host
                )

            asyncio.run_coroutine_threadsafe(run_app(), io_loop.asyncio_loop).result()  # type: ignore[attr-defined]
            cls._stack = stack.pop_all()

    @classmethod
    def teardown_class(cls) -> None:
        cls._stack.close()
