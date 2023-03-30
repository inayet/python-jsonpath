import asyncio
from collections.abc import Mapping
from typing import Iterator
from typing import List

import jsonpath


class MockLazyMapping(Mapping[str, object]):
    def __init__(self, val: object):
        self.key = "bar"
        self.val = val
        self.call_count = 0
        self.await_count = 0

    def __len__(self) -> int:  # pragma: no cover
        return 1

    def __iter__(self) -> Iterator[str]:  # pragma: no cover
        return iter([self.key])

    def __getitem__(self, k: str) -> object:  # pragma: no cover
        self.call_count += 1
        if k == self.key:
            return self.val
        raise KeyError(k)

    async def __getitem_async__(self, k: str) -> object:
        self.await_count += 1
        if k == self.key:
            return self.val
        raise KeyError(k)  # pragma: no cover


def test_async_getitem() -> None:
    lazy_mapping = MockLazyMapping("thing")
    data = {"foo": lazy_mapping}

    async def coro() -> List[object]:
        return await jsonpath.findall_async("$.foo.bar", data)

    matches = asyncio.run(coro())

    assert len(matches) == 1
    assert matches[0] == "thing"
    assert lazy_mapping.call_count == 0
    assert lazy_mapping.await_count == 1
