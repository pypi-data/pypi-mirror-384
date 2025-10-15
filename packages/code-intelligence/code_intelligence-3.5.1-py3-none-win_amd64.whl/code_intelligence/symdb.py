import os
import ctypes
import platform
from enum import IntEnum, IntFlag
from pathlib import Path
from dataclasses import dataclass, field


class Language(IntEnum):
    # UNKNOWN = 0
    PYTHON = 1
    JAVASCRIPT = 2  # Not implemented yet - enum exists but no parser
    TYPESCRIPT = 3  # Not implemented yet - enum exists but no parser
    CPP = 4
    C = 5
    JAVA = 6        # Not implemented yet - enum exists but no parser
    RUST = 7
    GO = 8
    PHP = 9


class SymbolType(IntEnum):
    UNKNOWN = 0
    CLASS = 1
    FUNCTION = 2
    METHOD = 3
    VARIABLE = 4
    MODULE = 5
    IMPORT = 6
    FROM_IMPORT = 7


class SymbolFilter(IntFlag):
    """Symbol filter flags for find_symbols_in_text (bitwise combinable)"""
    NONE = 0
    CLASSES = 1 << 0
    FUNCTIONS = 1 << 1
    OTHER = 1 << 2
    ALL = CLASSES | FUNCTIONS | OTHER

Path_Like = str | Path

@dataclass(slots=True)
class Location:
    """Source code span."""
    path: str = ""
    line: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0

    def __repr__(self) -> str:
        return f"Location({self.path}:{self.line}:{self.column})"

@dataclass(slots=True)
class Symbol:
    """Language-agnostic symbol record."""
    name: str = ""
    symbol_type: SymbolType = SymbolType.UNKNOWN
    definition: Location = field(default_factory=Location)
    parent: str | None = None
    signature: str | None = None
    documentation: str | None = None

    def __repr__(self) -> str:
        return f"Symbol({self.name}, {self.symbol_type.name}, {self.definition})"

    # Convenience properties for backward compatibility with TASK.md API
    @property
    def filename(self) -> str:
        return self.definition.path

    @property
    def line(self) -> int:
        return self.definition.line

    @property
    def column(self) -> int:
        return self.definition.column

    # Keep location as alias for backward compatibility
    @property
    def location(self) -> "Location":
        return self.definition

@dataclass(slots=True)
class SymbolLink:
    """A clickable link to a symbol in text."""
    start_offset_in_text: int = 0
    end_offset_in_text: int = 0
    symbol: Symbol = field(default_factory=Symbol)

    def __repr__(self) -> str:
        return f"SymbolLink({self.start_offset_in_text}-{self.end_offset_in_text}, {self.symbol.name})"

# --- Private ctypes Implementation ---

class _Location(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("line", ctypes.c_uint32),
        ("column", ctypes.c_uint32),
        ("end_line", ctypes.c_uint32),
        ("end_column", ctypes.c_uint32),
    ]

class _Symbol(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("symbol_type", ctypes.c_uint8),
        ("definition", _Location),
        ("parent", ctypes.c_char_p),
        ("signature", ctypes.c_char_p),
        ("documentation", ctypes.c_char_p),
        ("_is_stub", ctypes.c_bool),
        ("_target_module", ctypes.c_char_p),
    ]

class _SymbolLink(ctypes.Structure):
    _fields_ = [
        ("start_offset_in_text", ctypes.c_int),
        ("end_offset_in_text", ctypes.c_int),
        ("symbol", _Symbol),
    ]


class _PerfStat(ctypes.Structure):
    _fields_ = [
        ("language", ctypes.c_uint8),
        ("files", ctypes.c_uint64),
        ("symbols", ctypes.c_uint64),
        ("bytes_read", ctypes.c_uint64),
        ("read_ns", ctypes.c_uint64),
        ("parse_ns", ctypes.c_uint64),
        ("extract_ns", ctypes.c_uint64),
        ("alloc_read_inc_bytes", ctypes.c_uint64),
        ("alloc_parse_inc_bytes", ctypes.c_uint64),
        ("alloc_extract_inc_bytes", ctypes.c_uint64),
        ("rss_max_bytes", ctypes.c_uint64),
        ("nodes_visited", ctypes.c_uint64),
    ]


# Worker thread result structures - must match C ci_result_t exactly
class _SuccessSymbols(ctypes.Structure):
    _fields_ = [("symbols", ctypes.POINTER(_Symbol)), ("count", ctypes.c_uint32)]

