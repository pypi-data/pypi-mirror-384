import asyncio
import types

import pytest


class _Msg:
    def __init__(self, content):
        self.content = content


class _ChoiceMsg:
    def __init__(self, content):
        self.message = _Msg(content)


class _Delta:
    def __init__(self, content):
        self.content = content


class _ChoiceDelta:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_ChoiceMsg(content)]


class _StreamChunk:
    def __init__(self, content):
        self.choices = [_ChoiceDelta(content)]


class FakeSyncChat:
    def __init__(self, content: str = 'stubbed-sync', stream_chunks: list[str] | None = None):
        self._content = content
        self._stream_chunks = stream_chunks or ['Hello ', 'world']

    def completions_create(self, **kwargs):
        if kwargs.get('stream'):

            def _gen():
                for c in self._stream_chunks:
                    yield _StreamChunk(c)

            return _gen()
        return _Resp(self._content)

    @property
    def completions(self):
        obj = types.SimpleNamespace()
        obj.create = self.completions_create
        return obj


class FakeSyncClient:
    def __init__(self, *_a, **_kw):
        self.chat = FakeSyncChat()


class FakeAsyncChat:
    def __init__(self, content: str = 'stubbed-async', stream_chunks: list[str] | None = None):
        self._content = content
        self._stream_chunks = stream_chunks or ['Hello ', 'async ', 'world']

    async def completions_create(self, **kwargs):
        if kwargs.get('stream'):

            async def _agen():
                for c in self._stream_chunks:
                    await asyncio.sleep(0)
                    yield _StreamChunk(c)

            return _agen()
        return _Resp(self._content)

    @property
    def completions(self):
        obj = types.SimpleNamespace()
        obj.create = self.completions_create
        return obj


class FakeAsyncClient:
    def __init__(self, *_a, **_kw):
        self.chat = FakeAsyncChat()


@pytest.fixture(autouse=True)
def _set_env_key(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-123')


@pytest.fixture
def patch_openai(monkeypatch):
    import amsdal_ml.ml_models.openai_model as mod

    monkeypatch.setattr(mod, 'OpenAI', FakeSyncClient)
    monkeypatch.setattr(mod, 'AsyncOpenAI', FakeAsyncClient)
    monkeypatch.setattr(mod, 'FakeSyncChat', FakeSyncChat, raising=False)
    monkeypatch.setattr(mod, 'FakeAsyncChat', FakeAsyncChat, raising=False)
    return mod
