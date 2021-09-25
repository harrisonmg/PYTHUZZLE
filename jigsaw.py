# fmt: off
import argparse
from math import sqrt
import multiprocessing as mp
import os
import pickle
import platform
import socket
import struct
import subprocess
import sys
import time
import uuid

from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from common import (BG_COLOR, Cursor, CURSOR_LEN, IDX_LEN, IDX_REQ, IMG_RES_LEN, IMG_REQ,
                    INIT_RES_LEN, INIT_REQ, Move, MOVE_LEN, MOVE_REQ, resource_path, unpack_idx,
                    unpack_img_res, unpack_init_res, unpack_update_res, UPDATE_RES_LEN, UPDATE_REQ)
from puzzle import Puzzle
# fmt: on


server_process = None
viewer_process = None


class Moveplexer():
    def __init__(self, sock, idx, cursors):
        self.sock = sock
        self.incoming_moves = mp.Queue()
        self.outgoing_moves = mp.Queue()
        self.cursor = mp.Queue(1)
        self.cursor.put(Cursor(idx).pack())
        self.cursor_lock = mp.Lock()
        self.proc = mp.Process(target=self.run, args=(sock, cursors,))

    def send_move(self, piece):
        self.outgoing_moves.put(Move(piece))

    def get_move(self):
        if self.incoming_moves.empty():
            return None
        else:
            return self.incoming_moves.get()

    def init_puzzle(self, puzzle):
        self.sock.sendall(INIT_REQ)
        move_count = unpack_init_res(self.sock.recv(INIT_RES_LEN))[0]
        for _ in range(move_count):
            move = Move.unpack(self.sock.recv(MOVE_LEN))
            p = puzzle.matrix[(move.r, move.c)]
            puzzle.place_piece(p, move.x, move.y)

    def update(self, puzzle, holding, cursor_pos):
        move = self.get_move()
        while move is not None:
            p = puzzle.matrix[(move.r, move.c)]
            puzzle.place_piece(p, move.x, move.y)
            puzzle.connection_check(p)
            if holding in p.group:
                holding = None
            move = self.get_move()

        with self.cursor_lock:
            cursor = Cursor.unpack(self.cursor.get())
            cursor.x, cursor.y = cursor_pos
            if holding is None:
                cursor.pr, cursor.pc = -1, -1
            else:
                cursor.pr, cursor.pc = holding.row, holding.col
                cursor.px, cursor.py = holding.disp_x, holding.disp_y
            self.cursor.put(cursor.pack())

        return holding

    def start_process(self):
        self.proc.start()

    def run(self, sock, cursors):
        update_time = time.time()
        update_interval = 1 / 30
        try:
            while True:
                while not self.outgoing_moves.empty():
                    sock.sendall(MOVE_REQ)
                    sock.sendall(self.outgoing_moves.get().pack())
                t = time.time()
                if t >= update_time:
                    update_time = t + update_interval
                    sock.sendall(UPDATE_REQ)
                    with self.cursor_lock:
                        cursor = self.cursor.get()
                        sock.sendall(cursor)
                        self.cursor.put(cursor)

                    new_move_count, cursor_count = unpack_update_res(sock.recv(UPDATE_RES_LEN))

                    for _ in range(new_move_count):
                        self.incoming_moves.put(Move.unpack(sock.recv(MOVE_LEN)))

                    updated = set()
                    for _ in range(cursor_count):
                        c = Cursor.unpack(sock.recv(CURSOR_LEN))
                        cursors[c.idx] = c
                        updated.add(c.idx)
                    for i in cursors.keys():
                        if i not in updated:
                            cursors.pop(i)
        except struct.error:
            pass

    def shutdown(self):
        self.proc.terminate()


def open_image_viewer(img):
    try:
        os.mkdir(resource_path("image_cache"))
    except FileExistsError:
        pass
    filename = resource_path("image_cache/" + str(uuid.uuid4()) + ".png")
    img.save(filename)
    image_viewer = {'linux': 'xdg-open', 'win32': 'start', 'darwin': 'open'}[sys.platform]
    shell = sys.platform == 'win32'
    with open(os.devnull, 'wb') as shutup:
        subprocess.run([image_viewer, filename], stdout=shutup, stderr=shutup, shell=shell)