class _SuccessLinks(ctypes.Structure):
    _fields_ = [("links", ctypes.POINTER(_SymbolLink)), ("count", ctypes.c_uint32)]

class _SuccessSymbol(ctypes.Structure):
    _fields_ = [("symbol", _Symbol)]

class _SuccessJson(ctypes.Structure):
    _fields_ = [("json", ctypes.c_char_p)]

class _SuccessBool(ctypes.Structure):
    _fields_ = [("success", ctypes.c_bool)]

class _Error(ctypes.Structure):
    _fields_ = [("message", ctypes.c_char_p)]

class _ResultUnion(ctypes.Union):
    _fields_ = [
        ("success_symbols", _SuccessSymbols),
        ("success_links", _SuccessLinks),
        ("success_symbol", _SuccessSymbol),
        ("success_json", _SuccessJson),
        ("success_bool", _SuccessBool),
        ("error", _Error),
    ]

class _Result(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint64),                    # request ID
        ("type", ctypes.c_uint8),                   # ci_result_type_t (RES_SUCCESS=0, RES_ERROR=1)
        ("union_data", _ResultUnion),
    ]


# Request type enum (must match C code)
class RequestType(IntEnum):
    SCAN_FILE = 1
    REMOVE_FILE = 2
    UPDATE_FILE = 3
    FIND_DEFINITIONS = 4
    FIND_REFERENCES = 5
    GET_SYMBOL = 6
    GET_ALL_SYMBOLS = 7
    GET_FILE_SYMBOLS = 8
    FIND_SYMBOLS_IN_TEXT = 9
    EXPORT_JSON = 10
    SHUTDOWN = 11


CURRENT_OS = platform.system().lower()

if CURRENT_OS == "darwin":
    LIB_EXT = ".dylib"
elif CURRENT_OS == "windows":
    LIB_EXT = ".dll"
else:
    LIB_EXT = ".so"

def _load_library(name: str):
    # Try module directory first (where nob.py now puts the library)
    lib_path = Path(__file__).parent / f"{name}{LIB_EXT}"
    if not lib_path.exists():
        # Fallback to build directory for backward compatibility
        lib_path = Path(__file__).parent.parent / "build" / f"{name}{LIB_EXT}"
        if not lib_path.exists():
            # Final fallback to project root
            lib_path = Path(__file__).parent.parent / f"{name}{LIB_EXT}"
            if not lib_path.exists():
                raise ImportError(
                    f"Cannot find compiled library at {lib_path}. Please build it first using 'python nob.py lib'."
                )

    lib = ctypes.CDLL(os.fsdecode(lib_path))
    return lib

_lib = _load_library("_code_intelligence")

# C function signatures (match code_intelligence.c)
_lib.symbol_db_create.argtypes = []
_lib.symbol_db_create.restype = ctypes.c_void_p

# Worker thread async API signatures
# Enqueue functions - return request ID
_lib.enqueue_scan_file.argtypes = [ctypes.c_char_p, ctypes.c_uint8]
_lib.enqueue_scan_file.restype = ctypes.c_uint64

_lib.enqueue_remove_file.argtypes = [ctypes.c_char_p]
_lib.enqueue_remove_file.restype = ctypes.c_uint64

_lib.enqueue_update_file.argtypes = [ctypes.c_char_p, ctypes.c_uint8]
_lib.enqueue_update_file.restype = ctypes.c_uint64

_lib.enqueue_find_definitions.argtypes = [ctypes.c_char_p]
_lib.enqueue_find_definitions.restype = ctypes.c_uint64

_lib.enqueue_find_references.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
_lib.enqueue_find_references.restype = ctypes.c_uint64

_lib.enqueue_get_symbol.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
_lib.enqueue_get_symbol.restype = ctypes.c_uint64

_lib.enqueue_get_all_symbols.argtypes = []
_lib.enqueue_get_all_symbols.restype = ctypes.c_uint64

_lib.enqueue_get_file_symbols.argtypes = [ctypes.c_char_p]
_lib.enqueue_get_file_symbols.restype = ctypes.c_uint64

_lib.enqueue_find_symbols_in_text.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
_lib.enqueue_find_symbols_in_text.restype = ctypes.c_uint64

