import math
import pygame as pg
from PIL import Image, ImageTk

BG_COLOR = (44, 47, 51)

class Piece():
    # piece types
    TLC = 0
    TRC = 1
    BLC = 2
    BRC = 3
    BEE = 4
    TEE = 5
    BOE = 6
    TOE = 7
    ROE = 8
    LOE = 9
    REE = 10
    LEE = 11
    MID = 12
    MDR = 13

    def __init__(self, img, ptype, row, col, x_ext, y_ext):
        self.sprite = pg.image.fromstring(img.tobytes("raw", 'RGBA'), img.size, 'RGBA')
        self.w, self.h = img.size
        self.ptype = ptype
        self.row, self.col = row, col
        self.x_ext, self.y_ext = x_ext, y_ext
        self.x, self.y = 0, 0


    def sx(self):
        if self.ptype in (self.TRC, self.BRC, self.BEE,
                          self.TEE, self.ROE, self.MID):
            return self.x - self.x_ext
        else:
            return self.x


    def sy(self):
        if self.ptype in (self.BOE, self.REE, self.LEE, self.MDR):
            return self.y - self.y_ext
        else:
            return self.y


class Puzzle():
    def __init__(self, img_path, W, H, downscale=-1):
        if W % 2 == 0 or H % 2 == 0: raise ValueError("Puzzle dimensions must be odd")
        img = Image.open(img_path)
        img_w, img_h = img.size

        if downscale > 0 and max(img.size) > downscale:
            if img_w > img_h:
                img_h = int(img_h * downscale / img_w)
                img_w = downscale
            else:
                img_w = int(img_w * downscale / img_h)
                img_h = downscale
            img = img.resize((img_w, img_h))

        self.scale = 1
        self.surface = pg.Surface((img_w * 3, img_h * 3))
        self.surface.fill(BG_COLOR)
        pg.draw.rect(self.surface, (0, 0, 0), (img_w, img_h, img_w, img_h))

        piece_w, piece_h = img_w / W, img_h / H
        base_mask = Image.open("mask.png")
        base_mask_w, base_mask_h = base_mask.size
        mask_xscale = piece_w / base_mask_w;
        mask_yscale = piece_h / base_mask_h;

        corner_mask = Image.open("corner.png")
        ext = (corner_mask.size[0] - base_mask_w)
        x_ext = ext * mask_xscale
        y_ext = ext * mask_yscale

        self.W, self.H = W, H
        self.img, self.img_w, self.img_h = img, img_w, img_h
        self.piece_w, self.piece_h = piece_w, piece_h
        self.x_ext, self.y_ext = x_ext, y_ext

        self.pieces = []
        self.moved_pieces = []
        for r in range(H):
            for c in range(W):
                if (r == 0 and c == 0):
                    # top left corner
                    ptype = Piece.TLC
                    mask = Image.open("corner_blur.png")
                    crop = img.crop((0, 0, piece_w + x_ext, piece_h))
                elif (r == 0 and c == W - 1):
                    # top right corner
                    ptype = Piece.TRC
                    mask = Image.open("corner_blur.png").transpose(Image.FLIP_LEFT_RIGHT)
                    crop = img.crop((img_w - piece_w - x_ext, 0, img_w, piece_h))
                elif (r == H - 1 and c == 0):
                    # bottom left corner
                    ptype = Piece.BLC
                    mask = Image.open("corner_blur.png").transpose(Image.FLIP_TOP_BOTTOM)
                    crop = img.crop((0, img_h - piece_h, piece_w + x_ext, img_h))
                elif (r == H - 1 and c == W - 1):
                    # bottom right corner
                    ptype = Piece.BRC
                    mask = Image.open("corner_blur.png").transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
                    crop = img.crop((img_w - piece_w - x_ext, img_h - piece_h, img_w, img_h))
                elif (r == 0 or r == H - 1):
                    # horizontal edge
                    if (c % 2 == 0):
                        mask = Image.open("even_edge_blur.png")
                        if (r == H - 1):
                            # bottom edge
                            ptype = Piece.BEE
                            mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                            crop = img.crop((c * piece_w - x_ext, img_h - piece_h, (c + 1) * piece_w + x_ext, img_h))
                        else:
                            # top edge
                            ptype = Piece.TEE
                            crop = img.crop((c * piece_w - x_ext, 0, (c + 1) * piece_w + x_ext, piece_h))
                    else:
                        mask = Image.open("odd_edge_blur.png")
                        if (r == H - 1):
                            # bottom edge
                            ptype = Piece.BOE
                            mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
                            crop = img.crop((c * piece_w, img_h - piece_h - y_ext, (c + 1) * piece_w, img_h))
                        else:
                            # top edge
                            ptype = Piece.TOE
                            crop = img.crop((c * piece_w, 0, (c + 1) * piece_w, piece_h + y_ext))
                elif (c == 0 or c == W - 1):
                    # vertical edge (switch odd and even edges)
                    if (r % 2 == 0):
                        mask = Image.open("odd_edge_blur.png")
                        if (c == W - 1):
                            # right edge
                            ptype = Piece.ROE
                            mask = mask.transpose(Image.ROTATE_270)
                            crop = img.crop((img_w - piece_w - x_ext, r * piece_h, img_w, (r + 1) * piece_h))
                        else:
                            # left edge
                            ptype = Piece.LOE
                            mask = mask.transpose(Image.ROTATE_90)
                            crop = img.crop((0, r * piece_h, piece_w + x_ext, (r + 1) * piece_h))
                    else:
                        mask = Image.open("even_edge_blur.png")
                        if (c == W - 1):
                            # right edge
                            ptype = Piece.REE
                            mask = mask.transpose(Image.ROTATE_270)
                            crop = img.crop((img_w - piece_w, r * piece_h - y_ext, img_w, (r + 1) * piece_h + y_ext))
                        else:
                            # left edge
                            ptype = Piece.LEE
                            mask = mask.transpose(Image.ROTATE_90)
                            crop = img.crop((0, r * piece_h - y_ext, piece_w, (r + 1) * piece_h + y_ext))
                elif (r % 2 == c % 2):
                    ptype = Piece.MID
                    mask = Image.open("middle_blur.png")
                    crop = img.crop((c * piece_w - x_ext, r * piece_h,
                                    (c + 1) * piece_w + x_ext, (r + 1) * piece_h))
                else:
                    ptype = Piece.MDR
                    mask = Image.open("middle_blur.png").transpose(Image.ROTATE_90)
                    crop = img.crop((c * piece_w, r * piece_h - y_ext,
                                    (c + 1) * piece_w, (r + 1) * piece_h + y_ext))

                mask = mask.resize(crop.size)
                piece = Piece(Image.composite(crop, mask, mask), ptype, r, c, x_ext, y_ext)
                self.pieces.append(piece)
                piece.x = c * piece_w + img_w
                piece.y = r * piece_h + img_h
                sprite = pg.transform.scale(piece.sprite, (int(piece.sprite.get_width() * self.scale),
                                                        int(piece.sprite.get_height() * self.scale)))
                self.surface.blit(sprite, (piece.sx() * self.scale, piece.sy() * self.scale))
            

