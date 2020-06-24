from PIL import Image
import select
import socket
import sys

from common import *
from puzzle import Puzzle


def main():
    port = int(sys.argv[1])
    img_path = sys.argv[2]
    W = int(sys.argv[3])
    H = int(sys.argv[4])

    img = Image.open(img_path)
    puzzle = Puzzle(img, int(W), int(H))
    moves = []
    for p in puzzle.pieces:
        moves.append(Move(p).pack())

    img_bytes = pickle.dumps(img)
    init_res = pack_init_res(len(img_bytes), W, H)

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(("0.0.0.0", port))
    lsock.listen(32)
    clients = {}
    indices = {}
    cursors = {}

    to_read = [lsock]
    while True:
        try:
            ready_to_read, ready_to_write, in_error = \
                select.select(to_read, [], [])

            for sock in ready_to_read:
                if sock == lsock:
                    csock, addr = sock.accept()
                    clients[csock] = 0
                    idx = len(indices)
                    indices[csock] = idx
                    cursors[idx] = Cursor(idx).pack()
                    to_read.append(csock)
                    print("Server: Client connected")
                    continue

                req = sock.recv(REQ_LEN)
                if req == IDX_REQ:
                    sock.sendall(pack_idx(indices[sock]))
                elif req == INIT_REQ:
                    sock.sendall(init_res)
                    sock.sendall(img_bytes)
                elif req == UPDATE_REQ:
                    idx = indices[sock]
                    cursors[indices[sock]] = sock.recv(CURSOR_LEN)
                    cpos = clients[sock]
                    sock.sendall(pack_update_res(len(moves) - cpos, len(cursors) - 1))
                    while cpos < len(moves):
                        sock.sendall(moves[cpos])
                        cpos += 1
                    clients[sock] = cpos
                    for i, c in cursors.items():
                        if i != idx:
                            sock.sendall(c)
                elif req == MOVE_REQ:
                    moves.append(sock.recv(MOVE_LEN))
                elif req == bytes():
                    print("Server: Client disconnected")
                    cursors.pop(indices[sock])
                    to_read.remove(sock)
                else:
                    print("Error: unknown request type " + str(req))
        except socket.error as exc:
            print("Socket error: " + str(exc))


if __name__ == "__main__":
    main()