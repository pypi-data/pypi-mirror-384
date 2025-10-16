import wandb
import weave

from pathlib import Path

from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message

from pinetext.settings import Settings


settings = Settings()


class PineText:
    def __init__(self):
        pass

    def get_or_create_assistant(self, name: str):
        try:
            return self.pinecone.assistant.describe_assistant(assistant_name=name)
        except Exception:
            return self.pinecone.assistant.create_assistant(assistant_name=name)

    def upload_files(self, path: str):
        folder = Path(path)
        if folder.is_dir():
            uploaded = [x.name for x in self.assistant.list_files()]
            for x in sorted(folder.iterdir()):
                if x.name not in uploaded:
                    self.assistant.upload_file(
                        file_path=str(x.resolve()),
                        metadata={
                            "filename": x.name,
                            "extension": x.suffix.lower().lstrip("."),
                        },
                        timeout=None,
                    )

    @weave.op()
    def chat(self, text: str, model: str):
        msg = Message(role="user", content=text)
        resp = self.assistant.chat(messages=[msg], model=model)
        return resp.message.content

    def run(self):
        if settings.wandb.api_key:
            wandb.login(key=settings.wandb.api_key)
            weave.init(settings.wandb.project)
        self.pinecone = Pinecone(api_key=settings.pinecone.api_key)
        self.assistant = self.get_or_create_assistant(settings.pinecone.assistant)
        self.upload_files(settings.pinecone.data_dir)

        while True:
            text = input("> ").strip()
            if text.lower() in ("exit", "quit"):
                break
            res = self.chat(text, settings.pinecone.model)
            print(res)
