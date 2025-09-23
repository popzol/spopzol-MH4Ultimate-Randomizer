# Copyright 2016 dasding
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from etc1 import *
from util import *

from PIL import Image
import array
import struct

blockorder = [0, 1, 8, 9, 2, 3, 10, 11, 16, 17, 24, 25, 18, 19, 26, 27, 4, 5, 12, 13, 6, 7, 14, 15, 20, 21, 28, 29, 22, 23, 30, 31, 32, 33, 40, 41, 34, 35, 42, 43, 48, 49, 56, 57, 50, 51, 58, 59, 36, 37, 44, 45, 38, 39, 46, 47, 52, 53, 60, 61, 54, 55, 62, 63]

map8bit6bit = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15, 16, 16, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 23, 24, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 26, 27, 27, 27, 27, 28, 28, 28, 28, 29, 29, 29, 29, 30, 30, 30, 30, 31, 31, 31, 31, 32, 32, 32, 32, 32, 33, 33, 33, 33, 34, 34, 34, 34, 35, 35, 35, 35, 36, 36, 36, 36, 37, 37, 37, 37, 38, 38, 38, 38, 39, 39, 39, 39, 40, 40, 40, 40, 41, 41, 41, 41, 42, 42, 42, 42, 43, 43, 43, 43, 44, 44, 44, 44, 45, 45, 45, 45, 46, 46, 46, 46, 47, 47, 47, 47, 48, 48, 48, 48, 48, 49, 49, 49, 49, 50, 50, 50, 50, 51, 51, 51, 51, 52, 52, 52, 52, 53, 53, 53, 53, 54, 54, 54, 54, 55, 55, 55, 55, 56, 56, 56, 56, 57, 57, 57, 57, 58, 58, 58, 58, 59, 59, 59, 59, 60, 60, 60, 60, 61, 61, 61, 61, 62, 62, 62, 62, 63, 63]
map8bit5bit = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25, 25, 25, 25, 25, 26, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 27, 27, 27, 28, 28, 28, 28, 28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 30, 30, 30, 31, 31, 31, 31]
map8bit4bit = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]

mod_order = [
(0, 0), (0, 1), (0, 2), (0, 3),
(1, 0), (1, 1), (1, 2), (1, 3),
(2, 0), (2, 1), (2, 2), (2, 3),
(3, 0), (3, 1), (3, 2), (3, 3)
]

def num_k_to_n_bits(v, k, n):
    return ((v << (n - k)) | (v >> (k + k - n))) & 0xFF

def readImage(path):
    log_loading(path)
    try:
        image = Image.open(path)
        return image
    except IOError:
        error('Loading ' + path)

def writeImage(path, image):
    log_saving(path)
    try:
        image.save(path)
    except IOError:
        error('Saving ' + path)

def packpixel(px):
    return (px[0] & 255) + ((px[1] & 255) << 8) + ((px[2] & 255) << 16) + ((px[3] & 255) << 24)

def clamp(px):
    for i in xrange(4):
        if px[i] > 255:
            px[i] = 255
    return px

def mux_alpha(rgb, alpha):
    width  = rgb.width
    height = rgb.height
    pixel_count = width * height

    rgb   = list(rgb.getdata())
    alpha = list(alpha.getdata())
    raw   = array.array('I', [0]) * pixel_count

    for px in range(pixel_count):
        px_color = [0, 0, 0, 0]
        px_color[0] = rgb[px][0]
        px_color[1] = rgb[px][1]
        px_color[2] = rgb[px][2]
        px_color[3] = (alpha[px][0] + alpha[px][1] + alpha[px][2]) // 3

        pixel  = packpixel(px_color)
        raw[px] = pixel
    return Image.frombytes('RGBA', (width, height), raw.tostring(), 'raw', 'RGBA')


def demux_alpha(data):
    pixel_count = len(data) // 4
    rgb   = array.array('I', [0]) * pixel_count
    alpha = array.array('I', [0]) * pixel_count

    for px in range(pixel_count):
        px_color = [0, 0, 0, 255]
        px_alpha = [0, 0, 0, 255]
        px_color[0] = ord(data[px * 4 + 0])
        px_color[1] = ord(data[px * 4 + 1])
        px_color[2] = ord(data[px * 4 + 2])
        px_alpha[0] = ord(data[px * 4 + 3])
        px_alpha[1] = ord(data[px * 4 + 3])
        px_alpha[2] = ord(data[px * 4 + 3])

        pixel  = packpixel(px_color)
        pixela = packpixel(px_alpha)

        rgb[px] = pixel
        alpha[px] = pixela

    return rgb, alpha

