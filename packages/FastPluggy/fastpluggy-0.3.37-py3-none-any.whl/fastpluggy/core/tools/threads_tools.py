import threading

from loguru import logger
import sys
import threading
import ctypes


def set_os_thread_name(name: str) -> bool:
    """
    Set the OS-level name of the *current* thread.

    Returns True on success, False if unsupported or on failure.

    Limits:
      - Linux: 16 bytes total (15 visible + NUL). Truncated to 15 bytes.
      - macOS: 64 bytes (implementation-dependent). Truncated to 63 bytes.
      - Windows: No small fixed limit (UTF-16), but viewers may truncate.
    """
    try:
        if sys.platform == "win32":
            # Windows 10 RS2+ (Server 2016+) supports SetThreadDescription
            kernel32 = ctypes.windll.kernel32
            GetCurrentThread = kernel32.GetCurrentThread
            GetCurrentThread.restype = ctypes.c_void_p  # HANDLE

            SetThreadDescription = kernel32.SetThreadDescription
            # HRESULT SetThreadDescription(HANDLE, PCWSTR)
            SetThreadDescription.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
            SetThreadDescription.restype = ctypes.c_long  # HRESULT

            hthread = GetCurrentThread()
            hr = SetThreadDescription(hthread, name)
            return hr >= 0  # SUCCEEDED(hr)

        elif sys.platform.startswith("darwin"):
            # macOS: only sets the *current* thread name
            libc = ctypes.cdll.LoadLibrary("libc.dylib")
            pthread_setname_np = libc.pthread_setname_np
            pthread_setname_np.argtypes = [ctypes.c_char_p]
            pthread_setname_np.restype = ctypes.c_int

            # macOS typically allows up to 64 incl NUL → truncate to 63 bytes
            bname = name.encode("utf-8")[:63]
            return pthread_setname_np(bname) == 0

        elif sys.platform.startswith("linux"):
            # Linux: prctl(PR_SET_NAME, name) sets *current* thread name
            libc = ctypes.cdll.LoadLibrary("libc.so.6")
            prctl = libc.prctl
            prctl.argtypes = [ctypes.c_int, ctypes.c_char_p,
                              ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
            prctl.restype = ctypes.c_int

            PR_SET_NAME = 15
            # Linux limit: 16 bytes incl NUL → truncate to 15 bytes
            bname = name.encode("utf-8")[:15]
            return prctl(PR_SET_NAME, bname, 0, 0, 0) == 0

        else:
            # Unsupported OS: fall back to Python-level name and report False
            threading.current_thread().name = name
            return False
    except Exception:
        # Be robust: never crash worker threads because of naming
        return False

def get_tid():
    """Get the current thread's OS-level thread ID (TID)."""

    thread_info = threading.current_thread()
    logger.info(f"thread_info: {thread_info} ")

    if hasattr(threading, "get_native_id"):
        return threading.get_native_id()


def get_py_ident():
    """Get the current python ident of thread."""

    if hasattr(threading, "get_ident"):
        return threading.get_ident()


def is_thread_alive(native_id):
    for thread in threading.enumerate():
        if thread.native_id == native_id:
            return thread.is_alive()
    return False


def is_thread_alive_by_ident(ident):
    for thread in threading.enumerate():
        if thread.ident == ident:
            return thread.is_alive()
    return False
