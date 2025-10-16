from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Pinecone(BaseModel):
    api_key: str | None = None
    assistant: str | None = "test-assistant"
    data_dir: str | None = "data"
    model: str | None = "o4-mini"


class WandB(BaseModel):
    api_key: str | None = None
    project: str | None = "pinetext"


class Settings(BaseSettings):
    pinecone: Pinecone = Pinecone()
    wandb: WandB = WandB()
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_prefix="PINETEXT_",
    )