def main(argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""
Do a jigsaw puzzle.
The puzzle will attempt to hit the desired piece count while keeping the pieces square.
The port (default=7777) must be forwarded to host an online game.

    Install dependencies:

        python3 -m pip install -r requirements.txt

    Start a ~100 piece offline game:

        python3 jigsaw.py -o rock.png 100

    Join an online game:

        python3 jigsaw.py -c 8.8.8.8

    Host an 11x11 online game:

        python3 jigsaw.py -s itachi.png -d 11 11""")

    parser.add_argument('piece_count', help="Piece count to attempt to hit when cutting puzzle",
                        nargs='*', metavar='PIECE_COUNT', type=int, default=False)
    parser.add_argument('-o', '--offline', help="Play an offline game",
                        metavar='IMAGE', default=False)
    parser.add_argument('-c', '--connect', help="Connect to an online game",
                        metavar='SERVER_IP', default=False)
    parser.add_argument('-s', '--server', help="Host an online game",
                        metavar='IMAGE', default=False)
    parser.add_argument('-p', '--port', help="Port to connect to or host from",
                        default="7777")
    parser.add_argument('-d', '--dimensions', help="Specify puzzle dimensions (pieces)",
                        nargs=2, metavar=('WIDTH', 'HEIGHT'), type=int, default=False)
    parser.add_argument('-n', '--no-viewer', help="Don't open an accompanying image viewer",
                        action='store_true', default=False)
    parser.add_argument('-e', '--escape-exit', help="Let the escape key exit the program",
                        action='store_true', default=False)
    args = parser.parse_args(argv)

    if args.offline or args.server:
        if args.offline:
            img_path = args.offline
        else:
            img_path = args.server
        img = Image.open(img_path)

        if args.dimensions:
            width, height = args.dimensions
        else:
            if not args.piece_count:
                print("Error: Missing puzzle piece count or dimensions")
                sys.exit()
            elif len(args.piece_count) > 1:
                print("Error: Too many piece count arguments given, should be 1")
            else:
                pc = args.piece_count[0]
                if pc < 1:
                    print("Error: Piece count must be positive")
                    sys.exit()
                ratio = img.size[0] / img.size[1]
                height = sqrt(pc / ratio)
                width = ratio * height

                width = int(width + 0.5)
                height = int(height + 0.5)

                width = max(2, width)
                height = max(2, height)

    if args.server or args.connect:
        if args.server:
            print("Starting server...")
            global server_process

            if platform.system() == 'Linux':
                py_cmd = "python3"
            else:
                py_cmd = "python"
            server_process = subprocess.Popen(
                [py_cmd, "server.py", args.port, img_path, str(width), str(height)])
            args.connect = socket.gethostname()
        else:
            print("Connecting to server...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                print("Error: Could not connect to server")
                sys.exit(1)
                # start_time = time.time()
            try:
                sock.connect((args.connect, int(args.port)))
                break
            except Exception:
                pass
        print("Done.")

        sock.sendall(IDX_REQ)
        idx = unpack_idx(sock.recv(IDX_LEN))[0]

        if not args.server:
            print("Downloading image...")
            sock.sendall(IMG_REQ)
            img_size, width, height = unpack_img_res(sock.recv(IMG_RES_LEN))
            img = pickle.loads(sock.recv(img_size, socket.MSG_WAITALL))
            print("Done.")

        manager = mp.Manager()
        cursors = manager.dict()
        moveplexer = Moveplexer(sock, idx, cursors)
    elif not args.offline:
        print("Error: A game mode argume is required [-o | -c | -s]")
        sys.exit()

    pg.init()
    try:
        pg.mixer.init()
    except pg.error:
        pass

    display_flags = pg.RESIZABLE
    print("Building puzzle...")
    puzzle = Puzzle(img, int(width), int(height))
    if not args.offline:
        moveplexer.init_puzzle(puzzle)
    print("Done.")

    if not args.no_viewer:
        open_image_viewer(puzzle.img)

    sw, sh = 1500, 1000
    screen = pg.display.set_mode([sw, sh], flags=display_flags)

    icon = pg.image.load(resource_path('icon.ico'))
    pg.display.set_icon(icon)
    pg.display.set_caption('Rompecabezas')

    pw, ph = puzzle.w, puzzle.h
    scale = min(sw / pw, sh / ph)
    scale_factor = 10 / 9
    max_scale = 15000 / (2 * max(puzzle.piece_w, puzzle.piece_h))

    panning = False
    pan_x = pw / 2 - sw / scale / 2
    pan_y = ph / 2 - sh / scale / 2

    holding = None
    mouse_pos = (0, 0)
    cursor_pos = (0, 0)
    cursor_img = pg.image.load(resource_path('cursor.png'))
    cursor_img = pg.transform.scale(
        cursor_img, (int(cursor_img.get_width() / 2), int(cursor_img.get_height() / 2)))

    if not args.offline:
        moveplexer.start_process()
    running = True
    while running:
        if not args.offline:
            holding = moveplexer.update(puzzle, holding, cursor_pos)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE and args.escape_exit:
                    running = False
                if event.key == pg.K_SPACE:
                    pan_x = pw / 2 - sw / scale / 2
                    pan_y = ph / 2 - sh / scale / 2
            elif event.type == pg.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pg.display.set_mode([sw, sh], flags=display_flags)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    holding = puzzle.click_check(
                        pan_x + event.pos[0] / scale, pan_y + event.pos[1] / scale)
                elif event.button == 3:
                    panning = True
                elif event.button in (4, 5):
                    pan_x += sw / scale / 2
                    pan_y += sh / scale / 2
                    if event.button == 4:
                        scale *= scale_factor
                        scale = min(scale, max_scale)
                    else:
                        scale /= scale_factor
                    pan_x -= sw / scale / 2
                    pan_y -= sh / scale / 2
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    if holding is not None:
                        if args.offline:
                            puzzle.place_piece(holding, holding.disp_x, holding.disp_y)
                            puzzle.connection_check(holding)
                        else:
                            moveplexer.send_move(holding)
                        holding = None
                elif event.button == 3:
                    panning = False
            elif event.type == pg.MOUSEMOTION:
                mouse_pos = event.pos
                mx = event.rel[0] / scale
                my = event.rel[1] / scale
                if panning:
                    pan_x -= mx
                    pan_y -= my
                elif holding is not None:
                    puzzle.move_piece(holding, mx, my)

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
        screen.blit(puzzle.subsurface(int(ss_x), int(ss_y), int(
            ss_width), int(ss_height), scale), (blit_x, blit_y))

        if not args.offline:
            for cursor in cursors.values():
                if (
                    pan_x < cursor.x < pan_x + sw / scale and
                    pan_y < cursor.y < pan_y + sh / scale
                ):
                    tinted_cursor_img = cursor_img.copy()
                    tinted_cursor_img.fill(cursor.color, special_flags=pg.BLEND_MIN)
                    screen.blit(tinted_cursor_img,
                                (int((cursor.x - pan_x) * scale), int((cursor.y - pan_y) * scale)))
                if cursor.pr != -1 and cursor.pc != -1:
                    p = puzzle.matrix[(cursor.pr, cursor.pc)]
                    if holding == p:
                        holding = None
                    dx, dy = cursor.px - p.disp_x, cursor.py - p.disp_y
                    puzzle.move_piece(p, dx, dy)

        pg.display.update()

        cursor_pos = (mouse_pos[0] / scale + pan_x, mouse_pos[1] / scale + pan_y)

        if puzzle.complete() and pg.mixer.get_init() and not pg.mixer.music.get_busy():
            pg.mixer.music.load(resource_path('congrats.wav'))
            pg.mixer.music.set_volume(1)
            pg.mixer.music.play(-1)

    if not args.offline:
        moveplexer.shutdown()
    pg.quit()


def run(argv):
    try:
        main(argv)
    finally:
        if server_process is not None:
            server_process.kill()
        if viewer_process is not None:
            viewer_process.kill()


if __name__ == "__main__":
    run(sys.argv[1:])
