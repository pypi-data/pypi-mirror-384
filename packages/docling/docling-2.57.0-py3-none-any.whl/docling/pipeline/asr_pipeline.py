import logging
import os
import re
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Union, cast

from docling_core.types.doc import DoclingDocument, DocumentOrigin

# import whisper  # type: ignore
# import librosa
# import numpy as np
# import soundfile as sf  # type: ignore
from docling_core.types.doc.labels import DocItemLabel
from pydantic import BaseModel, Field, validator

from docling.backend.abstract_backend import AbstractDocumentBackend
from docling.backend.noop_backend import NoOpBackend

# from pydub import AudioSegment  # type: ignore
# from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline
from docling.datamodel.accelerator_options import (
    AcceleratorOptions,
)
from docling.datamodel.base_models import (
    ConversionStatus,
    FormatToMimeType,
)
from docling.datamodel.document import ConversionResult, InputDocument
from docling.datamodel.pipeline_options import (
    AsrPipelineOptions,
)
from docling.datamodel.pipeline_options_asr_model import (
    InlineAsrNativeWhisperOptions,
    # AsrResponseFormat,
    InlineAsrOptions,
)
from docling.datamodel.pipeline_options_vlm_model import (
    InferenceFramework,
)
from docling.datamodel.settings import settings
from docling.pipeline.base_pipeline import BasePipeline
from docling.utils.accelerator_utils import decide_device
from docling.utils.profiling import ProfilingScope, TimeRecorder

_log = logging.getLogger(__name__)


class _ConversationWord(BaseModel):
    text: str
    start_time: Optional[float] = Field(
        None, description="Start time in seconds from video start"
    )
    end_time: Optional[float] = Field(
        None, ge=0, description="End time in seconds from video start"
    )


class _ConversationItem(BaseModel):
    text: str
    start_time: Optional[float] = Field(
        None, description="Start time in seconds from video start"
    )
    end_time: Optional[float] = Field(
        None, ge=0, description="End time in seconds from video start"
    )
    speaker_id: Optional[int] = Field(None, description="Numeric speaker identifier")
    speaker: Optional[str] = Field(
        None, description="Speaker name, defaults to speaker-{speaker_id}"
    )
    words: Optional[list[_ConversationWord]] = Field(
        None, description="Individual words with time-stamps"
    )

    def __lt__(self, other):
        if not isinstance(other, _ConversationItem):
            return NotImplemented
        return self.start_time < other.start_time

    def __eq__(self, other):
        if not isinstance(other, _ConversationItem):
            return NotImplemented
        return self.start_time == other.start_time

    def to_string(self) -> str:
        """Format the conversation entry as a string"""
        result = ""
        if (self.start_time is not None) and (self.end_time is not None):
            result += f"[time: {self.start_time}-{self.end_time}] "

        if self.speaker is not None:
            result += f"[speaker:{self.speaker}] "

        result += self.text
        return result


