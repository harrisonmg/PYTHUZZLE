from io import StringIO
import struct

BG_COLOR = (44, 47, 51)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

INIT_MSG_LEN = len(struct.pack(">lll", 1, 2, 3))

def pack_init_msg(img_size, w, h):
    return struct.pack(">lll", img_size, w, h)

def unpack_init_msg(msg):
    return struct.unpack(">lll", msg)

def get_img_str(img_path):
    img_io = StringIO(img_path)
    img_str = img_io.getvalue()
    img_io.close()
    return img_str