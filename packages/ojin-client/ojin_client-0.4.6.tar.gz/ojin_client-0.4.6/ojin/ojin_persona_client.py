"""WebSocket client for OJIN Persona service."""

import asyncio
import contextlib
import json
import logging
import pathlib
import ssl
import time
import uuid
from typing import Any, Dict, Optional, Type, TypeVar

import websockets
from pydantic import BaseModel
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import (
    ConnectionClosedError,
    ConnectionClosedOK,
    WebSocketException,
)

from ojin.entities.interaction_messages import (
    CancelInteractionMessage,
    ErrorResponse,
    ErrorResponseMessage,
    InteractionInput,
    InteractionInputMessage,
    InteractionResponseMessage,
)
from ojin.ojin_persona_messages import (
    IOjinPersonaClient,
    OjinPersonaCancelInteractionMessage,
    OjinPersonaEndInteractionMessage,
    OjinPersonaInteractionInputMessage,
    OjinPersonaInteractionResponseMessage,
    OjinPersonaMessage,
    OjinPersonaSessionReadyMessage,
    OjinPersonaSessionReadyPing,
)

T = TypeVar("T", bound=OjinPersonaMessage)

logger = logging.getLogger(__name__)


ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
localhost_pem = pathlib.Path(__file__).with_name("cacert.pem")
ssl_context.load_verify_locations(localhost_pem)


