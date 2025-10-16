import ctypes
import enum
import threading
from pathlib import Path

from pyautd3.native_methods.autd3capi_driver import OptionDuration, ResultLink


class SourceTag(enum.IntEnum):
    Auto = 0
    Addr = 1
    Request = 2

    @classmethod
    def from_param(cls, obj):
        return int(obj)  # pragma: no cover


class Source(ctypes.Structure):
    _fields_ = [("tag", ctypes.c_uint8), ("addr", ctypes.c_char_p)]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Source) and self._fields_ == other._fields_  # pragma: no cover

    def __hash__(self) -> int:
        return super().__hash__()  # pragma: no cover


class Timeouts(ctypes.Structure):
    _fields_ = [("connect", OptionDuration), ("read", OptionDuration), ("write", OptionDuration)]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Timeouts) and self._fields_ == other._fields_  # pragma: no cover

    def __hash__(self) -> int:
        return super().__hash__()  # pragma: no cover


class RemoteTwinCATOption(ctypes.Structure):
    _fields_ = [("timeouts", Timeouts), ("source", Source)]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RemoteTwinCATOption) and self._fields_ == other._fields_  # pragma: no cover

    def __hash__(self) -> int:
        return super().__hash__()  # pragma: no cover


class Singleton(type):
    _instances = {}  # type: ignore[var-annotated]
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:  # pragma: no cover
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class NativeMethods(metaclass=Singleton):
    def init_dll(self, bin_location: Path, bin_prefix: str, bin_ext: str) -> None:
        self.dll = ctypes.CDLL(str(bin_location / f"{bin_prefix}autd3_capi_link_remote_twincat{bin_ext}"))

        self.dll.AUTDLinkRemoteTwinCAT.argtypes = [ctypes.c_char_p, ctypes.c_char_p, RemoteTwinCATOption]
        self.dll.AUTDLinkRemoteTwinCAT.restype = ResultLink

    def link_remote_twin_cat(self, addr: bytes, ams_net_id: bytes, option: RemoteTwinCATOption) -> ResultLink:
        return self.dll.AUTDLinkRemoteTwinCAT(addr, ams_net_id, option)
