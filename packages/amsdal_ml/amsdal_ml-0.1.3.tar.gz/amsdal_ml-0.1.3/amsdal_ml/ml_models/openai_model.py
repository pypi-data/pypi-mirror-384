from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from collections.abc import Iterator
from typing import Any
from typing import Optional
from typing import cast

import openai
from openai import AsyncOpenAI
from openai import AsyncStream
from openai import OpenAI
from openai import Stream

from amsdal_ml.fileio.base_loader import FILE_ID
from amsdal_ml.fileio.base_loader import PLAIN_TEXT
from amsdal_ml.fileio.base_loader import FileAttachment
from amsdal_ml.ml_config import ml_config
from amsdal_ml.ml_models.models import MLModel
from amsdal_ml.ml_models.models import ModelAPIError
from amsdal_ml.ml_models.models import ModelConnectionError
from amsdal_ml.ml_models.models import ModelError
from amsdal_ml.ml_models.models import ModelRateLimitError


class OpenAIModel(MLModel):
    """OpenAI LLM wrapper using a single Responses API pathway for all modes."""

    def __init__(self) -> None:
        self.client: Optional[OpenAI | AsyncOpenAI] = None
        self.async_mode: bool = bool(ml_config.async_mode)
        self.model_name: str = ml_config.llm_model_name
        self.temperature: float = ml_config.llm_temperature
        self._api_key: Optional[str] = None

    # ---------- Public sync API ----------
    def invoke(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> str:
        if self.async_mode:
            msg = "Async mode is enabled. Use 'ainvoke' instead."
            raise RuntimeError(msg)
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        if self._has_file_ids(atts):
            input_content = self._build_input_content(prompt, atts)
            return self._call_responses(input_content)

        final_prompt = self._merge_plain_text(prompt, atts)
        return self._call_chat(final_prompt)

    def stream(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> Iterator[str]:
        if self.async_mode:
            msg = "Async mode is enabled. Use 'astream' instead."
            raise RuntimeError(msg)
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        if self._has_file_ids(atts):
            input_content = self._build_input_content(prompt, atts)
            for chunk in self._call_responses_stream(input_content):
                yield chunk
            return

        final_prompt = self._merge_plain_text(prompt, atts)
        for chunk in self._call_chat_stream(final_prompt):
            yield chunk

    # ---------- Public async API ----------
    async def ainvoke(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> str:
        if not self.async_mode:
            msg = "Async mode is disabled. Use 'invoke' instead."
            raise RuntimeError(msg)
        self._ensure_async_client()
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        if self._has_file_ids(atts):
            input_content = self._build_input_content(prompt, atts)
            return await self._acall_responses(input_content)

        final_prompt = self._merge_plain_text(prompt, atts)
        return await self._acall_chat(final_prompt)

    async def astream(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> AsyncIterator[str]:
        if not self.async_mode:
            msg = "Async mode is disabled. Use 'stream' instead."
            raise RuntimeError(msg)
        self._ensure_async_client()
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)

        atts = self._validate_attachments(attachments)
        if self._has_file_ids(atts):
            input_content = self._build_input_content(prompt, atts)
            async for chunk in self._acall_responses_stream(input_content):
                yield chunk
            return

        final_prompt = self._merge_plain_text(prompt, atts)
        async for chunk in self._acall_chat_stream(final_prompt):
            yield chunk

    # ---------- lifecycle ----------
    def setup(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or ml_config.resolved_openai_key
        if not api_key:
            msg = (
                "OPENAI_API_KEY is required. "
                "Set it via env or ml_config.api_keys.openai."
            )
            raise RuntimeError(msg)
        self._api_key = api_key

        try:
            if self.async_mode:
                # Only create async client if loop is running; otherwise defer.
                try:
                    asyncio.get_running_loop()
                    self._ensure_async_client()
                except RuntimeError:
                    self.client = None
            else:
                self.client = OpenAI(api_key=self._api_key)
        except Exception as e:  # pragma: no cover
            raise self._map_openai_error(e) from e

    def _ensure_async_client(self) -> None:
        if self.client is None:
            try:
                self.client = AsyncOpenAI(api_key=self._api_key)
            except Exception as e:  # pragma: no cover
                raise self._map_openai_error(e) from e

    def teardown(self) -> None:
        self.client = None

    def _require_sync_client(self) -> OpenAI:
        if not isinstance(self.client, OpenAI):
            msg = "Sync client is not initialized. Call setup() first."
            raise RuntimeError(msg)
        return self.client

    def _require_async_client(self) -> AsyncOpenAI:
        if not isinstance(self.client, AsyncOpenAI):
            msg = "Async client is not initialized. Call setup() first."
            raise RuntimeError(msg)
        return self.client

    # ---------- attachments ----------
    def supported_attachments(self) -> set[str]:
        # Universal kinds supported by this model
        return {PLAIN_TEXT, FILE_ID}

    def _validate_attachments(
        self, attachments: list[FileAttachment] | None
    ) -> list[FileAttachment]:
        atts = attachments or []
        kinds = {a.type for a in atts}
        unsupported = kinds - self.supported_attachments()
        if unsupported:
            msg = (
                f"{self.__class__.__name__} does not support attachments: "
                f"{', '.join(sorted(unsupported))}"
            )
            raise ModelAPIError(msg)

        foreign = [
            a for a in atts if a.type == FILE_ID and (a.metadata or {}).get("provider") != "openai"
        ]
        if foreign:
            provs = {(a.metadata or {}).get("provider", "unknown") for a in foreign}
            msg = (
                f"{self.__class__.__name__} only supports FILE_ID with provider='openai'. "
                f"Got providers: {', '.join(sorted(provs))}"
            )
            raise ModelAPIError(msg)

        return atts

    @staticmethod
    def _has_file_ids(atts: list[FileAttachment]) -> bool:
        return any(a.type == FILE_ID for a in atts)

    def _build_input_content(self, prompt: str, atts: list[FileAttachment]) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        for a in atts:
            if a.type == PLAIN_TEXT:
                parts.append({"type": "input_text", "text": str(a.content)})
            elif a.type == FILE_ID:
                parts.append({"type": "input_file", "file_id": str(a.content)})
        return [{"role": "user", "content": parts}]

    def _merge_plain_text(self, prompt: str, atts: list[FileAttachment]) -> str:
        extras = [str(a.content) for a in atts if a.type == PLAIN_TEXT]
        if not extras:
            return prompt
        return f"{prompt}\n\n[ATTACHMENTS]\n" + "\n\n".join(extras)

    # ---------- error mapping ----------
    @staticmethod
    def _map_openai_error(err: Exception) -> ModelError:
        if isinstance(err, openai.RateLimitError):
            return ModelRateLimitError(str(err))
        if isinstance(err, openai.APIConnectionError):
            return ModelConnectionError(str(err))
        if isinstance(err, openai.APIStatusError):
            status = getattr(err, "status_code", None)
            resp = getattr(err, "response", None)
            payload_repr = None
            try:
                payload_repr = resp.json() if resp is not None else None
            except Exception:
                payload_repr = None
            return ModelAPIError(f"OpenAI API status error ({status}). payload={payload_repr!r}")
        if isinstance(err, openai.APIError):
            return ModelAPIError(str(err))
        return ModelAPIError(str(err))

    # ---------- Sync core callers ----------
    def _call_chat(self, prompt: str) -> str:
        client = self._require_sync_client()
        try:
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise self._map_openai_error(e) from e

    def _call_chat_stream(self, prompt: str) -> Iterator[str]:
        client = self._require_sync_client()
        try:
            stream = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            raise self._map_openai_error(e) from e

    def _call_responses(self, input_content: list[dict[str, Any]]) -> str:
        client = self._require_sync_client()
        try:
            resp: Any = client.responses.create(
                model=self.model_name,
                input=cast(Any, input_content),
                temperature=self.temperature,
            )
            return (getattr(resp, "output_text", None) or "").strip()
        except Exception as e:
            raise self._map_openai_error(e) from e

    def _call_responses_stream(self, input_content: list[dict[str, Any]]) -> Iterator[str]:
        client = self._require_sync_client()
        try:
            stream_or_resp = client.responses.create(
                model=self.model_name,
                input=cast(Any, input_content),
                temperature=self.temperature,
                stream=True,
            )
            if isinstance(stream_or_resp, Stream):
                for ev in stream_or_resp:
                    delta = getattr(getattr(ev, "delta", None), "content", None)
                    if delta:
                        yield delta
            else:
                text = (getattr(stream_or_resp, "output_text", None) or "").strip()
                if text:
                    yield text
        except Exception as e:
            raise self._map_openai_error(e) from e

    # ---------- Async core callers ----------
    async def _acall_chat(self, prompt: str) -> str:
        client = self._require_async_client()
        print("acall_chat:", prompt)  # noqa: T201
        try:
            resp = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise self._map_openai_error(e) from e

    async def _acall_chat_stream(self, prompt: str) -> AsyncIterator[str]:
        client = self._require_async_client()
        try:
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            raise self._map_openai_error(e) from e

    async def _acall_responses(self, input_content: list[dict[str, Any]]) -> str:
        client = self._require_async_client()
        try:
            resp: Any = await client.responses.create(
                model=self.model_name,
                input=cast(Any, input_content),
                temperature=self.temperature,
            )
            return (getattr(resp, "output_text", None) or "").strip()
        except Exception as e:
            raise self._map_openai_error(e) from e

    async def _acall_responses_stream(self, input_content: list[dict[str, Any]]) -> AsyncIterator[str]:
        client = self._require_async_client()
        try:
            stream_or_resp = await client.responses.create(
                model=self.model_name,
                input=cast(Any, input_content),
                temperature=self.temperature,
                stream=True,
            )
            if isinstance(stream_or_resp, AsyncStream):
                async for ev in stream_or_resp:
                    delta = getattr(getattr(ev, "delta", None), "content", None)
                    if delta:
                        yield delta
            else:
                text = (getattr(stream_or_resp, "output_text", None) or "").strip()
                if text:
                    yield text
        except Exception as e:
            raise self._map_openai_error(e) from e
