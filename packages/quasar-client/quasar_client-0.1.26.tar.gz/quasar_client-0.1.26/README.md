# Quasar Python Client

[![PyPI version](https://img.shields.io/pypi/v/quasar-client.svg)](https://pypi.org/project/quasar-client/)

## Installation

```sh
pip install quasar-client
```

## Usage

```python
from quasar_client import Quasar

quasar_base = "URL for Quasar-compatible server"
quasar = Quasar(quasar_base=quasar_base)

# Use OpenAI-compatible interfaces...
chat_completion = quasar.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Hello quasar",
        }
    ],
    model="gpt-3.5-turbo",
)

# Use Quasar-specific interfaces like NER...
entities = quasar.tagger.tag(
    task="ner", 
    text="Yurts Technologies is based in SF."
)
```

Quasar provides a convenient interface for common RAG APIs. In addition to the OpenAI APIs, the client supports:

- Coreference Resolution
- Entities
- Embedding
- Ranking
- Topics/Keywords

## Asynchronous Support

For developers looking to leverage asynchronous programming for improved performance and non-blocking IO operations, Quasar introduces async support for its APIs. This allows you to efficiently handle large volumes of requests and data processing in a non-blocking manner.

### Async Usage Example

Below is an example of how to use the asynchronous interface for embedding texts:

```python
from quasar_client import AsyncQuasar

quasar_base = "URL for Quasar-compatible server"
quasar = AsyncQuasar(quasar_base=quasar_base)

# Asynchronously embed texts
async def embed_texts(texts):
    embeddings = await quasar.embedding.embed(texts=texts)
    return embeddings

# Example texts
texts = ["Hello, world!", "How are you?"]

# Remember to run this in an async context
```

This async support ensures that your application can scale more efficiently, handling concurrent operations without the need for complex threading or multiprocessing setups.

### Sync and Async Resource Modules

Quasar provides both synchronous and asynchronous resource classes to cater to different use cases and preferences. Whether you prefer the simplicity of synchronous code or the efficiency of asynchronous operations, Quasar has you covered.

```python
# Synchronous Embedding Resource Class
class SyncEmbeddingResource(SyncResource):
    ...

# Asynchronous Embedding Resource Class
class AsyncEmbeddingResource(AsyncResource):
    ...
```