_lib.enqueue_export_json.argtypes = []
_lib.enqueue_export_json.restype = ctypes.c_uint64

# Poll results function
_lib.poll_results.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
_lib.poll_results.restype = ctypes.c_void_p  # Returns ci_result_t*

# Free results array
_lib.result_array_free.argtypes = [ctypes.c_void_p]
_lib.result_array_free.restype = None

# Async API is mandatory in this build
_ASYNC_API_AVAILABLE = True

_lib.symbol_db_destroy.argtypes = [ctypes.c_void_p]
_lib.symbol_db_destroy.restype = None

_lib.symbol_db_set_project_root.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.symbol_db_set_project_root.restype = None

_lib.symbol_db_scan_file.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint8]
_lib.symbol_db_scan_file.restype = ctypes.c_bool

# Batch scan
_lib.symbol_db_scan_files.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint32, ctypes.c_uint8]
_lib.symbol_db_scan_files.restype = ctypes.c_bool

_lib.symbol_db_remove_file.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.symbol_db_remove_file.restype = ctypes.c_bool

# Update file (re-scan and replace)
_lib.symbol_db_update_file.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint8]
_lib.symbol_db_update_file.restype = ctypes.c_bool

# Arrays with out_count
_lib.symbol_db_find_definitions.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_find_definitions.restype = ctypes.POINTER(_Symbol)

_lib.symbol_db_find_references.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_find_references.restype = ctypes.POINTER(_Symbol)

_lib.symbol_db_get_all_symbols.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_get_all_symbols.restype = ctypes.POINTER(_Symbol)

_lib.symbol_db_get_file_symbols.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_get_file_symbols.restype = ctypes.POINTER(_Symbol)

# bool return + out _Symbol
_lib.symbol_db_get_symbol.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(_Symbol)]
_lib.symbol_db_get_symbol.restype = ctypes.c_bool

# Free for arrays (void*)
_lib.symbol_array_free.argtypes = [ctypes.c_void_p]
_lib.symbol_array_free.restype = None

_lib.ci_flush_coverage.argtypes = []
_lib.ci_flush_coverage.restype = None

_lib.symbol_db_clear.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.symbol_db_clear.restype = None

_lib.symbol_db_dump_stats.argtypes = [ctypes.c_void_p]
_lib.symbol_db_dump_stats.restype = None

_lib.symbol_db_get_stats.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PerfStat), ctypes.c_uint32]
_lib.symbol_db_get_stats.restype = ctypes.c_uint32

_lib.symbol_db_find_symbols_in_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_find_symbols_in_text.restype = ctypes.POINTER(_SymbolLink)

_lib.symbol_db_find_symbols_in_text_filtered.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
_lib.symbol_db_find_symbols_in_text_filtered.restype = ctypes.POINTER(_SymbolLink)

_lib.symbol_db_export_symbols_to_json.argtypes = [ctypes.c_void_p]
_lib.symbol_db_export_symbols_to_json.restype = ctypes.c_char_p

def _flush_coverage():
    try:
        _lib.ci_flush_coverage()
    except Exception:
        pass

# Helper conversions

class CStringView:
    """A view into a C string that delays decoding until needed."""
    __slots__ = ('_ptr', '_decoded')

    def __init__(self, c_char_p):
        self._ptr = c_char_p
        self._decoded = None

    def __str__(self):
        if self._decoded is None:
            if self._ptr:
                self._decoded = self._ptr.decode("utf-8", errors="replace")
            else:
                self._decoded = ""
        return self._decoded

    def __repr__(self):
        return f"CStringView({str(self)!r})"

    def __bool__(self):
        return bool(self._ptr)

    def __eq__(self, other):
        if isinstance(other, CStringView):
            return str(self) == str(other)
        elif isinstance(other, str):
            return str(self) == other
        return False


def _to_py_symbol_lazy(c_symbol: _Symbol) -> Symbol:
    """Convert C symbol to Python symbol with lazy string decoding."""
    definition = Location(
        path=str(CStringView(c_symbol.definition.path)),  # Decode immediately for file paths (needed for path operations)
        line=c_symbol.definition.line,
        column=c_symbol.definition.column,
        end_line=c_symbol.definition.end_line,
        end_column=c_symbol.definition.end_column,
    )
    return Symbol(
        name=str(CStringView(c_symbol.name)),  # Most accessed field, decode immediately
        symbol_type=SymbolType(c_symbol.symbol_type),
        definition=definition,
        parent=str(CStringView(c_symbol.parent)) if c_symbol.parent else None,
        signature=CStringView(c_symbol.signature) if c_symbol.signature else None,  # Keep as view
        documentation=CStringView(c_symbol.documentation) if c_symbol.documentation else None,  # Keep as view
    )


