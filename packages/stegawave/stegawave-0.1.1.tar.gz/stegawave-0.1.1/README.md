# Stegawave Python Client

`stegawave` is an unofficial Python SDK for the Stegawave forensic watermarking platform. It wraps the public REST API and helps you validate `/create` payloads, manage pipeline lifecycle, and trigger watermark decode jobs without hand-writing HTTP calls.

## Installation

```bash
pip install stegawave
```

## Quick start

```python
from stegawave import StegawaveClient, models

client = StegawaveClient(api_key="your-api-key")

create_request = models.CreatePipelineRequest(
    name="launch-stream",
    description="Product launch livestream",
    segmentDuration=4,
    input=models.InputConfig(  # RTMP push by default
        Type="RTMP_PUSH",
        whitelist=["0.0.0.0/0"],
    ),
    encoder=models.EncoderConfig(
        vodArchive=False,
        output_group=models.OutputGroup(
            Name="cmaf-main",
            Outputs=[
                models.OutputConfig(
                    OutputName="cmaf-1080p",
                    resolution="1920x1080",
                    FramerateNumerator=30,
                    FramerateDenominator=1,
                    VideoBitrate=7_500_000,
                    AudioBitrate=128_000,
                )
            ],
        ),
    ),
    packager=models.PackagerConfig(
        originEndpoints=[
            models.OriginEndpoint(
                name="cmaf-hybrid",
                ContainerType="CMAF",
                HlsManifests=[models.HlsManifest(ManifestName="index")],
            )
        ]
    ),
)

session = client.create_pipeline_session(create_request, wait=True)
print(session.event_id)

print("Input:", session.input_uri)
print("Manifests:")
for url in session.signed_manifest_uris("john_doe"):
    print("  ", url)
```

The SDK automatically injects your API key, validates payload structure using Pydantic models, and surfaces HTTP issues as rich exceptions.

## Configuration

Set your base URL or API key explicitly, or rely on environment variables.

```python
client = StegawaveClient()
```

| Environment variable      | Description                            |
|---------------------------|----------------------------------------|
| `STEGAWAVE_API_KEY`       | API key provided by Stegawave          |
| `STEGAWAVE_API_BASE_URL`  | Override the default `https://api.stegawave.com` |

## Features

- Strongly-typed request and response models for `/create`, `/get`, `/state`, `/delete`, `/token`, `/decode`, `/iptv`, `/passphrase`
- High-level `PipelineSession` workflow helper to provision, poll, and sign manifests in a few lines
- Convenience helpers for SRT listener inputs, ABR ladders, and asynchronous provisioning workflows
- Configurable retries, timeouts, and polling intervals
- First-class error types for authentication, validation, rate limiting, and server-side failures

## Status

This client is pre-release software targeting the October 2025 API schema. Expect breaking changes as the platform evolves. Contributions and issue reports are welcome.

## Development

```bash
pip install -e .[dev]
pytest
```

Refer to `CHANGELOG.md` for planned enhancements and release history.
