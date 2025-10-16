import threading, asyncio
from concurrent.futures import Future
from typing import Any, Coroutine


class LoopRunner:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="maniac-loop"
        )
        self._thread.start()

    def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        fut: Future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result()

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
