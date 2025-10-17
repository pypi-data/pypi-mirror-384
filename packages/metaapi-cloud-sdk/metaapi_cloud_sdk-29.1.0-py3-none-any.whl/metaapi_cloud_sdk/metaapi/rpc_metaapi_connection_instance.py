import asyncio
from datetime import datetime
from typing import Coroutine, List, TypedDict

from .metaapi_connection_instance import MetaApiConnectionInstance
from .models import (
    MetatraderSymbolSpecification,
    MetatraderAccountInformation,
    MetatraderPosition,
    MetatraderOrder,
    MetatraderHistoryOrders,
    MetatraderDeals,
    MetatraderSymbolPrice,
    MetatraderCandle,
    MetatraderTick,
    MetatraderBook,
    ServerTime,
    GetAccountInformationOptions,
    GetPositionsOptions,
    GetPositionOptions,
    GetOrdersOptions,
    GetOrderOptions,
)
from .rpc_metaapi_connection import RpcMetaApiConnection
from ..clients.metaapi.metaapi_websocket_client import MetaApiWebsocketClient
from ..logger import LoggerManager


class RpcMetaApiConnectionDict(TypedDict, total=False):
    instanceIndex: int
    synchronized: bool
    disconnected: bool


class RpcMetaApiConnectionInstance(MetaApiConnectionInstance):
    """Exposes MetaApi MetaTrader RPC API connection instance to consumers."""

    def __init__(self, websocket_client: MetaApiWebsocketClient, meta_api_connection: RpcMetaApiConnection):
        """Initializes MetaApi MetaTrader RPC Api connection instance.

        Args:
            websocket_client: MetaApi websocket client.
            meta_api_connection: RPC MetaApi connection.
        """
        super().__init__(websocket_client, meta_api_connection)
        self._meta_api_connection = meta_api_connection
        self._logger = LoggerManager.get_logger('RpcMetaApiConnectionInstance')

    async def connect(self):
        """Opens the connection. Can only be called the first time, next calls will be ignored.

        Returns:
            A coroutine resolving when the connection is opened
        """
        if self._closed:
            raise Exception('This connection has been closed, please create a new connection')
        if not self._opened:
            self._opened = True
            await self._meta_api_connection.connect(self.instance_id)

    async def close(self):
        """Closes the connection. The instance of the class should no longer be used after this method is invoked."""
        if not self._closed:
            asyncio.create_task(self._meta_api_connection.close(self.instance_id))
            self._closed = True

    def get_account_information(
        self, options: GetAccountInformationOptions = None
    ) -> 'Coroutine[asyncio.Future[MetatraderAccountInformation]]':
        """Returns account information.

        Args:
            options: Additional request options.

        Returns:
            A coroutine resolving with account information.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_account_information(self._meta_api_connection.account.id, options)

    def get_positions(
        self, options: GetPositionsOptions = None
    ) -> 'Coroutine[asyncio.Future[List[MetatraderPosition]]]':
        """Returns positions.

        Args:
            options: Additional request options.

        Returns:
            A coroutine resolving with array of open positions.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_positions(self._meta_api_connection.account.id, options)

    def get_position(
        self, position_id: str, options: GetPositionOptions = None
    ) -> 'Coroutine[asyncio.Future[MetatraderPosition]]':
        """Returns specific position.

        Args:
            position_id: Position id.
            options: Additional request options.

        Returns:
            A coroutine resolving with MetaTrader position found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_position(self._meta_api_connection.account.id, position_id, options)

    def get_orders(self, options: GetOrdersOptions = None) -> 'Coroutine[asyncio.Future[List[MetatraderOrder]]]':
        """Returns open orders.

        Args:
            options: Additional request options.

        Returns:
            A coroutine resolving with open MetaTrader orders.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_orders(self._meta_api_connection.account.id, options)

    def get_order(self, order_id: str, options: GetOrderOptions = None) -> 'Coroutine[asyncio.Future[MetatraderOrder]]':
        """Returns specific open order.

        Args:
            order_id: Order id (ticket number).
            options: Additional request options.

        Returns:
            A coroutine resolving with metatrader order found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_order(self._meta_api_connection.account.id, order_id, options)

    def get_history_orders_by_ticket(self, ticket: str) -> 'Coroutine[MetatraderHistoryOrders]':
        """Returns the history of completed orders for a specific ticket number.

        Args:
            ticket: Ticket number (order id).

        Returns:
            A coroutine resolving with request results containing history orders found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_history_orders_by_ticket(self._meta_api_connection.account.id, ticket)

    def get_history_orders_by_position(self, position_id: str) -> 'Coroutine[MetatraderHistoryOrders]':
        """Returns the history of completed orders for a specific position id.

        Args:
            position_id: Position id.

        Returns:
            A coroutine resolving with request results containing history orders found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_history_orders_by_position(self._meta_api_connection.account.id, position_id)

    def get_history_orders_by_time_range(
        self, start_time: datetime, end_time: datetime, offset: int = 0, limit: int = 1000
    ) -> 'Coroutine[MetatraderHistoryOrders]':
        """Returns the history of completed orders for a specific time range.

        Args:
            start_time: Start of time range, inclusive.
            end_time: End of time range, exclusive.
            offset: Pagination offset, default is 0.
            limit: Pagination limit, default is 1000.

        Returns:
            A coroutine resolving with request results containing history orders found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_history_orders_by_time_range(
            self._meta_api_connection.account.id, start_time, end_time, offset, limit
        )

    def get_deals_by_ticket(self, ticket: str) -> 'Coroutine[MetatraderDeals]':
        """Returns history deals with a specific ticket number.

        Args:
            ticket: Ticket number (deal id for MT5 or order id for MT4).

        Returns:
            A coroutine resolving with request results containing deals found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_deals_by_ticket(self._meta_api_connection.account.id, ticket)

    def get_deals_by_position(self, position_id) -> 'Coroutine[MetatraderDeals]':
        """Returns history deals for a specific position id.

        Args:
            position_id: Position id.

        Returns:
            A coroutine resolving with request results containing deals found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_deals_by_position(self._meta_api_connection.account.id, position_id)

    def get_deals_by_time_range(
        self, start_time: datetime, end_time: datetime, offset: int = 0, limit: int = 1000
    ) -> 'Coroutine[MetatraderDeals]':
        """Returns history deals with for a specific time range.

        Args:
            start_time: Start of time range, inclusive.
            end_time: End of time range, exclusive.
            offset: Pagination offset, default is 0.
            limit: Pagination limit, default is 1000.

        Returns:
            A coroutine resolving with request results containing deals found.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_deals_by_time_range(
            self._meta_api_connection.account.id, start_time, end_time, offset, limit
        )

    def get_symbols(self) -> 'Coroutine[asyncio.Future[List[str]]]':
        """Retrieves available symbols for an account.

        Returns:
            A coroutine which resolves when symbols are retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_symbols(self._meta_api_connection.account.id)

    def get_symbol_specification(self, symbol: str) -> 'Coroutine[asyncio.Future[MetatraderSymbolSpecification]]':
        """Retrieves specification for a symbol.

        Args:
            symbol: Symbol to retrieve specification for.

        Returns:
            A coroutine which resolves when specification MetatraderSymbolSpecification is retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_symbol_specification(self._meta_api_connection.account.id, symbol)

    def get_symbol_price(
        self, symbol: str, keep_subscription: bool = False
    ) -> 'Coroutine[asyncio.Future[MetatraderSymbolPrice]]':
        """Retrieves latest price for a symbol.

        Args:
            symbol: Symbol to retrieve price for.
            keep_subscription: if set to true, the account will get a long-term subscription to symbol market data.
            Long-term subscription means that on subsequent calls you will get updated value faster. If set to false or
            not set, the subscription will be set to expire in 12 minutes.

        Returns:
            A coroutine which resolves when price MetatraderSymbolPrice is retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_symbol_price(self._meta_api_connection.account.id, symbol, keep_subscription)

    def get_candle(
        self, symbol: str, timeframe: str, keep_subscription: bool = False
    ) -> 'Coroutine[asyncio.Future[MetatraderCandle]]':
        """Retrieves latest candle for a symbol and timeframe.

        Args:
            symbol: Symbol to retrieve candle for.
            timeframe: Defines the timeframe according to which the candle must be generated. Allowed values for
            MT5 are 1m, 2m, 3m, 4m, 5m, 6m, 10m, 12m, 15m, 20m, 30m, 1h, 2h, 3h, 4h, 6h, 8h, 12h, 1d, 1w, 1mn.
            Allowed values for MT4 are 1m, 5m, 15m 30m, 1h, 4h, 1d, 1w, 1mn.
            keep_subscription: if set to true, the account will get a long-term subscription to symbol market data.
            Long-term subscription means that on subsequent calls you will get updated value faster. If set to false or
            not set, the subscription will be set to expire in 12 minutes.

        Returns:
            A coroutine which resolves when candle is retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_candle(
            self._meta_api_connection.account.id, symbol, timeframe, keep_subscription
        )

    def get_tick(self, symbol: str, keep_subscription: bool = False) -> 'Coroutine[asyncio.Future[MetatraderTick]]':
        """Retrieves latest tick for a symbol. MT4 G1 accounts do not support this API.

        Args:
            symbol: Symbol to retrieve tick for.
            keep_subscription: if set to true, the account will get a long-term subscription to symbol market data.
            Long-term subscription means that on subsequent calls you will get updated value faster. If set to false or
            not set, the subscription will be set to expire in 12 minutes.

        Returns:
            A coroutine which resolves when tick is retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_tick(self._meta_api_connection.account.id, symbol, keep_subscription)

    def get_book(self, symbol: str, keep_subscription: bool = False) -> 'Coroutine[asyncio.Future[MetatraderBook]]':
        """Retrieves latest order book for a symbol. MT4 G1 accounts do not support this API.

        Args:
            symbol: Symbol to retrieve order book for.
            keep_subscription: if set to true, the account will get a long-term subscription to symbol market data.
            Long-term subscription means that on subsequent calls you will get updated value faster. If set to false or
            not set, the subscription will be set to expire in 12 minutes.

        Returns:
            A coroutine which resolves when order book is retrieved.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_book(self._meta_api_connection.account.id, symbol, keep_subscription)

    def get_server_time(self) -> 'Coroutine[asyncio.Future[ServerTime]]':
        """Returns server time for a specified MetaTrader account.

        Returns:
            A coroutine resolving with server time.
        """
        self._check_is_connection_active()
        return self._websocket_client.get_server_time(self._meta_api_connection.account.id)

    async def wait_synchronized(self, timeout_in_seconds: float = 300):
        """Waits until synchronization to RPC application is completed.

        Args:
            timeout_in_seconds: Timeout for synchronization.

        Returns:
            A coroutine which resolves when synchronization to RPC application is completed.

        Raises:
            TimeoutException: If application failed to synchronize with the terminal within timeout allowed.
        """
        self._check_is_connection_active()
        return await self._meta_api_connection.wait_synchronized(timeout_in_seconds)
