from typing import Self

from pyautd3.driver.link import Link
from pyautd3.native_methods.autd3capi_driver import LinkPtr
from pyautd3.native_methods.utils import ConstantADT, _to_null_terminated_utf8, _validate_ptr
from pyautd3.utils.duration import Duration, into_option_duration

from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import NativeMethods as LinkTwinCAT
from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import RemoteTwinCATOption as RemoteTwinCATOption_
from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import Source as Source_
from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import SourceTag
from pyautd3_link_remote_twincat.native_methods.autd3_capi_link_remote_twincat import Timeouts as Timeouts_


class Timeouts:
    connect: Duration | None
    read: Duration | None
    write: Duration | None

    def __init__(self: Self, *, connect: Duration | None = None, read: Duration | None = None, write: Duration | None = None) -> None:
        self.connect = connect
        self.read = read
        self.write = write

    def _inner(self: Self) -> Timeouts_:
        return Timeouts_(
            into_option_duration(self.connect),
            into_option_duration(self.read),
            into_option_duration(self.write),
        )


class Source(metaclass=ConstantADT):
    _tag: SourceTag
    _addr: str

    @classmethod
    def __private_new__(cls: type["Source"], tag: SourceTag, addr: str) -> "Source":
        ins = super().__new__(cls)
        ins._tag = tag
        ins._addr = addr
        return ins

    def __new__(cls: type["Source"]) -> "Source":
        raise NotImplementedError

    @staticmethod
    def Auto() -> "Source":  # noqa: N802
        return Source.__private_new__(SourceTag.Auto, "")

    @staticmethod
    def Addr(addr: str) -> "Source":  # noqa: N802
        return Source.__private_new__(SourceTag.Addr, addr)

    @staticmethod
    def Request() -> "Source":  # noqa: N802
        return Source.__private_new__(SourceTag.Request, "")

    def _inner(self: Self) -> Source_:
        return Source_(
            self._tag,
            _to_null_terminated_utf8(self._addr) if self._tag == SourceTag.Addr else None,
        )


class RemoteTwinCATOption:
    timeouts: Timeouts
    source: Source

    def __init__(self: Self, *, timeouts: Timeouts | None = None, source: Source | None = None) -> None:
        self.timeouts = timeouts if timeouts is not None else Timeouts()
        self.source = source if source is not None else Source.Auto()

    def _inner(self: Self) -> RemoteTwinCATOption_:
        return RemoteTwinCATOption_(
            self.timeouts._inner(),
            self.source._inner(),
        )


class RemoteTwinCAT(Link):
    addr: str
    ams_net_id: str
    option: RemoteTwinCATOption

    def __init__(self: Self, addr: str, ams_net_id: str, option: RemoteTwinCATOption) -> None:
        super().__init__()
        self.addr = addr
        self.ams_net_id = ams_net_id
        self.option = option

    def _resolve(self: Self) -> LinkPtr:
        return _validate_ptr(  # pragma: no cover
            LinkTwinCAT().link_remote_twin_cat(
                _to_null_terminated_utf8(self.addr),
                _to_null_terminated_utf8(self.ams_net_id),
                self.option._inner(),
            ),
        )
