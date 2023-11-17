from typing import List, Optional, Any, Set


class BaseProcessor:
    NAME: str = ''

    async def process(self, state: Any):
        raise NotImplementedError

    async def __call__(self, state: Any):
        return await self.process(state)


class Executor:
    processors: List[BaseProcessor] = []

    def __init__(self, processors: Optional[List[BaseProcessor]] = None):
        self.processors.extend(processors or [])

    async def __call__(self, text: str) -> List[Optional[str]]:
        return await self.run(text)

    async def run(self, state: Any) -> Any:
        for process in self.processors:
            state = await process(state)
            if state is None:
                return None
        return state


class StopWordProcessor(BaseProcessor):
    NAME = 'stop word processor'

    def __init__(self, stopwords: Set[str]):
        self.stopwords = stopwords or set()

    async def process(self, state: str) -> Optional[str]:
        if state and not any(map(lambda w: w.lower() in state.lower(), self.stopwords)):
            return state


class ReplyGuard(Executor):
    processors = [
        StopWordProcessor({
            'fake', 'f4ke',
            'fuck', 'f4ck',
            'invalid', 'wrong',
            'ban', 'report',
            'blad', 'syka', 'suka',
        })
    ]


guard = ReplyGuard()

if __name__ == '__main__':
    import asyncio

    assert asyncio.run(guard.run('ABCDABCD is fake')) is None, 'stop word not intercepted'
    assert asyncio.run(guard.run('ABCDABCD suka blad')) is None, 'stop word not intercepted'
