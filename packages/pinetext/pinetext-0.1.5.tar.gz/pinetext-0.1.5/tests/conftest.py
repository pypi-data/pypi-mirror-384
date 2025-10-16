import pytest

from pathlib import Path

import pinetext.client as client_mod
from pinetext.client import PineText


@pytest.fixture
def cli(monkeypatch):
    def dummy_run(self):
        return

    monkeypatch.setattr(
        "pinetext.client.PineText.run",
        dummy_run,
    )


@pytest.fixture
def pinetext(monkeypatch):
    class DummyAssistant:
        def __init__(self):
            self.files = []

        def create_assistant(self, assistant_name: str, instructions: str = None):
            return self

        def describe_assistant(self, assistant_name: str):
            return self

        def list_files(self):
            return self.files

        def upload_file(self, file_path: str, metadata=None, timeout=None):
            self.files.append(Path(file_path).name)

        def chat(self, messages, model=None):
            class Message:
                def __init__(self, content):
                    self.content = content

            class Response:
                def __init__(self, content):
                    self.message = Message(content)

            return Response("Test")

    assistant = DummyAssistant()

    class DummyPinecone:
        def __init__(self, api_key):
            self.assistant = assistant

    monkeypatch.setattr(client_mod, "Pinecone", DummyPinecone)

    client = PineText()
    client.assistant = assistant
    client.pinecone = DummyPinecone(None)
    return client
