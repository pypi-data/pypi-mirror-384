#!/usr/bin/env python3

import json
import logging
import re
from collections.abc import Iterator
from enum import Enum
from typing import Annotated, BinaryIO, Optional, TextIO

import google.protobuf.duration_pb2
import grpc
import numpy as np
import soundfile
import typer
from google.protobuf.json_format import MessageToDict
from phonexia.grpc.common.core_pb2 import Audio, RawAudioConfig, TimeRange
from phonexia.grpc.technologies.deepfake_detection.v1.deepfake_detection_pb2 import (
    DetectRequest,
    DetectResponse,
)
from phonexia.grpc.technologies.deepfake_detection.v1.deepfake_detection_pb2_grpc import (
    DeepfakeDetectionStub,
)


def parse_time_range(
    ctx: typer.Context, time_range: str
) -> tuple[Optional[float], Optional[float]]:
    """Parse time range in format 'start:end' where both start and end are optional."""
    if ctx.resilient_parsing or time_range is None:
        return None, None

    if len(time_range) == 0:
        raise typer.BadParameter("Parameter 'time_range' must be of the form '[START]:[END]'.")

    # Regex pattern to match [START]:[END] format where START and END are optional positive floats
    pattern = r"^(\d+(?:\.\d+)?)?:(\d+(?:\.\d+)?)?$"
    match = re.match(pattern, time_range.strip())

    if not match:
        raise typer.BadParameter(
            "Parameter 'time_range' must be of the form '[START]:[END]' where START and END are positive float numbers."
        )

    # Parse START and END from regex groups
    start_str = match.group(1)
    end_str = match.group(2)

    # Ensure at least one of START or END is provided
    if not start_str and not end_str:
        raise typer.BadParameter(
            "Parameter 'time_range' must specify at least one of START or END."
        )

    start = float(start_str) if start_str else None
    end = float(end_str) if end_str else None

    return start, end


def time_to_duration(time: Optional[float]) -> Optional[google.protobuf.duration_pb2.Duration]:
    if time is None:
        return None
    duration = google.protobuf.duration_pb2.Duration()
    duration.seconds = int(time)
    duration.nanos = int((time - duration.seconds) * 1e9)
    return duration


def make_request(
    file: BinaryIO,
    start: Optional[float],
    end: Optional[float],
    use_raw_audio: bool,
) -> Iterator[DetectRequest]:
    time_range = TimeRange(start=time_to_duration(start), end=time_to_duration(end))
    chunk_size = 1024 * 100
    if use_raw_audio:
        with soundfile.SoundFile(file) as r:
            raw_audio_config = RawAudioConfig(
                channels=r.channels,
                sample_rate_hertz=r.samplerate,
                encoding=RawAudioConfig.AudioEncoding.PCM16,
            )
            for data in r.blocks(blocksize=r.samplerate, dtype="float32"):
                int16_info = np.iinfo(np.int16)
                data_scaled = np.clip(
                    data * (int16_info.max + 1), int16_info.min, int16_info.max
                ).astype("int16")
                yield DetectRequest(
                    audio=Audio(
                        content=data_scaled.flatten().tobytes(),
                        raw_audio_config=raw_audio_config,
                        time_range=time_range,
                    ),
                )
                time_range = None
                raw_audio_config = None

    else:
        while chunk := file.read(chunk_size):
            yield DetectRequest(audio=Audio(content=chunk, time_range=time_range))
            time_range = None


def write_result(audio_path: str, response: DetectResponse, output_file: TextIO) -> None:
    logging.info(f"{audio_path} -> {output_file.name}")
    json.dump(
        MessageToDict(
            message=response,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
        ),
        output_file,
        indent=2,
        ensure_ascii=False,
    )


def detect(
    channel: grpc.Channel,
    file: BinaryIO,
    output_file: TextIO,
    start: Optional[float],
    end: Optional[float],
    metadata: Optional[list[tuple[str, str]]],
    use_raw_audio: bool,
) -> None:
    logging.info(f"Detecting deepfakes in {file.name}")
    stub = DeepfakeDetectionStub(channel)
    response = stub.Detect(
        make_request(file, start, end, use_raw_audio),
        metadata=metadata,
    )
    write_result(file.name, response, output_file)


class LogLevel(str, Enum):
    """Log levels."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


def _parse_metadata_callback(
    ctx: typer.Context, metadata_list: Optional[list[str]]
) -> list[tuple[str, str]]:
    if ctx.resilient_parsing or metadata_list is None:
        return []

    params = []
    for item in metadata_list:
        t = tuple(item.split("=", 1))
        if len(t) != 2:
            raise typer.BadParameter(f"Metadata must be in format 'KEY=VALUE': {item}")
        params.append(t)
    return params


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


@app.command()
def cli(
    file: Annotated[
        typer.FileBinaryRead,
        typer.Argument(
            help="Input audio file. If omitted, the client reads audio bytes from standard input.",
            lazy=False,
        ),
    ] = "-",
    host: Annotated[
        str,
        typer.Option(
            "-H",
            "--host",
            help="Server address (host:port).",
        ),
    ] = "localhost:8080",
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "-l",
            "--log-level",
            help="Logging level.",
        ),
    ] = LogLevel.ERROR,
    metadata: Annotated[
        Optional[list[str]],
        typer.Option(
            "--metadata",
            metavar="KEY=VALUE",
            help="Custom client metadata.",
            show_default=False,
            callback=_parse_metadata_callback,
        ),
    ] = None,
    output: Annotated[
        typer.FileTextWrite,
        typer.Option(
            "-o",
            "--output",
            help="Output file path. If omitted, prints to stdout.",
            lazy=False,
        ),
    ] = "-",
    time_range: Annotated[
        Optional[str],
        typer.Option(
            "-t",
            "--time-range",
            callback=parse_time_range,
            metavar="[START]:[END]",
            help="Time range in seconds using format [START]:[END] where START and END are positive float numbers. "
            "START can be omitted to process from beginning, END can be omitted to process to the end of the recording. "
            "Examples: --time-range :10 (0 to 10), --time-range 10.1: (10.1 to end), --time-range 5:10 (5 to 10).",
        ),
    ] = None,
    plaintext: Annotated[
        bool,
        typer.Option(
            "--plaintext",
            help="Use plain-text HTTP/2 when connecting to server (no TLS).",
        ),
    ] = False,
    use_raw_audio: Annotated[
        bool,
        typer.Option(
            "--use-raw-audio",
            help="Send raw audio in chunks. Enables continuous audio processing with less server memory usage.",
        ),
    ] = False,
) -> None:
    """Run deepfake detection on an input audio file or standard input."""

    # Setup logging
    logging.basicConfig(
        level=log_level.upper(),
        format="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Connect and execute
    try:
        logging.info(f"Connecting to {host}")
        with (
            grpc.insecure_channel(target=host)
            if plaintext
            else grpc.secure_channel(
                target=host, credentials=grpc.ssl_channel_credentials()
            ) as channel
        ):
            detect(
                channel,
                file,
                output,
                time_range[0] if time_range else None,
                time_range[1] if time_range else None,
                metadata,
                use_raw_audio,
            )

    except grpc.RpcError:
        logging.exception("RPC failed")
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception:
        logging.exception("Unknown error")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
