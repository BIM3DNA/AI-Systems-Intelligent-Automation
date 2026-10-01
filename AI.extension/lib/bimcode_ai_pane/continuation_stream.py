"""Bounded .NET pipe drain for final-explanation transport only."""
import threading


class Drain(object):
    def __init__(self, stream, limit):
        self.stream, self.limit = stream, limit
        self.done = threading.Event()
        self.text = ""
        self.overflow = False
        self.failed = False
        thread = threading.Thread(target=self._read)
        thread.daemon = True
        thread.start()

    def _read(self):
        from System import Array, Char
        chunks, count = [], 0
        try:
            buffer = Array.CreateInstance(Char, 4096)
            while True:
                size = self.stream.Read(buffer, 0, len(buffer))
                if not size:
                    break
                take = min(size, max(0, self.limit - count))
                if take:
                    chunks.append(u"".join(buffer[:take]))
                count = min(self.limit + 1, count + size)
                self.overflow = count > self.limit
                # Continue draining/discarding excess; bounded memory, no pipe deadlock.
            self.text = u"".join(chunks)
        except Exception:
            self.failed = True
        finally:
            self.done.set()

    def Wait(self, milliseconds):
        self.done.wait(milliseconds / 1000.0)
        return self.done.is_set() and not self.failed

    @property
    def Result(self):
        return self.text + (" " if self.overflow and self.limit else "")
