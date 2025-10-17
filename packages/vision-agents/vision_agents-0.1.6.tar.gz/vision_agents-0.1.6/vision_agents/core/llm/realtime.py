from __future__ import annotations

from typing import (
    Any,
)

from getstream.video.rtc.audio_track import AudioStreamTrack
from vision_agents.core.edge.types import PcmData


import abc
import logging
import uuid

from vision_agents.core.events import PluginClosedEvent

from . import events, LLM


logger = logging.getLogger(__name__)


class Realtime(LLM, abc.ABC):
    """
    Realtime is an abstract base class for LLMs that can receive audio and video

    Example:

        llm = Realtime()
        llm.connect()
        llm.simple_response("what do you see?")

    Emits the following events:

    TODO: document/ evaluate how many events we want/ need...
        - Transcript incoming audio
        - Transcript outgoing audio

    """
    fps : int = 1

    def __init__(
        self,
        fps: int = 1, # the number of video frames per second to send (for implementations that support setting fps)
    ):
        super().__init__()
        self._is_connected = False

        self.provider_name = "realtime_base"
        self.session_id = str(uuid.uuid4())
        self.fps = fps
        # The most common style output track (webrtc)
        # TODO: do we like the output track here, or do we want to do an event, and have the agent manage the output track
        self.output_track: AudioStreamTrack = AudioStreamTrack(
            framerate=48000, stereo=True, format="s16"
        )

    @property
    def is_connected(self) -> bool:
        """Return True if the realtime session is currently active."""
        return self._is_connected

    @abc.abstractmethod
    async def connect(self): ...

    @abc.abstractmethod
    async def simple_audio_response(self, pcm: PcmData): ...


    async def _watch_video_track(self, track: Any, **kwargs) -> None:
        """Optionally overridden by providers that support video input."""
        return None

    async def _stop_watching_video_track(self) -> None:
        """Optionally overridden by providers that support video input."""
        return None

    def _emit_connected_event(self, session_config=None, capabilities=None):
        """Emit a structured connected event."""
        self._is_connected = True
        # Mark ready when connected if provider uses base emitter
        try:
            self._ready_event.set()  # type: ignore[attr-defined]
        except Exception:
            pass
        event = events.RealtimeConnectedEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            session_config=session_config,
            capabilities=capabilities,
        )
        self.events.send(event)

    def _emit_disconnected_event(self, reason=None, was_clean=True):
        """Emit a structured disconnected event."""
        self._is_connected = False
        event = events.RealtimeDisconnectedEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            reason=reason,
            was_clean=was_clean,
        )
        self.events.send(event)

    def _emit_audio_input_event(
        self, audio_data, sample_rate=16000, user_metadata=None
    ):
        """Emit a structured audio input event."""
        event = events.RealtimeAudioInputEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            audio_data=audio_data,
            sample_rate=sample_rate,
            user_metadata=user_metadata,
        )
        self.events.send(event)

    # TODO: discussion around event vs output_track... why do we have both?
    def _emit_audio_output_event(
        self, audio_data, sample_rate=16000, response_id=None, user_metadata=None
    ):
        """Emit a structured audio output event."""
        event = events.RealtimeAudioOutputEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            audio_data=audio_data,
            sample_rate=sample_rate,
            response_id=response_id,
            user_metadata=user_metadata,
        )
        self.events.send(event)

    def _emit_partial_transcript_event(self, text: str, user_metadata=None, original=None):
        event = events.RealtimeTranscriptEvent(
            text=text,
            user_metadata=user_metadata,
            original=original,
        )
        self.events.send(event)

    def _emit_transcript_event(
        self,
        text: str,
        user_metadata=None,
        original=None,
    ):
        event = events.RealtimeTranscriptEvent(
            text=text,
            user_metadata=user_metadata,
            original=original,
        )
        self.events.send(event)

    def _emit_response_event(
        self,
        text,
        response_id=None,
        is_complete=True,
        conversation_item_id=None,
        user_metadata=None,
    ):
        """Emit a structured response event."""
        event = events.RealtimeResponseEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            text=text,
            response_id=response_id,
            is_complete=is_complete,
            conversation_item_id=conversation_item_id,
            user_metadata=user_metadata,
        )
        self.events.send(event)

    def _emit_conversation_item_event(
        self, item_id, item_type, status, role, content=None, user_metadata=None
    ):
        """Emit a structured conversation item event."""
        event = events.RealtimeConversationItemEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            item_id=item_id,
            item_type=item_type,
            status=status,
            role=role,
            content=content,
            user_metadata=user_metadata,
        )
        self.events.send(event)

    def _emit_error_event(self, error, context="", user_metadata=None):
        """Emit a structured error event."""
        event = events.RealtimeErrorEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            error=error,
            context=context,
            user_metadata=user_metadata,
        )
        self.events.send(event)

    async def close(self):
        """Close the Realtime service and release any resources."""
        if self._is_connected:
            await self._close_impl()
            self._emit_disconnected_event("service_closed", True)

        close_event = PluginClosedEvent(
            session_id=self.session_id,
            plugin_name=self.provider_name,
            cleanup_successful=True,
        )
        self.events.send(close_event)

    @abc.abstractmethod
    async def _close_impl(self): ...

