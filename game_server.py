import random
from dataclasses import dataclass

import asyncio
import logging

@dataclass
class Client:
    id: int
    x: int
    y: int

    writer: asyncio.StreamWriter

class GameServer:
    def __init__(self):
        self.clients = []
        self.buffer_size = 1024
        self.game_field_width = 800
        self.game_field_height = 800
        self.running = True

    def process_client_state(self, client_id, message):
        logging.info(f"Client {client_id} sent: {message}")

    async def handle_client(self, reader, writer):
        # Assign ID to the client
        client_id = len(self.clients)
        logging.info(f'New client connected: {client_id}')
        cli = Client(client_id, writer, random.randint(0, self.game_field_width), random.randint(0, self.game_field_height))
        self.clients.append(cli)

        writer.write(f"id:{client_id},{cli.x},{cli.y}\n".encode())
        await writer.drain()

        logging.info(f'Written initial data for client.')

        # Listen for messages from the client and broadcast them to all other clients
        while True:
            logging.info(f'Waiting for a message from client {client_id}')
            message = (await reader.read(self.buffer_size)).decode()
            if not message:
                break

            self.process_client_state(client_id, message)

        # Remove the client from the list of connected clients
        del self.clients[client_id]
        logging.info(f'Client disconnected: {client_id}')

    async def update_game_state(self):
        loop_count = 0
        while self.running:
            loop_count += 1
            if len(self.clients) == 0:
                if loop_count % 10 == 0:
                    logging.info("No clients connected, waiting...")

                await asyncio.sleep(1)
                continue

            logging.info("Updating game state...")
            await asyncio.sleep(2)
            logging.info("Game state updated")

        logging.info("update_game_state exiting...")

    async def start(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888)

        task1 =  self.update_game_state()
        task2 = server.serve_forever()

        await asyncio.gather(task1, task2)

        logging.info("Game server finished.")
        self.running = False

if __name__ == '__main__':
    format = "GS: %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    game_server = GameServer()
    asyncio.run(game_server.start())
