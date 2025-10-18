#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""TTS switcher for switching between different TTS services at runtime, with different switching strategies."""

from typing import List, Optional, Type

from pipecat.pipeline.service_switcher import ServiceSwitcher, StrategyType
from pipecat.services.tts_service import TTSService


class TTSSwitcher(ServiceSwitcher[StrategyType]):
    """A pipeline that switches between different TTS services at runtime."""

    def __init__(self, tts_services: List[TTSService], strategy_type: Type[StrategyType]):
        """Initialize the TTS switcher with a list of TTS services and a switching strategy."""
        super().__init__(tts_services, strategy_type)

    @property
    def tts_services(self) -> List[TTSService]:
        """Get the list of TTS services managed by this switcher."""
        return self.services

    @property
    def active_tts(self) -> Optional[TTSService]:
        """Get the currently active TTS service, if any."""
        return self.strategy.active_service