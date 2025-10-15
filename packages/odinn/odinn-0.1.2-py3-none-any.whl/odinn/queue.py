import struct
from contextlib import suppress
from pathlib import Path

import lmdb
from rocksdict import Options, Rdict


class RocksDiskQueue:
    def __init__(self, path: str = "./rocks_disk_queue", format_size: str = ">Q"):
        self.format_size: str = format_size
        self.path: str = str(path)
        self.db = Rdict(path=self.path, options=Options(raw_mode=True))
        self.tail_idx: int = self.load_counter(b"tail_idx") or 0
        self.head_idx: int = self.load_counter(b"head_idx") or 0

    def load_counter(self, key: bytes) -> int:
        value = self.db.get(key)
        return struct.unpack(self.format_size, value)[0] if value else None

    def save_counter(self, key: bytes, value: int):
        self.db.put(key, struct.pack(self.format_size, value))

    def enqueue(self, value: bytes):
        key = struct.pack(self.format_size, self.tail_idx)
        self.db.put(key, value)
        self.tail_idx += 1
        self.save_counter(b"tail_idx", self.tail_idx)

    def dequeue(self) -> bytes | None:
        if self.is_empty():
            return None

        key = struct.pack(self.format_size, self.head_idx)
        value = self.db.get(key)
        if value is not None:
            self.db.delete(key)
            self.head_idx += 1
            self.save_counter(b"head_idx", self.head_idx)
        return value

    def size(self) -> int:
        return self.tail_idx - self.head_idx

    def peek(self) -> bytes | None:
        if self.is_empty():
            return None
        key = struct.pack(self.format_size, self.head_idx)
        return self.db.get(key)

    def is_empty(self) -> bool:
        return self.head_idx >= self.tail_idx

    def close(self) -> None:
        self.db.close()

    def destroy(self) -> None:
        Rdict.destroy(self.path)


class LMDBDiskQueue:
    def __init__(self, path: str = "./lmdb_disk_queue", format_size: str = ">Q"):
        self.format_size: str = format_size
        self.path: str = str(path)
        self.db = lmdb.open(path=self.path, map_size=100 * 1024 * 1024)
        self.tail_idx: int = self.load_counter(b"tail_idx") or 0
        self.head_idx: int = self.load_counter(b"head_idx") or 0

    def load_counter(self, key: bytes) -> int:
        with self.db.begin() as txn:
            value = txn.get(key)
            return struct.unpack(self.format_size, value)[0] if value else None

    def save_counter(self, txn, key: bytes, value: int):
        txn.put(key, struct.pack(self.format_size, value))

    def enqueue(self, value: bytes):
        with self.db.begin(write=True) as txn:
            key = struct.pack(self.format_size, self.tail_idx)
            txn.put(key, value)
            self.tail_idx += 1
            self.save_counter(txn, b"tail_idx", self.tail_idx)

    def dequeue(self) -> bytes | None:
        with self.db.begin(write=True) as txn:
            key = struct.pack(self.format_size, self.head_idx)
            value = txn.get(key)
            if value is None:
                return None
            txn.delete(key)
            self.head_idx += 1
            self.save_counter(txn, b"head_idx", self.head_idx)
            return value

    def size(self) -> int:
        return self.tail_idx - self.head_idx

    def peek(self) -> bytes | None:
        with self.db.begin() as txn:
            key = struct.pack(self.format_size, self.head_idx)
            return txn.get(key)

    def is_empty(self) -> bool:
        return self.head_idx >= self.tail_idx

    def close(self) -> None:
        self.db.close()

    def destroy(self) -> None:
        for mdb in Path(self.path).glob("*.mdb"):
            mdb.unlink()
        with suppress(OSError):
            Path(self.path).rmdir()
