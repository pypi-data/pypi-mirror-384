# Lazy Socket


An attempt at creating a websocket based communication system that handles all the threading and async stuff 
in the background. 

## Installation

```bash
pip install lazy-socket
```

## Usage

### Server

The server can be created by subclassing `LazyServer` and implementing the `process_message` method. This is an async method that will be called whenever a message is received from a client. To respond to the client, use the `send` method of the `client` object passed to the method. A list of clients is available via the `clients` attribute of the server.

```python
import asyncio
from lazy_socket.server import LazyServer


class Server(LazyServer):

    async def process_message(self, client, message):
        await client.send(f"Received: {message}")

if __name__ == "__main__":
    server = Server(name="TestServer", host="0.0.0.0", port=5000, version="1.0")

    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
```

### Client

The client can be created by instantiating the `LazyClient` class. The client has a `queue` attribute that can be used to receive messages from the server. The client must be started using the `start` method. Messages can be sent to the server using the `send` method.

A message `lazy_client:connected:{uri}` is sent to the queue when the client successfully connects to the server.

```python
from lazy_socket.client import LazyClient

client = LazyClient()
client.start()

while True:
    if client.queue.empty():
        continue

    message = client.queue.get()
    if message.startswith("lazy_client:connected:"): 
        client.send("Hello, Lazy Server!")
```