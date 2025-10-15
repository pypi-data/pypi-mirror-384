import ctypes as C
import os
import sys
import time
import platform
from pathlib import Path
from dataclasses import dataclass, fields
from enum import IntEnum, IntFlag


DIR = Path(__file__).parent

_lib = C.CDLL(str(DIR / "libcode_intelligence.so"))

SCAN_CALLBACK = C.CFUNCTYPE(None, C.c_void_p)
_lib.enqueue_scan_file.argtypes = [SCAN_CALLBACK, C.c_void_p, C.c_char_p, C.c_uint64]
_lib.enqueue_scan_file.restype = None

class Definition_Link_C(C.Structure):
    _fields_ = [
        ("start_offset_in_utf8_text", C.c_uint32),
        ("end_offset_in_utf8_text"  , C.c_uint32),
        ("source_file"              , C.c_char_p),
        ("line_0_based"             , C.c_uint32),
        ("column_0_based"           , C.c_uint32),
    ]

FIND_CALLBACK = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(Definition_Link_C), C.c_int, C.c_void_p)
_lib.enqueue_find_symbols_in_text.argtypes = [FIND_CALLBACK, C.c_void_p, C.c_char_p, C.c_bool, C.c_bool]
_lib.enqueue_find_symbols_in_text.restype = None

_lib.enqueue_stop.argtypes = []
_lib.enqueue_stop.restype = None

_lib.enqueue_clear.argtypes = []
_lib.enqueue_clear.restype = None

_lib.start_workers.argtypes = []
_lib.start_workers.restype = None

_lib.get_pending_tasks_count.argtypes = []
_lib.get_pending_tasks_count.restype = C.c_uint64

_lib.free_memory.argtypes = [C.c_void_p]
_lib.free_memory.restype = None


def positional_repr(cls):
    def __repr__(self):
        values = ', '.join(repr(getattr(self, f.name)) for f in fields(self))
        return f"{cls.__name__}({values})"
    cls.__repr__ = __repr__
    return cls


class Language(IntEnum):
    UNKNOWN    = 0
    PYTHON     = 1
    JAVASCRIPT = 2

@dataclass
@positional_repr
class Definition_Link:
    start_offset_in_text: int = 0
    end_offset_in_text  : int = 0
    source_file         : str = ""
    line_0_based        : int = 0
    column_0_based      : int = 0


# IMPORTANT: KEEP THIS ALIVE FOR GO THREAD WORKER
C_NO_CALLBACK = SCAN_CALLBACK(0)
_KEEPALIVE = dict[int, tuple]()


def _wrap_data_ptr(tup: tuple):
    ptr = id(tup)
    _KEEPALIVE[ptr] = tup
    return ptr


def _unwrap_data_ptr(ptr) -> tuple:
    tup = _KEEPALIVE.pop(ptr, None)
    assert tup is not None, "keepalive missing for callback"
    return tup


# def _wrap_data_ptr(tup: tuple):
#     # MANUALLY INCREMENT THE REFERENCE COUNT
#     # We are now responsible for its lifetime
#     C.pythonapi.Py_IncRef(C.py_object(tup))
#
#     return id(tup) # C.cast(obj, C.c_void_p)
#
#
# def _unwrap_data_ptr(data_ptr) -> tuple:
#     assert data_ptr != 0, "we got NULL"
#
#     tup = C.cast(data_ptr, C.py_object).value
#
#     # MANUALLY DECREMENT THE REFERENCE COUNT.
#     # We are fulfilling our promise
#     C.pythonapi.Py_DecRef(C.py_object(tup))
#
#     return tup


def scan_file(file, language: Language, callback=None, data=None) -> bool:
    if callback is None:
        c_callback, data_ptr = C_NO_CALLBACK, 0
    else:
        c_callback, data_ptr = C_AFTER_SCAN, _wrap_data_ptr((callback, data))

    # print(f"[PY] sending next request {file}")
    _lib.enqueue_scan_file(c_callback, data_ptr, os.fsencode(file), language)

    # never drop the request (it would be a memory leak)
    return True


@SCAN_CALLBACK
def C_AFTER_SCAN(data_ptr):
    callback, data = _unwrap_data_ptr(data_ptr)
    if callback is not None:
        callback(data)


def find_symbols_in_text(text: str, callback=None, data=None, ignore_word_like: bool = False, sync: bool = False) -> bool:
    if callback is None:
        c_callback, data_ptr = C_NO_CALLBACK, 0
    else:
        c_callback, data_ptr = C_AFTER_FIND, _wrap_data_ptr((callback, data))

    # print("[PY] sending find_symbols_in_text")
    _lib.enqueue_find_symbols_in_text(c_callback, data_ptr, text.encode(), ignore_word_like, sync)

    # never drop the request (it would be a memory leak)
    return True


@FIND_CALLBACK
def C_AFTER_FIND(data_ptr, links_ptr, count, strings_handle):
    callback, data = _unwrap_data_ptr(data_ptr)
    try:
        if callback is not None:
            results = [Definition_Link()] * count
            for i in range(count):
                link = links_ptr[i]
                results[i] = Definition_Link(
                    start_offset_in_text=link.start_offset_in_utf8_text,
                    end_offset_in_text=link.end_offset_in_utf8_text,
                    source_file=link.source_file.decode('utf-8'),
                    line_0_based=link.line_0_based,
                    column_0_based=link.column_0_based,
                )
            callback(data, results)
    finally:
        if links_ptr: _lib.free_memory(links_ptr)
        if strings_handle: _lib.free_memory(strings_handle)


def pending_tasks() -> int:
    return _lib.get_pending_tasks_count()


def init():
    _lib.start_workers()


def stop():
    _lib.enqueue_stop()


def clear():
    _lib.enqueue_clear()


def wait_for_callbacks_in_seconds(timeout_s, step_s=0.15):
    # print(f"[PY] Waiting for callbacks (~{timeout_s}s)...")
    deadline = time.time() + timeout_s
    while True:
        if pending_tasks() == 0:
            # print("[PY] All pending tasks have completed.")
            return True

        if time.time() >= deadline:
            print("[PY] Timeout reached.")
            return False

        # print(f"[PY] pending_tasks={pending_tasks()}")
        time.sleep(step_s)


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("usage: python goober.py text folder...")
        exit(1)

    def scan_callback(data):
        print(f"[PY] {data}")

    def find_callback(data, links):
        text, label = data
        print(f"[PY] Callback for '{label}': Found {len(links)} symbols in text \"{text}\"")
        for res in links:
            matched_symbol = text[res.start_offset_in_text:res.end_offset_in_text]
            print(f"  '{matched_symbol}' -> {res.source_file}:{res.line_0_based}:{res.column_0_based}")

    for folder in sys.argv[2:]:
        path = Path(folder)
        if path.is_dir():
            for file in path.rglob("*.py"):
                scan_file(file, Language.PYTHON, scan_callback, file)
        else:
            scan_file(path, Language.PYTHON, scan_callback, path)

    text = sys.argv[1]
    find_symbols_in_text(text, find_callback, data=(text, "before"))

    print("[PY] WAIT, WAIT, WAIT!")
    wait_for_callbacks_in_seconds(20)

    find_symbols_in_text(text, find_callback, data=(text, "after"))

    wait_for_callbacks_in_seconds(1)

    stop()
