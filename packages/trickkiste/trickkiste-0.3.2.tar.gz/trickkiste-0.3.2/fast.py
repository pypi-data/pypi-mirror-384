#!/usr/bin/env -S uv run --script --python 3.14t
# /// script
# requires-python = ">=3.10.4,<4"
# dependencies = ["rich", "trickkiste", "checkmk-dev-tools>=1.0.0"]
# [tool.uv]
# # sources = {checkmk-dev-tools={path="../../checkmk_dev_tools", editable=true}}
# ///

import asyncio
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

class Numbercruncher:
    def __init__(self, threads) -> None:
        self._executor = ThreadPoolExecutor(max_workers=threads)

    def __call__(self, fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor, lambda: fn(*args, **kwargs)
            )

        return wrapper

numbercruncher = Numbercruncher(int(sys.argv[1]))

def slow_fib(n):
    return n if n <= 1 else slow_fib(n - 1) + slow_fib(n - 2)

@numbercruncher
def crunch(n):
    return slow_fib(n)

async def main() -> None:
    t = time.time()
    await asyncio.gather(*(crunch(34) for _ in range(40)))
    dur = time.time() - t
    print(f"{'.'.join(map(str, sys.version_info))} {int(sys.argv[1]):>2}"
          f" {dur * 1000:.2f} {'X' * int(dur*5)}")

asyncio.run(main())