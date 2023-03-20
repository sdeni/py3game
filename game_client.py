# Example file showing a basic pygame "game loop"
import time
from dataclasses import dataclass
from random import random

import asyncio

import pygame
import threading
import logging

do_data_exchange = True

def prepare_image(file_name, scale, angle):
    img = pygame.image.load(file_name)
    img.convert()
    img = pygame.transform.rotozoom(img, angle, scale)

    img.set_colorkey("black")

    return img

class Console:
    def __init__(self, screen):
        self.x = 0
        self.y = 0
        self.width = screen.get_width()
        self.height = 100
        self.color = "white"
        self.text = ""
        self.font = pygame.font.SysFont(None, 22)
        self.screen = screen
        self.visible = True

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    def draw(self):
        if not self.visible:
            return

        # draw transparent background with alpha 128
        # pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.width, self.height), 0, pygame.BLEND_RGBA_MULT)

        s = pygame.Surface((self.width, self.height))  # the size of your rect
        s.set_alpha(80)  # alpha level
        s.fill(self.color)  # this fills the entire surface
        self.screen.blit(s, (self.x, self.y))

        # pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.width, self.height))

        text = self.font.render(self.text, True, "white")

        # draw transparent text
        text.set_alpha(190)
        self.screen.blit(text, (self.x + 10, self.y + 10))

    def log(self, text):
        self.text = text

    def update(self):
        pass

class Player:
    def __init__(self, screen, image_files, scale, angle):
        self.x = 0
        self.y = 0
        self.screen = screen

        self.color = "green"

        self.is_active = False

        self.image_index = 0

        self.images = []
        for file_name in image_files:
            self.images.append(prepare_image(file_name, scale, angle))

        self.image = self.images[self.image_index]
        self.rect = self.image.get_rect()

    def draw(self):
        if self.is_active:
            self.screen.blit(self.image, self.rect)

    def update(self):
        if self.is_active:
            self.image_index += 1
            self.image_index %= len(self.images)

            self.image = self.images[self.image_index]

            try:
                self.rect.x = self.x
                self.rect.y = self.y
            except:
                logging.warning("Player.update EXCEPTION: self.x or self.y is None")


class Bullet:
    def __init__(self, screen, image_files, scale, angle):
        self.x = 0
        self.y = 0

        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.screen = screen

        self.width = 10
        self.height = 10
        self.color = "red"
        self.speed_x = 0
        self.speed_y = 0

        self.is_active = True

        self.image_index = 0

        self.images = []
        for file_name in image_files:
            self.images.append(prepare_image(file_name, scale, angle))

        self.image = self.images[self.image_index]
        self.rect = self.image.get_rect()

    def draw(self):
        if not self.is_active:
            return

        pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.width, self.height))

    def update(self):

        self.x += self.speed_x
        self.y += self.speed_y

        if self.x < 0 or self.x > self.screen_width or self.y < 0 or self.y > self.screen_height:
            self.is_active = False
            return

        self.image_index += 1
        self.image_index %= len(self.images)

        self.image = self.images[self.image_index]

        self.rect.x = self.x
        self.rect.y = self.y

@dataclass
class PlayerEvents:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    fire: bool = False

def main():
    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    clock = pygame.time.Clock()
    running = True

    console = Console(screen)
    player = Player(screen, ["images/ship1.png", "images/ship2.png", "images/ship3.png"], 0.25, 0)
    player_events = PlayerEvents()

    bullets = []
    other_players = []

    do_data_exchange = True
    de_thread = threading.Thread(target=data_exchange_thread, args=(player, player_events, other_players))
    de_thread.start()

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player_events.up = True
                elif event.key == pygame.K_DOWN:
                    player_events.down = True
                elif event.key == pygame.K_LEFT:
                    player_events.left = True
                elif event.key == pygame.K_RIGHT:
                    player_events.right = True
                elif event.key == pygame.K_SPACE:
                    player_events.fire = True

                elif event.key == pygame.K_c:
                    if console.visible:
                        console.hide()
                    else:
                        console.show()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    player_events.up = False
                elif event.key == pygame.K_DOWN:
                    player_events.down = False
                elif event.key == pygame.K_LEFT:
                    player_events.left = False
                elif event.key == pygame.K_RIGHT:
                    player_events.right = False

        # fill the screen with a color to wipe away anything from last frame
        screen.fill("black")

        player.update()
        player.draw()

        for other_player in other_players:
            other_player.update()
            other_player.draw()

        # remove inactive bullets
        # for bullet in bullets:
        #     bullet.update()
        #     bullet.draw()

        # bullets = [bullet for bullet in bullets if bullet.is_active]

        # bullet = Bullet(screen, ['images/bullet.png'], 0.25, 0)
        # bullet.x = player.x + player.width / 2 - bullet.width / 2
        # bullet.y = player.y + player.height / 2 - bullet.height / 2
        # bullet.speed_y = -1
        # bullets.append(bullet)

        console.log(f"Player x: {int(player.x)}, y: {int(player.y)};")
        console.draw()

        # flip() the display to put your work on screen
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()

    do_data_exchange = False
    de_thread.join()

