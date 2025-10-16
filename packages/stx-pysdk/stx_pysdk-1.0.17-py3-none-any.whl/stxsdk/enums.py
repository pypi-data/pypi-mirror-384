from enum import Enum


class RootType(Enum):
    MUTATION = "RootMutationType"
    QUERY = "RootQueryType"


class Channels(Enum):
    PORTFOLIO = "portfolio"
    MARKET_INFO = "market_info"
    ACTIVE_TRADES = "active_trades"
    ACTIVE_ORDERS = "active_orders"
    ACTIVE_SETTLEMENTS = "active_settlements"
    ACTIVE_POSITIONS = "active_positions"
    USER_INFO = "user_info"
    PHONEIX = "phoenix"


class ChannelEvents(Enum):
    CLOSE = "phx_close"
    ERROR = "phx_error"
    JOIN = "phx_join"
    REPLY = "phx_reply"
    LEAVE = "phx_leave"
    HEARTBEAT = "heartbeat"
