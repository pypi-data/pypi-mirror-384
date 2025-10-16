from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator

from amsdal_ml.fileio.base_loader import PLAIN_TEXT
from amsdal_ml.fileio.base_loader import FileAttachment


class ModelError(Exception):
    """Base exception for all ML models."""


class ModelConnectionError(ModelError):
    """Network or connection failure to the provider (timeouts, DNS, TLS, etc.)."""


class ModelRateLimitError(ModelError):
    """Provider's rate limit reached (HTTP 429)."""


class ModelAPIError(ModelError):
    """API responded with an error (any 4xx/5xx, except 429)."""


class MLModel(ABC):
    @abstractmethod
    def setup(self) -> None:
        """Initialize any clients or resources needed before inference."""
        raise NotImplementedError

    @abstractmethod
    def teardown(self) -> None:
        """Clean up resources after use."""
        raise NotImplementedError

    def supported_attachments(self) -> set[str]:
        """Return a set of universal attachment kinds, e.g. {PLAIN_TEXT, FILE_ID}."""
        return {PLAIN_TEXT}

    @abstractmethod
    def invoke(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> str:
        """Run synchronous inference with the model."""
        raise NotImplementedError

    @abstractmethod
    async def ainvoke(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> str:
        """Run asynchronous inference with the model."""
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ):
        """Stream synchronous inference results from the model."""
        raise NotImplementedError

    @abstractmethod
    def astream(
        self,
        prompt: str,
        *,
        attachments: list[FileAttachment] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream asynchronous inference results as an async generator.

        Subclasses should implement this like:

            async def astream(... ) -> AsyncIterator[str]:
                yield "chunk"
        """
        raise NotImplementedError
