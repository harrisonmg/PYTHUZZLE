from PIL import Image
import socket
import sys

from common import *

def main():
    port = int(sys.argv[1])
    img_path = sys.argv[2]
    W = int(sys.argv[3])
    H = int(sys.argv[4])

    img_str = get_img_str(img_path).encode()
    init_msg = pack_init_msg(len(img_str), W, H)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(32)
    clients = []

    while True:
        csock, addr = sock.accept()
        clients.append(csock)
        csock.send(init_msg)
        csock.send(img_str)


if __name__ == "__main__":
    main()