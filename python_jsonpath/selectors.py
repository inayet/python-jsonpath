"""JSONPath selector objects, as returned from :meth:`Parser.parse`."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from collections.abc import Mapping
from collections.abc import Sequence

from typing import Any
from typing import AsyncIterable
from typing import Iterable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import TYPE_CHECKING
from typing import Union

from .match import JSONPathMatch

if TYPE_CHECKING:
    from .token import Token
    from .env import JSONPathEnvironment
    from .filter import BooleanExpression


class JSONPathSelector(ABC):
    """Base class for all JSONPath selectors."""

    __slots__ = ("env", "token")

    def __init__(self, *, env: JSONPathEnvironment, token: Token) -> None:
        self.env = env
        self.token = token

    @abstractmethod
    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        """Expand matches from previous JSONPath selectors in to new matches."""

    @abstractmethod
    def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        """An async version of :meth:`expand`."""


class PropertySelector(JSONPathSelector):
    """A JSONPath property."""

    __slots__ = ("name", "path")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        name: str,
    ) -> None:
        super().__init__(env=env, token=token)
        self.name = name
        self.path = str(self)

    def __str__(self) -> str:
        if self.env.re_key.fullmatch(self.name):
            return f".{self.name}"
        return f'["{self.name}"]'

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if not isinstance(match.obj, Mapping):
                continue
            try:
                yield JSONPathMatch(
                    path=match.path + self.path,
                    obj=self.env.getitem(match.obj, self.name),
                    root=match.root,
                )
            except KeyError:
                pass

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if not isinstance(match.obj, Mapping):
                continue
            try:
                yield JSONPathMatch(
                    path=match.path + self.path,
                    obj=await self.env.getitem_async(match.obj, self.name),
                    root=match.root,
                )
            except KeyError:
                pass


class IndexSelector(JSONPathSelector):
    """Dotted and bracketed sequence access by index."""

    __slots__ = ("index", "path", "_as_key")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        index: int,
    ) -> None:
        super().__init__(env=env, token=token)
        self.index = index
        self.path = str(self)
        self._as_key = str(self.index)

    def __str__(self) -> str:
        return f"[{self.index}]"

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if isinstance(match.obj, Mapping):
                # Try the string representation of the index as a key.
                try:
                    yield JSONPathMatch(
                        path=f'{match.path}["{self.index}"]',
                        obj=self.env.getitem(match.obj, self._as_key),
                        root=match.root,
                    )
                except KeyError:
                    pass
            elif isinstance(match.obj, Sequence):
                try:
                    yield JSONPathMatch(
                        path=match.path + self.path,
                        obj=self.env.getitem(match.obj, self.index),
                        root=match.root,
                    )
                except IndexError:
                    pass

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if isinstance(match.obj, Mapping):
                # Try the string representation of the index as a key.
                try:
                    yield JSONPathMatch(
                        path=f'{match.path}["{self.index}"]',
                        obj=await self.env.getitem_async(match.obj, self._as_key),
                        root=match.root,
                    )
                except KeyError:
                    pass
            elif isinstance(match.obj, Sequence):
                try:
                    yield JSONPathMatch(
                        path=match.path + self.path,
                        obj=await self.env.getitem_async(match.obj, self.index),
                        root=match.root,
                    )
                except IndexError:
                    pass


class SliceSelector(JSONPathSelector):
    """Sequence slicing selector."""

    __slots__ = ("slice",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        super().__init__(env=env, token=token)
        self.slice = slice(start, stop, step)

    def __str__(self) -> str:
        stop = self.slice.stop if self.slice.stop is not None else ""
        start = self.slice.start if self.slice.start is not None else ""
        step = self.slice.step if self.slice.step is not None else "1"
        return f"[{start}:{stop}:{step}]"

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if not isinstance(match.obj, Sequence):
                continue

            idx = self.slice.start or 0
            step = self.slice.step or 1
            for obj in self.env.getitem(match.obj, self.slice):
                yield JSONPathMatch(
                    path=f"{match.path}[{idx}]",
                    obj=obj,
                    root=match.root,
                )
                idx += step

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if not isinstance(match.obj, Sequence):
                continue

            idx = self.slice.start or 0
            step = self.slice.step or 1
            for obj in await self.env.getitem_async(match.obj, self.slice):
                yield JSONPathMatch(
                    path=f"{match.path}[{idx}]",
                    obj=obj,
                    root=match.root,
                )
                idx += step


class WildSelector(JSONPathSelector):
    """Wildcard expansion selector."""

    def __str__(self) -> str:
        return ".*"

    def _path(self, key: object) -> str:
        """Return a string representation of an object property key."""
        if not isinstance(key, str):
            key = str(key)

        if self.env.re_key.match(key):
            return f".{key}"
        return f'["{key}"]'

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if isinstance(match.obj, str):
                continue
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    yield JSONPathMatch(
                        path=match.path + self._path(key),
                        obj=val,
                        root=match.root,
                    )
            elif isinstance(match.obj, Sequence):
                for i, val in enumerate(match.obj):
                    yield JSONPathMatch(
                        path=f"{match.path}[{i}]",
                        obj=val,
                        root=match.root,
                    )

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if isinstance(match.obj, Mapping):
                for key, val in match.obj.items():
                    yield JSONPathMatch(
                        path=match.path + self._path(key),
                        obj=val,
                        root=match.root,
                    )
            elif isinstance(match.obj, Sequence):
                for i, val in enumerate(match.obj):
                    yield JSONPathMatch(
                        path=f"{match.path}[{i}]",
                        obj=val,
                        root=match.root,
                    )


class RecursiveDescentSelector(JSONPathSelector):
    """A JSONPath selector that visits all objects recursively."""

    def __str__(self) -> str:
        return ".."

    def _path(self, key: object) -> str:
        """Return a string representation of an object property key."""
        if not isinstance(key, str):
            key = str(key)

        if self.env.re_key.match(key):
            return f".{key}"
        return f'["{key}"]'

    def _expand(self, match: JSONPathMatch) -> Iterable[JSONPathMatch]:
        if isinstance(match.obj, str):
            # strings are sequences too
            pass
        elif isinstance(match.obj, Mapping):
            for key, val in match.obj.items():
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _match = JSONPathMatch(
                        path=match.path + self._path(key),
                        obj=val,
                        root=match.root,
                    )
                    yield _match
                    yield from self._expand(_match)
        elif isinstance(match.obj, Sequence):
            for i, val in enumerate(match.obj):
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _match = JSONPathMatch(
                        path=f"{match.path}[{i}]",
                        obj=val,
                        root=match.root,
                    )
                    yield _match
                    yield from self._expand(_match)

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            yield match
            yield from self._expand(match)

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            yield match
            for _match in self._expand(match):
                yield _match


T = TypeVar("T")


async def _alist(it: List[T]) -> AsyncIterable[T]:
    for item in it:
        yield item


class ListSelector(JSONPathSelector):
    """A JSONPath selector representing a list of properties, slices or indices."""

    __slots__ = ("items",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        items: List[Union[SliceSelector, IndexSelector, PropertySelector]],
    ) -> None:
        super().__init__(env=env, token=token)
        self.items = items

    def __str__(self) -> str:
        buf: List[str] = []
        for item in self.items:
            if isinstance(item, SliceSelector):
                stop = item.slice.stop if item.slice.stop is not None else ""
                start = item.slice.start if item.slice.start is not None else ""
                step = item.slice.step if item.slice.step is not None else "1"
                buf.append(f"{start}:{stop}:{step}")
            elif isinstance(item, PropertySelector):
                buf.append(item.name)
            else:
                buf.append(str(item.index))
        return f"[{', '.join(buf)}]"

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        _matches = list(matches)
        for item in self.items:
            yield from item.resolve(_matches)

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        _matches = [m async for m in matches]
        for item in self.items:
            async for match in item.resolve_async(_alist(_matches)):
                yield match


class Filter(JSONPathSelector):
    """"""

    __slots__ = ("expression",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        expression: BooleanExpression,
    ) -> None:
        super().__init__(env=env, token=token)
        self.expression = expression

    def __str__(self) -> str:
        return f"[?({self.expression})]"

    def resolve(self, matches: Iterable[JSONPathMatch]) -> Iterable[JSONPathMatch]:
        for match in matches:
            if isinstance(match.obj, Mapping):
                context = FilterContext(
                    env=self.env, current=match.obj, root=match.root
                )
                if self.expression.evaluate(context):
                    yield match

            # TODO: consider strings
            elif isinstance(match.obj, Sequence):
                for i, obj in enumerate(match.obj):
                    context = FilterContext(env=self.env, current=obj, root=match.root)
                    if self.expression.evaluate(context):
                        yield JSONPathMatch(
                            path=f"{match.path}[{i}]",
                            obj=obj,
                            root=match.root,
                        )

    # pylint: disable=invalid-overridden-method
    async def resolve_async(
        self, matches: AsyncIterable[JSONPathMatch]
    ) -> AsyncIterable[JSONPathMatch]:
        async for match in matches:
            if isinstance(match.obj, Mapping):
                context = FilterContext(
                    env=self.env, current=match.obj, root=match.root
                )
                if await self.expression.evaluate_async(context):
                    yield match

            elif isinstance(match.obj, Sequence):
                for i, obj in enumerate(match.obj):
                    context = FilterContext(env=self.env, current=obj, root=match.root)
                    if await self.expression.evaluate_async(context):
                        yield JSONPathMatch(
                            path=f"{match.path}[{i}]",
                            obj=obj,
                            root=match.root,
                        )


class FilterContext:
    """"""

    __slots__ = ("current", "env", "root", "scope")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        current: object,
        root: Union[Sequence[Any], Mapping[str, Any]],
        scope: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.env = env
        self.current = current
        self.root = root
        self.scope = scope or {}
