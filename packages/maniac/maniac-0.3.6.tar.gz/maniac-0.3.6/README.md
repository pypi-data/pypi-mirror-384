## Maniac Python Client

A minimal python client for Maniac's API. Supports chat completions and dataset uploads.

### Installation

```bash
pip install maniac
```

### Example Usage

```py
from __future__ import annotations

import asyncio

from maniac import Maniac


async def main() -> None:
    client = Maniac()  # or Maniac({"apiKey": os.environ["MANIAC_API_KEY"]})
    try:
        # Run inference without a container
        # Using kwargs
        standard_response = await client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Tell me a story about france"}],
        )
        print(standard_response["choices"][0]["message"]["content"])  # type: ignore[index]

        # Create a container to collect telemetry
        container = await client.containers.create(
            label="local-test",
            initial_model="openai/gpt-4o-mini",
            initial_system_prompt="You are a helpful assistant that answers questions and discusses travel topics.",
        )

        container_response = await client.chat.completions.create(
            container=container,
            messages=[{"role": "user", "content": "Tell me a story about france"}],
        )
        print(container_response["choices"][0]["message"]["content"])  # type: ignore[index]

        # Stream responses as async iterable
        gen = await client.chat.completions.stream(
            container=container,
            messages=[{"role": "user", "content": "Tell me a story about france"}],
        )
        async for chunk in gen:  # type: ignore[union-attr]
            piece = (
                (chunk.get("choices") or [{}])[0].get("delta", {}).get("content", "")
            )
            if piece:
                print(piece, end="", flush=True)
        print()

        # Stream responses with callback
        async def on_chunk(chunk) -> None:
            piece = (
                (chunk.get("choices") or [{}])[0].get("delta", {}).get("content", "")
            )
            if piece:
                print(piece, end="", flush=True)

        await client.chat.completions.stream(
            {"container": container, "messages": [{"role": "user", "content": "Tell me a story about france"}]},
            on_chunk,
        )

        # Get a container by label and run a completion
        travel_agent = await client.containers.get("local-test")
        email_resp = await client.chat.completions.create(
            container=travel_agent,
            messages=[{"role": "user", "content": "Tell me a story about france"}],
        )
        print(email_resp["choices"][0]["message"]["content"])  # type: ignore[index]

        # Models list / retrieve
        models = await client.models.list()
        print([m["id"] for m in models.get("data", [])])
        model = await client.models.retrieve("openai/gpt-4o-mini")
        print(model)
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())

```
