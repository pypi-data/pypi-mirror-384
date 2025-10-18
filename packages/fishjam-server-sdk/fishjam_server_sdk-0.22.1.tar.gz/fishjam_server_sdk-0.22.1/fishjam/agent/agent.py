from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Literal

import betterproto
from websockets import ClientConnection, ConnectionClosed
from websockets.asyncio import client

from fishjam.agent.errors import AgentAuthError
from fishjam.events._protos.fishjam import (
    AgentRequest,
    AgentRequestAddTrack,
    AgentRequestAddTrackCodecParameters,
    AgentRequestAuthRequest,
    AgentRequestInterruptTrack,
    AgentResponse,
)
from fishjam.events._protos.fishjam import AgentRequestTrackData as OutgoingTrackData
from fishjam.events._protos.fishjam import AgentResponseTrackData as IncomingTrackData
from fishjam.events._protos.fishjam.notifications import Track, TrackEncoding, TrackType

IncomingAgentMessage = IncomingTrackData


@dataclass
class OutgoingAudioTrackOptions:
    """Parameters of an outgoing audio track."""

    encoding: TrackEncoding = TrackEncoding.TRACK_ENCODING_UNSPECIFIED
    """
    The encoding of the audio source.
    Defaults to raw 16-bit PCM.
    """

    sample_rate: Literal[16000, 24000] = 16000
    """
    The sample rate of the audio source.
    Defaults to 16000.
    """

    channels: Literal[1, 2] = 1
    """
    The number of channels in the audio source.
    Supported values are 1 (mono) and 2 (stereo).
    Defaults to 1 (mono)
    """

    metadata: dict[str, Any] | None = None
    """
    Custom metadata for the track.
    Must be JSON-encodable.
    """


@dataclass(frozen=True)
class OutgoingTrack:
    """
    Represents an outgoing track of an agent connected to Fishjam,
    created by :func:`Agent.add_track`.
    """

    id: str
    """The global identifier of the track."""
    session: AgentSession
    """The agent the track belongs to."""
    options: OutgoingAudioTrackOptions
    """The parameters used to create the track."""

    async def send_chunk(self, data: bytes):
        """
        Send a chunk of audio to Fishjam on this track.

        Peers connected to the room of the agent will receive this data.
        """
        message = AgentRequest(
            track_data=OutgoingTrackData(
                track_id=self.id,
                data=data,
            )
        )

        await self.session._send(message)

    async def interrupt(self):
        """
        Interrupt current track.

        Any audio that has been sent, but not played
        will be cleared and be prevented from playing.

        Audio sent after the interrupt will be played normally.
        """
        message = AgentRequest(
            interrupt_track=AgentRequestInterruptTrack(
                track_id=self.id,
            )
        )

        await self.session._send(message)


class AgentSession:
    def __init__(self, agent: Agent, websocket: ClientConnection):
        self.agent = agent

        self._ws = websocket
        self._closed = False

    async def receive(self) -> AsyncIterator[IncomingAgentMessage]:
        """
        Returns an infinite async iterator over the incoming messages from Fishjam to
        the agent.
        """
        while message := await self._ws.recv(decode=False):
            parsed = AgentResponse().parse(message)
            _, msg = betterproto.which_one_of(parsed, "content")
            match msg:
                case IncomingTrackData() as content:
                    yield content

    async def add_track(self, options: OutgoingAudioTrackOptions):
        """
        Adds a track to the connected agent, with the specified options and metadata.

        Returns an instance of :class:`OutgoingTrack`, which can be used to send data
        over the added track.
        """
        track_id = uuid.uuid4().hex
        metadata_json = json.dumps(options.metadata)
        message = AgentRequest(
            add_track=AgentRequestAddTrack(
                track=Track(
                    id=track_id,
                    type=TrackType.TRACK_TYPE_AUDIO,
                    metadata=metadata_json,
                ),
                codec_params=AgentRequestAddTrackCodecParameters(
                    encoding=options.encoding,
                    sample_rate=options.sample_rate,
                    channels=options.channels,
                ),
            )
        )
        await self._send(message)
        return OutgoingTrack(id=track_id, session=self, options=options)

    async def _send(self, message: AgentRequest):
        await self._ws.send(bytes(message), text=False)

    async def disconnect(self):
        """
        Ends the agent session by closing the websocket connection.
        Useful when you don't use the context manager to obtain the session.
        """
        await self._ws.close()


class Agent:
    """
    Allows for connecting to a Fishjam room as an agent peer.
    Provides callbacks for receiving audio.
    """

    def __init__(self, id: str, room_id: str, token: str, fishjam_url: str):
        """
        Create Agent instance, providing the fishjam id and management token.

        This constructor should not be called directly.
        Instead, you should call :func:`fishjam.FishjamClient.create_agent`.
        """

        self.id = id
        self.room_id = room_id

        self._socket_url = f"{fishjam_url}/socket/agent/websocket".replace("http", "ws")
        self._token = token

    @asynccontextmanager
    async def connect(self):
        """
        Connect the agent to Fishjam to start receiving messages.

        Incoming messages from Fishjam will be routed to handlers
        defined with :func:`on_track_data`.

        :raises AgentAuthError: authentication failed
        """
        async with client.connect(self._socket_url) as websocket:
            await self._authenticate(websocket)
            yield AgentSession(self, websocket)

    async def _authenticate(self, websocket: ClientConnection):
        req = AgentRequest(auth_request=AgentRequestAuthRequest(token=self._token))
        try:
            await websocket.send(bytes(req))
            # Fishjam will close the socket if auth fails and send a response on success
            await websocket.recv(decode=False)
        except ConnectionClosed:
            raise AgentAuthError(websocket.close_reason or "")
