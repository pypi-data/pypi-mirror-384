import asyncio

# Adapted from https://discuss.python.org/t/boundedtaskgroup-to-control-parallelism/27171

class BoundedTaskGroup(asyncio.TaskGroup):
    def __init__(self, *args, max_concurrency = 0, **kwargs):
        super().__init__(*args)
        if max_concurrency:
            self._sem = asyncio.Semaphore(max_concurrency)
        else:
            self._sem = None
    
    def create_task(self, coro, *args, **kwargs):
        if self._sem:
            async def _wrapped_coro(sem, coro):
                async with sem:
                    return await coro
            coro = _wrapped_coro(self._sem, coro)

        return super().create_task(coro, *args, **kwargs)