#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""ElevenLabs speech-to-text service implementation."""

import asyncio
from typing import AsyncGenerator, Optional

from loguru import logger

from pipecat.frames.frames import ErrorFrame, Frame, TranscriptionFrame
from pipecat.services.stt_service import SegmentedSTTService
from pipecat.transcriptions.language import Language
from pipecat.utils.time import time_now_iso8601
from pipecat.utils.tracing.service_decorators import traced_stt

try:
    from elevenlabs.client import ElevenLabs
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error("In order to use ElevenLabs, you need to `pip install pipecat-ai[elevenlabs]`.")
    raise Exception(f"Missing module: {e}")


def language_to_elevenlabs_language(language: Language) -> Optional[str]:
    """Maps pipecat Language enum to ElevenLabs language codes.

    Args:
        language: A Language enum value representing the input language.

    Returns:
        str or None: The corresponding ElevenLabs language code, or None if not supported.
    """
    language_map = {
        # English
        Language.EN: "eng",
        Language.EN_US: "eng",
        Language.EN_GB: "eng",
        Language.EN_AU: "eng",
        Language.EN_CA: "eng",
        Language.EN_IN: "eng",
        Language.EN_IE: "eng",
        Language.EN_NZ: "eng",
        Language.EN_ZA: "eng",
        Language.EN_SG: "eng",
        Language.EN_HK: "eng",
        Language.EN_PH: "eng",
        Language.EN_KE: "eng",
        Language.EN_NG: "eng",
        Language.EN_TZ: "eng",
        # Spanish
        Language.ES: "spa",
        Language.ES_ES: "spa",
        Language.ES_MX: "spa",
        Language.ES_AR: "spa",
        Language.ES_CO: "spa",
        Language.ES_CL: "spa",
        Language.ES_VE: "spa",
        Language.ES_PE: "spa",
        Language.ES_EC: "spa",
        Language.ES_GT: "spa",
        Language.ES_CU: "spa",
        Language.ES_BO: "spa",
        Language.ES_DO: "spa",
        Language.ES_HN: "spa",
        Language.ES_PY: "spa",
        Language.ES_SV: "spa",
        Language.ES_NI: "spa",
        Language.ES_CR: "spa",
        Language.ES_PA: "spa",
        Language.ES_UY: "spa",
        Language.ES_PR: "spa",
        Language.ES_US: "spa",
        Language.ES_GQ: "spa",
        # French
        Language.FR: "fra",
        Language.FR_FR: "fra",
        Language.FR_CA: "fra",
        Language.FR_BE: "fra",
        Language.FR_CH: "fra",
        # German
        Language.DE: "deu",
        Language.DE_DE: "deu",
        Language.DE_AT: "deu",
        Language.DE_CH: "deu",
        # Italian
        Language.IT: "ita",
        Language.IT_IT: "ita",
        # Portuguese
        Language.PT: "por",
        Language.PT_PT: "por",
        Language.PT_BR: "por",
        # Hindi
        Language.HI: "hin",
        Language.HI_IN: "hin",
        # Arabic
        Language.AR: "ara",
        Language.AR_SA: "ara",
        Language.AR_EG: "ara",
        Language.AR_AE: "ara",
        Language.AR_BH: "ara",
        Language.AR_DZ: "ara",
        Language.AR_IQ: "ara",
        Language.AR_JO: "ara",
        Language.AR_KW: "ara",
        Language.AR_LB: "ara",
        Language.AR_LY: "ara",
        Language.AR_MA: "ara",
        Language.AR_OM: "ara",
        Language.AR_QA: "ara",
        Language.AR_SY: "ara",
        Language.AR_TN: "ara",
        Language.AR_YE: "ara",
        # Japanese
        Language.JA: "jpn",
        Language.JA_JP: "jpn",
        # Korean
        Language.KO: "kor",
        Language.KO_KR: "kor",
        # Chinese
        Language.ZH: "cmn",
        Language.ZH_CN: "cmn",
        Language.ZH_TW: "cmn",
        Language.ZH_HK: "cmn",
        # Russian
        Language.RU: "rus",
        Language.RU_RU: "rus",
        # Dutch
        Language.NL: "nld",
        Language.NL_NL: "nld",
        Language.NL_BE: "nld",
        # Polish
        Language.PL: "pol",
        Language.PL_PL: "pol",
        # Turkish
        Language.TR: "tur",
        Language.TR_TR: "tur",
        # Swedish
        Language.SV: "swe",
        Language.SV_SE: "swe",
        # Norwegian
        Language.NO: "nor",
        Language.NB: "nor",
        Language.NN: "nor",
        # Danish
        Language.DA: "dan",
        Language.DA_DK: "dan",
        # Finnish
        Language.FI: "fin",
        Language.FI_FI: "fin",
        # Czech
        Language.CS: "ces",
        Language.CS_CZ: "ces",
        # Hungarian
        Language.HU: "hun",
        Language.HU_HU: "hun",
        # Greek
        Language.EL: "ell",
        Language.EL_GR: "ell",
        # Hebrew
        Language.HE: "heb",
        Language.HE_IL: "heb",
        # Thai
        Language.TH: "tha",
        Language.TH_TH: "tha",
        # Vietnamese
        Language.VI: "vie",
        Language.VI_VN: "vie",
        # Indonesian
        Language.ID: "ind",
        Language.ID_ID: "ind",
        # Malay
        Language.MS: "msa",
        Language.MS_MY: "msa",
        # Ukrainian
        Language.UK: "ukr",
        Language.UK_UA: "ukr",
        # Bulgarian
        Language.BG: "bul",
        Language.BG_BG: "bul",
        # Croatian
        Language.HR: "hrv",
        Language.HR_HR: "hrv",
        # Slovak
        Language.SK: "slk",
        Language.SK_SK: "slk",
        # Slovenian
        Language.SL: "slv",
        Language.SL_SI: "slv",
        # Estonian
        Language.ET: "est",
        Language.ET_EE: "est",
        # Latvian
        Language.LV: "lav",
        Language.LV_LV: "lav",
        # Lithuanian
        Language.LT: "lit",
        Language.LT_LT: "lit",
        Language.TA: "tam",  # Tamil
        Language.TA_IN: "tam",  # Tamil
        Language.TE: "tel",  # Telugu
        Language.TE_IN: "tel",  # Telugu
        Language.KN: "kan",  # Kannada
        Language.KN_IN: "kan",  # Kannada
        Language.ML: "mal",  # Malayalam
        Language.ML_IN: "mal",  # Malayalam
        Language.MR: "mar",  # Marathi
        Language.MR_IN: "mar",  # Marathi
    }
    return language_map.get(language)


