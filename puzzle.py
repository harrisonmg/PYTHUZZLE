# fmt: off
import os
import random

from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from common import BG_COLOR, BLACK
# fmt: on


def rect_overlap(r1, r2):
    return (r1[0] < r2[0] + r2[2] and
            r1[0] + r1[2] > r2[0] and
            r1[1] < r2[1] + r2[3] and
            r1[1] + r1[3] > r2[1])


class Piece():
    # piece types
    TLC = 0   # top left corner
    TRC = 1   # top right corner
    BLC = 2   # bottom left corner
    BRC = 3   # bottom right corner
    BEE = 4   # bottom even edge
    TEE = 5   # top even edge
    BOE = 6   # bottom odd edge
    TOE = 7   # top odd edge
    ROE = 8   # right odd edge
    LOE = 9   # left odd edge
    REE = 10  # right even edge
    LEE = 11  # left even edge
    MID = 12  # middle piece
    MDR = 13  # middle piece rotated
    TRE = 14  # top right corner even
    BLE = 15  # bottom left corner even

    def __init__(self, img, crop, ptype, row, col, x_ext, y_ext):
        self.sprite = pg.image.fromstring(img.tobytes("raw", 'RGBA'), img.size, 'RGBA')
        self.crop = pg.image.fromstring(crop.tobytes("raw", 'RGB'), crop.size, 'RGB')
        self.w, self.h = img.size
        self.ptype = ptype
        self.row, self.col = row, col
        self.x_ext, self.y_ext = x_ext, y_ext
        self.x, self.y = 0, 0
        self.disp_x, self.disp_y = 0, 0
        self.group = set([self])
        self.locked = False
        self.adj = None

    def spos(self):
        return (self.sx(), self.sy())

    def sx(self):
        if self.ptype in (self.TRC, self.BRC, self.BEE,
                          self.TEE, self.ROE, self.MID):
            return self.disp_x - self.x_ext
        else:
            return self.disp_x

    def sy(self):
        if self.ptype in (self.BOE, self.REE, self.LEE,
                          self.MDR, self.BLE):
            return self.disp_y - self.y_ext
        else:
            return self.disp_y

    def place(self):
        self.disp_x, self.disp_y = self.x, self.y