# DECODING

def decode_pvrtc(data, width, height):
    data = array.array('I', data)
    w = width / 4
    h = height / 4
    out_a = array.array('I', [0]) * (w * h)
    out_b = array.array('I', [0]) * (w * h)
    out_mod = array.array('I', [0]) * (width * height)
    rgba = array.array('I', [0]) * (width * height)

    ONCE = 0
    for y in range(h):
        for x in range(w):
            k_x = ( (x&1)|((x&2)<<1)|((x&4)<<2)|((x&8)<<3)|((x&16)<<4)|((x&32)<<5)|((x&64)<<6)|((x&128)<<7)|((x&256)<<8)|((x&512)<<9) )
            k_y = ( (y&1)|((y&2)<<1)|((y&4)<<2)|((y&8)<<3)|((y&16)<<4)|((y&32)<<5)|((y&64)<<6)|((y&128)<<7)|((y&256)<<8)|((y&512)<<9) )
            k = k_y | (k_x << 1)

            mod_data = data[k * 2]

            word2 = data[k * 2 + 1] & 0xFFFF
            word1 = data[k * 2 + 1] >> 16 & 0xFFFF

            # fe 0f ff 0f
            color_a = [0, 0, 0, 0]
            color_b = [0, 0, 0, 0]

            alpha_a = word1 & 0x8000

            if alpha_a == 0:
                color_a[3] = (word1 & 0x7000) >> 12
                color_a[0] = (word1 & 0x0F00) >> 8
                color_a[1] = (word1 & 0x00F0) >> 4
                color_a[2] = word1 & 0x000F
                color_a[3] = num_k_to_n_bits(color_a[3], 3, 6)
                color_a[3] = num_k_to_n_bits(color_a[3], 6, 8)
                color_a[0] = num_k_to_n_bits(color_a[0], 4, 8)
                color_a[1] = num_k_to_n_bits(color_a[1], 4, 8)
                color_a[2] = num_k_to_n_bits(color_a[2], 4, 8)
            else:
                color_a[3] = 255
                color_a[0] = (word1 & 0x7C00) >> 10
                color_a[1] = (word1 & 0x03E0) >> 5
                color_a[2] = word1 & 0x001F
                color_a[0] = num_k_to_n_bits(color_a[0], 5, 8)
                color_a[1] = num_k_to_n_bits(color_a[1], 5, 8)
                color_a[2] = num_k_to_n_bits(color_a[2], 5, 8)

            alpha_b = word2 & 0x8000

            if alpha_b == 0:
                color_b[3] = (word2 & 0x7000) >> 12
                color_b[0] = (word2 & 0x0F00) >> 8
                color_b[1] = (word2 & 0x00F0) >> 4
                color_b[2] = (word2 & 0x000E) >> 1
                color_b[3] = num_k_to_n_bits(color_b[3], 3, 6)
                color_b[3] = num_k_to_n_bits(color_b[3], 6, 8)
                color_b[0] = num_k_to_n_bits(color_b[0], 4, 8)
                color_b[1] = num_k_to_n_bits(color_b[1], 4, 8)
                color_b[2] = num_k_to_n_bits(color_b[2], 3, 6)
                color_b[2] = num_k_to_n_bits(color_b[2], 6, 8)
            else:
                color_b[3] = 255
                color_b[0] = (word2 & 0x7C00) >> 10
                color_b[1] = (word2 & 0x03E0) >> 5
                color_b[2] = (word2 & 0x001e) >> 1
                color_b[0] = num_k_to_n_bits(color_b[0], 5, 8)
                color_b[1] = num_k_to_n_bits(color_b[1], 5, 8)
                color_b[2] = num_k_to_n_bits(color_b[2], 4, 8)


            mode = word2 & 0x1

            for i in xrange(4):
                for j in xrange(4):
                    mod = mod_data & 0x3
                    mod_data = mod_data >> 2

                    if mode:
                        v = [0, 4, 9, 8][mod]
                    else:
                        v = [0, 3, 5, 8][mod]
                    v *= 25
                    color_mod = [v, v, v, 255]
                    pixel_mod = packpixel(color_mod)
                    i_k, j_k = mod_order[i + j * 4]
                    out_mod[x * 4 + i_k + (y * 4 + j_k) * width] = pixel_mod

            pixel_a = packpixel(color_a)
            pixel_b = packpixel(color_b)
            out_a[y * w + x] = pixel_a
            out_b[y * w + x] = pixel_b

    image_a = Image.frombytes('RGBA', (w, h), out_a, 'raw', 'RGBA')
    image_b = Image.frombytes('RGBA', (w, h), out_b, 'raw', 'RGBA')
    image_mod = Image.frombytes('RGBA', (width, height), out_mod, 'raw', 'RGBA')

    image_a = image_a.resize((width, height), resample=Image.BILINEAR)
    image_b = image_b.resize((width, height), resample=Image.BILINEAR)

    for x in xrange(height):
        for y in xrange(width):
            color_a = image_a.getpixel((x,y))
            color_b = image_b.getpixel((x,y))
            color_mod = image_mod.getpixel((x,y))
            mod_a = (color_mod[0] / 25) / 8.
            mod_b = 1 - mod_a

            color = [0,0,0,0]
            color[0] = int(color_a[0] * mod_a + color_b[0] * mod_b)
            color[1] = int(color_a[1] * mod_a + color_b[1] * mod_b)
            color[2] = int(color_a[2] * mod_a + color_b[2] * mod_b)
            color[3] = int(color_a[3] * mod_a + color_b[3] * mod_b)

            if (color_mod[0] == 25 * 9):
                color = [0,0,0,0]

            color = clamp(color)
            pixel = packpixel(color)
            rgba[x + y * width] = pixel

    return rgba.tostring()


