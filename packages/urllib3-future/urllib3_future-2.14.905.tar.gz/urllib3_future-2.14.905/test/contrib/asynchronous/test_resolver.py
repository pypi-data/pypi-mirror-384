from __future__ import annotations

import asyncio
import socket
from test import requires_network

import pytest

from urllib3 import ConnectionInfo
from urllib3.contrib.resolver import ProtocolResolver
from urllib3.contrib.resolver._async import (
    AsyncBaseResolver,
    AsyncManyResolver,
    AsyncResolverDescription,
)
from urllib3.contrib.resolver._async.doh import HTTPSResolver

_MISSING_QUIC_SENTINEL = object()

try:
    from urllib3.contrib.resolver._async.doq._qh3 import QUICResolver
except ImportError:
    QUICResolver = _MISSING_QUIC_SENTINEL  # type: ignore

from urllib3.contrib.resolver._async.dot import TLSResolver  # noqa: E402
from urllib3.contrib.resolver._async.dou import PlainResolver  # noqa: E402
from urllib3.contrib.resolver._async.in_memory import InMemoryResolver  # noqa: E402
from urllib3.contrib.resolver._async.null import NullResolver  # noqa: E402
from urllib3.contrib.resolver._async.system import SystemResolver  # noqa: E402
from urllib3.exceptions import InsecureRequestWarning  # noqa: E402


@pytest.mark.parametrize(
    "hostname, expect_error",
    [
        ("abc.com", True),
        ("1.1.1.1", False),
        ("8.8.8.com", True),
        ("cloudflare.com", True),
    ],
)
@pytest.mark.asyncio
async def test_null_resolver(hostname: str, expect_error: bool) -> None:
    null_resolver = AsyncResolverDescription(ProtocolResolver.NULL).new()

    if expect_error:
        with pytest.raises(socket.gaierror):
            await null_resolver.getaddrinfo(
                hostname,
                80,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
    else:
        res = await null_resolver.getaddrinfo(
            hostname,
            80,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )

        assert len(res)


@pytest.mark.parametrize(
    "url, expected_resolver_class",
    [
        ("dou://1.1.1.1", PlainResolver),
        ("dox://ooooo.com", None),
        ("doh://dns.google/resolve", HTTPSResolver),
        ("doq://dns.nextdns.io/?timeout=5&cert_reqs=0", QUICResolver),
        ("dns://dns.nextdns.io", None),
        ("null://default", NullResolver),
        ("default://null", None),
        ("system://default", SystemResolver),
        ("system://noop", SystemResolver),
        ("in-memory://noop", InMemoryResolver),
        ("in-memory://default", InMemoryResolver),
        ("DoU://1.1.1.1", PlainResolver),
        ("DOH+GOOGLE://default", HTTPSResolver),
        ("doT://1.1.1.1", TLSResolver),
        ("dot://1.1.1.1/?implementation=nonexistent", None),
        ("system://", SystemResolver),
        ("dot://", None),
        (
            "doq://dns.nextdns.io/?implementation=qh3&timeout=1&cert_reqs=0",
            QUICResolver,
        ),
    ],
)
@pytest.mark.asyncio
async def test_url_resolver(
    url: str, expected_resolver_class: type[AsyncBaseResolver] | None
) -> None:
    if expected_resolver_class is _MISSING_QUIC_SENTINEL:
        pytest.skip("Test requires qh3 installed")

    if expected_resolver_class is None:
        with pytest.raises(
            (
                NotImplementedError,
                ValueError,
                TypeError,
            )
        ):
            AsyncResolverDescription.from_url(url).new()
        return

    resolver = AsyncResolverDescription.from_url(url).new()

    assert isinstance(resolver, expected_resolver_class)
    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "dou://1.1.1.1",
        "dou://one.one.one.one",
        "dou://dns.google",
        "doh://cloudflare-dns.com/dns-query",
        "doh://dns.google",
        "system://default",
        "dot://dns.google",
        "dot://one.one.one.one",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "doh+google://",
        "doh+cloudflare://default",
    ],
)
@pytest.mark.asyncio
async def test_1_1_1_1_ipv4_resolution_across_protocols(dns_url: str) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    res = await resolver.getaddrinfo(
        "one.one.one.one",
        443,
        socket.AF_INET,
        socket.SOCK_STREAM,
        quic_upgrade_via_dns_rr=False,
    )

    assert any([_[-1][0] in ["1.1.1.1", "1.0.0.1"] for _ in res])
    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "dou://1.1.1.1",
        "dou://one.one.one.one",
        "dou://dns.google",
        "doh://cloudflare-dns.com/dns-query",
        "doh://dns.google",
        "dot://dns.google",
        "dot://one.one.one.one",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
    ],
)
@pytest.mark.parametrize(
    "hostname, expected_failure",
    [
        ("brokendnssec.net", True),
        ("one.one.one.one", False),
        ("google.com", False),
    ],
)
@pytest.mark.asyncio
async def test_dnssec_exception(
    dns_url: str, hostname: str, expected_failure: bool
) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    if expected_failure:
        with pytest.raises(socket.gaierror, match="DNSSEC|DNSKEY"):
            await resolver.getaddrinfo(
                hostname,
                443,
                socket.AF_INET,
                socket.SOCK_STREAM,
                quic_upgrade_via_dns_rr=False,
            )
        await resolver.close()
        return

    res = await resolver.getaddrinfo(
        hostname,
        443,
        socket.AF_INET,
        socket.SOCK_STREAM,
        quic_upgrade_via_dns_rr=False,
    )

    assert len(res)
    await resolver.close()