class Puzzle():
    def __init__(self, img, width, height, downscale=-1, margin=2):
        if width <= 1 or height <= 1:
            raise ValueError("Puzzle dimensions must be greater than 1")
        img_w, img_h = img.size

        if downscale > 0 and max(img.size) > downscale:
            if img_w > img_h:
                img_h = int(img_h * downscale / img_w)
                img_w = downscale
            else:
                img_w = int(img_w * downscale / img_h)
                img_h = downscale
            img = img.resize((img_w, img_h))

        self.w, self.h = img_w * (margin * 2 + 1), img_h * (margin * 2 + 1)
        self.origin_x, self.origin_y = img_w * margin, img_h * margin

        piece_w, piece_h = img_w / width, img_h / height
        base_mask = Image.open("mask.png")
        base_mask_w, base_mask_h = base_mask.size
        mask_xscale = piece_w / base_mask_w
        mask_yscale = piece_h / base_mask_h

        corner_mask = Image.open("corner.png")
        ext = (corner_mask.size[0] - base_mask_w)
        x_ext = ext * mask_xscale
        y_ext = ext * mask_yscale

        self.width, self.height = width, height
        self.img, self.img_w, self.img_h = img, img_w, img_h
        self.piece_w, self.piece_h = piece_w, piece_h
        self.connect_tol = min(piece_w, piece_h) / 5

        self.pieces = []
        self.matrix = {}
        for r in range(height):
            for c in range(width):
                if r == 0 and c == 0:
                    # top left corner
                    ptype = Piece.TLC
                    base = Image.open("corner.png")
                    mask = Image.open("corner_blur.png")
                    crop = img.crop((0, 0, piece_w + x_ext, piece_h))
                elif r == 0 and c == width - 1:
                    # top right corner
                    if width % 2 == 0:
                        ptype = Piece.TRE
                        base = Image.open("corner.png").transpose(Image.ROTATE_270)
                        mask = Image.open("corner_blur.png").transpose(Image.ROTATE_270)
                        crop = img.crop((img_w - piece_w, 0, img_w, piece_h + y_ext))
                    else:
                        ptype = Piece.TRC
                        base = Image.open("corner.png").transpose(Image.FLIP_LEFT_RIGHT)
                        mask = Image.open("corner_blur.png").transpose(Image.FLIP_LEFT_RIGHT)
                        crop = img.crop((img_w - piece_w - x_ext, 0, img_w, piece_h))
                elif r == height - 1 and c == 0:
                    # bottom left corner
                    if height % 2 == 0:
                        ptype = Piece.BLE
                        base = Image.open("corner.png").transpose(Image.ROTATE_90)
                        mask = Image.open("corner_blur.png").transpose(Image.ROTATE_90)
                        crop = img.crop((0, img_h - piece_h - y_ext, piece_w, img_h))
                    else:
                        ptype = Piece.BLC
                        base = Image.open("corner.png").transpose(Image.FLIP_TOP_BOTTOM)
                        mask = Image.open("corner_blur.png").transpose(Image.FLIP_TOP_BOTTOM)
                        crop = img.crop((0, img_h - piece_h, piece_w + x_ext, img_h))
                elif r == height - 1 and c == width - 1:
                    # bottom right corner
                    ptype = Piece.BRC
                    base = Image.open("corner.png").transpose(
                        Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
                    mask = Image.open("corner_blur.png").transpose(
                        Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
                    crop = img.crop((img_w - piece_w - x_ext, img_h - piece_h, img_w, img_h))
                elif r == 0 or r == height - 1:
                    # horizontal edge
                    if bool(c % 2 == 0) ^ bool(height % 2 == 0 and r == height - 1):
                        base = Image.open("even_edge.png")
                        mask = Image.open("even_edge_blur.png")
                        if r == height - 1:
                            # bottom edge
                            ptype = Piece.BEE
                            base = base.transpose(Image.FLIP_TOP_BOTTOM)
                            mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                            crop = img.crop((c * piece_w - x_ext, img_h - piece_h,
                                            (c + 1) * piece_w + x_ext, img_h))
                        else:
                            # top edge
                            ptype = Piece.TEE
                            crop = img.crop(
                                (c * piece_w - x_ext, 0, (c + 1) * piece_w + x_ext, piece_h))
                    else:
                        base = Image.open("odd_edge.png")
                        mask = Image.open("odd_edge_blur.png")
                        if r == height - 1:
                            # bottom edge
                            ptype = Piece.BOE
                            base = base.transpose(Image.FLIP_TOP_BOTTOM)
                            mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                            crop = img.crop((c * piece_w, img_h - piece_h -
                                            y_ext, (c + 1) * piece_w, img_h))
                        else:
                            # top edge
                            ptype = Piece.TOE
                            crop = img.crop((c * piece_w, 0, (c + 1) * piece_w, piece_h + y_ext))
                elif c == 0 or c == width - 1:
                    # vertical edge (switch odd and even edges)
                    if bool(r % 2 == 0) ^ bool(width % 2 == 0 and c == width - 1):
                        base = Image.open("odd_edge.png")
                        mask = Image.open("odd_edge_blur.png")
                        if c == width - 1:
                            # right edge
                            ptype = Piece.ROE
                            base = base.transpose(Image.ROTATE_270)
                            mask = mask.transpose(Image.ROTATE_270)
                            crop = img.crop((img_w - piece_w - x_ext, r *
                                            piece_h, img_w, (r + 1) * piece_h))
                        else:
                            # left edge
                            ptype = Piece.LOE
                            base = base.transpose(Image.ROTATE_90)
                            mask = mask.transpose(Image.ROTATE_90)
                            crop = img.crop((0, r * piece_h, piece_w + x_ext, (r + 1) * piece_h))
                    else:
                        base = Image.open("even_edge.png")
                        mask = Image.open("even_edge_blur.png")
                        if c == width - 1:
                            # right edge
                            ptype = Piece.REE
                            base = base.transpose(Image.ROTATE_270)
                            mask = mask.transpose(Image.ROTATE_270)
                            crop = img.crop((img_w - piece_w, r * piece_h - y_ext,
                                            img_w, (r + 1) * piece_h + y_ext))
                        else:
                            # left edge
                            ptype = Piece.LEE
                            base = base.transpose(Image.ROTATE_90)
                            mask = mask.transpose(Image.ROTATE_90)
                            crop = img.crop((0, r * piece_h - y_ext, piece_w,
                                            (r + 1) * piece_h + y_ext))
                elif r % 2 == c % 2:
                    ptype = Piece.MID
                    base = Image.open("middle.png")
                    mask = Image.open("middle_blur.png")
                    crop = img.crop((c * piece_w - x_ext, r * piece_h,
                                    (c + 1) * piece_w + x_ext, (r + 1) * piece_h))
                else:
                    ptype = Piece.MDR
                    base = Image.open("middle.png").transpose(Image.ROTATE_90)
                    mask = Image.open("middle_blur.png").transpose(Image.ROTATE_90)
                    crop = img.crop((c * piece_w, r * piece_h - y_ext,
                                    (c + 1) * piece_w, (r + 1) * piece_h + y_ext))

                base = base.resize(crop.size)
                mask = mask.resize(crop.size)
                piece = Piece(Image.composite(crop, base, mask), crop, ptype, r, c, x_ext, y_ext)
                self.pieces.append(piece)
                self.matrix[(r, c)] = piece

                if random.choice([True, False]):
                    piece.x = random.choice(
                        [random.randrange(int(img_w / 2), int(self.origin_x - piece.w)),
                         random.randrange(int(self.origin_x + img_w + piece.x - piece.sx()),
                                          int(self.w - img_w / 2))])
                    piece.y = random.randrange(int(img_h / 2), int(self.h - img_h / 2))
                else:
                    piece.y = random.choice(
                        [random.randrange(int(img_h / 2), int(self.origin_y - piece.h)),
                         random.randrange(int(self.origin_y + img_h + piece.y - piece.sy()),
                                          int(self.h - img_h / 2))])
                    piece.x = random.randrange(int(img_w / 2), int(self.w - img_w / 2))
                piece.place()

    def click_check(self, x, y):
        for i in range(len(self.pieces) - 1, -1, -1):
            p = self.pieces[i]
            if (not p.locked and
                p.disp_x < x < p.disp_x + self.piece_w and
                    p.disp_y < y < p.disp_y + self.piece_h):
                self.pieces.pop(i)
                self.pieces.append(p)
                return p
        return None

    def move_piece(self, piece, dx, dy):
        if piece.locked:
            return
        for p in piece.group:
            if p.sx() + dx < 0 or p.sx() + dx + p.w > self.w:
                dx = 0
            if p.sy() + dy < 0 or p.sy() + dy + p.h > self.h:
                dy = 0
            if dx == 0 and dy == 0:
                break
        for p in piece.group:
            p.disp_x += dx
            p.disp_y += dy
            self.pieces.remove(p)
            self.pieces.append(p)

    def place_piece(self, piece, x, y):
        if piece.locked:
            return
        dx = x - piece.x
        dy = y - piece.y
        for p in piece.group:
            p.x += dx
            p.y += dy
            p.place()
            self.pieces.remove(p)
            self.pieces.append(p)

    def subsurface(self, ss_x, ss_y, ss_width, ss_height, scale):
        scale_dims = (int(ss_width * scale), int(ss_height * scale))
        frame = pg.Surface(scale_dims, flags=pg.HWSURFACE)
        frame.fill(BG_COLOR)
        rx = max(self.origin_x, ss_x)
        ry = max(self.origin_y, ss_y)
        rw = min(self.origin_x + self.img_w, ss_x + ss_width) - rx
        rh = min(self.origin_y + self.img_h, ss_y + ss_height) - ry
        rx -= ss_x
        ry -= ss_y
        if rw > 0 and rh > 0:
            pg.draw.rect(frame, BLACK, (int(rx * scale), int(ry * scale),
                         int(rw * scale), int(rh * scale)))

        for p in self.pieces:
            if not p.locked:
                continue
            if rect_overlap((ss_x, ss_y, ss_width, ss_height), (p.sx(), p.sy(), p.w, p.h)):
                frame.blit(pg.transform.scale(p.sprite, (int(p.w * scale), int(p.h * scale))),
                           (int((p.sx() - ss_x) * scale), int((p.sy() - ss_y) * scale)))

        for p in self.pieces:
            if p.locked:
                continue
            if rect_overlap((ss_x, ss_y, ss_width, ss_height), (p.sx(), p.sy(), p.w, p.h)):
                frame.blit(pg.transform.scale(p.sprite, (int(p.w * scale), int(p.h * scale))),
                           (int((p.sx() - ss_x) * scale), int((p.sy() - ss_y) * scale)))

        return frame

    def complete(self):
        return len(self.pieces[0].group) == self.width * self.height

    def landlock_check(self, piece):
        if piece.adj is None:
            piece.adj = set()
            neighbors = [self.matrix.get((piece.row - 1, piece.col), None),
                         self.matrix.get((piece.row + 1, piece.col), None),
                         self.matrix.get((piece.row, piece.col - 1), None),
                         self.matrix.get((piece.row, piece.col + 1), None)]
            for n in neighbors:
                if n is not None:
                    piece.adj.add(n)
        if piece.adj.issubset(piece.group):
            piece.sprite = piece.crop.convert()

    def connection_check(self, piece):
        for p in piece.group:
            self.single_connection_check(p)

    def single_connection_check(self, piece):
        if piece.locked:
            return

        def check_single(other, tx, ty):
            dx, dy = tx - piece.x, ty - piece.y
            if abs(dx) < self.connect_tol and abs(dy) < self.connect_tol:
                if piece.locked:
                    self.place_piece(other, other.x - dx, other.y - dy)
                else:
                    self.place_piece(piece, tx, ty)
                new_group = piece.group.union(other.group)
                locked = piece.locked or other.locked
                for p in new_group:
                    p.group = new_group
                    p.locked = locked
                    self.landlock_check(p)

        n = self.matrix.get((piece.row - 1, piece.col), None)
        if n is not None and n not in piece.group:
            check_single(n, n.x, n.y + self.piece_h)

        n = self.matrix.get((piece.row, piece.col - 1), None)
        if n is not None and n not in piece.group:
            check_single(n, n.x + self.piece_w, n.y)

        n = self.matrix.get((piece.row + 1, piece.col), None)
        if n is not None and n not in piece.group:
            check_single(n, n.x, n.y - self.piece_h)

        n = self.matrix.get((piece.row, piece.col + 1), None)
        if n is not None and n not in piece.group:
            check_single(n, n.x - self.piece_w, n.y)

        def check_corner(dx, dy):
            if abs(dx) < self.connect_tol and abs(dy) < self.connect_tol:
                self.place_piece(piece, piece.x + dx, piece.y + dy)
                for p in piece.group:
                    p.locked = True

        if piece.row == 0:
            if piece.col == 0:
                check_corner(self.origin_x - piece.x,
                             self.origin_y - piece.y)
            elif piece.col == self.width - 1:
                check_corner(self.origin_x + self.img_w - self.piece_w - piece.x,
                             self.origin_y - piece.y)
        if piece.row == self.height - 1:
            if piece.col == 0:
                check_corner(self.origin_x - piece.x,
                             self.origin_y + self.img_h - self.piece_h - piece.y)
            elif piece.col == self.width - 1:
                check_corner(self.origin_x + self.img_w - self.piece_w - piece.x,
                             self.origin_y + self.img_h - self.piece_h - piece.y)