class ElevenlabsSTTService(SegmentedSTTService):
    """ElevenLabs speech-to-text service using Scribe v1 model.

    This service uses ElevenLabs' batch STT API to transcribe audio segments.
    It extends SegmentedSTTService to handle VAD-based audio segmentation.

    Args:
        api_key: ElevenLabs API key for authentication.
        model_id: Model to use for transcription (default: "scribe_v1").
        language: Default language for transcription.
        tag_audio_events: Whether to tag audio events like laughter (default: False).
        diarize: Whether to enable speaker diarization (default: False).
        **kwargs: Additional arguments passed to SegmentedSTTService.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str = "scribe_v1",
        language: Optional[Language] = None,
        tag_audio_events: bool = False,
        sample_rate: Optional[int] = None,
        diarize: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._client = ElevenLabs(api_key=api_key)
        self._model_id = model_id
        self._tag_audio_events = tag_audio_events
        self._diarize = diarize

        self._settings = {
            "language": language,
            "model_id": self._model_id,
            "tag_audio_events": self._tag_audio_events,
            "diarize": self._diarize,
        }
        self.set_model_name(model_id)

    def can_generate_metrics(self) -> bool:
        """Check if this service can generate processing metrics.

        Returns:
            True, as ElevenLabs service supports metrics generation.
        """
        return True

    def language_to_service_language(self, language: Language) -> Optional[str]:
        """Convert from pipecat Language to ElevenLabs language code.

        Args:
            language: The Language enum value to convert.

        Returns:
            str or None: The corresponding ElevenLabs language code, or None if not supported.
        """
        return language_to_elevenlabs_language(language)

    async def set_language(self, language: Language):
        """Set the language for transcription.

        Args:
            language: The Language enum value to use for transcription.
        """
        self.logger.info(f"Switching STT language to: [{language}]")
        self._settings["language"] = language

    @traced_stt
    async def _handle_transcription(
        self, transcript: str, is_final: bool, language: Optional[Language] = None
    ):
        """Handle a transcription result with tracing."""
        pass

    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame, None]:
        """Transcribe the provided audio using ElevenLabs STT.

        Args:
            audio: Audio data (WAV format) to transcribe.

        Yields:
            Frame: TranscriptionFrame containing the transcribed text or ErrorFrame on failure.
        """
        try:
            await self.start_processing_metrics()
            await self.start_ttfb_metrics()

            # Get language code for ElevenLabs API
            params = {
                "file": audio,
                "model_id": self._model_id,
                "tag_audio_events": self._tag_audio_events,
                "diarize": self._diarize,
            }

            language = self._settings["language"]
            if language is not None:
                elevenlabs_lang = self.language_to_service_language(language)
                if elevenlabs_lang:
                    params["language_code"] = elevenlabs_lang
            else:
                params["language_code"] = None

            # Call ElevenLabs STT API in thread pool to avoid blocking
            transcription = await asyncio.to_thread(self._client.speech_to_text.convert, **params)

            await self.stop_ttfb_metrics()

            # Process transcription result
            if transcription and hasattr(transcription, "text") and transcription.text:
                transcript_text = transcription.text.strip()

                if transcript_text:
                    # Determine language if available from response
                    response_language = language
                    if hasattr(transcription, "language_code") and transcription.language_code:
                        # Try to map back from ElevenLabs language code to pipecat Language
                        try:
                            # This is a simplified mapping - you might want to create a reverse map
                            response_language = language  # For now, keep the original
                        except ValueError:
                            self.logger.warning(
                                f"Unknown language detected: {transcription.language_code}"
                            )

                    # Handle transcription with tracing
                    await self._handle_transcription(transcript_text, True, response_language)

                    self.logger.debug(f"ElevenLabs transcription: [{transcript_text}]")

                    yield TranscriptionFrame(
                        text=transcript_text,
                        user_id="",
                        timestamp=time_now_iso8601(),
                        language=response_language,
                        result=transcription,
                    )

            await self.stop_processing_metrics()

        except Exception as e:
            self.logger.error(f"ElevenLabs STT error: {e}")
            await self.stop_all_metrics()
            yield ErrorFrame(f"ElevenLabs STT error: {str(e)}")