def _to_py_symbol(c_symbol: _Symbol) -> Symbol:
    definition = Location(
        path=c_symbol.definition.path.decode("utf-8", errors="replace") if c_symbol.definition.path else "",
        line=c_symbol.definition.line,
        column=c_symbol.definition.column,
        end_line=c_symbol.definition.end_line,
        end_column=c_symbol.definition.end_column,
    )
    return Symbol(
        name=c_symbol.name.decode("utf-8", errors="replace") if c_symbol.name else "",
        symbol_type=SymbolType(c_symbol.symbol_type),
        definition=definition,
        parent=c_symbol.parent.decode("utf-8", errors="replace") if c_symbol.parent else None,
        signature=c_symbol.signature.decode("utf-8", errors="replace") if c_symbol.signature else None,
        documentation=c_symbol.documentation.decode("utf-8", errors="replace") if c_symbol.documentation else None,
    )


class SymbolArrayView:
    """A view into a C symbol array that manages the C memory and provides lazy access."""

    def __init__(self, ptr: ctypes.POINTER(_Symbol), count: int):
        self._ptr = ptr
        self._count = count
        self._symbols = None  # Lazy converted symbols

    def __len__(self):
        return self._count

    def __getitem__(self, index):
        if isinstance(index, slice):
            # Handle slice objects
            start, stop, step = index.indices(self._count)
            return [self[i] for i in range(start, stop, step)]

        if index < 0:
            index = self._count + index
        if index < 0 or index >= self._count:
            raise IndexError("Symbol array index out of range")

        # Lazy conversion - convert only accessed symbols
        if self._symbols is None:
            self._symbols = [None] * self._count

        if self._symbols[index] is None:
            self._symbols[index] = _to_py_symbol_lazy(self._ptr[index])

        return self._symbols[index]

    def __iter__(self):
        for i in range(self._count):
            yield self[i]

    def __del__(self):
        # Free the C array when Python object is garbage collected
        if hasattr(self, '_ptr') and self._ptr:
            _lib.symbol_array_free(self._ptr)
            self._ptr = None


def _convert_symbol_array(ptr: ctypes.POINTER(_Symbol), count: int) -> list[Symbol]:
    if not ptr or count <= 0:
        return []
    try:
        return [_to_py_symbol(ptr[i]) for i in range(count)]
    finally:
        # Free the shallow-copy array buffer
        _lib.symbol_array_free(ptr)


def _convert_symbol_array_lazy(ptr: ctypes.POINTER(_Symbol), count: int) -> SymbolArrayView:
    """Convert C symbol array to a lazy Python view without immediate copying."""
    if not ptr or count <= 0:
        if ptr:
            _lib.symbol_array_free(ptr)  # Free empty array
        return SymbolArrayView(None, 0)

    return SymbolArrayView(ptr, count)


def _to_py_symbol_link(c_link: _SymbolLink) -> SymbolLink:
    """Convert C symbol link to Python symbol link."""
    return SymbolLink(
        start_offset_in_text=c_link.start_offset_in_text,
        end_offset_in_text=c_link.end_offset_in_text,
        symbol=_to_py_symbol_lazy(c_link.symbol),
    )


def _convert_symbol_link_array(ptr: ctypes.POINTER(_SymbolLink), count: int) -> list[SymbolLink]:
    """Convert C symbol link array to Python list."""
    if not ptr or count <= 0:
        return []
    try:
        return [_to_py_symbol_link(ptr[i]) for i in range(count)]
    finally:
        # Free the array buffer
        _lib.symbol_array_free(ptr)


# --- Async API Result Handling ---

@dataclass
class AsyncResult:
    """Result from an async operation."""
    request_id: int
    success: bool
    error_message: str | None = None
    data: any = None  # Actual result data (symbols, boolean, etc.)


