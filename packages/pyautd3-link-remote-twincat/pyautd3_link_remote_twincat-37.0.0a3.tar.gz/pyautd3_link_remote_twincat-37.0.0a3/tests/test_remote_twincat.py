import pytest
from pyautd3 import Duration

from pyautd3_link_remote_twincat import RemoteTwinCAT, RemoteTwinCATOption, Source, Timeouts
from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import SourceTag


def test_timeouts():
    timeouts = Timeouts()
    inner = timeouts._inner()
    assert not inner.connect.has_value
    assert not inner.read.has_value
    assert not inner.write.has_value

    timeouts = Timeouts(connect=Duration.from_nanos(0), read=Duration.from_nanos(1), write=Duration.from_nanos(2))
    inner = timeouts._inner()
    assert inner.connect.has_value
    assert inner.connect.value == Duration.from_nanos(0)._inner
    assert inner.read.has_value
    assert inner.read.value == Duration.from_nanos(1)._inner
    assert inner.write.has_value
    assert inner.write.value == Duration.from_nanos(2)._inner


def test_source():
    auto = Source.Auto()
    addr = Source.Addr("0.0.0.0.0.0")
    req = Source.Request()

    assert auto._inner().tag == SourceTag.Auto
    assert auto._inner().addr is None
    assert addr._inner().tag == SourceTag.Addr
    assert addr._inner().addr == b"0.0.0.0.0.0"
    assert req._inner().tag == SourceTag.Request
    assert req._inner().addr is None

    with pytest.raises(NotImplementedError):
        _ = Source()


def test_option():
    option = RemoteTwinCATOption()
    inner = option._inner()
    assert not inner.timeouts.connect.has_value
    assert not inner.timeouts.read.has_value
    assert not inner.timeouts.write.has_value
    assert inner.source.tag == SourceTag.Auto
    assert inner.source.addr is None


def test_remote_twincat():
    _ = RemoteTwinCAT(
        "0.0.0.0",  # noqa: S104
        "1.1.1.1.1.1",
        RemoteTwinCATOption(),
    )
