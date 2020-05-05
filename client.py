import time
import socket
import threading

import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.sprite import Sprite

class Block(Sprite):
    def __init__(self, x, y, color):
        attack_image = pyglet.image.load("attack.png")
        super().__init__(attack_image, x, y)
        self.color = color
        self.to_update = "x += 0"

    def upd(self):
        exec(f"self.{self.to_update}")


class TestGame(pyglet.window.Window):
    def __init__(self):
        super().__init__(width=200, height=200)
        self.this_player = None
        self.enemy_player = None
        host = "127.0.0.1"
        port = 12345
        self.conn = socket.socket()
        self.conn.connect((host, port))
        counter = self.conn.recv(1024).decode()
        self.user_input = False
        self.msg_2_send = "Empty message"
        if counter == "1":
            self.this_player = Block(50, 50, (0, 255, 0))
            self.enemy_player = Block(100, 100, (255, 0, 0))
        else:
            self.this_player = Block(100, 100, (0, 255, 0))
            self.enemy_player = Block(50, 50, (255, 0, 0))

    def on_draw(self):
        self.clear()
        self.this_player.draw()
        self.enemy_player.draw()

    def update(self, delta_time):
        self.this_player.update()
        # msg_2_send = input("Enter some shit: ")
        if self.user_input:
            print(self.msg_2_send)
            self.conn.sendall(self.msg_2_send.encode())
            self.user_input = False
        else:
            self.conn.sendall("No input".encode())

    def incoming_msg(self):
        while True:
            print("Waiting for message")
            received_msg = self.conn.recv(1024).decode()
            print("received_msg =", received_msg)
            self.this_player.upd()
            self.this_player.to_update = "x += 0"
            if received_msg == "W":
                self.enemy_player.y += 20
            elif received_msg == "S":
                self.enemy_player.y -= 20
            elif received_msg == "A":
                self.enemy_player.x -= 20
            elif received_msg == "D":
                self.enemy_player.x += 20

    def on_key_press(self, symbol, modifiers):
        if symbol is key.W:
            self.this_player.to_update = "y += 20"
            self.msg_2_send = "W"
        elif symbol is key.S:
            self.this_player.to_update = "y -= 20"
            self.msg_2_send = "S"
        elif symbol is key.A:
            self.this_player.to_update = "x -= 20"
            self.msg_2_send = "A"
        elif symbol is key.D:
            self.this_player.to_update = "x += 20"
            self.msg_2_send = "D"
        elif symbol is key.F2:
            print(self.msg_2_send)
        self.user_input = True

    def on_mouse_press(self, x, y, button, modifiers):
        pass

def main():
    game_window = TestGame()
    inc_msg_thread = threading.Thread(target=game_window.incoming_msg)
    inc_msg_thread.start()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
