# -*- encoding: UTF-8 -*-


from typing import List


def ToChunks(data: bytes or memoryview, chunk_size: int, use_memoryview: bool = True) -> List[bytes or memoryview]:
    q, r = divmod(len(data), chunk_size)
    chunks = list(None for _ in range(q + (1 if (r > 0) else (0))))

    for i in range(0, len(data), chunk_size):
        if use_memoryview:
            chunks[i // chunk_size] = memoryview(data)[i:i + chunk_size]
        else:
            chunks[i // chunk_size] = data[i:i + chunk_size]

    return chunks