def decode_rgba4444(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 2

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]
            px_color[0] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1]) >> 4
            px_color[1] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1]) & 0xF
            px_color[2] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0]) >> 4
            px_color[3] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0]) & 0xF

            px_color[0] = px_color[0] << 4
            px_color[1] = px_color[1] << 4
            px_color[2] = px_color[2] << 4
            px_color[3] = px_color[3] << 4

            pixel = packpixel(px_color)

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()



def decode_rgb888(data, width, height, alpha=False):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 3 if not alpha else 4

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]
            if alpha:
                px_color[0] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 3])
                px_color[1] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 2])
                px_color[2] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1])
                px_color[3] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0])
            else:
                px_color[0] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 2])
                px_color[1] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1])
                px_color[2] = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0])
                px_color[3] = 255

            pixel = packpixel(px_color)

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()


def decode_rgb565(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 2

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]

            byte1 = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0])
            byte2 = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1])
            full = (byte2 << 8) + byte1

            px_color[2] = (full & 0x1F) << 3
            px_color[1] = (full >> 5 & 0x3f) << 2
            px_color[0] = (full >> 11 & 0x1f) << 3

            px_color[2] |=  px_color[2] >> 5
            px_color[1] |=  px_color[1] >> 6
            px_color[0] |=  px_color[0] >> 5

            px_color[3] = 255

            pixel = packpixel(px_color)

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()



