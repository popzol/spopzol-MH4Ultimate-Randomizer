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

from PIL import Image

from util import *
from texutil import *


class TEX:
    magic = ['TEX\x00', 'TEX ', ' XET', '\x00XET']
    formats = {
        1: 'rgba4444',
        3: 'rgba8888',
        4: 'rgb565',
        7: 'la88',
        11: 'etc1',
        12: 'etc1_4a',
        14: 'a4',
        15: 'l4',
        16: 'l8',
        17: 'rgb888',
        99: 'pvrtc 4bpp'
    }

    def __init__(self, tex=None):
        self.mipmaps = []
        if tex:
            self.import_tex(tex)

    def import_tex(self, tex):
        if read_block(tex, 0x0, 0x4) in [' XET', '\x00XET']:
            tex = byteswap(tex[:0x10]) + tex[0x10:]
        self._meta  = bytearray(read_block(tex, 0x0, 0x10))
        self.parse_meta(self._meta)

        if self.version == 165 or self.version == 166:
            self.mipmap_offsets = read_dword_array(tex, 0x10, self.mipmap_count)
        self.mipmaps = [None for i in range(self.mipmap_count)]

        for i in range(self.mipmap_count):
            self.mipmaps[i] = self.parse_mipmap(tex, self.mipmap_offsets[i] + self.data_offset, i)

    def export_tex(self):
        tex = bytearray()
        write_block(tex, 0x0, self._meta)
        write_byte(tex, 0xD, self.format)
        alloc_block(tex, len(self.mipmaps) * 4)

        for i in range(len(self.mipmaps)):
            if self.format == 1:
                # rgba4444
                data = encode_rgba4444(self.mipmaps[i])
            elif self.format == 3:
                # rgba8888
                data = encode_rgb888(self.mipmaps[i], True)
            elif self.format == 4:
                # rgb565
                data = encode_rgb565(self.mipmaps[i])
            elif self.format == 11:
                # etc1
                data = encode_etc1(self.mipmaps[i], False)
            elif self.format == 12:
                # etc1_4a
                data = encode_etc1(self.mipmaps[i], True)
            elif self.format == 14:
                # a4
                data = encode_a4(self.mipmaps[i])
            elif self.format == 16:
                # l8
                data = encode_l8(self.mipmaps[i])
            elif self.format == 17:
                # rgb888
                data = encode_rgb888(self.mipmaps[i])
            else:
                error('Unrecognized Format: %2d' % self.format)

            write_dword(tex, 0x10 + i * 4, len(tex) - self.data_offset)
            write_block(tex, len(tex), data)
        return tex

    def parse_meta(self, meta):
        self.magic  = read_block(meta, 0x0, 0x4)
        if self.magic not in TEX.magic:
            error("Invalid Magic Identifier")

        self.version  = read_word(meta, 0x4)

        header = [
            read_dword(meta, 0x4),
            read_dword(meta, 0x8),
            read_dword(meta, 0xC)
        ]

        if self.version == 165 or self.version == 166:
            self.alpha      = read_byte(meta, 0x06)
            self.format     = read_byte(meta, 0x0D)

            self.constant   = header[0] & 0xfff  # 0xA50
            # self.unknown1   = (header[0] >> 12) & 0xfff
            self.size_shift = (header[0] >> 24) & 0xf
            # self.unknown2   = (header[0] >> 28) & 0xf

            self.mipmap_count = header[1] & 0x3f
            self.width        = (header[1] >> 6) & 0x1fff
            self.height       = (header[1] >> 19) & 0x1fff

            self.mipmap_mul = header[2] & 0xff
            # self.unknown5   = (header[2] >> 16) & 0x1fff

            self.data_offset = 0x10 + 4 * self.mipmap_count

        elif self.version == 2:
            self.alpha      = read_byte(meta, 0x05)
            self.format     = read_byte(meta, 0x0E)
            self.mipmap_count = 1
            print hex(header[1])
            self.width        = (header[1]) & 0x1fff
            self.height       = (header[1] >> 13) & 0x1fff
            self.data_offset = 0x10
            self.mipmap_offsets = [0]


        elif self.version == 9:
            self.format = 99
            self.height = read_word(meta, 0x0C)
            self.width = read_byte(meta, 0xE) * 8
            self.mipmap_count = 1
            self.alpha = 0
            self.data_offset = 0x10

            self.mipmap_offsets = [0]
            for mipmap_level in xrange(1, self.mipmap_count):
                width = self.width // (2**(mipmap_level - 1))
                height = self.height // (2**(mipmap_level - 1))
                self.mipmap_offsets.append(self.mipmap_offsets[mipmap_level - 1] + (width * height) / 16 * 8)
        else:
            error('Unsupported Version: {}'.format(self.version))

    def parse_mipmap(self, tex, offset, mipmap_level):
        width = self.width // (2**mipmap_level)
        height = self.height // (2**mipmap_level)
        pixel_count = width * height
        if self.format == 1:
            # rgba4444
            raw = read_block(tex, offset, pixel_count * 2)
            raw_rgba = decode_rgba4444(raw, width, height)
        elif self.format == 3:
            # rgba
            raw = read_block(tex, offset, pixel_count * 4)
            raw_rgba = decode_rgb888(raw, width, height, True)
        elif self.format == 4:
            # rgb565
            raw = read_block(tex, offset, pixel_count * 2)
            raw_rgba = decode_rgb565(raw, width, height)
        elif self.format == 7:
            # la88
            raw = read_block(tex, offset, pixel_count * 2)
            raw_rgba = decode_la88(raw, width, height)
        elif self.format == 11:
            # etc1
            raw = read_block(tex, offset, pixel_count // 2)
            raw_rgba = decode_etc1(raw, width, height)
        elif self.format == 12:
            # etc1_4a
            raw = read_block(tex, offset, pixel_count)
            raw_rgba = decode_etc1(raw, width, height, True)
        elif self.format == 14:
            # a4
            raw = read_block(tex, offset, pixel_count // 2)
            raw_rgba = decode_a4(raw, width, height)
        elif self.format == 15:
            # l4
            raw = read_block(tex, offset, pixel_count // 2)
            raw_rgba = decode_l4(raw, width, height)
        elif self.format == 16:
            # l8
            raw = read_block(tex, offset, pixel_count)
            raw_rgba = decode_l8(raw, width, height)
        elif self.format == 17:
            # rgb8
            raw = read_block(tex, offset, pixel_count * 3)
            raw_rgba = decode_rgb888(raw, width, height)
        elif self.format == 99:
            # pvrtc
            raw = read_block(tex, offset, pixel_count // 2)
            raw_rgba = decode_pvrtc(raw, width, height)
        else:
            error('Unrecognized Format: %2d' % self.format)

        if self.alpha != 0x00:
            noalpha_rgba, alpha_rgba = demux_alpha(raw_rgba)
            if mipmap_level == 0:
                self.alpha_mipmap = Image.frombytes('RGBA', (width, height), alpha_rgba, 'raw', 'RGBA')
                self.noalpha_mipmap = Image.frombytes('RGBA', (width, height), noalpha_rgba, 'raw', 'RGBA')

        image = Image.frombytes('RGBA', (width, height), raw_rgba, 'raw', 'RGBA')
        return image

    def add_mipmap(self, image):
        self.mipmaps.append(image)

    def export_meta(self):
        return self._meta

    def import_meta(self, meta):
        self._meta = meta
        self.parse_meta(meta)

    def __str__(self):
        info = """TEX
Format : {}
Alpha  : {alpha}
Width  : {width}
Height : {height}
Mipmaps: {mipmap_count}""".format(TEX.formats[self.format], **self.__dict__)
        return info
