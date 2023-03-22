import random

import asyncio
import logging
from dataclasses import dataclass

@dataclass
class Player:
    x: float
    y: float
    id: int
    writer: asyncio.StreamWriter

    speed_x: float = 0
    speed_y: float = 0

class GameServer:
    def __init__(self):
        self.players = []
        self.game_field_width = 800
        self.game_field_height = 800
        self.acceleration = 0.1
        self.player_width = 50
        self.player_height = 50

    async def update_and_send_state(self):
        while True:
            if len(self.players) == 0:
                await asyncio.sleep(0.1)
                continue

            logging.info(f'Updating and sending state')
            game_state_encoded = ''

            for player in self.players:
                player.x += player.speed_x
                player.y += player.speed_y

                # prevent player from going off screen
                if player.x < 0:
                    player.x = 0
                    player.speed_x = 0
                elif player.x > self.game_field_width - self.player_width:
                    player.x = self.game_field_width - self.player_width
                    player.speed_x = 0
                if player.y < 0:
                    player.y = 0
                    player.speed_y = 0
                elif player.y > self.game_field_height - self.player_height:
                    player.y = self.game_field_height - self.player_height
                    player.speed_y = 0

                # add friction
                if player.speed_x > 0:
                    player.speed_x -= self.acceleration * 0.5
                elif player.speed_x < 0:
                    player.speed_x += self.acceleration * 0.5
                if player.speed_y > 0:
                    player.speed_y -= self.acceleration * 0.5
                elif player.speed_y < 0:
                    player.speed_y += self.acceleration * 0.5
                
                
                game_state_encoded += f'{player.id},{player.x},{player.y},'

            for player in self.players:
                player.writer.write(f"{game_state_encoded[:-1]}\n".encode())
                await player.writer.drain()

            logging.info(f'State sent: {game_state_encoded}')
            await asyncio.sleep(0.05)
    async def handle_client(self, reader, writer):
        # Get the client's name
        logging.error(f'New player connected: {len(self.players)}')

        # get random position
        player = Player(random.randint(0, self.game_field_width), random.randint(0, self.game_field_height), len(self.players), writer)

        writer.write(f"id:{player.id}\n".encode())
        await writer.drain()

        self.players.append(player)

        # Listen for messages from the client and broadcast them to all other clients
        while True:
            message = (await reader.readline()).decode()
            if not message:
                break

            logging.info(f'Player sent: {message}')
            x_action, y_action, fire_action = message.split(',')
            player.speed_x += float(x_action)
            player.speed_y += float(y_action)

        # Remove the client from the list of connected clients
        # del self.clients[name]
        logging.info(f'Client disconnected')

    async def start(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888)

        async with server:
            await server.serve_forever()

    async def run(self):
        await asyncio.gather(self.start(), self.update_and_send_state())

if __name__ == '__main__':
    format = "SRV: %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%F-%H-%M-%S")

    logging.info("Starting server...")
    game_server = GameServer()

    asyncio.run(game_server.run())

    # loop = asyncio.get_event_loop()
    # t1 = asyncio.create_task(game_server.start())
    # t2 = asyncio.create_task(game_server.update_and_send_state())
    #
    # await asyncio.gather(t1, t2)
    #
    # loop.close()

