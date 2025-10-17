import asyncio

from pipecat.frames.frames import (
    BotSpeakingFrame,
    CancelFrame,
    DTMFUpdateSettingsFrame,
    EndDTMFCaptureFrame,
    EndFrame,
    Frame,
    InputDTMFFrame,
    StartDTMFCaptureFrame,
    StartInterruptionFrame,
    TranscriptionFrame,
    WaitForDTMFFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.utils.time import time_now_iso8601


class DTMFAggregator(FrameProcessor):
    """Aggregates DTMF frames using idle wait logic.
    The aggregator accumulates digits from incoming InputDTMFFrame instances.
    It flushes the aggregated digits by emitting a TranscriptionFrame when:
      - No new digit arrives within the specified timeout period,
      - The termination digit (“#”) is received, or
      - The number of digits aggregated equals the configured 'digits' value.
    """

    def __init__(
        self,
        timeout: float = 3.0,
        end_on: set[str] = None,
        reset_on: set[str] = None,
        digits: int = None,
        **kwargs,
    ):
        """:param timeout: Idle timeout in seconds before flushing the aggregated digits.
        :param digits: Number of digits to aggregate before flushing.
        """
        super().__init__(**kwargs)
        self._aggregation = ""
        self._idle_timeout = timeout
        self._digits = digits
        self._digit_event = asyncio.Event()
        self._aggregation_task = None
        self._end_on = end_on if end_on else set()
        self._reset_on = reset_on if reset_on else set()
        self._dtmf_capture_active = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        # Handle DTMF frames.
        await super().process_frame(frame, direction)

        if isinstance(frame, InputDTMFFrame):
            # Push the DTMF frame downstream first
            await self.push_frame(frame, direction)
            # Then handle it for proper frame ordering
            await self._handle_dtmf_frame(frame)
        elif isinstance(frame, (EndFrame, CancelFrame)):
            # For EndFrame, flush any pending aggregation and stop the digit aggregation task.
            if self._aggregation:
                await self.flush_aggregation()
            if self._aggregation_task:
                await self._stop_aggregation_task()
            await self.push_frame(frame, direction)
        elif isinstance(frame, WaitForDTMFFrame):
            self.logger.debug("Received WaitForDTMFFrame: Waiting for DTMF input")
            self._create_aggregation_task(raise_timeout=True)
            self._digit_event.set()  # Trigger the timeout handler
            await self._start_dtmf_capture()
            await self.push_frame(frame, direction)
        elif isinstance(frame, StartInterruptionFrame):
            self.logger.debug("Received StartInterruptionFrame")
            if self._aggregation:
                await self.flush_aggregation()
            await self._end_dtmf_capture()
            await self.push_frame(frame, direction)
        elif isinstance(frame, BotSpeakingFrame):
            # Signal the aggregation task to continue when bot speaks
            if self._aggregation_task is not None:
                self._digit_event.set()
            await self.push_frame(frame, direction)
        elif isinstance(frame, DTMFUpdateSettingsFrame):
            await self._update_settings(frame.settings)
            # Don't pass the settings frame downstream
        else:
            # Pass all other frames through
            await self.push_frame(frame, direction)

    async def _update_settings(self, settings: dict) -> None:
        """Update DTMF aggregator settings dynamically.

        Args:
            settings: Dictionary containing new DTMF settings
                     Supported keys: timeout, digits, end, reset
        """
        settings_changed = False

        if "timeout" in settings and settings["timeout"] is not None:
            new_timeout = float(settings["timeout"])
            if new_timeout != self._idle_timeout:
                self.logger.debug(
                    f"Updating DTMF timeout from {self._idle_timeout} to {new_timeout}"
                )
                self._idle_timeout = new_timeout
                settings_changed = True

        if "digits" in settings:
            new_digits = settings["digits"]
            if new_digits != self._digits:
                self.logger.debug(
                    f"Updating DTMF digits from {self._digits} to {new_digits}"
                )
                self._digits = new_digits
                settings_changed = True

        if "end" in settings:
            # Convert single string to set if needed
            end_value = settings["end"]
            if end_value is None:
                new_end_on = set()
            elif isinstance(end_value, str):
                new_end_on = {end_value} if end_value else set()
            else:
                new_end_on = set(end_value)

            if new_end_on != self._end_on:
                self.logger.debug(
                    f"Updating DTMF end_on from {self._end_on} to {new_end_on}"
                )
                self._end_on = new_end_on
                settings_changed = True

        if "reset" in settings:
            # Convert single string to set if needed
            reset_value = settings["reset"]
            if reset_value is None:
                new_reset_on = set()
            elif isinstance(reset_value, str):
                new_reset_on = {reset_value} if reset_value else set()
            else:
                new_reset_on = set(reset_value)

            if new_reset_on != self._reset_on:
                self.logger.debug(
                    f"Updating DTMF reset_on from {self._reset_on} to {new_reset_on}"
                )
                self._reset_on = new_reset_on
                settings_changed = True

        if settings_changed:
            self.logger.info(f"DTMF settings updated successfully")

    async def _handle_dtmf_frame(self, frame: InputDTMFFrame):
        """Handle DTMF input frame processing."""
        # Create aggregation task if needed
        if self._aggregation_task is None:
            self._create_aggregation_task()

        digit_value = frame.button.value

        # Handle reset digits
        if digit_value in self._reset_on:
            self._aggregation = ""
            return

        # Handle end digits
        if digit_value in self._end_on:
            if self._aggregation:  # Only flush if we have aggregation
                await self.flush_aggregation()
            return

        # Add digit to aggregation
        self._aggregation += digit_value

        # Signal the aggregation task that a digit was received
        self._digit_event.set()

        # Check if we reached the digit limit
        if self._digits and len(self._aggregation) == self._digits:
            await self.flush_aggregation()

    def _create_aggregation_task(self, raise_timeout: bool = False) -> None:
        """Creates the aggregation task if it hasn't been created yet."""
        if not self._aggregation_task:
            self._aggregation_task = self.create_task(
                self._aggregation_task_handler(raise_timeout)
            )

    async def _stop_aggregation_task(self) -> None:
        """Stops the aggregation task."""
        if self._aggregation_task:
            await self.cancel_task(self._aggregation_task)
            self._aggregation_task = None

    async def _aggregation_task_handler(self, raise_timeout=False):
        """Background task that handles timeout-based flushing."""
        while True:
            try:
                # Wait for a new digit signal with a timeout.
                await asyncio.wait_for(
                    self._digit_event.wait(), timeout=self._idle_timeout
                )
                self._digit_event.clear()
            except asyncio.TimeoutError:
                # No new digit arrived within the timeout period; flush if needed
                await self.flush_aggregation(raise_timeout=raise_timeout)

    async def flush_aggregation(self, *, raise_timeout: bool = False):
        """Flush the aggregated digits by emitting a TranscriptionFrame downstream."""
        if self._aggregation:
            # Create transcription frame
            aggregated_frame = TranscriptionFrame(
                f"User inputted: {self._aggregation}.", "", time_now_iso8601()
            )
            aggregated_frame.metadata["push_aggregation"] = True

            # Send interruption frame (as per original design)
            await self.push_frame(StartInterruptionFrame(), FrameDirection.DOWNSTREAM)

            # Push the transcription frame
            await self.push_frame(aggregated_frame, FrameDirection.DOWNSTREAM)

            # Reset state
            self._aggregation = ""
            await self._end_dtmf_capture()

        elif raise_timeout and not self._aggregation:
            # Timeout with no aggregation (WaitForDTMFFrame case)
            transcript_frame = TranscriptionFrame(
                "User didn't press any digits on the keyboard.", "", time_now_iso8601()
            )
            transcript_frame.metadata["push_aggregation"] = True
            await self.push_frame(transcript_frame, FrameDirection.DOWNSTREAM)
            await self._end_dtmf_capture()

    async def _start_dtmf_capture(self):
        """Signal the start of DTMF capture upstream."""
        if self._dtmf_capture_active:
            return
        await self.push_frame(StartDTMFCaptureFrame(), FrameDirection.UPSTREAM)
        self._dtmf_capture_active = True

    async def _end_dtmf_capture(self):
        """Signal the end of DTMF capture upstream."""
        if not self._dtmf_capture_active:
            return
        await self.push_frame(EndDTMFCaptureFrame(), FrameDirection.UPSTREAM)
        self._dtmf_capture_active = False

    async def cleanup(self) -> None:
        """Cleans up resources, ensuring that the digit aggregation task is cancelled."""
        await super().cleanup()
        if self._aggregation_task:
            await self._stop_aggregation_task()
