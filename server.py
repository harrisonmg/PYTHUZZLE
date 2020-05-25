from PIL import Image
import select
import socket
import sys

from common import *
from puzzle import *

def main():
    port = int(sys.argv[1])
    img_path = sys.argv[2]
    W = int(sys.argv[3])
    H = int(sys.argv[4])

    img_str = get_img_str(img_path).encode()
    puzzle = Puzzle(img_str, int(W), int(H))
    moves = []
    for p in puzzle.pieces:
        moves.append(Move(p).pack())

    init_res = pack_init_res(len(img_str), W, H)

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(("0.0.0.0", port))
    lsock.listen(32)
    clients = {}

    to_read = [lsock]

    while True:
        ready_to_read, ready_to_write, in_error = \
            select.select(to_read, [], [])

        for sock in ready_to_read:
            if sock == lsock:
                csock, addr = sock.accept()
                clients[csock] = 0
                to_read.append(csock)
                continue

            req = sock.recv(REQ_LEN)
            if req == INIT_REQ:
                sock.sendall(init_res)
                sock.sendall(img_str)
            elif req == UPDATE_REQ:
                cpos = clients[sock]
                sock.sendall(pack_update_res(len(moves) - cpos))
                while cpos < len(moves):
                    sock.sendall(moves[cpos])
                    cpos += 1
                clients[sock] = cpos
            elif req == MOVE_REQ:
                moves.append(sock.recv(MOVE_LEN))
            else:
                print("Error: unknown request type " + req.decode())



if __name__ == "__main__":
    main()