def _process_results(results_ptr: ctypes.c_void_p, count: int) -> list[AsyncResult]:
    """Process results from poll_results.

    IMPORTANT: All result payloads must become fully Python-owned before we free
    the C results array to avoid use-after-free. Eagerly copy symbols/arrays.
    """
    if not results_ptr or count <= 0:
        return []

    # Cast to a flat pointer to _Result entries
    results_array = ctypes.cast(results_ptr, ctypes.POINTER(_Result))
    processed_results = []

    for i in range(count):
        result = results_array[i]
        request_id = result.id
        result_type = result.type  # RES_SUCCESS=0, RES_ERROR=1
        
        success = (result_type == 0)  # RES_SUCCESS
        error_msg = None
        data = None
        
        if not success:  # RES_ERROR
            error_msg = result.union_data.error.message.decode("utf-8", errors="replace") if result.union_data.error.message else "Unknown error"
        else:
            # For now, assume all success results are boolean (scan/remove/update operations)
            # TODO: Implement proper request type tracking to handle different result types
            data = result.union_data.success_bool.success

        processed_results.append(AsyncResult(
            request_id=request_id,
            success=success,
            error_message=error_msg,
            data=data
        ))

    return processed_results



# --- Backend Implementations ---

class _BaseSymbolDatabase:
    """Base class for code intelligence operations (not for direct use)."""
    def __init__(self):
        self._handle = _lib.symbol_db_create()
        # Note: _handle may be NULL if creation fails, but all API functions
        # are designed to handle NULL gracefully by returning empty/stub results

    def __del__(self):
        if hasattr(self, "_handle") and self._handle:
            _lib.symbol_db_destroy(self._handle)
            self._handle = None

    def clear(self, *, reuse_memory: bool = True):
        """Reset the database state while keeping the same Python object.

        Frees the current native database state and reinitializes it. Any
        previously scanned files, symbols, and project root are discarded.

        Args:
            reuse_memory: If True (default), keep allocated arena memory for reuse.
                         If False, free all memory and start fresh.
        """
        _lib.symbol_db_clear(self._handle, ctypes.c_int(1 if reuse_memory else 0))

    def dump_stats(self):
        """If CI_PROFILE=1, print internal timing counters to stderr."""
        _lib.symbol_db_dump_stats(self._handle)

    def get_stats(self) -> list[dict]:
        """Return structured per-language profiling stats when built with CI_PROFILE=1.

        If profiling is disabled or CI_PROFILE env is not set, returns an empty list.
        """
        # Query count first
        count = _lib.symbol_db_get_stats(self._handle, None, 0)
        if count == 0:
            return []
        buf = (_PerfStat * count)()
        written = _lib.symbol_db_get_stats(self._handle, buf, ctypes.c_uint32(count))
        out: list[dict] = []
        for i in range(int(written)):
            s = buf[i]
            lang_id = int(s.language)
            lang_name = Language(lang_id).name if lang_id in Language._value2member_map_ else f"LANG_{lang_id}"
            out.append({
                "language": lang_name,
                "files": int(s.files),
                "symbols": int(s.symbols),
                "bytes_read": int(s.bytes_read),
                "read_ns": int(s.read_ns),
                "parse_ns": int(s.parse_ns),
                "extract_ns": int(s.extract_ns),
                "alloc_read_inc_bytes": int(s.alloc_read_inc_bytes),
                "alloc_parse_inc_bytes": int(s.alloc_parse_inc_bytes),
                "alloc_extract_inc_bytes": int(s.alloc_extract_inc_bytes),
                "rss_max_bytes": int(s.rss_max_bytes),
                "nodes_visited": int(s.nodes_visited),
            })
        return out

    def set_project_root(self, path: Path_Like):
        _lib.symbol_db_set_project_root(self._handle, os.fsencode(path))

    def scan_file(self, path: Path_Like, language: Language) -> bool:
        return _lib.symbol_db_scan_file(
            self._handle,
            os.fsencode(path),
            int(language),
        )

    def scan_files(self, paths: list[Path_Like], language: Language) -> bool:
        arr = (ctypes.c_char_p * len(paths))()
        for i, p in enumerate(paths):
            arr[i] = os.fsencode(p)
        return _lib.symbol_db_scan_files(
            self._handle,
            arr,
            ctypes.c_uint32(len(paths)),
            int(language),
        )

    def init_project(self, files_by_language: dict[Language, list[Path_Like]]) -> bool:
        all_ok = True
        for lang, files in files_by_language.items():
            if not files:
                continue
            ok = self.scan_files(files, lang)
            if not ok:
                all_ok = False
        return all_ok

    def remove_file(self, path: Path_Like) -> bool:
        return _lib.symbol_db_remove_file(
            self._handle,
            os.fsencode(path),
        )

    def update_file(self, path: Path_Like, language: Language) -> bool:
        return _lib.symbol_db_update_file(
            self._handle,
            os.fsencode(path),
            int(language),
        )

    def get_symbol(self, path: Path_Like, line: int, column: int) -> Symbol | None:
        out = _Symbol()
        ok = _lib.symbol_db_get_symbol(
            self._handle,
            os.fsencode(path),
            ctypes.c_uint32(line),
            ctypes.c_uint32(column),
            ctypes.byref(out),
        )
        return _to_py_symbol(out) if ok else None

    def find_symbols_in_text(self, text: str, *, classes: bool = True, functions: bool = True, other: bool = True) -> list[SymbolLink]:
        """Find all symbol references in the given text and return clickable links.

        Args:
            text: Text to search for symbol references
            classes: Include class symbols (default: True)
            functions: Include function/method symbols (default: True)
            other: Include other symbol types (default: True)
        """
        # Build filter mask using enum constants
        filter_mask = SymbolFilter.NONE
        if classes:
            filter_mask |= SymbolFilter.CLASSES
        if functions:
            filter_mask |= SymbolFilter.FUNCTIONS
        if other:
            filter_mask |= SymbolFilter.OTHER

        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_find_symbols_in_text_filtered(
            self._handle,
            text.encode("utf-8"),
            ctypes.c_uint32(filter_mask),
            ctypes.byref(count),
        )
        return _convert_symbol_link_array(ptr, int(count.value))

    def export_symbols_to_json(self) -> str:
        """Export all symbols to JSON format grouped by type (classes, methods, functions).

        Returns:
            JSON string containing all symbols organized by type, or empty string if no symbols.
        """
        result = _lib.symbol_db_export_symbols_to_json(self._handle)
        if result:
            # Convert C string to Python string and free the C memory
            json_str = result.decode("utf-8", errors="replace")
            # Note: The C function returns malloc'd memory, but ctypes automatically
            # handles the memory management for c_char_p return types
            return json_str
        return "{}"


