import random
from dataclasses import dataclass

import asyncio
import logging



@dataclass
class Player:
    id: int
    x: int
    y: int
    speed_x: float
    speed_y: float

    writer: asyncio.StreamWriter = None

    width:int = 50
    height:int = 50
    acceleration:float = 0.5

class GameServer:
    def __init__(self):
        self.clients = []
        self.buffer_size = 1024
        self.game_field_width = 800
        self.game_field_height = 800
        self.running = True

    async def send_game_state(self, player):
        # logging.info(f"Sending game state to client {player.id}")
        state = ""
        for other_player in self.clients:
            if other_player.id == player.id:
                state = f"{other_player.x},{other_player.y}," + state
            else:
                state += f"{other_player.x},{other_player.y},"

        state = state[:-1]
        # logging.info(f"Sending game state to client {player.id}: {state}")
        player.writer.write(f"{state}\n".encode())
        await player.writer.drain()
        # logging.info(f"Game state sent to client {player.id}")

    def process_client_state(self, client_id, message):
        # logging.info(f"Client {client_id} sent: {message}")
        parts = message.split(",")
        player = self.clients[client_id]
        if float(parts[0]) == 1:
            player.speed_x += player.acceleration
        elif float(parts[0]) == -1:
            player.speed_x -= player.acceleration

        if float(parts[1]) == 1:
            player.speed_y += player.acceleration
        elif float(parts[1]) == -1:
            player.speed_y -= player.acceleration

    async def handle_client(self, reader, writer):
        # Assign ID to the client
        client_id = len(self.clients)
        logging.info(f'New player connected: {client_id}')
        cli = Player(client_id, 0, 0, 0, 0, writer)
        cli.x = random.randint(0, self.game_field_width - cli.width)
        cli.y = random.randint(0, self.game_field_height - cli.height)
        self.clients.append(cli)

        msg = f"id:{client_id},{int(cli.x)},{int(cli.y)}\n"
        writer.write(msg.encode())
        await writer.drain()

        logging.info(f'Written initial data for client: {msg}')

        # Listen for messages from the client and broadcast them to all other clients
        while True:
            # logging.info(f'Waiting for a message from client {client_id}')
            message = (await reader.readline()).decode()
            if not message:
                break

            # logging.info(f'Client {client_id} sent: {message}')
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

            # logging.info("Updating game state...")

            send_state_tasks = []

            for player in self.clients:
                player.x += player.speed_x
                player.y += player.speed_y

                if player.x < 0:
                    player.x = 0
                elif player.x > self.game_field_width - player.width:
                    player.x = self.game_field_width - player.width
                if player.y < 0:
                    player.y = 0
                elif player.y > self.game_field_height - player.height:
                    player.y = self.game_field_height - player.height
    
                # add friction
                # if player.speed_x > 0:
                #     player.speed_x -= player.acceleration * 0.5
                # elif player.speed_x < 0:
                #     player.speed_x += player.acceleration * 0.5
                # if player.speed_y > 0:
                #     player.speed_y -= player.acceleration * 0.5
                # elif player.speed_y < 0:
                #     player.speed_y += player.acceleration * 0.5

                t = asyncio.create_task(self.send_game_state(player))
                send_state_tasks.append(t)

            await asyncio.gather(*send_state_tasks)

            # logging.info(f"Game state updated and sent to clients {self.clients[0].x}, {self.clients[0].y}")
            await asyncio.sleep(0.1)


        logging.info("update_game_state exiting...")

    async def start(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', 8888)

        task1 =  self.update_game_state()
        task2 = server.serve_forever()

        await asyncio.gather(task1, task2)

        logging.info("Game server finished.")
        self.running = False

if __name__ == '__main__':
    format = "SRV: %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    game_server = GameServer()
    asyncio.run(game_server.start())