class GameClient:
    def __init__(self, player, player_events, other_players):
        self.id = None
        self.player = player
        self.player_events = player_events
        self.other_players = other_players
        self.do_data_exchange = True

    # read messages from the server and print them to the console
    async def receive_messages(self, reader):
        while self.do_data_exchange:
            # logging.info("Waiting for message")
            message = await reader.readline()
            # logging.info(f"Message received: {message}")
            if not message:
                logging.warning("Empty message!")
                self.do_data_exchange = False
                break

            message_data = message.decode().rstrip()
            # logging.info(f"Message: {message_data}")
            data_parts = []

            if ':' in message_data:
                logging.info(f"Command message.")
                cmd, data = message_data.split(":")
                data_parts = data.split(",")

                if cmd == "id":
                    # get the id from the message
                    self.id = data_parts[0]
                    logging.info(f"Player ID got: {self.id}")
                    self.player.x = int(data_parts[1])
                    self.player.y = int(data_parts[2])
                    self.player.is_active = True
            else:
                data_parts = message_data.split(",")
                self.player.x = float(data_parts[0])
                self.player.y = float(data_parts[1])

                if len(data_parts) > 2:
                    k = (len(data_parts) - 2) // 2

                    # todo: check IDs
                    if len(self.other_players) >= k:
                        self.other_players = self.other_players[:k]

                    for i in range(k):
                        x = float(data_parts[2 + i * 2])
                        y = float(data_parts[2 + i * 2 + 1])

                        if len(self.other_players) <= i:
                            other_player = Player(self.player.screen, ["images/e-ship1.png", "images/e-ship2.png", "images/e-ship3.png"], 0.25, 0)
                            self.other_players.append(other_player)

                        self.other_players[i].x = x
                        self.other_players[i].y = y
                        self.other_players[i].is_active = True

                await asyncio.sleep(0.1)


    # read messages from the user and send them to the server
    async def send_messages(self, writer):
        logging.info(f'Send message loop started.')
        while self.do_data_exchange:
            if self.id is not None:
                x_move = 0
                if self.player_events.right:
                    x_move = 1
                elif self.player_events.left:
                    x_move = -1

                y_move = 0
                if self.player_events.up:
                    y_move = -1
                elif self.player_events.down:
                    y_move = 1

                message = f"{x_move},{y_move}\n"
                # logging.info(f'Sending: {message}')
                writer.write((message).encode())
                # writer.write_eof()
                await writer.drain()
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)
                # logging.info("Player ID is not set yet.")

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection('localhost', 8888)
        # get event loop
        loop = asyncio.get_event_loop()

        t2 = asyncio.create_task(self.receive_messages(self.reader))
        t1 = asyncio.create_task(self.send_messages(self.writer))

        # await asyncio.create_task(self.receive_messages(self.reader))
        # await asyncio.create_task(self.send_messages(self.writer))
        # #
        await asyncio.gather(t1, t2)
def data_exchange_thread(player, player_events, other_players):
    logging.info("Data exchange thread started.")

    loop = asyncio.new_event_loop()

    client = GameClient(player, player_events, other_players)
    # loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(client.connect())
    except KeyboardInterrupt:
        pass

def demo_thread():
    test = 2
    while do_data_exchange:
        logging.info("Demo thread round started.")
        for n in range(10000000):
            if not do_data_exchange:
                break

            test = int(random()*10000.0)+1
            if test == 0:
                test = 3

            test %= 10000
            if (test % 12432534123) == 64234324:
                logging.info(f"Lucky data got: {test}")
                time.sleep(5)

        logging.info("Demo thread round finished.")

    logging.info("Demo thread thread finished.")


if __name__ == "__main__":
    format = "CLI: %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Game client program started.")

    main()

    logging.info("Main game loop finished.")

    logging.info("Game program finished.")