class OjinPersonaClient(IOjinPersonaClient):
    """WebSocket client for communicating with the OJIN Persona service.

    This client handles the WebSocket connection, authentication, and message
    serialization/deserialization for the OJIN Persona service.
    """

    def __init__(
        self,
        ws_url: str,
        api_key: str,
        config_id: str,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
        mode: str | None = None,
    ):
        """Initialize the OJIN Persona WebSocket client.

        Args:
            ws_url: WebSocket URL of the OJIN Persona service
            api_key: API key for authentication
            config_id: Configuration ID for the persona
            reconnect_attempts: Number of reconnection attempts on failure
            reconnect_delay: Delay between reconnection attempts in seconds
            assumed_rountrip_lat: latency to be added to the computed

        """
        super().__init__()
        self.ws_url = ws_url
        self.api_key = api_key
        self.config_id = config_id
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self._ws: Optional[ClientConnection] = None
        self._available_response_messages_queue: asyncio.Queue[BaseModel] = asyncio.Queue()
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._inference_server_ready: bool = False
        self._cancelled: bool = False
        self._active_interaction_id: str | None = None
        self._process_messages_task: Optional[asyncio.Task] = None
        self._pending_client_messages_queue: asyncio.Queue[OjinPersonaMessage] = asyncio.Queue()
        self._mode: str | None = mode
        self._pending_first_input: bool = False

    async def connect(self) -> None:
        """Establish WebSocket connection and authenticate with the service."""
        if self._running:
            logger.warning("Client is already connected")
            return

        attempt = 0
        last_error = None

        try:
            while attempt < self.reconnect_attempts:
                headers = {"Authorization": f"{self.api_key}"}

                # Add query parameters for API key and config ID
                url = f"{self.ws_url}?config_id={self.config_id}"
                if self._mode == "dev":
                    url = f"{url}&mode={self._mode}"
                self._ws = await websockets.connect(
                    url, extra_headers=headers, ping_interval=30, ping_timeout=10
                )
                self._running = True
                self._receive_task = asyncio.create_task(self._receive_server_messages())
                self._process_messages_task = asyncio.create_task(self._process_client_messages())
                logger.info("Successfully connected to OJIN Persona service")
                return
        except WebSocketException as e:
            last_error = e
            attempt += 1
            if attempt < self.reconnect_attempts:
                logger.warning(
                    "Connection attempt %d/%d failed. Retrying in %d seconds...",
                    attempt, self.reconnect_attempts, self.reconnect_delay
                )
                await asyncio.sleep(self.reconnect_delay)

        logger.error("Failed to connect after %d attempts", self.reconnect_attempts)
        raise ConnectionError(
            f"Failed to connect to OJIN Persona service: {last_error}"
        )

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if not self._running:
            return

        self._running = False
        self._active_interaction_id = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.error("Error closing WebSocket connection: %s", e)
            self._ws = None
        
        if self._process_messages_task:
            self._process_messages_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._process_messages_task
            self._process_messages_task = None

        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
            self._receive_task = None   


        logger.info("Disconnected from OJIN Persona service")

    async def _receive_server_messages(self) -> None:
        """Continuously receive and process incoming messages from the server."""
        if not self._ws:
            raise RuntimeError("WebSocket connection not established")

        try:
            async for message in self._ws:
                await self._handle_server_message(message)
        except (ConnectionClosedOK, ConnectionClosedError) as e:
            if self._running:  # Only log if we didn't initiate the close
                logger.error("WebSocket connection closed: %s", e)
        except Exception as e:
            logger.exception("Error in WebSocket receive loop: %s", e)
        finally:
            await self.close()

    async def _handle_server_message(self, message: str | bytes) -> None:
        """Handle an incoming WebSocket message.

        Args:
            message: Raw JSON message from WebSocket

        """
        try:
            if isinstance(message, bytes):
                try:
                    interaction_server_response = InteractionResponseMessage.from_bytes(
                        message
                    )
                    interaction_response = OjinPersonaInteractionResponseMessage(
                        interaction_id=interaction_server_response.payload.interaction_id,
                        video_frame_bytes=interaction_server_response.payload.payload,
                        is_final_response=interaction_server_response.payload.is_final_response,
                        index=interaction_server_response.payload.index
                    )
                    logger.debug("Received InteractionResponse for id %s", interaction_response.interaction_id)
                    
                    if interaction_response.interaction_id != self._active_interaction_id:
                        logger.debug("Interaction id changed.")
                        self._active_interaction_id = interaction_response.interaction_id

                    await self._available_response_messages_queue.put(interaction_response)
                    return
                except Exception as e:
                    logger.error(e)
                    raise

            # NOTE: str type
            # TODO: clean when the proxy add structured logs for this error
            if message == "No backend servers available. Please try again later.":
                await self._available_response_messages_queue.put(
                    ErrorResponseMessage(
                        payload=ErrorResponse(
                            interaction_id=None,
                            code="NO_BACKEND_SERVER_AVAILABLE",
                            message=message,
                            timestamp=int(time.monotonic() * 1000),
                            details=None,
                        )
                    )
                )
                raise Exception(message)

            data = json.loads(message)
            msg_type = data.get("type")

            # Map message types to their corresponding classes
            message_types: Dict[str, Type[BaseModel]] = {
                "interactionResponse": OjinPersonaInteractionResponseMessage,
                "sessionReady": OjinPersonaSessionReadyMessage,
                "errorResponse": ErrorResponseMessage,
                "sessionPing": OjinPersonaSessionReadyPing,
            }

            if msg_type in message_types:
                msg_class = message_types[msg_type]
                # Convert the message data to the appropriate message class
                #logger.debug("Received message type %s", msg_type)
                if msg_type == "interactionResponse":
                    interaction_response = OjinPersonaInteractionResponseMessage(
                        interaction_id=data["interaction_id"],
                        video_frame_bytes=data["payload"],
                        index=data["index"],
                        is_final_response=data["is_final_response"],
                    )
                    await self._available_response_messages_queue.put(interaction_response)
                    return

                if msg_type == "sessionReady":
                    session_ready = OjinPersonaSessionReadyMessage(
                        parameters=data["payload"]["parameters"],
                    )
                    self._inference_server_ready = True
                    await self._available_response_messages_queue.put(session_ready)
                    return

                msg = msg_class(**data)
                await self._available_response_messages_queue.put(msg)

                if isinstance(msg, ErrorResponseMessage):
                    raise RuntimeError(f"Error in Inference Server received: {msg}")

                if isinstance(msg, OjinPersonaSessionReadyPing):
                    logger.debug("Discarding Session Ready ping: %s", msg)
                    pass
                
                logger.info("Received message: %s", msg)
            else:
                logger.warning("Unknown message type: %s", msg_type)

        except Exception as e:
            logger.exception("Error handling message: %s", e)
            raise Exception(e) from e

    async def start_interaction(self):
        # TODO(mouad): do we need to do this
        while not self._available_response_messages_queue.empty():
            await self._available_response_messages_queue.get()

    async def send_message(self, message: BaseModel) -> None:
        """Send a message to the OJIN Persona service.

        Args:
            message: The message to send

        Raises:
            ConnectionError: If not connected to the WebSocket

        """
        if not self._ws or not self._running:
            raise ConnectionError("Not connected to OJIN Persona service")

        if self._inference_server_ready is not True:
            raise ConnectionError("Infernece Server is not ready to receive messsages")

        if isinstance(message, OjinPersonaCancelInteractionMessage):
            logger.info("Interrupt")
            
            self._cancelled = True
            cancel_input = CancelInteractionMessage(
                    payload=message.to_proxy_message()
            )

            await self._ws.send(cancel_input.model_dump_json())

            try:
                while not self._available_response_messages_queue.empty():
                    self._available_response_messages_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass # do nothing, just stop processing

            self._cancelled = False

            return

        if isinstance(message, (
            OjinPersonaInteractionInputMessage, OjinPersonaEndInteractionMessage
        )):
            logger.info("InteractionMessage")
            await self._pending_client_messages_queue.put(message)
            return

        logger.error("The message %s is Unknown", message)
        error = ErrorResponseMessage(
                payload=ErrorResponse(
                    interaction_id=self._active_interaction_id,
                    code="UNKNOWN",
                    message="The message is Unknown",
                    timestamp=int(time.monotonic() * 1000),
                    details=None,
                )
        )
        raise Exception(error)

    async def _process_client_messages(self) -> None:
        while self._running:
            if self._cancelled:
                continue

            if self._ws is None:
                logger.debug("[_process_messages:] no websocket connection.")
                await asyncio.sleep(1.0)
                continue

            message: OjinPersonaMessage = await self._pending_client_messages_queue.get()
            if isinstance(message, OjinPersonaInteractionInputMessage):
                max_chunk_size = 1024 * 500
                audio_chunks = [
                    message.audio_int16_bytes[i : i + max_chunk_size]
                    for i in range(0, len(message.audio_int16_bytes), max_chunk_size)
                ]
                logger.info(
                    "Split audio into %d chunks of max %d bytes",
                    len(audio_chunks), max_chunk_size
                )

                # NOTE(mouad): make sure we handle the case where the input is empty
                if len(audio_chunks) == 0:
                    audio_chunks.append(bytes())

                for _, chunk in enumerate(audio_chunks):
                    interaction_input = InteractionInput(
                        payload_type="audio",
                        payload=chunk,
                        timestamp=int(time.monotonic() * 1000),
                        params=message.params
                    )
                    proxy_message = InteractionInputMessage(payload=interaction_input)

                    await self._ws.send(proxy_message.to_bytes())
            elif isinstance(message, OjinPersonaEndInteractionMessage):
                end_interaction_message = message.to_proxy_message()
                await self._ws.send(end_interaction_message.model_dump_json())


    async def receive_message(self) -> BaseModel | None:
        """Receive the next message from the OJIN Persona service.

        Returns:
            The next available message

        Raises:
            asyncio.QueueEmpty: If no messages are available

        """
        if self._cancelled:
            return None
        return await self._available_response_messages_queue.get()

    def is_connected(self) -> bool:
        """Check if the client is connected to the WebSocket."""
        return (self._running and self._ws is not None and 
            self._ws.state == websockets.State.OPEN)