def decode_l4(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]
            if px_index % 2 == 0:
                px_color = ord(data[block * BLOCK_SIZE // 2 + px_index // 2]) & 0xF
            else:
                px_color = (ord(data[block * BLOCK_SIZE // 2 + px_index // 2]) & 0xF0) >> 4

            px_color = px_color << 4 | px_color
            pixel = packpixel([px_color, px_color, px_color, px_color])

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()


def decode_l8(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]
            px_color = ord(data[block * BLOCK_SIZE + px_index])

            if px_color == 0:
                pixel = packpixel([px_color, px_color, px_color, 0])
            else:
                pixel = packpixel([px_color, px_color, px_color, 255])

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()


def decode_la88(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 2

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]
            px_color = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0])
            alpha = ord(data[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1])

            pixel = packpixel([px_color, px_color, px_color, alpha])

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()


def decode_a4(data, width, height):
    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT

    pixel_count = width * height
    rgba = array.array('I', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]
            if px_index % 2 == 0:
                px_color = ord(data[block * BLOCK_SIZE // 2 + px_index // 2]) & 0xF
            else:
                px_color = (ord(data[block * BLOCK_SIZE // 2 + px_index // 2]) & 0xF0) >> 4

            px_color = px_color << 4 | px_color
            pixel = packpixel([255, 255, 255, px_color])

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            rgba[y * width + x] = pixel

    return rgba.tostring()

# ENCODING


def encode_etc1(image, alpha=False):
    data = list(image.getdata())

    BLOCK_WIDTH  = 4
    BLOCK_HEIGHT = 4
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES        = 8 if not alpha else 16

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * (pixel_count // BLOCK_SIZE * BYTES)

    for block_idx in range(pixel_count // BLOCK_SIZE):
        block = [None for i in range(16)]
        for px_idx in range(16):
            offset = block_idx % 4
            x = (block_idx - offset) % (width // 2) * 2
            y = (block_idx - offset) // (width // 2) * 8
            if offset & 1:
                x += 4
            if offset & 2:
                y += 4

            x += px_idx % 4
            y += px_idx // 4

            pixel = data[y * width + x]

            block[px_idx] = Color(pixel[0], pixel[1], pixel[2], pixel[3])

        block_data = GenETC1(block)

        if alpha:
            for i in range(8):
                x = (i * 2) // 4
                y = (i * 2) % 4

                alpha1 = map8bit4bit[block[x + (y + 0) * 4].A]
                alpha2 = map8bit4bit[block[x + (y + 1) * 4].A] << 4
                raw[block_idx * BYTES + i]  = alpha1
                raw[block_idx * BYTES + i] |= alpha2

        for i in range(8):
            raw[block_idx * BYTES + i + BYTES - 8] = block_data >> (i * 8) & 0xFF

    return raw.tostring()


def encode_rgb888(image, alpha=False):
    data = list(image.getdata())

    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 3 if not alpha else 4

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * pixel_count * BYTES

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH

            px_color[0] = data[y * width + x][2]
            px_color[1] = data[y * width + x][1]
            px_color[2] = data[y * width + x][0]
            px_color[3] = data[y * width + x][3]

            if alpha:
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0] = px_color[3]
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1] = px_color[0]
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 2] = px_color[1]
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 3] = px_color[2]
            else:
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0] = px_color[0]
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1] = px_color[1]
                raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 2] = px_color[2]

    return raw.tostring()


def encode_rgba4444(image):
    data = list(image.getdata())

    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 2

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * pixel_count * BYTES

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px_color = [0, 0, 0, 0]
            px = blockorder[px_index]

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH

            px_color[0] = data[y * width + x][0]
            px_color[1] = data[y * width + x][1]
            px_color[2] = data[y * width + x][2]
            px_color[3] = data[y * width + x][3]

            px0 = map8bit4bit[px_color[3]] | (map8bit4bit[px_color[2]] << 4)
            px1 = map8bit4bit[px_color[1]] | (map8bit4bit[px_color[0]] << 4)
            raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0] = px0
            raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1] = px1

    return raw.tostring()



def encode_a4(image):
    data = list(image.getdata())

    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * (pixel_count // 2)

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            px_color = data[y * width + x][3]

            px_color = map8bit4bit[px_color]

            if px_index % 2 == 0:
                raw[block * BLOCK_SIZE // 2 + px_index // 2] = px_color
            else:
                raw[block * BLOCK_SIZE // 2 + px_index // 2] |= px_color << 4

    return raw.tostring()


def encode_l8(image):
    data = list(image.getdata())

    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * pixel_count

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH
            px_color = data[y * width + x][0]
            px_color += data[y * width + x][1]
            px_color += data[y * width + x][2]
            px_color = px_color // 3

            if data[y * width + x][3] == 0:
                px_color = 0

            raw[block * BLOCK_SIZE + px_index] = px_color

    return raw.tostring()

def encode_rgb565(image):
    data = list(image.getdata())

    BLOCK_WIDTH  = 8
    BLOCK_HEIGHT = 8
    BLOCK_SIZE   = BLOCK_WIDTH * BLOCK_HEIGHT
    BYTES = 2

    width  = image.width
    height = image.height
    pixel_count = width * height

    raw = array.array('B', [0]) * pixel_count * BYTES

    for block in range(pixel_count // BLOCK_SIZE):
        for px_index in range(BLOCK_SIZE):
            px = blockorder[px_index]

            x = (block % (width // BLOCK_WIDTH)) * BLOCK_WIDTH + px % BLOCK_WIDTH
            y = (block // (width // BLOCK_WIDTH)) * BLOCK_HEIGHT + px // BLOCK_WIDTH

            r = map8bit5bit[data[y * width + x][0]]
            g = map8bit6bit[data[y * width + x][1]]
            b = map8bit5bit[data[y * width + x][2]]

            full = b + (g << 5) + (r << 11)

            byte1 = full & 0xFF
            byte2 = full >> 8 & 0xFF

            raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 0] = byte1
            raw[block * BLOCK_SIZE * BYTES + px_index * BYTES + 1] = byte2

    return raw.tostring()


