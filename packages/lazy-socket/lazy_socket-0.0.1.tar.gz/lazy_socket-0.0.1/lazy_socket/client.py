import socket
import asyncio
import websockets
import threading
import logging
from queue import Queue
from websockets.exceptions import ConnectionClosed
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

logger = logging.getLogger("LazyClient")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | [%(name)s] | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class LazyListener(ServiceListener):

    def __init__(self, client):
        self.client = client
        self.service = None

    def update_service(self, zc, type_, name):
        pass

    def remove_service(self, zc, type_, name):
        if self.service and self.service["name"] == name:
            self.service = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if self.service:
            return


        info = zc.get_service_info(type_, name)
        properties = {}
        address = None

        if info:
            # Extract IPv4 address
            address = socket.inet_ntoa(info.addresses[0])
            if info.properties:
                for key, value in info.properties.items():
                    decoded_key = key.decode("utf-8") if isinstance(key, bytes) else key
                    decoded_value = value.decode("utf-8") if isinstance(value, bytes) else value
                    properties[decoded_key] = decoded_value
        else:
            return


        if address:
            self.service = {
                "name": name,
                "address": address,
                "port": info.port,
                "properties": properties,
            }
            logger.info(f"(LazyListener) Discovered service: {name}")
            logger.info(f"    {self.service}")


class LazyClient:

    def __init__(self):
        self.service = None
        self.socket = None
        self.queue = Queue()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)

    def start(self):
        self.thread.start()

    def send(self, message):
        asyncio.run_coroutine_threadsafe(self._send(message), self.loop)

    def _start_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_listen())

    async def _find_service(self):
        zeroconf = Zeroconf()
        listener = LazyListener(self)
        ServiceBrowser(zeroconf, "_lazy._tcp.local.", listener)
        while True:
            logger.info("Searching for service...")
            if listener.service:
                self.service = listener.service
                logger.info(f"Service found: {self.service}")
                zeroconf.close()
                return
            await asyncio.sleep(1)

    async def _connect(self, reconnect=True):
        if reconnect:
            logger.info("Reconnecting to service...")
            self.queue.put("lazy_client:reconnecting")
        else:
            logger.info("Connecting to service...")
            self.queue.put("lazy_client:connecting")

        if not self.service:
            logger.warning("No service to connect to.")
            return

        uri = f"ws://{self.service['address']}:{self.service['port']}"
        try:
            self.socket = await websockets.connect(uri)
            logger.info(f"Connected to {uri}")
            self.queue.put(f"lazy_client:connected:{uri}")
        except Exception as e:
            logger.error(f"Failed to connect to {uri}: {e}")

    async def _close(self):
        if self.socket:
            logger.info("Closing socket connection")
            await self.socket.close()

    async def _connect_and_listen(self):
        await self._find_service()
        if self.service:
            await self._connect(reconnect=False)

        while True:
            try:
                response = await self.socket.recv()
                logger.info(f"Received message: {response}")
                self.queue.put(response)
            except ConnectionClosed:
                await self._connect()
            except Exception as e:
                logger.error(f"Error during receive: {e}")
                await asyncio.sleep(5)

    async def _send(self, message):
        try:
            await self.socket.send(message)
        except ConnectionClosed:
            await self._connect()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.queue.put(f"lazy_client:error:send:{e}")


if __name__ == "__main__":
    client = LazyClient()
    try:
        asyncio.run(client._connect_and_listen())
    except KeyboardInterrupt:
        print("Shutting down client...")
    finally:
        asyncio.run(client._close())