class _NativeWhisperModel:
    def __init__(
        self,
        enabled: bool,
        artifacts_path: Optional[Path],
        accelerator_options: AcceleratorOptions,
        asr_options: InlineAsrNativeWhisperOptions,
    ):
        """
        Transcriber using native Whisper.
        """
        self.enabled = enabled

        _log.info(f"artifacts-path: {artifacts_path}")
        _log.info(f"accelerator_options: {accelerator_options}")

        if self.enabled:
            try:
                import whisper  # type: ignore
            except ImportError:
                raise ImportError(
                    "whisper is not installed. Please install it via `pip install openai-whisper` or do `uv sync --extra asr`."
                )
            self.asr_options = asr_options
            self.max_tokens = asr_options.max_new_tokens
            self.temperature = asr_options.temperature

            self.device = decide_device(
                accelerator_options.device,
                supported_devices=asr_options.supported_devices,
            )
            _log.info(f"Available device for Whisper: {self.device}")

            self.model_name = asr_options.repo_id
            _log.info(f"loading _NativeWhisperModel({self.model_name})")
            if artifacts_path is not None:
                _log.info(f"loading {self.model_name} from {artifacts_path}")
                self.model = whisper.load_model(
                    name=self.model_name,
                    device=self.device,
                    download_root=str(artifacts_path),
                )
            else:
                self.model = whisper.load_model(
                    name=self.model_name, device=self.device
                )

            self.verbose = asr_options.verbose
            self.timestamps = asr_options.timestamps
            self.word_timestamps = asr_options.word_timestamps

    def run(self, conv_res: ConversionResult) -> ConversionResult:
        # Access the file path from the backend, similar to how other pipelines handle it
        path_or_stream = conv_res.input._backend.path_or_stream

        # Handle both Path and BytesIO inputs
        temp_file_path: Optional[Path] = None

        if isinstance(path_or_stream, BytesIO):
            # For BytesIO, write to a temporary file since whisper requires a file path
            suffix = Path(conv_res.input.file.name).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(path_or_stream.getvalue())
                temp_file_path = Path(tmp_file.name)
            audio_path = temp_file_path
        elif isinstance(path_or_stream, Path):
            audio_path = path_or_stream
        else:
            raise RuntimeError(
                f"ASR pipeline requires a file path or BytesIO stream, but got {type(path_or_stream)}"
            )

        try:
            conversation = self.transcribe(audio_path)

            # Ensure we have a proper DoclingDocument
            origin = DocumentOrigin(
                filename=conv_res.input.file.name or "audio.wav",
                mimetype="audio/x-wav",
                binary_hash=conv_res.input.document_hash,
            )
            conv_res.document = DoclingDocument(
                name=conv_res.input.file.stem or "audio.wav", origin=origin
            )

            for citem in conversation:
                conv_res.document.add_text(
                    label=DocItemLabel.TEXT, text=citem.to_string()
                )

            return conv_res

        except Exception as exc:
            _log.error(f"Audio tranciption has an error: {exc}")
            conv_res.status = ConversionStatus.FAILURE
            return conv_res

        finally:
            # Clean up temporary file if created
            if temp_file_path is not None and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    _log.warning(
                        f"Failed to delete temporary file {temp_file_path}: {e}"
                    )

    def transcribe(self, fpath: Path) -> list[_ConversationItem]:
        result = self.model.transcribe(
            str(fpath), verbose=self.verbose, word_timestamps=self.word_timestamps
        )

        convo: list[_ConversationItem] = []
        for _ in result["segments"]:
            item = _ConversationItem(
                start_time=_["start"], end_time=_["end"], text=_["text"], words=[]
            )
            if "words" in _ and self.word_timestamps:
                item.words = []
                for __ in _["words"]:
                    item.words.append(
                        _ConversationWord(
                            start_time=__["start"],
                            end_time=__["end"],
                            text=__["word"],
                        )
                    )
            convo.append(item)

        return convo


class AsrPipeline(BasePipeline):
    def __init__(self, pipeline_options: AsrPipelineOptions):
        super().__init__(pipeline_options)
        self.keep_backend = True

        self.pipeline_options: AsrPipelineOptions = pipeline_options

        if isinstance(self.pipeline_options.asr_options, InlineAsrNativeWhisperOptions):
            asr_options: InlineAsrNativeWhisperOptions = (
                self.pipeline_options.asr_options
            )
            self._model = _NativeWhisperModel(
                enabled=True,  # must be always enabled for this pipeline to make sense.
                artifacts_path=self.artifacts_path,
                accelerator_options=pipeline_options.accelerator_options,
                asr_options=asr_options,
            )
        else:
            _log.error(f"No model support for {self.pipeline_options.asr_options}")

    def _has_text(self, document: "DoclingDocument") -> bool:
        """
        Helper method to check if the document contains any transcribed text.
        A transcription is considered non-empty if the .texts list contains items with actual, non whitespace content.
        """
        if not document or not document.texts:
            return False
        for item in document.texts:
            if item.text and item.text.strip():
                return True
        return False

    def _determine_status(self, conv_res: ConversionResult) -> ConversionStatus:
        """Determines the final status of ASR Conversion based on its result."""
        if conv_res.status == ConversionStatus.FAILURE or conv_res.errors:
            return ConversionStatus.FAILURE
        if not self._has_text(conv_res.document):
            _log.warning(
                "ASR conversion resulted in an empty document."
                f"File: {conv_res.input.file.name}"
            )
            return ConversionStatus.PARTIAL_SUCCESS
        return ConversionStatus.SUCCESS

    @classmethod
    def get_default_options(cls) -> AsrPipelineOptions:
        return AsrPipelineOptions()

    def _build_document(self, conv_res: ConversionResult) -> ConversionResult:
        _log.info(f"start _build_document in AsrPipeline: {conv_res.input.file}")
        with TimeRecorder(conv_res, "doc_build", scope=ProfilingScope.DOCUMENT):
            self._model.run(conv_res=conv_res)

        return conv_res

    @classmethod
    def is_backend_supported(cls, backend: AbstractDocumentBackend):
        return isinstance(backend, NoOpBackend)
