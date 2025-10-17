# asterisk_ws_serializer.py
import base64
import json
from typing import Literal, Optional

from pydantic import BaseModel

from pipecat.audio.utils import create_stream_resampler, pcm_to_ulaw, ulaw_to_pcm
from pipecat.frames.frames import (
    AudioRawFrame,
    CancelFrame,
    EndFrame,
    Frame,
    InputAudioRawFrame,
    StartFrame,
    StartInterruptionFrame,
    TransportMessageFrame,
    TransportMessageUrgentFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer, FrameSerializerType


class AsteriskFrameSerializer(FrameSerializer):
    class InputParams(BaseModel):
        """Configuration parameters for AsteriskFrameSerializer.

        Parameters:
            telephony_encoding: The encoding used by the telephony system (e.g., "pcmu" for μ-law).
            telephony_sample_rate: The sample rate used by the telephony system (e.g., 8000 Hz).
            sample_rate: Optional override for pipeline input sample rate.
            auto_hang_up: Whether to automatically terminate call on EndFrame.
        """

        # What the ADAPTER/Asterisk is sending/expecting on the wire:
        # "pcmu" -> μ-law @ 8k; "pcm16" -> signed 16-bit @ 8k
        telephony_encoding: Literal["pcmu", "pcma", "pcm16"] = "pcmu"
        telephony_sample_rate: int = 8000
        sample_rate: Optional[int] = None  # pipeline input rate
        auto_hang_up: bool = False  # no-op here; adapter handles hangup

    def __init__(self, stream_id: str, params: Optional[InputParams] = None):
        self._stream_id = stream_id
        self._params = params or AsteriskFrameSerializer.InputParams()
        self._tel_rate = self._params.telephony_sample_rate
        self._sample_rate = 0
        self._in_resampler = create_stream_resampler()
        self._out_resampler = create_stream_resampler()
        self._hangup_sent = False

    @property
    def type(self) -> FrameSerializerType:
        return FrameSerializerType.TEXT  # we send/recv JSON strings

    async def setup(self, frame: StartFrame):
        self._sample_rate = self._params.sample_rate or frame.audio_in_sample_rate

    # Pipecat -> Adapter (play to caller)
    async def serialize(self, frame: Frame) -> str | bytes | None:
        # On pipeline end, ask bridge to hang up
        if (
            self._params.auto_hang_up
            and not self._hangup_sent
            and isinstance(frame, (EndFrame, CancelFrame))
        ):
            self._hangup_sent = True
            return json.dumps({"event": "hangup"})
        if isinstance(frame, StartInterruptionFrame):
            return json.dumps({"event": "clear", "streamId": self._stream_id})
        if isinstance(frame, AudioRawFrame):
            pcm = frame.audio
            if self._params.telephony_encoding == "pcmu":
                ul = await pcm_to_ulaw(pcm, frame.sample_rate, self._tel_rate, self._out_resampler)
                if not ul:
                    return None
                payload = base64.b64encode(ul).decode("utf-8")
                return json.dumps(
                    {
                        "event": "media",
                        "encoding": "pcmu",
                        "sampleRate": self._tel_rate,
                        "payload": payload,
                    }
                )
            elif self._params.telephony_encoding == "pcma":
                al = await pcm_to_alaw(pcm, frame.sample_rate, self._tel_rate, self._out_resampler)
                if not al:
                    return None
                payload = base64.b64encode(al).decode("utf-8")
                return json.dumps(
                    {
                        "event": "media",
                        "encoding": "pcma",
                        "sampleRate": self._tel_rate,
                        "payload": payload,
                    }
                )
            else:  # "pcm16"
                # resample to 8k if needed, but data stays PCM16 bytes
                pcm8 = await self._out_resampler.resample(pcm, frame.sample_rate, self._tel_rate)
                if not pcm8:
                    return None
                payload = base64.b64encode(pcm8).decode("utf-8")
                return json.dumps(
                    {
                        "event": "media",
                        "encoding": "pcm16",
                        "sampleRate": self._tel_rate,
                        "payload": payload,
                    }
                )
        if isinstance(frame, (TransportMessageFrame, TransportMessageUrgentFrame)):
            return json.dumps(frame.message)
        return None

    # Adapter -> Pipecat (audio from caller)
    async def deserialize(self, data: str | bytes) -> Frame | None:
        try:
            msg = json.loads(data)
        except Exception:
            return None
        if msg.get("event") == "media":
            sr = int(msg.get("sampleRate", self._tel_rate))
            raw = base64.b64decode(msg.get("payload", ""))
            if not raw:
                return None
            # Use our configured telephony_encoding instead of trusting the message
            if self._params.telephony_encoding == "pcmu":
                pcm = await ulaw_to_pcm(raw, sr, self._sample_rate, self._in_resampler)
            elif self._params.telephony_encoding == "pcma":
                pcm = await alaw_to_pcm(raw, sr, self._sample_rate, self._in_resampler)
            elif self._params.telephony_encoding == "pcm16":
                # resample if pipeline rate != 8k
                pcm = await self._in_resampler.resample(raw, sr, self._sample_rate)
            else:
                return None
            if not pcm:
                return None
            return InputAudioRawFrame(audio=pcm, num_channels=1, sample_rate=self._sample_rate)
        elif msg.get("event") == "dtmf":
            # optional: map to InputDTMFFrame if you want
            return None
        elif msg.get("event") == "hangup":
            # Bridge is hanging up; you can treat as EndFrame if you want.
            return CancelFrame()
        return None
