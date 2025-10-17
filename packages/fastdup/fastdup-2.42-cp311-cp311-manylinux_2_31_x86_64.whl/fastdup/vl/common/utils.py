

def iter_batches(data: list, batch_size: int=1, func=None):
    batch = []
    for row in data:
        val = func(row) if func else row
        batch.append(val)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch
