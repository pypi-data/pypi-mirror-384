# pylint: disable=C0301
from stxsdk.enums import ChannelEvents, Channels

# This is collection of all the available channels with their available operations and commands

CHANNELS = {
    Channels.PORTFOLIO.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.PORTFOLIO.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.MARKET_INFO.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.MARKET_INFO.value}", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.ACTIVE_TRADES.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.ACTIVE_TRADES.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.ACTIVE_ORDERS.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.ACTIVE_ORDERS.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.ACTIVE_SETTLEMENTS.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.ACTIVE_SETTLEMENTS.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.ACTIVE_POSITIONS.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.ACTIVE_POSITIONS.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
    Channels.USER_INFO.value: {
        "operations": {
            "join": f'["3", "3", "{Channels.USER_INFO.value}:user_uid", "{ChannelEvents.JOIN.value}", ""]'
        },
    },
}
