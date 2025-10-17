#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Custom/External telephony serializer for Pipecat with Ringg AI WebSocket API. Customers will directly connect to Ringg AI WebSocket API."""

import base64
import json
import uuid
from typing import Optional

from loguru import logger
from pydantic import BaseModel

from pipecat.audio.utils import (
    alaw_to_pcm,
    create_stream_resampler,
    pcm_to_alaw,
    pcm_to_ulaw,
    ulaw_to_pcm,
)
from pipecat.frames.frames import (
    AudioRawFrame,
    CallTransferFrame,
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


class CustomFrameSerializer(FrameSerializer):
    """Serializer for Custom/External telephony WebSocket protocol (Ringg AI API).

    This serializer handles converting between Pipecat frames and the Ringg AI
    WebSocket protocol for external/custom telephony providers. It supports
    PCMU (μ-law), PCMA (A-law), and PCM codecs with automatic conversion.

    Supported events:
    - start: Initialize call with agent configuration
    - media: Bidirectional audio streaming
    - clear: Clear audio buffers (interruption)
    - call_transfer: Transfer call to another number
    - hang_up: End call notification

    Audio format:
    - Sample Rate: Configurable (default 8kHz)
    - Channels: Mono (1 channel)
    - Bit Depth: 16-bit
    - Encoding: Little-endian
    - Payload Encoding: Base64
    - Supported Codecs: PCMU (μ-law), PCMA (A-law), PCM (raw)
    """

    class InputParams(BaseModel):
        """Configuration parameters for CustomFrameSerializer.

        Parameters:
            custom_sample_rate: Sample rate used by external client, defaults to 8000 Hz.
            sample_rate: Optional override for pipeline input sample rate.
            codec: Audio codec - "pcmu" (μ-law), "pcma" (A-law), or "pcm" (raw PCM).
        """

        custom_sample_rate: int = 8000
        sample_rate: Optional[int] = None
        codec: str = "pcmu"  # "pcmu" or "pcm"

    def __init__(
        self, stream_sid: str, call_sid: Optional[str] = None, params: Optional[InputParams] = None
    ):
        """Initialize the CustomFrameSerializer.

        Args:
            stream_sid: The stream identifier from external client.
            call_sid: The call identifier from external client.
            params: Configuration parameters.
        """
        self._stream_sid = stream_sid
        self._call_sid = call_sid
        self._params = params or CustomFrameSerializer.InputParams()

        self._custom_sample_rate = self._params.custom_sample_rate
        self._sample_rate = 0  # Pipeline input rate
        self._codec = self._params.codec.lower()

        self._input_resampler = create_stream_resampler()
        self._output_resampler = create_stream_resampler()

    @property
    def type(self) -> FrameSerializerType:
        """Gets the serializer type.

        Returns:
            The serializer type, TEXT for JSON-based protocol.
        """
        return FrameSerializerType.TEXT

    async def setup(self, frame: StartFrame):
        """Sets up the serializer with pipeline configuration.

        Args:
            frame: The StartFrame containing pipeline configuration.
        """
        self._sample_rate = self._params.sample_rate or frame.audio_in_sample_rate

    async def serialize(self, frame: Frame) -> str | bytes | None:
        """Serializes a Pipecat frame to Custom telephony WebSocket format.

        Handles conversion of various frame types to Ringg AI WebSocket messages.

        Args:
            frame: The Pipecat frame to serialize.

        Returns:
            Serialized data as JSON string, or None if the frame isn't handled.
        """
        if isinstance(frame, StartInterruptionFrame):
            # Send clear event to instruct client to discard buffered audio
            answer = {"event": "clear", "stream_sid": self._stream_sid}
            return json.dumps(answer)

        elif isinstance(frame, CallTransferFrame):
            # Send call_transfer event to transfer the call to another number
            answer = {
                "event": "call_transfer",
                "call_sid": self._call_sid or self._stream_sid,
                "to": frame.target,
            }
            return json.dumps(answer)

        elif isinstance(frame, (EndFrame, CancelFrame)):
            # Send hang_up event to end the call
            answer = {"event": "hang_up", "stream_sid": self._stream_sid}
            return json.dumps(answer)

        elif isinstance(frame, AudioRawFrame):
            data = frame.audio

            # Convert audio based on codec
            if self._codec == "pcmu":
                # Convert PCM to μ-law for PCMU codec
                serialized_data = await pcm_to_ulaw(
                    data, frame.sample_rate, self._custom_sample_rate, self._output_resampler
                )
            elif self._codec == "pcma":
                # Convert PCM to A-law for PCMA codec
                serialized_data = await pcm_to_alaw(
                    data, frame.sample_rate, self._custom_sample_rate, self._output_resampler
                )
            else:  # pcm
                # Resample PCM to target sample rate
                serialized_data = await self._output_resampler.resample(
                    data, frame.sample_rate, self._custom_sample_rate
                )

            if serialized_data is None or len(serialized_data) == 0:
                # Skip if no audio data
                return None

            payload = base64.b64encode(serialized_data).decode("ascii")
            answer = {
                "event": "media",
                "stream_sid": self._stream_sid,
                "media": {"payload": payload},
            }

            return json.dumps(answer)

        elif isinstance(frame, (TransportMessageFrame, TransportMessageUrgentFrame)):
            return json.dumps(frame.message)

        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        """Deserializes Custom telephony WebSocket data to Pipecat frames.

        Handles conversion of Ringg AI WebSocket events to appropriate Pipecat frames.

        Args:
            data: The raw WebSocket data from external client.

        Returns:
            A Pipecat frame corresponding to the event, or None if unhandled.
        """
        try:
            message = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            return None

        event = message.get("event")

        if event == "media":
            media = message.get("media", {})
            payload_base64 = media.get("payload")
            uuid = message.get("uuid")

            if not payload_base64:
                logger.warning("Media event missing payload")
                return None

            try:
                payload = base64.b64decode(payload_base64)
            except Exception as e:
                logger.error(f"Failed to decode base64 payload: {e}")
                return None

            # Convert audio based on codec
            if self._codec == "pcmu":
                # Convert μ-law to PCM
                deserialized_data = await ulaw_to_pcm(
                    payload, self._custom_sample_rate, self._sample_rate, self._input_resampler
                )
            elif self._codec == "pcma":
                # Convert A-law to PCM
                deserialized_data = await alaw_to_pcm(
                    payload, self._custom_sample_rate, self._sample_rate, self._input_resampler
                )
            else:  # pcm
                # Resample PCM to pipeline sample rate
                deserialized_data = await self._input_resampler.resample(
                    payload,
                    self._custom_sample_rate,
                    self._sample_rate,
                )

            if deserialized_data is None or len(deserialized_data) == 0:
                # Skip if no audio data
                return None

            audio_frame = InputAudioRawFrame(
                audio=deserialized_data,
                num_channels=1,  # Mono audio
                sample_rate=self._sample_rate,
            )
            return audio_frame

        elif event == "start":
            # Log start event but don't generate a frame (handled by WebSocketService)
            logger.debug(f"Received start event for stream {self._stream_sid}")
            return None

        elif event == "clear":
            # External client requesting to clear our audio buffers
            logger.debug(f"Received clear event for stream {self._stream_sid}")
            return None

        else:
            logger.debug(f"Unhandled event type: {event} for stream {self._stream_sid}")
            return None
