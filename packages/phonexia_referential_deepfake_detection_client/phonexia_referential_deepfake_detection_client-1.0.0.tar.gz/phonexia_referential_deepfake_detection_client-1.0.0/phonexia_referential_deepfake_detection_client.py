import json
import logging
import re
from enum import Enum
from typing import Annotated, Any, BinaryIO, Iterator, Optional

import grpc
import numpy as np
import soundfile
import typer
import ubjson
from google.protobuf.duration_pb2 import Duration
from google.protobuf.json_format import MessageToDict
from phonexia.grpc.common.core_pb2 import (
    Audio,
    RawAudioConfig,
    TimeRange,
    # Voiceprint,
)
from phonexia.grpc.technologies.referential_deepfake_detection.v1.referential_deepfake_detection_pb2 import (
    # Authenticityprint,
    DetectRequest,
    DetectResponse,
    # ExtractConfig,
    # ExtractRequest,
    # ExtractResponse,
)
from phonexia.grpc.technologies.referential_deepfake_detection.v1.referential_deepfake_detection_pb2_grpc import (
    ReferentialDeepfakeDetectionStub,
)

MAX_BATCH_SIZE = 1024


class LogLevel(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class InputFormat(str, Enum):
    UBJSON = "ubjson"
    WAV = "wav"


class ExtractOutputFormat(str, Enum):
    VP = "voiceprint"
    JSON = "json"


def time_to_duration(time: Optional[float]) -> Optional[Duration]:
    if time is None:
        return None
    duration = Duration()
    duration.seconds = int(time)
    duration.nanos = int((time - duration.seconds) * 1e9)
    return duration


def vp_type(f: BinaryIO):
    try:
        json = ubjson.load(f)
        if json["model"] == "sid-xl5":
            return "vprint"
        elif json["model"] == "generic":
            return "aprint"
        else:
            return "none"
    except Exception:  # noqa: S110
        pass
    finally:
        f.seek(0)

    try:
        if f.read(4) == b"VPT ":
            return "vprint"
    except Exception:  # noqa: S110
        pass
    finally:
        f.seek(0)

    return "none"


def audio_chunks(
    file: BinaryIO,
    start: Optional[float],
    end: Optional[float],
    use_raw_audio: bool,
) -> Iterator[Audio]:
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
                yield Audio(
                    content=data_scaled.flatten().tobytes(),
                    raw_audio_config=raw_audio_config,
                    time_range=time_range,
                )

                time_range = None
                raw_audio_config = None

    else:
        while chunk := file.read(chunk_size):
            yield Audio(content=chunk, time_range=time_range)
            time_range = None


# def make_extract_request(
#     file: BinaryIO,
#     start: Optional[float],
#     end: Optional[float],
#     speech_length: Optional[float],
#     use_raw_audio: bool,
# ) -> Iterator[ExtractRequest]:
#     config = ExtractConfig(speech_length=time_to_duration(speech_length))
#     for audio in audio_chunks(file, start, end, use_raw_audio):
#         yield ExtractRequest(audio=audio, config=config)
#         config = None


def make_detect_request(
    file_reference: BinaryIO,
    file_questioned: BinaryIO,
    start: Optional[float],
    end: Optional[float],
    use_raw_audio: bool,
) -> Iterator[DetectRequest]:
    reference_type = vp_type(file_reference)
    questioned_type = vp_type(file_questioned)
    # detect_request = DetectRequest()

    # if reference_type == "vprint":
    #     detect_request.voiceprint_reference.CopyFrom(Voiceprint(content=file_reference.read()))
    # if reference_type == "aprint":
    #     detect_request.authenticityprint_reference.CopyFrom(
    #         Authenticityprint(content=file_reference.read())
    #     )

    # if questioned_type == "vprint":
    #     detect_request.voiceprint_questioned.CopyFrom(Voiceprint(content=file_questioned.read()))
    # if questioned_type == "aprint":
    #     detect_request.authenticityprint_questioned.CopyFrom(
    #         Authenticityprint(content=file_questioned.read())
    #     )

    # if not (reference_type == "none" and questioned_type == "none"):
    #     yield detect_request

    if not (reference_type == "none" and questioned_type == "none"):
        raise typer.BadParameter("Reference and questioned must both be audio files.")

    if reference_type == "none":
        for audio in audio_chunks(file_reference, start, end, use_raw_audio):
            yield DetectRequest(audio_reference=audio)
    if questioned_type == "none":
        for audio in audio_chunks(file_questioned, start, end, use_raw_audio):
            yield DetectRequest(audio_questioned=audio)


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


def _parse_time_range(
    ctx: typer.Context, time_range: str
) -> tuple[Optional[float], Optional[float]]:
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


def write_json(obj: Any, output: BinaryIO):
    output.write(
        json.dumps(
            MessageToDict(
                obj,
                always_print_fields_with_no_presence=True,
                preserving_proto_field_name=True,
            ),
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")
    )


def handle_grpc_error(e: grpc.RpcError):
    logging.error(f"gRPC call failed with status code: {e.code()}")
    logging.error(f"Error details: {e.details()}")

    if e.code() == grpc.StatusCode.UNAVAILABLE:
        logging.error("Service is unavailable.")
    elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        logging.error("Invalid arguments were provided to the RPC.")
    elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        logging.error("The RPC deadline was exceeded.")
    else:
        logging.error(f"An unexpected error occurred: {e.code()} - {e.details()}")


# @app.command()
# def extract(
#     ctx: typer.Context,
#     file: Annotated[
#         typer.FileBinaryRead,
#         typer.Argument(
#             lazy=False,
#             help="Input audio file. If omitted, the client reads audio bytes from standard input.",
#         ),
#     ] = "-",
#     time_range: Annotated[
#         Optional[str],
#         typer.Option(
#             "-t",
#             "--time-range",
#             callback=_parse_time_range,
#             metavar="[START]:[END]",
#             help=(
#                 "Time range in seconds using format [START]:[END] where START and END are positive float numbers. "
#                 "START can be omitted to process from beginning, END can be omitted to process to the end of the recording. "
#                 "Examples: --time-range :10 (0 to 10), --time-range 10.1: (10.1 to end), --time-range 5:10 (5 to 10)."
#             ),
#         ),
#     ] = None,
#     speech_length: Annotated[
#         Optional[float],
#         typer.Option("--speech-length", help="Maximum amount of speech in seconds.", min=1e-6),
#     ] = None,
#     use_raw_audio: Annotated[
#         bool,
#         typer.Option(
#             "--use-raw-audio",
#             help="Send raw audio in chunks. Enables continuous audio processing with less server memory usage.",
#         ),
#     ] = False,
#     output: Annotated[
#         typer.FileBinaryWrite,
#         typer.Option(
#             "--output", "-o", help="Output file path. If omitted, prints to stdout.", lazy=False
#         ),
#     ] = "-",
#     out_format: Annotated[
#         ExtractOutputFormat,
#         typer.Option(
#             "-f",
#             "--out-format",
#             help="Output file format for 'extract' operation.",
#         ),
#     ] = ExtractOutputFormat.JSON,
# ) -> None:
#     """Extract voiceprint from an input audio file."""

#     try:
#         logging.info(f"Connecting to {ctx.obj['host']}")
#         with (
#             grpc.insecure_channel(target=ctx.obj["host"])
#             if ctx.obj["plaintext"]
#             else grpc.secure_channel(
#                 target=ctx.obj["host"], credentials=grpc.ssl_channel_credentials()
#             )
#         ) as channel:
#             start = time_range[0] if time_range is not None else None
#             end = time_range[1] if time_range is not None else None

#             stub = ReferentialDeepfakeDetectionStub(channel)

#             extract_request = make_extract_request(file, start, end, speech_length, use_raw_audio)
#             response: ExtractResponse = stub.Extract(extract_request, metadata=ctx.obj["metadata"])

#             if out_format == ExtractOutputFormat.JSON:
#                 write_json(response, output)
#             else:
#                 output.write(response.result.voiceprint.content)

#     except grpc.RpcError as e:
#         handle_grpc_error(e)
#         raise typer.Exit(code=1) from None
#     except (typer.Exit, typer.BadParameter):
#         raise
#     except Exception:
#         logging.exception("Unknown error")
#         raise typer.Exit(code=2) from None


@app.command()
def detect(
    ctx: typer.Context,
    file_reference: Annotated[
        typer.FileBinaryRead,
        typer.Argument(
            lazy=False,
            help="Input reference file. Can be audio or voiceprint file.",
        ),
    ],
    file_questioned: Annotated[
        typer.FileBinaryRead,
        typer.Argument(
            lazy=False,
            help="Input questioned file. Can be audio or voiceprint file.",
        ),
    ],
    use_raw_audio: Annotated[
        bool,
        typer.Option(
            "--use-raw-audio",
            help="Send raw audio in chunks. Enables continuous audio processing with less server memory usage.",
        ),
    ] = False,
    output: Annotated[
        typer.FileBinaryWrite,
        typer.Option(
            "--output", "-o", help="Output file path. If omitted, prints to stdout.", lazy=False
        ),
    ] = "-",
) -> None:
    """Detect deepfake based on reference and questioned files."""

    try:
        logging.info(f"Connecting to {ctx.obj['host']}")
        with (
            grpc.insecure_channel(target=ctx.obj["host"])
            if ctx.obj["plaintext"]
            else grpc.secure_channel(
                target=ctx.obj["host"], credentials=grpc.ssl_channel_credentials()
            )
        ) as channel:
            stub = ReferentialDeepfakeDetectionStub(channel)

            response: DetectResponse = stub.Detect(
                make_detect_request(file_reference, file_questioned, None, None, use_raw_audio)
            )

            write_json(response, output)

    except grpc.RpcError as e:
        handle_grpc_error(e)
        raise typer.Exit(code=1) from None
    except (typer.Exit, typer.BadParameter):
        raise
    except Exception:
        logging.exception("Unknown error")
        raise typer.Exit(code=2) from None


@app.callback()
def cli(
    ctx: typer.Context,
    host: Annotated[
        str,
        typer.Option("--host", "-H", help="Server address (host:port)."),
    ] = "localhost:8080",
    log_level: Annotated[
        LogLevel, typer.Option("--log-level", "-l", help="Logging level.")
    ] = LogLevel.ERROR,
    metadata: Annotated[
        list[str],
        typer.Option(
            "--metadata",
            metavar="key=value",
            help="Custom client metadata.",
            show_default=False,
            callback=_parse_metadata_callback,
        ),
    ] = [],
    plaintext: Annotated[
        bool,
        typer.Option(
            "--plaintext", help="Use plain-text HTTP/2 when connecting to server (no TLS)."
        ),
    ] = False,
) -> None:
    """Referential deepfake detection gRPC client. Detect deepfake in an input files."""

    ctx.obj = {
        "host": host,
        "metadata": metadata,
        "log_level": log_level,
        "plaintext": plaintext,
    }

    logging.basicConfig(
        level=log_level.value.upper(),
        format="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    app()
