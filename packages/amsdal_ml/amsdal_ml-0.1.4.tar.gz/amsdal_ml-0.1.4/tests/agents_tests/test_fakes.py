from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.mcp_client.base import ToolClient
from amsdal_ml.mcp_client.base import ToolInfo
from amsdal_ml.ml_models.models import MLModel

# ---- Fake LLM model ----

def _chunk_cycle(text: str) -> list[str]:
    sizes = [3, 4, 5]
    res: list[str] = []
    pos, i, n = 0, 0, len(text)
    while pos < n:
        sz = sizes[i % len(sizes)]
        res.append(text[pos : pos + sz])
        pos += sz
        i += 1
    return res


class FakeModel(MLModel):
    def __init__(self, *, async_mode: bool, scripted: list[str]):
        self.async_mode = async_mode
        self._scripted = list(scripted)

    def setup(self) -> None:  # pragma: no cover
        ...

    def teardown(self) -> None:  # pragma: no cover
        ...

    def invoke(
        self,
        _prompt: str,
        *,
        attachments: Optional[Iterable[FileAttachment]] = None,
    ) -> str:
        _ = attachments  # silence unused
        if self.async_mode:
            msg = "async_mode=True, use ainvoke()"
            raise RuntimeError(msg)
        return self._scripted.pop(0)

    async def ainvoke(
        self,
        _prompt: str,
        *,
        attachments: Optional[Iterable[FileAttachment]] = None,
    ) -> str:
        _ = attachments  # silence unused
        if not self.async_mode:
            msg = "async_mode=False, use invoke()"
            raise RuntimeError(msg)
        await asyncio.sleep(0)
        return self._scripted.pop(0)

    def stream(
        self,
        _prompt: str,
        *,
        attachments: Optional[Iterable[FileAttachment]] = None,
    ) -> Iterator[str]:
        _ = attachments  # silence unused
        if self.async_mode:
            msg = "async_mode=True, use astream()"
            raise RuntimeError(msg)
        if not self._scripted:
            return
        text = self._scripted.pop(0)
        yield from _chunk_cycle(text)

    async def astream(
        self,
        _prompt: str,
        *,
        attachments: Optional[Iterable[FileAttachment]] = None,
    ) -> AsyncIterator[str]:
        _ = attachments  # silence unused
        if not self.async_mode:
            msg = "async_mode=False, use stream()"
            raise RuntimeError(msg)

        if not self._scripted:
            return

        text = self._scripted.pop(0)
        for chunk in _chunk_cycle(text):
            await asyncio.sleep(0)
            yield chunk

# ---- Fake tool schema + tool ----
class _FakeRetrieverArgs(BaseModel):
    query: str = Field(..., description="User search query for semantic similarity retrieval")
    k: int = Field(ge=1, default=3)
    include_tags: list[str] = Field(default_factory=list)
    exclude_tags: list[str] = Field(default_factory=list)


class _ToolResult(BaseModel):
    name: str
    content: Any
    meta: dict[str, Any] = {}


class FakeRetrieverTool:
    """
    Duck-typed MCP tool:
      - name
      - function_spec()
      - call()/acall() -> obj from .content
    """
    name = "retriever.search"
    description = "Search by semantic similarity"
    args_schema = _FakeRetrieverArgs

    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def function_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
            "return_direct": False,
        }

    def call(self, **kwargs: Any) -> _ToolResult:
        args = self.args_schema.model_validate(kwargs).model_dump()
        self.calls.append(args.copy())
        return _ToolResult(name=self.name, content=[{"text": "chunk-A"}], meta={"k": args.get("k")})

    async def acall(self, **kwargs: Any) -> _ToolResult:
        return self.call(**kwargs)


class FakeToolClient(ToolClient):
    def __init__(self, tool: FakeRetrieverTool | None = None, alias: str = "retriever"):
        self._tool = tool or FakeRetrieverTool()
        self.alias: str = alias  # writeable attribute to match base

    async def list_tools(self) -> list[ToolInfo]:
        return [
            ToolInfo(
                alias=self.alias,
                name="search",
                description=self._tool.description,
                input_schema=self._tool.function_spec().get("parameters", {}),
            )
        ]

    async def call(self, _tool_name: str, args: dict[str, Any], *, timeout: float | None = None):
        _unused_timeout = timeout
        return await self._tool.acall(**args)


# ---- Helpers for ReAct markup ----
def tool_call(action: str, arg_json: str = '{"query":"q"}') -> str:
    return f"Thought: Do I need to use a tool? Yes\nAction: {action}\nAction Input: {arg_json}\n"


def final_answer(text: str) -> str:
    return f"Thought: Do I need to use a tool? No\nFinal Answer: {text}\n"
