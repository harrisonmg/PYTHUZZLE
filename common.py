import os
from random import randrange
import struct
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


BG_COLOR = (44, 47, 51)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

REQ_LEN = len("a".encode())

IMG_REQ = "g".encode()
IMG_FMT = ">III"
IMG_RES_LEN = len(struct.pack(IMG_FMT, 1, 2, 3))

INIT_REQ = "i".encode()
INIT_FMT = ">I"
INIT_RES_LEN = len(struct.pack(INIT_FMT, 1))

UPDATE_REQ = "u".encode()
UPDATE_FMT = ">II"
UPDATE_RES_LEN = len(struct.pack(UPDATE_FMT, 1, 2))

MOVE_REQ = "m".encode()
MOVE_FMT = ">IIII"
MOVE_LEN = len(struct.pack(MOVE_FMT, 1, 2, 3, 4))

IDX_REQ = "d".encode()
IDX_FMT = ">I"
IDX_LEN = len(struct.pack(IDX_FMT, 1))

CURSOR_FMT = ">IddiiddBBB"
CURSOR_LEN = len(struct.pack(CURSOR_FMT, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9))


def pack_img_res(img_size, w, h):
    return struct.pack(IMG_FMT, img_size, w, h)


def unpack_img_res(msg):
    return struct.unpack(IMG_FMT, msg)


def pack_init_res(move_count):
    return struct.pack(INIT_FMT, move_count)


def unpack_init_res(msg):
    return struct.unpack(INIT_FMT, msg)


def pack_update_res(move_count, cursor_count):
    return struct.pack(UPDATE_FMT, move_count, cursor_count)


def unpack_update_res(msg):
    return struct.unpack(UPDATE_FMT, msg)


def pack_idx(idx):
    return struct.pack(IDX_FMT, idx)


def unpack_idx(msg):
    return struct.unpack(IDX_FMT, msg)


class Move():
    def __init__(self, piece=None):
        if piece is not None:
            self.r, self.c = int(piece.row), int(piece.col)
            self.x, self.y = int(piece.disp_x), int(piece.disp_y)

    def __str__(self):
        return f"piece: ({self.r}, {self.c}), pos: ({self.x}, {self.y})"

    def pack(self):
        return struct.pack(MOVE_FMT, self.r, self.c, self.x, self.y)

    @classmethod
    def unpack(self, string):
        ret = Move()
        ret.r, ret.c, ret.x, ret.y = struct.unpack(MOVE_FMT, string)
        return ret


class Cursor():
    def __init__(self, idx=0, x=0, y=0, pr=-1, pc=-1, px=0, py=0, r=None, g=None, b=None):
        self.idx = idx
        self.x = x
        self.y = y
        self.pr = pr
        self.pc = pc
        self.px = px
        self.py = py
        if None in (r, g, b):
            self.color = (randrange(256), randrange(256), randrange(256))
        else:
            self.color = (r, g, b)

    def pack(self):
        return struct.pack(
            CURSOR_FMT, self.idx, self.x, self.y, self.pr, self.pc, self.px, self.py, *self.color)

    @classmethod
    def unpack(self, string):
        return Cursor(*struct.unpack(CURSOR_FMT, string))
