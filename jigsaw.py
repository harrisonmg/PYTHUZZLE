import argparse
import multiprocessing
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import platform
import pygame as pg
import socket
import subprocess
import sys
import time

from common import *
from puzzle import Puzzle


server_process = None


class Moveplexer():
    def __init__(self, sock):
        self.sock = sock
        self.incoming_moves = multiprocessing.Queue()
        self.outgoing_moves = multiprocessing.Queue()
        self.running = True
        self.proc = multiprocessing.Process(target=self.run)
        self.proc.start()
    

    def send_move(self, piece):
        self.outgoing_moves.put(Move(piece))


    def get_move(self):
        if self.incoming_moves.empty():
            return None
        else:
            return self.incoming_moves.get()

        
    def update(self, puzzle):
        move = self.get_move()
        while move != None:
            p = puzzle.matrix[(move.r, move.c)]
            puzzle.place_piece(p, move.x, move.y)
            puzzle.connection_check(p)
            move = self.get_move()


    def run(self):
        update_time = time.time()
        update_interval = 0.1
        while self.running:
            while not self.outgoing_moves.empty():
                self.sock.sendall(MOVE_REQ)
                self.sock.sendall(self.outgoing_moves.get().pack())
            t = time.time()
            if t >= update_time:
                udpate_time = t + update_interval
                self.sock.sendall(UPDATE_REQ)
                new_move_count = unpack_update_res(self.sock.recv(UPDATE_RES_LEN))[0]
                for _ in range(new_move_count):
                    self.incoming_moves.put(Move().unpack(self.sock.recv(MOVE_LEN)))
                
            
    def shutdown(self):
        self.running = False
        

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""
Do a jigsaw puzzle. Puzzle dimensions must be odd. The port (default=7777) must be forwarded to host an online game.

    Start a 3x3 offline game:

        python3 jigsaw.py -o rock.png 3 3

    Join an online game:

        python3 jigsaw.py -c 8.8.8.8

    Host an 11x11 online game:

        python3 jigsaw.py -s itachi.png 11 11""")

    parser.add_argument('-o', '--offline', help="Play an offline game",
                        nargs=3, metavar=('IMAGE', 'WIDTH', 'HEIGHT'), default=False)
    parser.add_argument('-c', '--connect', help="Connect to an online game",
                        metavar='SERVER_IP', default=False)
    parser.add_argument('-s', '--server', help="Host an online game",
                        nargs=3, metavar=('IMAGE', 'WIDTH', 'HEIGHT'), default=False)
    parser.add_argument('-p', '--port', help="Port to connect to or host from",
                        default="7777")
    parser.add_argument('-d', '--downscale', help="Locally downscale the resolution of the puzzle's largest dimension. Not currently compatible with online.",
                        metavar='RESOLUTION', type=int, default=-1)
    args = parser.parse_args()

    if args.offline:
        img_path, W, H = args.offline;
        img_str = get_img_str(img_path)
        pass
    elif args.server or args.connect:
        if args.server:
            img_path, W, H = args.server;
            img_str = get_img_str(img_path)
            print("Starting server...")
            global server_process

            if platform.system() == 'Linux':
                py_cmd = "python3"
            else:
                py_cmd = "python"
            server_process = subprocess.Popen([py_cmd, "server.py", args.port, img_path, W, H])
            args.connect = socket.gethostname()
        else:
            print("Connecting to server...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start_time = time.time()
        while True:
            if time.time() - start_time > 10:
                print("Error: Could not connect to server")
                sys.exit()
            try:
                sock.connect((args.connect, int(args.port)))
                break
            except:
                pass
        print("Done.")

        if not args.server:
            print("Downloading image...")
            sock.sendall(INIT_REQ)
            img_size, W, H = unpack_init_res(sock.recv(INIT_RES_LEN))
            img_str = sock.recv(img_size).decode()
            print("Done")

        moveplexer = Moveplexer(sock)
    else:
        print("Error: a game mode argume is required [-o | -c | -s]")
        sys.exit()

    pg.init()
    try:
        pg.mixer.init()
    except pg.error:
        pass

    display_flags = pg.RESIZABLE
    print("Building puzzle...")
    puzzle = Puzzle(img_str, int(W), int(H), downscale=args.downscale)
    print("Done.")

    sw, sh = 1500, 1000
    screen = pg.display.set_mode([sw, sh], flags=display_flags)

    pw, ph = puzzle.w, puzzle.h
    scale = min(sw / pw, sh / ph)
    scale_factor = 10 / 9

    panning = False
    pan_x = pw / 2 - sw / scale / 2
    pan_y = ph / 2 - sh / scale / 2

    holding = None

    running = True
    while running:
        if not args.offline: moveplexer.update(puzzle)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                # if event.key == pg.K_ESCAPE:
                #     running = False
                if event.key == pg.K_SPACE:
                    pan_x = pw / 2 - sw / scale / 2
                    pan_y = ph / 2 - sh / scale / 2
            elif event.type == pg.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pg.display.set_mode([sw, sh], flags=display_flags)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    holding = puzzle.click_check(pan_x + event.pos[0] / scale, pan_y + event.pos[1] / scale)
                elif event.button == 3:
                    panning = True
                elif event.button in (4, 5):
                    pan_x += sw / scale / 2
                    pan_y += sh / scale / 2
                    if event.button == 4:
                        scale *= scale_factor
                    else:
                        scale /= scale_factor
                    pan_x -= sw / scale / 2
                    pan_y -= sh / scale / 2
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    if holding != None:
                        if args.offline:
                            for p in holding.group:
                                puzzle.place_piece(p, p.disp_x, p.disp_y)
                                puzzle.connection_check(p)
                        else:
                            moveplexer.send_move(holding)
                        holding = None
                elif event.button == 3:
                    panning = False
            elif event.type == pg.MOUSEMOTION:
                mx = event.rel[0] / scale
                my = event.rel[1] / scale
                if panning:
                    pan_x -= mx
                    pan_y -= my
                if holding != None:
                    puzzle.move_piece(holding, mx, my)

        pan_x

        ss_width = min(max(1, sw / scale), pw)
        ss_height = min(max(1, sh / scale), ph)

        if pan_x < 0:
            ss_x = 0
            blit_x = int(-pan_x * scale)
        else:
            ss_x = min(pan_x, pw)
            blit_x = 0

        if pan_y < 0:
            ss_y = 0
            blit_y = int(-pan_y * scale)
        else:
            ss_y = min(pan_y, ph)
            blit_y = 0

        if pan_x > pw - ss_width:
            ss_width = max(pw - pan_x, 0)

        if pan_y > ph - ss_height:
            ss_height = max(ph - pan_y, 0)

        screen.fill(BG_COLOR)
        screen.blit(puzzle.subsurface(int(ss_x), int(ss_y), int(ss_width), int(ss_height), scale), (blit_x, blit_y))
        pg.display.flip()
        
        if puzzle.complete() and pg.mixer.get_init() and not pg.mixer.music.get_busy():
            pg.mixer.music.load('congrats.wav')
            pg.mixer.music.set_volume(1)
            pg.mixer.music.play(-1)

    if not args.offline: moveplexer.shutdown()
    pg.quit()


if __name__ == "__main__":
    try:
        main()
    finally:
        if server_process != None:
            server_process.kill()