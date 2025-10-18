import asyncio
import logging
import socket
import threading
import time
import websockets
from queue import Queue
from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger("LazyServer")
logger.setLevel(logging.DEBUG)
logger.propagate = False
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ServiceBroadcaster:

    def __init__(self, port, name, properties):
        self.port = port
        self.name = name
        self.properties = properties

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))  # Doesn't need to be reachable, just used to determine local IP
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def run(self):
        local_ip = self.get_local_ip()

        service_type = "_lazy._tcp.local."
        service_name = f"{self.name}._lazy._tcp.local."

        zeroconf = Zeroconf()
        info = ServiceInfo(
            service_type,
            service_name,
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties=self.properties,
            server=f"{socket.gethostname()}.local.",
        )
        zeroconf.register_service(info)

        try:
            logger.debug("Broadcaster running")
            while True:  # Keep the service running
                time.sleep(1)
        except KeyboardInterrupt:
            logger.debug("Shutting down broadcaster")
        finally:
            logger.debug("Unregistering service...")
            zeroconf.unregister_service(info)
            zeroconf.close()
            logger.debug("Service stopped.")


class LazyServer:
    def __init__(self, name, host="0.0.0.0", port=1726, **properties):
        self.name = name
        self.properties = properties
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        self.queue = Queue()

    async def handler(self, client):
        logger.debug("Client connected")
        self.clients.add(client)
        try:
            async for message in client:
                logger.debug(f"Received message: {message}")
                asyncio.create_task(self.process_message(client, message))
        except websockets.ConnectionClosed:
            logger.debug("Client disconnected")
        except Exception as e:
            await client.close(1011, str(e))
        finally:
            self.clients.remove(client)

    async def _start(self):
        self.server = await websockets.serve(self.handler, self.host, self.port)
        logger.debug(f"WebSocket server started on ws://{self.host}:{self.port}")
        await self.server.wait_closed()

    def start(self):
        logger.debug("Starting broadcaster...")
        broadcaster = ServiceBroadcaster(self.port, self.name, self.properties)
        broadcast_thread = threading.Thread(target=broadcaster.run, daemon=True)
        broadcast_thread.start()
        logger.debug("Starting server...")
        # Create event loop and run server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._start())
        except KeyboardInterrupt:
            logger.debug("Shutting down server...")
        finally:
            loop.close()

if __name__ == "__main__":
    server = LazyServer(name="LazyServer")
    server.start()