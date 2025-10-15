import logging
import traceback

from azure.eventhub import EventData, EventDataBatch, TransportType
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub.exceptions import (
    AuthenticationError,
    ClientClosedError,
    ConnectError,
    ConnectionLostError,
    EventHubError,
)
from azure.identity.aio import DefaultAzureCredential

from aio_azure_clients_toolbox import connection_pooling

from .types import CredentialFactory

TRANSPORT_PURE_AMQP = "amqp"
EVENTHUB_SEND_TTL_SECONDS = 220
logger = logging.getLogger(__name__)


class Eventhub:
    __slots__ = [
        "credential",
        "evhub_name",
        "evhub_namespace",
        "_client",
        "transport_type",
    ]

    def __init__(
        self,
        eventhub_namespace: str,
        eventhub_name: str,
        credential: DefaultAzureCredential,
        eventhub_transport_type: str = TRANSPORT_PURE_AMQP,
    ):
        self.evhub_namespace = eventhub_namespace
        self.evhub_name = eventhub_name
        self.credential = credential
        self.transport_type = (
            {}
            if eventhub_transport_type == TRANSPORT_PURE_AMQP
            else {"transport_type": TransportType.AmqpOverWebsocket}
        )
        self._client: EventHubProducerClient | None = self.get_client()

    def __getattr__(self, name):
        return getattr(self._client, name)

    def get_client(self) -> EventHubProducerClient:
        return EventHubProducerClient(
            fully_qualified_namespace=self.evhub_namespace,
            eventhub_name=self.evhub_name,
            credential=self.credential,
            **self.transport_type,
        )

    @property
    def client(self) -> EventHubProducerClient:
        if self._client is None:
            self._client = self.get_client()
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.close()
            self._client = None
        try:
            await self.credential.close()
        except Exception as exc:
            logger.exception(f"Eventhub credential close failed with {exc}")

    async def send_event_data(
        self,
        event: EventData,
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Send a *single* EventHub event which is already encoded as `EventData`.

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        # Create a batch.
        event_data_batch: EventDataBatch = await self.client.create_batch(partition_key=partition_key)

        # Add events to the batch.
        event_data_batch.add(event)

        # Send the batch of events to the event hub.
        await self.client.send_batch(event_data_batch)

        return event_data_batch

    async def send_event(
        self,
        event: bytes | str,
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Send a *single* EventHub event. See `send_events_batch` for
        sending multiple events

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        # Create a batch.
        event_data_batch: EventDataBatch = await self.client.create_batch(partition_key=partition_key)

        # Add events to the batch.
        event_data_batch.add(EventData(event))

        # Send the batch of events to the event hub.
        await self.client.send_batch(event_data_batch)

        return event_data_batch

    async def send_events_batch(
        self,
        events_list: list[bytes | str],
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Sending events in a batch is more performant than sending individual events.

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        # Create a batch.
        event_data_batch: EventDataBatch = await self.client.create_batch(partition_key=partition_key)

        # Add events to the batch.
        for event in events_list:
            event_data_batch.add(EventData(event))

        # Send the batch of events to the event hub.
        await self.client.send_batch(event_data_batch)
        return event_data_batch

    async def send_events_data_batch(
        self,
        event_data_batch: EventDataBatch,
    ) -> EventDataBatch:
        """
        Sending events in a batch is more performant than sending individual events.
        """
        # Send the batch of events to the event hub.
        await self.client.send_batch(event_data_batch)
        return event_data_batch


class ManagedAzureEventhubProducer(connection_pooling.AbstractorConnector):
    """Azure Eventhub Producer client with connnection pooling built in.

    Args:
      eventhub_namespace:
        String representing the Eventhub namespace.
      eventhub_name:
        Eventhub name (the "topic").
      credential_factory:
        A callable that returns an async DefaultAzureCredential which may be used to authenticate to the container.
      client_limit:
        Client limit per connection (default: 100).
      max_size:
        Connection pool size (default: 10).
      max_idle_seconds:
        Maximum duration allowed for an idle connection before recycling it.
      max_lifespan_seconds:
        Optional setting which controls how long a connection lives before recycling.
      pool_connection_create_timeout:
        Timeout for creating a connection in the pool (default: 10 seconds).
      pool_get_timeout:
        Timeout for getting a connection from the pool (default: 60 seconds).
      ready_message:
        A string, bytes, or EventData object representing the first "ready" message sent to establish connection.
    """

    def __init__(
        self,
        eventhub_namespace: str,
        eventhub_name: str,
        credential_factory: CredentialFactory,
        eventhub_transport_type: str = TRANSPORT_PURE_AMQP,
        client_limit: int = connection_pooling.DEFAULT_SHARED_TRANSPORT_CLIENT_LIMIT,
        max_size: int = connection_pooling.DEFAULT_MAX_SIZE,
        max_idle_seconds: int = EVENTHUB_SEND_TTL_SECONDS,
        ready_message: str | bytes | EventData = "Connection established",
        max_lifespan_seconds: int | None = None,
        pool_connection_create_timeout: int = 10,
        pool_get_timeout: int = 60,
    ):
        self.eventhub_namespace = eventhub_namespace
        self.eventhub_name = eventhub_name
        self.eventhub_transport_type = eventhub_transport_type
        if not callable(credential_factory):
            raise ValueError(
                "credential_factory must be a callable returning a credential"
            )
        self.credential_factory = credential_factory
        self.pool = connection_pooling.ConnectionPool(
            self,
            client_limit=client_limit,
            max_size=max_size,
            max_idle_seconds=max_idle_seconds,
            max_lifespan_seconds=max_lifespan_seconds,
        )
        if not isinstance(ready_message, (str, bytes, EventData)):
            raise ValueError("ready_message must be a string, bytes, or EventData")
        self.ready_message = ready_message

        self.pool_kwargs = {
            "timeout": pool_get_timeout,
            "acquire_timeout": pool_connection_create_timeout,
        }

    async def create(self) -> Eventhub:
        """Creates a new connection for our pool"""
        return Eventhub(
            self.eventhub_namespace,
            self.eventhub_name,
            self.credential_factory(),
            eventhub_transport_type=self.eventhub_transport_type,
        )

    async def close(self):
        """Closes all connections in our pool"""
        await self.pool.closeall()

    @connection_pooling.send_time_deco(logger, "Eventhub.ready")
    async def ready(self, conn: Eventhub) -> bool:
        """Establishes readiness for a new connection"""
        # Create a batch.
        event_data_batch: EventDataBatch = await conn.create_batch()
        # Prepare ready message as an event
        if isinstance(self.ready_message, EventData):
            event_data_batch.add(self.ready_message)
        else:
            event_data_batch.add(EventData(self.ready_message))
        attempts = 2

        while attempts > 0:
            try:
                # Send the batch of events to the event hub.
                await conn.send_batch(event_data_batch)
                return True
            except AuthenticationError:
                logger.warning("Eventhub readiness check failed due to authentication error. Cancelling.")
                logger.error(f"{traceback.format_exc()}")
                return False
            except EventHubError:
                logger.warning(f"Eventhub readiness check #{3 - attempts} failed; trying again.")
                logger.error(f"{traceback.format_exc()}")
                attempts -= 1

        logger.error("Eventhub readiness check failed. Not ready.")
        return False

    @connection_pooling.send_time_deco(logger, "Eventhub.send_event_data")
    async def send_event_data(
        self,
        event: EventData,
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Send a *single* EventHub event which is already encoded as `EventData`.

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        async with self.pool.get(**self.pool_kwargs) as conn:
            # Create a batch.
            event_data_batch: EventDataBatch = await conn.create_batch(partition_key=partition_key)

            # Add events to the batch.
            event_data_batch.add(event)

            logger.debug("Sending eventhub batch")
            # Send the batch of events to the event hub.
            try:
                await conn.send_batch(event_data_batch)
                return event_data_batch
            except (AuthenticationError, ClientClosedError, ConnectionLostError, ConnectError):
                logger.error(f"Error sending event: {event}")
                logger.error(f"{traceback.format_exc()}")
                # Mark this connection closed so it won't be reused
                await self.pool.expire_conn(conn)
                raise

    @connection_pooling.send_time_deco(logger, "Eventhub.send_event")
    async def send_event(
        self,
        event: bytes | str,
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Send a *single* EventHub event. See `send_events_batch` for
        sending multiple events

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        async with self.pool.get(**self.pool_kwargs) as conn:
            # Create a batch.
            event_data_batch: EventDataBatch = await conn.create_batch(partition_key=partition_key)

            # Add events to the batch.
            event_data_batch.add(EventData(event))

            logger.debug("Sending eventhub batch")

            try:
                # Send the batch of events to the event hub.
                await conn.send_batch(event_data_batch)
            except (AuthenticationError, ClientClosedError, ConnectionLostError, ConnectError):
                logger.error(f"Error sending event: {event}")
                logger.error(f"{traceback.format_exc()}")
                # Mark this connection closed so it won't be reused
                await self.pool.expire_conn(conn)
                raise
            return event_data_batch

    @connection_pooling.send_time_deco(logger, "Eventhub.send_events_batch")
    async def send_events_batch(
        self,
        events_list: list[bytes | str],
        partition_key: str | None = None,
    ) -> EventDataBatch:
        """
        Sending events in a batch is more performant than sending individual events.

        `partition_key` will make a particular string identifier
        "sticky" for a particular partition.

        For instance, if you use a Salesforce record identifier as the `partition_key`
        then you can ensure that a _particular consumer_ always receives _those_ events.
        """
        async with self.pool.get(**self.pool_kwargs) as conn:
            # Create a batch.
            event_data_batch: EventDataBatch = await conn.create_batch(partition_key=partition_key)

            # Add events to the batch.
            for event in events_list:
                event_data_batch.add(EventData(event))

            logger.debug("Sending eventhub batch")
            # Send the batch of events to the event hub.
            try:
                await conn.send_batch(event_data_batch)
                return event_data_batch
            except (AuthenticationError, ClientClosedError, ConnectionLostError, ConnectError):
                logger.error(f"Error sending event: {traceback.format_exc()}")
                # Mark this connection closed so it won't be reused
                await self.pool.expire_conn(conn)
                raise

    @connection_pooling.send_time_deco(logger, "Eventhub.send_events_data_batch")
    async def send_events_data_batch(
        self,
        event_data_batch: EventDataBatch,
    ) -> EventDataBatch:
        """
        Sending events in a batch is more performant than sending individual events.
        """
        async with self.pool.get(**self.pool_kwargs) as conn:
            logger.debug("Sending eventhub batch")
            # Send the batch of events to the event hub.
            try:
                await conn.send_batch(event_data_batch)
                return event_data_batch
            except (AuthenticationError, ClientClosedError, ConnectionLostError, ConnectError):
                logger.error(f"Error sending batch {traceback.format_exc()}")
                # Mark this connection closed so it won't be reused
                await self.pool.expire_conn(conn)
                raise
