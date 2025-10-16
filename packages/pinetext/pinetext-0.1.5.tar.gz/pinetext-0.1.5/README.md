## PineText

[![test](https://github.com/ezhuk/pinetext/actions/workflows/test.yml/badge.svg)](https://github.com/ezhuk/pinetext/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/ezhuk/pinetext/graph/badge.svg?token=0YJASFE5OM)](https://codecov.io/github/ezhuk/pinetext)
[![PyPI - Version](https://img.shields.io/pypi/v/pinetext.svg)](https://pypi.org/p/pinetext)

A lightweight assistant built using [Pinecone](https://docs.pinecone.io/guides/assistant/overview) that helps create RAG-based chat applications for reasoning over documents, retrieving relevant context, and providing grounded answers.

## Getting Started

Use [uv](https://github.com/astral-sh/uv) to add and manage PineText as a dependency in your project, or install it directly via `uv pip install` or `pip install`. See the [Installation](https://github.com/ezhuk/pinetext/blob/main/docs/pinetext/installation.mdx) section of the documentation for full installation instructions and more details.

```bash
uv add pinetext
```

It can be embedded in and run directly from your application.

```python
# app.py
from pinetext import PineText

def main():
    pt = PineText()
    pt.run()
```

It can also be launched from the command line using the provided `CLI` without modifying the source code.

```
pinetext
```

Or in an ephemeral, isolated environment using `uvx`. Check out the [Using tools](https://docs.astral.sh/uv/guides/tools/) guide for more details.

```bash
uvx pinetext
```

## Configuration

Place documents in the `data` folder and make sure to set `PINECONE_API_KEY` and the assistant name before starting PineText.

```bash
export PINETEXT_PINECONE__API_KEY=your-api-key
export PINETEXT_PINECONE__ASSISTANT=assistant-name
export PINETEXT_PINECONE__DATA_DIR=data
export PINETEXT_PINECONE__MODEL=o4-mini
```

These settings can also be specified in a `.env` file in the working directory.

```text
pinetext_pinecone__api_key=your-api-key
pinetext_pinecone__assistant=assistant-name
pinetext_pinecone__data_dir=data
pinetext_pinecone__model=o4-mini
```

## Docker

The PineText CLI can be deployed as a Docker container as follows:

```bash
docker run -it \
  --name pinetext \
  --env-file .env \
  -v $(pwd)/data:/app/data
  ghcr.io/ezhuk/pinetext:latest
```

Or using Docker Compose:

```bash
docker compose up
```

## License

The server is licensed under the [MIT License](https://github.com/ezhuk/pinetext?tab=MIT-1-ov-file).
