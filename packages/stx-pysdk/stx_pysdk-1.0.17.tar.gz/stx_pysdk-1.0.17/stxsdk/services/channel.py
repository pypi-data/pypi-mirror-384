import json
import logging
from typing import Optional, Callable

import websockets

from stxsdk.config.configs import Configs
from stxsdk.typings import ChannelMessage

logger = logging.getLogger(__name__)


class Channel:
    def __init__(self, client, channel_command: str):
        """
        :param channel_command: The command that will be sent to the server to request a channel
        """
        self.client = client
        self.user = client.user
        self.raw_channel_command = channel_command

    @property
    def socket_url(self):
        return Configs.CHANNEL_CONNECTION_URL.format(
            url=self.client.url, token=self.user.token
        )

    @property
    def channel_command(self):
        return self.raw_channel_command.replace("user_uid", self.user.uid)

    async def event_default_consumer(self, message):
        """
        This is default consumer function that will be called if neither event nor default
        function is provided to the handler
        """
        logger.info(  # pylint: disable=W1203
            f"Websocket responded with message: {message}"
        )

    async def channel_handler(
        self,
        *,
        on_open: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        default: Optional[Callable] = None,
    ):
        """
        It connects to a websocket, sends a command, and then waits for a response
        :param on_open:    a consumer function that will be trigger when connect with the channel
        :param on_message: a consumer function that will be trigger when server send the message
        :param on_close:   a consumer function that will be trigger when the server connection
                            timeout or close
        :param on_error:   a consumer function that will be trigger on any error response or exception
        :param default:    a consumer function that will be trigger if the specific event function
                           is not provided then this function runs
        """
        try:
            # starts the websocket connection with the server
            async with websockets.connect(self.socket_url) as websocket:
                # send the channel command to the server to get the messages
                await websocket.send(self.channel_command)
                # it handles the messages send by the channel
                await self.__message_handler(
                    websocket,
                    on_open=on_open,
                    on_message=on_message,
                    on_close=on_close,
                    on_error=on_error,
                    default=default,
                )
        except Exception as exc:
            # consumer function precedence
            #    event function > provided default function > channel objects predefined function
            consumer = on_error or default or self.event_default_consumer
            await consumer(
                ChannelMessage(
                    closed=True,
                    message_received=False,
                    message=str(exc),
                    data=None,
                )
            )

    async def __load_message(self, message):
        # parse the json message to the pythonic data structure
        return json.loads(message)

    async def __message_handler(
        self,
        websocket,
        *,
        on_open: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        default: Optional[Callable] = None,
    ):
        """
        It takes a websocket and a consumer function as arguments, and then it asynchronously loops
        through the messages received from the websocket, and passes the data to consumer function
        :param websocket: The websocket object that is returned from the websocket.connect() method
        :param on_open:    a consumer function that will be trigger when connect with the channel
        :param on_message: a consumer function that will be trigger when server send the message
        :param on_close:   a consumer function that will be trigger when the server connection
                            timeout or close
        :param on_error:   a consumer function that will be trigger on any error response or exception
        :param default:    a consumer function that will be trigger if the specific event function
                           is not provided then this function runs
        """
        try:
            async for message in websocket:
                data_object = await self.__load_message(message)
                # if the server send message with type phx_reply, means the joining message
                if data_object[3] == "phx_reply":
                    consumer, msg = on_open, "Connection Initiated"
                else:
                    consumer, msg = on_message, "Message received"
                consumer = consumer or default or self.event_default_consumer
                await consumer(
                    ChannelMessage(
                        closed=False,
                        message_received=True,
                        message=msg,
                        data=data_object,
                    )
                )
        except websockets.ConnectionClosed:
            # if the channels connection get closed
            consumer = on_close or default or self.event_default_consumer
            await consumer(
                ChannelMessage(
                    closed=True,
                    message_received=False,
                    message="Connection Terminated",
                    data=None,
                )
            )
        except Exception as exc:
            # if any general exception occurs or server responded with error
            consumer = on_error or default or self.event_default_consumer
            await consumer(
                ChannelMessage(
                    closed=True,
                    message_received=False,
                    message=str(exc),
                    data=None,
                )
            )
