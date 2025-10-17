import os
import sys

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class LockFile:
    def __init__(self, path):
        self.path = path
        self.file = None

    def acquire(self):
        self.file = open(self.path, "w")

        try:
            if sys.platform == "win32":
                # Windows locking
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Unix locking
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID for debugging
            self.file.seek(0)
            self.file.write(str(os.getpid()))
            self.file.flush()
            return True
        except (OSError, BlockingIOError):
            self.file.close()
            self.file = None
            return False

    def release(self):
        if not self.file:
            return
        if sys.platform == "win32":
            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()
        os.remove(self.path)


# # Usage
# lock = LockFile("/tmp/myapp.lock")
#
# if not lock.acquire():
#     print("Another instance is already running!")
#     sys.exit(1)
#
# print("Lock acquired, running...")
# import time
# time.sleep(5)
# lock.release()
# print("Lock released")
