from odinn.queue import LMDBDiskQueue, RocksDiskQueue

rocksq = RocksDiskQueue()
rocksq.enqueue(b"first")
rocksq.enqueue(b"second")
print(rocksq.size())
print(rocksq.peek())
print(rocksq.dequeue())
print(rocksq.dequeue())
print(rocksq.dequeue())
print(rocksq.is_empty())
for k, v in rocksq.db.items():
    print(f"{k} -> {v}")
rocksq.close()
rocksq.destroy()

lmdbq = LMDBDiskQueue()
lmdbq.enqueue(b"first")
lmdbq.enqueue(b"second")
print(lmdbq.size())
print(lmdbq.peek())
print(lmdbq.dequeue())
print(lmdbq.dequeue())
print(lmdbq.dequeue())
print(lmdbq.is_empty())
with lmdbq.db.begin() as txn:
    for k, v in txn.cursor():
        print(f"{k} -> {v}")
lmdbq.close()
lmdbq.destroy()