class ImmediateSymbolDatabase(_BaseSymbolDatabase):
    """Symbol database using copying (eager) backend."""
    def find_definitions(self, symbol_name: str) -> list[Symbol]:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_find_definitions(
            self._handle,
            symbol_name.encode("utf-8"),
            ctypes.byref(count),
        )
        return _convert_symbol_array(ptr, int(count.value))

    def find_symbols(self, symbol_name: str) -> list[Symbol]:
        return self.find_definitions(symbol_name)

    def find_references(self, path: Path_Like, line: int, column: int) -> list[Symbol]:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_find_references(
            self._handle,
            os.fsencode(path),
            ctypes.c_uint32(line),
            ctypes.c_uint32(column),
            ctypes.byref(count),
        )
        return _convert_symbol_array(ptr, int(count.value))

    def get_all_symbols(self) -> list[Symbol]:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_get_all_symbols(self._handle, ctypes.byref(count))
        return _convert_symbol_array(ptr, int(count.value))

    def get_file_symbols(self, path: Path_Like) -> list[Symbol]:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_get_file_symbols(
            self._handle,
            os.fsencode(path),
            ctypes.byref(count),
        )
        return _convert_symbol_array(ptr, int(count.value))


class LazySymbolDatabase(_BaseSymbolDatabase):
    """Symbol database using lazy backend."""
    def find_definitions(self, symbol_name: str) -> SymbolArrayView:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_find_definitions(
            self._handle,
            symbol_name.encode("utf-8"),
            ctypes.byref(count),
        )
        return _convert_symbol_array_lazy(ptr, int(count.value))

    def find_symbols(self, symbol_name: str) -> SymbolArrayView:
        return self.find_definitions(symbol_name)

    def find_references(self, path: Path_Like, line: int, column: int) -> SymbolArrayView:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_find_references(
            self._handle,
            os.fsencode(path),
            ctypes.c_uint32(line),
            ctypes.c_uint32(column),
            ctypes.byref(count),
        )
        return _convert_symbol_array_lazy(ptr, int(count.value))

    def get_all_symbols(self) -> SymbolArrayView:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_get_all_symbols(self._handle, ctypes.byref(count))
        return _convert_symbol_array_lazy(ptr, int(count.value))

    def get_file_symbols(self, path: Path_Like) -> SymbolArrayView:
        count = ctypes.c_uint32(0)
        ptr = _lib.symbol_db_get_file_symbols(
            self._handle,
            os.fsencode(path),
            ctypes.byref(count),
        )
        return _convert_symbol_array_lazy(ptr, int(count.value))


