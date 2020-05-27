import pickle
from PIL import Image
import struct


BG_COLOR = (44, 47, 51)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

REQ_LEN = len("a".encode())

INIT_REQ = "i".encode()
INIT_FMT = ">lll"
INIT_RES_LEN = len(struct.pack(INIT_FMT, 1, 2, 3))

UPDATE_REQ = "u".encode()
UPDATE_FMT = ">l"
UPDATE_RES_LEN = len(struct.pack(UPDATE_FMT, 1))

MOVE_REQ = "m".encode()
MOVE_LEN = len(struct.pack(">llll", 1, 2, 3, 4))


def pack_init_res(img_size, w, h):
    return struct.pack(INIT_FMT, img_size, w, h)


def unpack_init_res(msg):
    return struct.unpack(INIT_FMT, msg)


def pack_update_res(move_count):
    return struct.pack(UPDATE_FMT, move_count)


def unpack_update_res(msg):
    return struct.unpack(UPDATE_FMT, msg)


class Move():
    def __init__(self, piece=None):
        if piece != None:
            self.r, self.c = int(piece.row), int(piece.col)
            self.x, self.y = int(piece.disp_x), int(piece.disp_y)


    def pack(self):
        return struct.pack(">llll", self.r, self.c, self.x, self.y)


    def unpack(self, string):
        self.r, self.c, self.x, self.y = struct.unpack(">llll", string)
        return self