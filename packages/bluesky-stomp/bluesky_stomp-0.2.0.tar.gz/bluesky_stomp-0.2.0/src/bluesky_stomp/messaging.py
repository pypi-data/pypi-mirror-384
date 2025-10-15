import itertools
import logging
import time
import uuid
from collections.abc import Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from threading import Event
from typing import Any, TypeVar, cast

from observability_utils.tracing import (  # type: ignore
    add_span_attributes,
    get_tracer,
    propagate_context_in_stomp_headers,
    retrieve_context_from_stomp_headers,
)
from opentelemetry.trace import SpanKind
from stomp.connect import ConnectionListener  # type: ignore
from stomp.connect import StompConnection11 as Connection  # type: ignore
from stomp.exception import ConnectFailedException  # type: ignore
from stomp.utils import Frame  # type: ignore

from .models import (
    BasicAuthentication,
    Broker,
    DestinationBase,
    MessageQueue,
    MessageTopic,
    ReplyMessageQueue,
    TemporaryMessageQueue,
)
from .serdes import (
    MessageDeserializer,
    MessageSerializer,
    deserialize_message,
    determine_callback_deserialization_type,
    serialize_message,
)
from .utils import handle_all_exceptions

CORRELATION_ID_HEADER = "correlation-id"

T = TypeVar("T")


@dataclass
class MessageContext:
    """
    Context that comes with a message, provides useful information such as how to reply
    """

    destination: DestinationBase
    reply_destination: DestinationBase | None
    correlation_id: str | None


MessageListener = Callable[[Any, MessageContext], None]
ErrorListener = Callable[[Exception], None]


@dataclass
class StompReconnectPolicy:
    """
    Details of how often stomp will try to reconnect if connection is unexpectedly lost
    """

    initial_delay: float = 0.0
    attempt_period: float = 10.0


@dataclass
class _Subscription:
    """
    Details of a subscription, the client needs its own representation to
    defer subscriptions until after connection
    """

    destination: DestinationBase
    callback: Callable[[Frame], None]
    on_error: ErrorListener | None


