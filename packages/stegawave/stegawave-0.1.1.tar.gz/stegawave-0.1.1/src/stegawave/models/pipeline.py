"""Pydantic models describing Stegawave API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

InputType = Literal[
    "RTMP_PUSH",
    "RTMP_PULL",
    "RTP_PUSH",
    "HLS",
    "SRT_LISTENER",
    "SRT_CALLER",
    "MP4_FILE",
    "TS_FILE",
]

AdaptiveQuantization = Literal[
    "AUTO",
    "OFF",
    "LOW",
    "MEDIUM",
    "HIGH",
    "HIGHER",
    "MAX",
]

H264Profile = Literal[
    "BASELINE",
    "MAIN",
    "HIGH",
    "HIGH_10BIT",
    "HIGH_422",
    "HIGH_422_10BIT",
]

H265Profile = Literal[
    "MAIN",
    "MAIN_10BIT",
]

ContainerType = Literal["CMAF", "TS", "ISM"]


def _parse_bitrate(bitrate: Union[int, str, None]) -> Optional[int]:
    if bitrate is None:
        return None
    if isinstance(bitrate, int):
        return bitrate
    token = bitrate.strip().lower()
    if token.endswith("k"):
        return int(float(token[:-1]) * 1_000)
    if token.endswith("m"):
        return int(float(token[:-1]) * 1_000_000)
    return int(token)


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Url: HttpUrl


class SrtCallerDecryption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Algorithm: Literal["AES128", "AES192", "AES256"]
    Passphrase: str = Field(min_length=16, max_length=64)


class SrtCallerSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    SrtListenerAddress: str
    SrtListenerPort: int = Field(ge=1, le=65535)
    StreamId: Optional[str] = Field(default=None, max_length=512)
    SrtCallerDecryption: Optional[SrtCallerDecryption] = None


class SrtListenerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    IngestPort: int = Field(ge=1024, le=65535)
    MinLatency: int = Field(default=2000, ge=0, le=60000)
    MaxLatency: Optional[int] = Field(default=None, ge=0, le=60000)
    PassphraseEnabled: Optional[bool] = None
    Passphrase: Optional[str] = Field(default=None, min_length=32, max_length=32)

    @field_validator("IngestPort")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if value in {2077, 2088}:
            raise ValueError("SRT ingest port cannot be 2077 or 2088")
        return value

    @model_validator(mode="after")
    def _validate_passphrase(self) -> "SrtListenerSettings":
        if self.Passphrase and not (self.PassphraseEnabled or str(self.PassphraseEnabled).upper() in {"TRUE", "1"}):
            raise ValueError("Passphrase provided but PassphraseEnabled is not set")
        return self


class InputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Type: InputType = "RTMP_PUSH"
    whitelist: Optional[List[str]] = None
    Sources: Optional[List[SourceConfig]] = None
    SrtListenerSettings: Optional[SrtListenerSettings] = None
    SrtCallerSources: Optional[List[SrtCallerSource]] = None

    @field_validator("Type")
    @classmethod
    def _upper_type(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def _validate_structure(self) -> "InputConfig":
        if self.Type in {"RTMP_PULL", "HLS", "TS_FILE", "MP4_FILE"}:
            if not self.Sources:
                raise ValueError(f"{self.Type} inputs require at least one source URL")
        if self.Type == "SRT_LISTENER":
            if not self.SrtListenerSettings:
                raise ValueError("SRT_LISTENER inputs require SrtListenerSettings")
            if self.whitelist and len(self.whitelist) != 1:
                raise ValueError("SRT listener whitelist must contain exactly one CIDR")
        if self.Type == "SRT_CALLER" and not self.SrtCallerSources:
            raise ValueError("SRT_CALLER inputs require SrtCallerSources")
        return self


class InputSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Codec: Literal["AVC", "HEVC"] = "AVC"
    MaximumBitrate: Literal["MAX_10_MBPS", "MAX_20_MBPS", "MAX_50_MBPS"] = "MAX_20_MBPS"
    Resolution: Literal["SD", "HD", "UHD"] = "HD"


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    OutputName: Optional[str] = None
    resolution: Optional[str] = None
    Width: Optional[int] = Field(default=None, gt=0, le=7680)
    Height: Optional[int] = Field(default=None, gt=0, le=4320)
    FramerateNumerator: int = Field(gt=0)
    FramerateDenominator: int = Field(gt=0)
    VideoBitrate: Optional[int] = Field(default=None, gt=0)
    Bitrate: Optional[int] = Field(default=None, gt=0)
    AudioBitrate: Optional[int] = Field(default=128_000, gt=0)
    SampleRate: Optional[int] = Field(default=48_000, gt=0)
    Profile: Optional[Union[H264Profile, H265Profile]] = None
    AdaptiveQuantization: Optional[AdaptiveQuantization] = None

    @model_validator(mode="after")
    def _validate_resolution(self) -> "OutputConfig":
        if not self.resolution and not (self.Width and self.Height):
            raise ValueError("Output must define either resolution string or Width/Height")
        if self.resolution and (self.Width or self.Height):
            raise ValueError("Provide resolution string or Width/Height, not both")
        if self.resolution:
            parts = self.resolution.lower().split("x")
            if len(parts) != 2:
                raise ValueError("resolution must be in WIDTHxHEIGHT format")
            width, height = parts
            if not width.isdigit() or not height.isdigit():
                raise ValueError("resolution must contain numeric width/height")
        return self

    @model_validator(mode="after")
    def _coerce_bitrates(self) -> "OutputConfig":
        parsed_video = _parse_bitrate(self.VideoBitrate or self.Bitrate)
        if parsed_video is None:
            parsed_video = 5_000_000
        object.__setattr__(self, "VideoBitrate", parsed_video)
        object.__setattr__(self, "Bitrate", parsed_video)
        object.__setattr__(self, "AudioBitrate", _parse_bitrate(self.AudioBitrate) or 128_000)
        return self


class OutputGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Name: str = "cmaf-main"
    Outputs: List[OutputConfig]

    @model_validator(mode="after")
    def _validate_framerate(self) -> "OutputGroup":
        numerators = {o.FramerateNumerator for o in self.Outputs}
        denominators = {o.FramerateDenominator for o in self.Outputs}
        if len(numerators) > 1 or len(denominators) > 1:
            raise ValueError("All outputs must share the same framerate")
        return self


class EncoderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vodArchive: bool = False
    InputSpecification: Optional[InputSpecification] = None
    output_group: OutputGroup


class HlsManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ManifestName: str = "index"
    ManifestWindowSeconds: Optional[int] = Field(default=360, ge=30, le=3600)
    ProgramDateTimeIntervalSeconds: Optional[int] = Field(default=None, ge=0, le=3600)
    ChildManifestName: Optional[str] = None


class DashManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ManifestName: str = "index"
    ManifestWindowSeconds: Optional[int] = Field(default=360, ge=30, le=3600)
    MinUpdatePeriodSeconds: Optional[int] = Field(default=None, ge=1, le=120)
    MinBufferTimeSeconds: Optional[int] = Field(default=None, ge=1, le=900)
    SuggestedPresentationDelaySeconds: Optional[int] = Field(default=None, ge=1, le=900)


class MssManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ManifestName: str = "index"
    ManifestWindowSeconds: Optional[int] = Field(default=360, ge=30, le=3600)


class OriginEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ContainerType: ContainerType = "CMAF"
    description: Optional[str] = None
    HlsManifests: Optional[List[HlsManifest]] = None
    DashManifests: Optional[List[DashManifest]] = None
    MssManifests: Optional[List[MssManifest]] = None
    StartoverWindowSeconds: Optional[int] = Field(default=None, ge=60, le=1_209_600)
    TsUseAudioRenditionGroup: Optional[bool] = None

    @model_validator(mode="after")
    def _validate_manifests(self) -> "OriginEndpoint":
        if not any([self.HlsManifests, self.DashManifests, self.MssManifests]):
            raise ValueError("At least one manifest type must be provided")
        return self


class PackagerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    originEndpoints: List[OriginEndpoint]


class CreatePipelineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None
    segmentDuration: int = Field(default=4, ge=1, le=30)
    duplicationCount: Optional[int] = Field(default=2, ge=1, le=4)
    input: InputConfig
    encoder: EncoderConfig
    packager: PackagerConfig


class CreatePipelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    eventID: str
    status: str
    note: Optional[str] = None

    def is_success(self) -> bool:
        status = (self.status or "").lower()
        return status not in {"failed", "error", "invalid"}

    def valid(self) -> bool:
        return self.is_success()


class PipelineInputStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    protocol: Optional[str] = None
    endpoint: Optional[str] = None
    allowedIPs: Optional[List[str]] = None
    latency: Optional[str] = None
    status: Optional[str] = None


class PipelineEncoderProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    format: str
    renditions: int


class PipelineEncoderStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Optional[str] = None
    segmentLength: Optional[str] = None
    profiles: Optional[List[PipelineEncoderProfile]] = None


class PipelinePackagerEndpoint(BaseModel):
    model_config = ConfigDict(extra="allow")

    containerFormat: str
    segmentLength: Optional[str] = None
    manifests: Optional[List[str]] = None


class PipelinePackagerStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    endpoints: Optional[List[PipelinePackagerEndpoint]] = None


class PipelineCdnStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: Optional[str] = None
    endpoints: Optional[List[str]] = None


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    eventID: str
    name: str
    description: Optional[str] = None
    status: str
    createdAt: Optional[datetime] = None
    lastUpdated: Optional[datetime] = None
    input: Optional[PipelineInputStatus] = None
    encoder: Optional[PipelineEncoderStatus] = None
    packager: Optional[PipelinePackagerStatus] = None
    cdn: Optional[PipelineCdnStatus] = None

    PROVISIONING_STATUSES: ClassVar[Set[str]] = {"provisioning", "creating", "pending", "initializing"}
    TERMINAL_FAILURE_STATUSES: ClassVar[Set[str]] = {"failed", "error"}

    def is_ready(self) -> bool:
        status = (self.status or "").lower()
        if not status:
            return False
        if status in self.TERMINAL_FAILURE_STATUSES:
            return False
        return status not in self.PROVISIONING_STATUSES

    def is_terminal_failure(self) -> bool:
        status = (self.status or "").lower()
        return status in self.TERMINAL_FAILURE_STATUSES


class PipelineListEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventID: str
    name: str
    status: str
    createdAt: Optional[datetime] = None


class PipelineListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipelines: List[PipelineListEntry]


class StateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventID: str
    action: Literal["status", "start", "stop"]


class StateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    eventID: str
    action: Literal["status", "start", "stop"]
    state: Optional[str] = None
    note: Optional[str] = None


class DeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    eventID: str
    status: str
    note: Optional[str] = None


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tokens: Dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def _wrap(cls, value):  # type: ignore[override]
        if isinstance(value, dict) and "tokens" not in value:
            return {"tokens": value}
        return value


class DecodeJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventID: str
    input_stream: HttpUrl


class DecodeJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    eventID: str
    clientID: Optional[str] = None


class IptvQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: HttpUrl
    username: str
    password: str
    channelName: str
    categoryId: Optional[int] = None
    format: Optional[str] = None
    preferHD: Optional[bool] = None
    preferUK: Optional[bool] = None
    avoidVIP: Optional[bool] = None


class IptvStream(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    stream_id: int
    stream_urls: List[HttpUrl]


class IptvQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: List[IptvStream]

    @model_validator(mode="before")
    @classmethod
    def _wrap(cls, value):  # type: ignore[override]
        if isinstance(value, list):
            return {"results": value}
        return value


class PassphraseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passphrase: str
    lastRotated: Optional[datetime] = None
    usageExample: Optional[str] = None


class RotatePassphraseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passphrase: Optional[str] = Field(default=None, min_length=32, max_length=32)


class RotatePassphraseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    newPassphrase: str
    message: Optional[str] = None
