from dataclasses import dataclass, field
import json
from typing import Generator
from fastapi import WebSocket


@dataclass
class ResponseAccumulator:
    total_num_chunks: int = 0
    chunks_received: list[str] = field(default_factory=list)

    def add_chunk(self, chunk: str):
        self.chunks_received.append(chunk)

    def is_complete(self) -> bool:
        return len(self.chunks_received) == self.total_num_chunks

    def get_full_data(self) -> str | None:
        if self.is_complete():
            return "".join(self.chunks_received)
        return None

async def send_large_text(websocket: WebSocket, message: str, id: int):

    def ceil_div(a: int, b: int):
        return (a + b - 1) // b

    def chunker(message: str, id: int) -> Generator[str, None, None]:
        total_length = len(message)
        # note arbitrary size for initial test
        CHUNK_SIZE = 1024 * 10
        num_chunks = ceil_div(total_length, CHUNK_SIZE)
        yield json.dumps({"id": id, "total_num_chunks": num_chunks})
        for i in range(0, total_length, CHUNK_SIZE):
            max_index = min(total_length, i + CHUNK_SIZE)
            yield json.dumps({"id": id, "chunk": message[i:max_index]})

    for chunk in chunker(message, id):
        await websocket.send_text(chunk)