class StompClient:
    """
    Utility class with helper methods for communication with a STOMP
    broker such as ActiveMQ or RabbitMQ.
    """

    def __init__(
        self,
        conn: Connection,
        reconnect_policy: StompReconnectPolicy | None = None,
        authentication: BasicAuthentication | None = None,
        serializer: MessageSerializer = serialize_message,
        deserializer: MessageDeserializer[Any] = deserialize_message,
    ) -> None:
        """
        Constructor

        Args:
            conn: STOMP connection object
            reconnect_policy: Policy for how to handle unexpected disconnection.
            Defaults to the default settings of StompReconnectPolicy.
            authentication: Authentication credentials, if required. Defaults to None.
            serializer: Function to serialize messages to send to the broker.
            Defaults to serialize_message.
            deserializer: Function to deserialize messages from the broker.
            Defaults to deserialize_message.
        """

        self._conn = conn
        self._reconnect_policy = reconnect_policy or StompReconnectPolicy()
        self._authentication = authentication or None
        self._serializer = serializer
        self._deserializer = deserializer

        self._sub_num = itertools.count()
        self._listener = ConnectionListener()

        self._listener.on_message = self._on_message
        self._conn.set_listener("", self._listener)  # type: ignore

        self._subscriptions: dict[str, _Subscription] = {}
        self.tracer = get_tracer("bluesky-stomp")

    @classmethod
    def for_broker(cls, broker: Broker) -> "StompClient":
        """
        Alternative constructor that sets up a connection from host details

        Args:
            broker: Details of the message broker

        Returns:
            StompClient: A new client
        """

        return cls(
            Connection(
                [(broker.host, broker.port)],
                auto_content_length=False,
            ),
            authentication=broker.auth,
        )

    def send_and_receive(
        self,
        destination: DestinationBase,
        obj: Any,
        reply_type: type[T] = str,
        correlation_id: str | None = None,
    ) -> Future[T]:
        """
        Send a message expecting a single reply.

        Args:
            destination: Destination to send the message
            obj: Message to send, must be serializable
            reply_type: Expected type of reply, used in deserialization.
            Defaults to str.
            correlation_id: An id which correlates this request with requests it
            spawns or the request which spawned it etc.
        Returns:
            Future[T]: Future representing the reply
        """
        with self.tracer.start_as_current_span(
            "send_and_receive",
            attributes={"destination": str(destination), "obj": str(obj)},
            kind=SpanKind.SERVER,
        ):
            future: Future[T] = Future()

            def callback(reply: T, _: MessageContext) -> None:
                future.set_result(reply)

            callback.__annotations__["reply"] = reply_type
            self.send(
                destination,
                obj,
                on_reply=callback,
                on_reply_error=future.set_exception,
                correlation_id=correlation_id,
            )
            return future

    def send(
        self,
        destination: DestinationBase,
        obj: Any,
        on_reply: MessageListener | None = None,
        on_reply_error: ErrorListener | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """
        Send a message to a given destination, handle a reply if required

        Args:
            destination: Where to send the message
            obj: Message content
            on_reply: Callback for a reply, if supplied, the broker will be asked
            to create a temporary queue for replies. Defaults to None.
            on_reply_error: How to handle any errors in processing replies.
            Defaults to None.
            correlation_id: Correlation ID to be optionally included in message
            headers. Defaults to None.
        """
        with self.tracer.start_as_current_span(
            "send",
            attributes={"destination": str(destination), "obj": str(obj)},
            kind=SpanKind.SERVER,
        ):
            raw_destination = _destination(destination)
            serialized_message = self._serializer(obj)
            self._send_bytes(
                raw_destination,
                serialized_message,
                on_reply,
                on_reply_error,
                correlation_id,
            )

    def _send_bytes(
        self,
        destination: str,
        message: bytes,
        on_reply: MessageListener | None = None,
        on_reply_error: ErrorListener | None = None,
        correlation_id: str | None = None,
    ) -> None:
        logging.debug(f"SENDING {message} to {destination}")
        with self.tracer.start_as_current_span(
            "_send_bytes",
            attributes={"destination": destination, "message": message},
            kind=SpanKind.SERVER,
        ):
            headers: dict[str, Any] = {"JMSType": "TextMessage"}

            if on_reply is not None:
                reply_queue = TemporaryMessageQueue(name=str(uuid.uuid1()))
                headers["reply-to"] = _destination(reply_queue)
                self.subscribe(
                    reply_queue,
                    on_reply,
                    on_error=on_reply_error,
                )
            if correlation_id:
                headers[CORRELATION_ID_HEADER] = correlation_id

            propagate_context_in_stomp_headers(headers)
            add_span_attributes({"headers": str(headers)})
            self._conn.send(headers=headers, body=message, destination=destination)  # type: ignore

    def listener(
        self,
        destination: DestinationBase,
        on_error: ErrorListener | None = None,
    ):
        """
        Decorator for subscribing to a MessageTopic:

        @my_app.listener("my-destination")
        def callback(context: MessageContext, message: ???) -> None:
            ...

        Args:
            destination (str): Destination to subscribe to
        """

        def decorator(callback: MessageListener) -> MessageListener:
            self.subscribe(
                destination,
                callback,
                on_error=on_error,
            )
            return callback

        return decorator

    def subscribe(
        self,
        destination: DestinationBase,
        callback: MessageListener,
        on_error: ErrorListener | None = None,
    ) -> str:
        """
        Subscribe to messages on a particular queue or topic

        Args:
            destination: Where the messages will come from
            callback: Function for processing the messages.
            The message type is derived from the function signature.
            on_error: How to handle errors processing the message. Defaults to None.

        Return:
            A unqiue identifier to pass to unsubscribe()
        """
        logging.debug(f"New subscription to {destination}")
        with self.tracer.start_as_current_span(
            "subscribe",
            attributes={"destination": str(destination), "callback": str(callback)},
            kind=SpanKind.SERVER,
        ):
            obj_type = determine_callback_deserialization_type(callback)

            def wrapper(frame: Frame) -> None:
                headers = frame.headers  # type: ignore
                headers = cast(Mapping[str, str], headers)
                body = frame.body  # type: ignore
                body = cast(str | bytes | bytearray, body)

                value = self._deserializer(body, obj_type)

                reply_to: str | None = headers.get("reply-to")
                context = MessageContext(
                    _destination_from_str(headers["destination"]),
                    _destination_from_str(reply_to) if reply_to is not None else None,
                    headers.get(CORRELATION_ID_HEADER),
                )

                callback(value, context)

            sub_id = (
                _destination(destination)
                if isinstance(destination, TemporaryMessageQueue)
                else str(next(self._sub_num))
            )
            self._subscriptions[sub_id] = _Subscription(
                destination, wrapper, on_error=on_error
            )
            # If we're connected, subscribe immediately, otherwise the subscription is
            # deferred until connection.
            self._ensure_subscribed([sub_id])

            return sub_id

    def unsubscribe(self, sub_id: str) -> None:
        if sub_id in self._subscriptions:
            logging.debug(f"Unsubscribing ID {sub_id}")
            if self._conn.is_connected():
                logging.debug("Connection is live, sending unsubscribe request")
                self._conn.unsubscribe(sub_id)  # type: ignore
            del self._subscriptions[
                sub_id
            ]  # Ensure that client won't re-subscribe upon re-connection
        else:
            logging.debug(f"No subscription for ID {sub_id}, nothing to do")

    def connect(self) -> None:
        """
        Connect to the broker, blocks until connection established
        """
        with self.tracer.start_as_current_span(
            "connect",
            kind=SpanKind.SERVER,
        ):
            add_span_attributes({"initial": self._conn.is_connected()})
            if not self._conn.is_connected():
                connected: Event = Event()

                def finished_connecting(frame: Frame) -> None:
                    connected.set()

                self._listener.on_connected = finished_connecting
                self._listener.on_disconnected = self._on_disconnected

                logging.info("Stomp client connecting...")

                self._connect_to_broker()
                connected.wait()

            self._ensure_subscribed()

            add_span_attributes({"success": self._conn.is_connected()})

    def _connect_to_broker(self) -> None:
        if self._authentication is not None:
            self._conn.connect(  # type: ignore
                username=self._authentication.username,
                passcode=self._authentication.password.get_secret_value(),
                wait=True,
            )
        else:
            self._conn.connect(wait=True)  # type: ignore

    def _ensure_subscribed(self, sub_ids: list[str] | None = None) -> None:
        # Subscription must happen AFTER connection. Because stomp literally
        # sends a SUB to the broker. But it still nice to be able to call SUBSCRIBE
        # on the client instance before it CONNECTS,
        # then just run the SUBSCRIBES after connection.
        if self._conn.is_connected():
            for sub_id in sub_ids or self._subscriptions.keys():
                sub = self._subscriptions[sub_id]
                logging.info(f"Stomp client subscribing to {sub.destination}")
                raw_destination = _destination(sub.destination)
                self._conn.subscribe(  # type: ignore
                    destination=raw_destination,
                    id=sub_id,
                    ack="auto",
                )

    def disconnect(self) -> None:
        """
        Disconnect from the broker
        """
        logging.info("Stomp client disconnecting...")
        with self.tracer.start_as_current_span(
            "disconnect",
            attributes={"initial": self.is_connected()},
            kind=SpanKind.SERVER,
        ):
            if not self.is_connected():
                logging.info("Already disconnected")
                add_span_attributes({"success": not self.is_connected()})
                return
            # We need to synchronise the disconnect on an event because the stomp
            # Connection object doesn't do it for us
            disconnected = Event()
            self._listener.on_disconnected = disconnected.set
            self._conn.disconnect()  # type: ignore
            disconnected.wait()

            add_span_attributes({"success": not self.is_connected()})

    @handle_all_exceptions
    def _on_disconnected(self) -> None:
        logging.warning(
            "Stomp connection lost, will attempt reconnection with "
            f"policy {self._reconnect_policy}"
        )
        time.sleep(self._reconnect_policy.initial_delay)
        while not self._conn.is_connected():
            try:
                self.connect()
            except ConnectFailedException:
                logging.exception("Reconnect failed")
            time.sleep(self._reconnect_policy.attempt_period)

    @handle_all_exceptions
    def _on_message(self, frame: Frame) -> None:
        logging.debug(f"Received {frame}")
        headers: Mapping[str, Any] = cast(
            Mapping[str, Any],
            frame.headers,  # type: ignore
        )

        trace_context = retrieve_context_from_stomp_headers(frame)  # type:ignore
        with self.tracer.start_as_current_span(
            "_on_message",
            context=trace_context,
            attributes={"frame": str(frame)},
        ):
            if (sub_id := headers.get("subscription")) is not None:
                if (sub := self._subscriptions.get(sub_id)) is not None:
                    try:
                        sub.callback(frame)
                    except Exception as ex:
                        if sub.on_error is not None:
                            sub.on_error(ex)
                        else:
                            raise ex
                else:
                    logging.warning(f"No subscription active for id: {sub_id}")
            else:
                logging.warning(f"No subscription ID in message headers: {headers}")

    def is_connected(self) -> bool:
        return self._conn.is_connected()  # type: ignore


def _destination(destination: DestinationBase) -> str:
    match destination:
        case MessageQueue(name=name):
            return f"/queue/{name}"
        case TemporaryMessageQueue(name=name):
            return f"/temp-queue/{name}"
        case ReplyMessageQueue(name=name):
            return f"/reply-queue/{name}"
        case MessageTopic(name=name):
            return f"/topic/{name}"
        case _:
            raise TypeError(f"Unrecognized destination type: {destination}")


def _destination_from_str(destination: str) -> DestinationBase:
    if destination.startswith("/"):
        _, destination_type, destination_name = destination.split("/")
        constructor = {
            "queue": MessageQueue,
            "temp-queue": TemporaryMessageQueue,
            "reply-queue": ReplyMessageQueue,
            "topic": MessageTopic,
        }[destination_type]
        return constructor(name=destination_name)
    else:
        return MessageQueue(name=destination)