def main():
    pg.init()
    display_flags = pg.RESIZABLE
    sw, sh = 1000, 1000
    screen = pg.display.set_mode([sw, sh], flags=display_flags)
    puzzle = Puzzle("rock.png", 9, 7)
    pw, ph = puzzle.surface.get_width(), puzzle.surface.get_height()

    # scale = 1000 / max(pw, ph)
    scale = 1
    scale_factor = 10 / 9

    panning = False
    pan_x, pan_y = 0, 0
    # pan_x = pw / 2 - sw / 2
    # pan_y = ph / 2 - sh / 2

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_SPACE:
                    pan_x = pw / 2 - sw / 2
                    pan_y = ph / 2 - sh / 2
            elif event.type == pg.VIDEORESIZE:
                sw, sh = event.w, event.h
                screen = pg.display.set_mode([sw, sh], flags=display_flags)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pass
                elif event.button == 3:
                    panning = True
                elif event.button == 4:
                    pan_x = (pan_x + sw / 2) / scale
                    pan_y = (pan_y + sh / 2) / scale
                    scale *= scale_factor
                    pan_x = pan_x * scale - sw / 2
                    pan_y = pan_y * scale - sh / 2
                elif event.button == 5:
                    pan_x = (pan_x + sw / 2) / scale
                    pan_y = (pan_y + sh / 2) / scale
                    scale /= scale_factor
                    pan_x = pan_x * scale - sw / 2
                    pan_y = pan_y * scale - sh / 2
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    pass
                elif event.button == 3:
                    panning = False
            elif event.type == pg.MOUSEMOTION:
                if panning:
                    pan_x -= event.rel[0] / scale
                    pan_y -= event.rel[1] / scale

        ss_x, ss_y = pan_x, pan_y
        blit_x, blit_y = 0, 0
        ss_width = sw / scale
        ss_height = sh / scale

        if pan_x < 0:
            ss_x = 0
            blit_x = int(-pan_x * scale)
        if pan_y < 0:
            ss_y = 0
            blit_y = int(-pan_y * scale)
        if ss_x + ss_width > pw:
            ss_width = pw - ss_x
        if ss_y + ss_height > ph:
            ss_height = ph - ss_y

        screen.fill(BG_COLOR)
        print(scale)
        print((ss_width, ss_height, blit_x, blit_y))
        subsurf = puzzle.surface.subsurface(int(ss_x), int(ss_y), int(ss_width), int(ss_height))
        screen.blit(pg.transform.scale(subsurf, (int(ss_width * scale), int(ss_height * scale))), (blit_x, blit_y))
        pg.display.flip()
    pg.quit()


if __name__ == "__main__":
    main()