class AsyncSymbolDatabase:
    """Async symbol database using worker thread architecture."""

    def __init__(self):
        # Worker thread is initialized automatically when library loads
        self._pending_requests = {}  # request_id -> callback
        self._next_callback_id = 1

    def is_async_available(self) -> bool:
        """Check if async API is available."""
        return True

    def poll_results(self, timeout_ms: int = 0) -> list[AsyncResult]:
        """Poll for completed results from worker thread.

        Args:
            timeout_ms: Timeout in milliseconds (0 = non-blocking)

        Returns:
            List of completed AsyncResult objects
        """
        count = ctypes.c_uint32(0)
        results_ptr = _lib.poll_results(ctypes.byref(count))

        if not results_ptr or count.value == 0:
            return []

        try:
            return _process_results(results_ptr, count.value)
        finally:
            _lib.result_array_free(results_ptr)

    # Async API methods
    def async_scan_file(self, path: Path_Like, language: Language) -> int:
        """Asynchronously scan a file. Returns request ID."""
        return _lib.enqueue_scan_file(os.fsencode(path), int(language))

    def async_remove_file(self, path: Path_Like) -> int:
        """Asynchronously remove a file. Returns request ID."""
        return _lib.enqueue_remove_file(os.fsencode(path))

    def async_update_file(self, path: Path_Like, language: Language) -> int:
        """Asynchronously update a file. Returns request ID."""
        return _lib.enqueue_update_file(os.fsencode(path), int(language))

    def async_find_definitions(self, symbol_name: str) -> int:
        """Asynchronously find symbol definitions. Returns request ID."""
        return _lib.enqueue_find_definitions(symbol_name.encode("utf-8"))

    def async_find_references(self, filename: Path_Like, line: int, column: int) -> int:
        """Asynchronously find references for a symbol at filename:line:column. Returns request ID."""
        return _lib.enqueue_find_references(os.fsencode(filename), ctypes.c_uint32(line), ctypes.c_uint32(column))

    def async_get_symbol(self, path: Path_Like, line: int, column: int) -> int:
        """Asynchronously get symbol at position. Returns request ID."""
        return _lib.enqueue_get_symbol(os.fsencode(path), ctypes.c_uint32(line), ctypes.c_uint32(column))

    def async_get_all_symbols(self) -> int:
        """Asynchronously get all symbols. Returns request ID."""
        return _lib.enqueue_get_all_symbols()

    def async_get_file_symbols(self, path: Path_Like) -> int:
        """Asynchronously get symbols from a file. Returns request ID."""
        return _lib.enqueue_get_file_symbols(os.fsencode(path))

    def async_find_symbols_in_text(self, text: str, *, classes: bool = True, functions: bool = True, other: bool = True) -> int:
        """Asynchronously find symbols in text. Returns request ID."""
        # Build filter mask
        filter_mask = SymbolFilter.NONE
        if classes:
            filter_mask |= SymbolFilter.CLASSES
        if functions:
            filter_mask |= SymbolFilter.FUNCTIONS
        if other:
            filter_mask |= SymbolFilter.OTHER

        return _lib.enqueue_find_symbols_in_text(text.encode("utf-8"), ctypes.c_uint32(filter_mask))

    def async_export_json(self) -> int:
        """Asynchronously export symbols to JSON. Returns request ID."""
        return _lib.enqueue_export_json()

    # Convenience methods for blocking operations with polling

    def _wait_for_result(self, request_id: int, timeout_ms: int):
        """Wait for a specific request to complete."""
        import time
        start_time = time.time()

        while True:
            results = self.poll_results()
            for result in results:
                if result.request_id == request_id:
                    if result.success:
                        return result.data
                    else:
                        raise RuntimeError(f"Request {request_id} failed: {result.error_message}")

            # Check timeout
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms >= timeout_ms:
                raise TimeoutError(f"Request {request_id} timed out after {timeout_ms}ms")

            # Small sleep to avoid busy waiting
            time.sleep(0.001)  # 1ms