@pytest.mark.parametrize(
    "hostname",
    [
        ("a" * 253) + ".com",
        ("b" * 64) + "aa.fr",
    ],
)
@pytest.mark.parametrize(
    "dns_url",
    [
        "system://",
        "dou://localhost",
    ],
)
@pytest.mark.asyncio
async def test_hostname_too_long(dns_url: str, hostname: str) -> None:
    resolver = AsyncResolverDescription.from_url(dns_url).new()

    with pytest.raises(
        UnicodeError, match="exceed 63 characters|exceed 253 characters|too long"
    ):
        await resolver.getaddrinfo(
            hostname,
            80,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )

    await resolver.close()


@pytest.mark.asyncio
async def test_many_resolver_host_constraint_distribution() -> None:
    resolvers = [
        AsyncResolverDescription.from_url("system://default?hosts=localhost").new(),
        AsyncResolverDescription.from_url("dou://127.0.0.1").new(),
        AsyncResolverDescription.from_url("in-memory://").new(),
    ]

    assert resolvers[0].have_constraints()
    assert not resolvers[1].have_constraints()
    assert resolvers[2].have_constraints()

    imr = resolvers[-1]

    imr.register("notlocalhost", "127.5.5.1")  # type: ignore[attr-defined]
    imr.register("c.localhost.eu", "127.8.8.1")  # type: ignore[attr-defined]
    imr.register("c.localhost.eu", "::1")  # type: ignore[attr-defined]

    resolver = AsyncManyResolver(*resolvers)

    res = await resolver.getaddrinfo(
        "localhost",
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert len(res)
    assert any(_[-1][0] == "127.0.0.1" for _ in res)

    res = await resolver.getaddrinfo(
        "notlocalhost",
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert len(res) == 1
    assert any(_[-1][0] == "127.5.5.1" for _ in res)

    res = await resolver.getaddrinfo(
        "c.localhost.eu",
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert len(res) == 2
    assert any(_[-1][0] == "127.8.8.1" for _ in res)
    assert any(_[-1][0] == "::1" for _ in res)

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://default/?timeout=1",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_short_endurance_sprint(dns_url: str) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    for host in [
        "www.google.com",
        "www.google.fr",
        "www.cloudflare.com",
        "youtube.com",
    ]:
        for addr_type in [socket.AF_UNSPEC, socket.AF_INET, socket.AF_INET6]:
            res = await resolver.getaddrinfo(
                host,
                443,
                addr_type,
                socket.SOCK_STREAM,
            )

            assert len(res)

            if addr_type == socket.AF_UNSPEC:
                assert any(_[0] == socket.AF_INET6 for _ in res)
                assert any(_[0] == socket.AF_INET for _ in res)
            elif addr_type == socket.AF_INET:
                assert all(_[0] == socket.AF_INET for _ in res)
            elif addr_type == socket.AF_INET6:
                assert all(_[0] == socket.AF_INET6 for _ in res)

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://default?rfc8484=true",
        "doh+cloudflare://default?rfc8484=true",
        "doh://dns.nextdns.io/dns-query?rfc8484=true",
        "doh+adguard://",
    ],
)
@pytest.mark.asyncio
async def test_doh_rfc8484(dns_url: str) -> None:
    resolver = AsyncResolverDescription.from_url(dns_url).new()

    for host in [
        "www.google.com",
        "www.google.fr",
        "www.cloudflare.com",
        "youtube.com",
    ]:
        for addr_type in [socket.AF_UNSPEC, socket.AF_INET, socket.AF_INET6]:
            res = await resolver.getaddrinfo(
                host,
                443,
                addr_type,
                socket.SOCK_STREAM,
            )

            assert len(res)

            if addr_type == socket.AF_UNSPEC:
                assert any(_[0] == socket.AF_INET6 for _ in res)
                assert any(_[0] == socket.AF_INET for _ in res)
            elif addr_type == socket.AF_INET:
                assert all(_[0] == socket.AF_INET for _ in res)
            elif addr_type == socket.AF_INET6:
                assert all(_[0] == socket.AF_INET6 for _ in res)

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_task_safe_resolver(dns_url: str) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    tasks = []

    for name in [
        "www.google.com",
        "www.cloudflare.com",
        "youtube.com",
        "github.com",
        "api.github.com",
    ]:
        tasks.append(
            resolver.getaddrinfo(
                name,
                443,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        )

    results = await asyncio.gather(*tasks)

    for result in results:
        assert len(result)

    await resolver.close()


@requires_network()
@pytest.mark.asyncio
async def test_many_resolver_task_safe() -> None:
    resolvers = [
        AsyncResolverDescription.from_url("doh+google://").new(),
        AsyncResolverDescription.from_url("doh+cloudflare://").new(),
        AsyncResolverDescription.from_url("doh+adguard://").new(),
        AsyncResolverDescription.from_url("dot+google://").new(),
        AsyncResolverDescription.from_url("doh+google://").new(),
    ]

    resolver = AsyncManyResolver(*resolvers)

    tasks = []

    for name in [
        "www.google.com",
        "www.cloudflare.com",
        "youtube.com",
        "github.com",
        "api.github.com",
        "gist.github.com",
    ]:
        tasks.append(
            resolver.getaddrinfo(
                name,
                443,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        )

    results = await asyncio.gather(*tasks)

    for result in results:
        assert len(result)

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_resolver_recycle(dns_url: str) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    await resolver.close()

    old_resolver, resolver = resolver, resolver.recycle()

    assert type(old_resolver) is type(resolver)

    assert resolver.protocol == old_resolver.protocol
    assert resolver.specifier == old_resolver.specifier
    assert resolver.implementation == old_resolver.implementation

    assert resolver.is_available()
    assert not old_resolver.is_available()

    await resolver.close()

    assert not resolver.is_available()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_resolve_cannot_recycle_when_available(dns_url: str) -> None:
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    with pytest.raises(RuntimeError):
        resolver.recycle()

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_ipv6_always_preferred(dns_url: str) -> None:
    """Our resolvers must place IPV6 address in the beginning of returned list."""
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    inet_classes = []

    res = await resolver.getaddrinfo(
        "www.cloudflare.com",
        443,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    for r in res:
        if r[0] not in inet_classes:
            inet_classes.append(r[0])

    assert inet_classes[0] == socket.AF_INET6
    assert inet_classes[1] == socket.AF_INET

    await resolver.close()


@requires_network()
@pytest.mark.parametrize(
    "dns_url",
    [
        "doh+google://",
        "doh+cloudflare://",
        "doq://dns.nextdns.io/?timeout=5&cert_reqs=0",
        "dot://one.one.one.one",
        "dou://one.one.one.one",
    ],
)
@pytest.mark.asyncio
async def test_dgram_upgrade(dns_url: str) -> None:
    """www.cloudflare.com records HTTPS exist, we know it. This verify that we are able to propose a DGRAM upgrade."""
    if QUICResolver is _MISSING_QUIC_SENTINEL and dns_url.startswith("doq"):
        pytest.skip("Test requires qh3 installed")

    resolver = AsyncResolverDescription.from_url(dns_url).new()

    sock_types = []

    res = await resolver.getaddrinfo(
        "www.cloudflare.com",
        443,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
        quic_upgrade_via_dns_rr=True,
    )

    for r in res:
        if r[1] not in sock_types:
            sock_types.append(r[1])

    assert sock_types[0] == socket.SOCK_DGRAM
    assert sock_types[1] == socket.SOCK_STREAM

    await resolver.close()


@pytest.mark.parametrize(
    "dns_url, hostname, expected_addr",
    [
        (
            "in-memory://default/?hosts=abc.tld:1.1.1.1,def.tld:8.8.8.8",
            "abc.tld",
            "1.1.1.1",
        ),
        (
            "in-memory://default/?hosts=abc.tld:1.1.1.1,def.tld:8.8.8.8",
            "def.tld",
            "8.8.8.8",
        ),
        (
            "in-memory://default/?hosts=abc.tld:1.1.1.1,def.tld:8.8.8.8",
            "defe.tld",
            None,
        ),
        (
            "in-memory://default/?hosts=abc.tld:1.1.1.1,def.tld:8.8.8.8&hosts=a.company.internal:1.1.1.8",
            "a.company.internal",
            "1.1.1.8",
        ),
        (
            "in-memory://default/?hosts=abc.tld:1.1.1.1,def.tld:8.8.8.8&hosts=a.company.internal:1.1.1.8",
            "def.tld",
            "8.8.8.8",
        ),
        (
            "in-memory://default",
            "abc.tld",
            None,
        ),
        (
            "in-memory://default/?hosts=x",
            "abc.tld",
            None,
        ),
        (
            "in-memory://default/?hosts=x",
            "x",
            None,
        ),
        (
            "in-memory://default/?hosts=abc.tld:::1,def.tld:8.8.8.8",
            "abc.tld",
            "::1",
        ),
        (
            "in-memory://default/?hosts=abc.tld:[::1],def.tld:8.8.8.8",
            "abc.tld",
            "::1",
        ),
    ],
)
@pytest.mark.asyncio
async def test_in_memory_resolver(
    dns_url: str, hostname: str, expected_addr: str | None
) -> None:
    resolver = AsyncResolverDescription.from_url(dns_url).new()

    assert resolver.have_constraints()

    if expected_addr is None:
        with pytest.raises(socket.gaierror):
            await resolver.getaddrinfo(
                hostname,
                80,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        return

    res = await resolver.getaddrinfo(
        hostname,
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert any([_[-1][0] == expected_addr for _ in res])


@requires_network()
@pytest.mark.asyncio
async def test_doh_http11() -> None:
    """Ensure we can do DoH over HTTP/1.1 even if... that's absolutely not recommended!"""
    resolver = AsyncResolverDescription.from_url(
        "doh+google://default/?disabled_svn=h2,h3"
    ).new()

    res = await resolver.getaddrinfo(
        "www.cloudflare.com",
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert len(res)

    await resolver.close()


@requires_network()
@pytest.mark.asyncio
async def test_doh_http11_upgradable() -> None:
    """Ensure we can do DoH over HTTP/1.1 that can upgrade to HTTP/3"""
    resolver = AsyncResolverDescription.from_url(
        "doh+google://default/?disabled_svn=h2&cert_reqs=0"
    ).new()
    with pytest.warns(InsecureRequestWarning):
        res = await resolver.getaddrinfo(
            "www.cloudflare.com",
            80,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )

        assert len(res)
    await resolver.close()


@requires_network()
@pytest.mark.asyncio
async def test_doh_on_connection_callback() -> None:
    """Ensure we can inspect the resolver connection with a callback."""
    resolver_description = AsyncResolverDescription.from_url("doh+google://")

    toggle_witness: bool = False

    async def callback(conn_info: ConnectionInfo) -> None:
        nonlocal toggle_witness
        if conn_info:
            toggle_witness = True

    resolver_description["on_post_connection"] = callback

    resolver = resolver_description.new()

    res = await resolver.getaddrinfo(
        "www.cloudflare.com",
        80,
        socket.AF_UNSPEC,
        socket.SOCK_STREAM,
    )

    assert len(res)
    assert toggle_witness


@pytest.mark.parametrize("dns_url", ["system://", "in-memory://", "null://"])
@pytest.mark.asyncio
async def test_not_closeable_recycle(dns_url: str) -> None:
    r = AsyncResolverDescription.from_url(dns_url).new()

    await r.close()

    assert r.is_available()

    rr = r.recycle()

    assert rr == r


@pytest.mark.asyncio
async def test_recycle_in_memory_with_mock() -> None:
    r = AsyncResolverDescription.from_url(
        "in-memory://default/?hosts=localhost:8.8.8.8&hosts=local:1.1.1.1&maxsize=8"
    ).new()

    assert r.is_available()
    assert len(r._hosts) == 2  # type: ignore[attr-defined]
    assert "localhost" in r._hosts  # type: ignore[attr-defined]
    assert "local" in r._hosts  # type: ignore[attr-defined]
    assert r._maxsize == 8  # type: ignore[attr-defined]

    await r.close()

    assert r.is_available()

    r.is_available = lambda: False  # type: ignore

    assert not r.is_available()

    rr = AsyncBaseResolver.recycle(r)

    assert rr.is_available()
    assert len(rr._hosts) == 2  # type: ignore[attr-defined]
    assert "localhost" in rr._hosts  # type: ignore[attr-defined]
    assert "local" in rr._hosts  # type: ignore[attr-defined]
    assert rr._maxsize == 8  # type: ignore[attr-defined]
