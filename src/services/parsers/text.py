import re
from typing import Optional, List, Set, Any, Dict


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


class PartsReplaceProcessor(BaseProcessor):
    parts: Dict[str, str] = {}

    def __init__(self, fragments: Optional[Dict[str, str]] = None):
        self.parts.update(fragments or {})

    async def process(self, state: Optional[str] = None) -> Optional[str]:
        if state is None:
            return None

        for k, v in self.parts.items():
            state = state.replace(k, v)
        return state


class ReplaceEmojiProcessor(PartsReplaceProcessor):
    num_emojis = {
        '0️⃣': '0',
        '1️⃣': '1',
        '2️⃣': '2',
        '3️⃣': '3',
        '4️⃣': '4',
        '5️⃣': '5',
        '6️⃣': '6',
        '7️⃣': '7',
        '8️⃣': '8',
        '9️⃣': '9',
        '🔟': '10',
    }
    char_emojis = {
        '🅰️': 'A',
        '🅱️': 'B',
        '🆎': 'AB'
    }

    parts = {**num_emojis, **char_emojis}


class RemoveEmojiProcessor(BaseProcessor):
    def __init__(self):
        self.emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # chinese char
            u"\U00002702-\U000027B0"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # dingbats
            u"\u3030"
            "]+", flags=re.UNICODE
        )

    async def process(self, state: Optional[str] = None):
        if state is None:
            return None
        return self.emoji_pattern.sub(r'', state)


class CryptoboxProcessor(BaseProcessor):
    async def process(self, state: Optional[str] = None) -> Optional[List[str]]:
        if state is None:
            return None

        matched = []
        for chunk in state.split():
            if re.match(r'^[A-Z0-9]{8}$', chunk) and all([
                any([i.isdigit() for i in chunk]),
                any([i.isalpha() for i in chunk])
            ]):
                matched.append(chunk)

        return matched


class CryptoboxParser(Executor):
    processors = [
        StopWordProcessor({
            'fake', 'f4ke',
            'fuck', 'f4ck',
            'invalid', 'wrong',
            'ban', 'report',
            'blad', 'syka', 'suka',
            'bttc', 'bnb', 'btc', 'usdt'
        }),
        ReplaceEmojiProcessor(),
        RemoveEmojiProcessor(),
        CryptoboxProcessor()
    ]


cryptobox_parser = CryptoboxParser()

if __name__ == '__main__':
    import asyncio


    async def main():
        assert await RemoveEmojiProcessor()('😎😏😒😞😔') == '', 'emoji not removed'
        assert await ReplaceEmojiProcessor()('🅰️BC1️⃣') == 'ABC1', 'char emoji not replaced'

        assert await cryptobox_parser('my code AABBCCD1') == ['AABBCCD1']
        assert await cryptobox_parser('my next codes 00BBCCD1 000011AA') == ['00BBCCD1', '000011AA']
        assert await cryptobox_parser('AABBCCD1 fake') == None
        assert await cryptobox_parser('5000BTTC') == None


    asyncio.run(main())
