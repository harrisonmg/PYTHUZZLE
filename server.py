import pickle
from PIL import Image
import socket
import sys

from constants import *

def main():
    port = int(sys.argv[1])
    img_path = sys.argv[2]
    W = int(sys.argv[3])
    H = int(sys.argv[4])
    img = Image.open(img_path)
    img_bytes = img.tobytes("raw", 'RGB')
    init_msg = pickle.dumps((len(img_bytes), W, H))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((socket.gethostname(), port))
    sock.listen(5)

    while True:
        csock, addr = sock.accept()
        csock.send(init_msg)


if __name__ == "__main__":
    main()