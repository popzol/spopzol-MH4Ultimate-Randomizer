# Copyright 2016 dasding
# ported from github.com/Gericom/EveryFileExplorer/
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

import array

def ColorClamp(Color):
    if Color > 255:
        Color = 255
    if Color < 0:
        Color = 0
    return Color

class Color:
    def __init__(self, r=0, g=0, b=0, a=255):
        self.R = r
        self.G = g
        self.B = b
        self.A = a

    def FromArgbInt(self, c):
        self.R = (c >> 16) & 0xFF
        self.G = (c >> 8) & 0xFF
        self.B = (c >> 0) & 0xFF
        self.A = (c >> 24) & 0xFF
        return self

    def tostring(self):
        i = 0
        i += self.R << 0
        i += self.G << 8
        i += self.B << 16
        i += self.B << 24
        return i

    def __str__(self):
        return "Color({:3d}, {:3d}, {:3d}, {:3d})".format(self.R, self.G, self.B, self.A)

Color.White = Color(255, 255, 255, 255)
Color.Black = Color(0, 0, 0, 255)


class ColorFormat:
    def __init__(self, AShift, ASize, RShift, RSize, GShift, GSize, BShift, BSize):
        self.AShift = AShift
        self.ASize = ASize
        self.RShift = RShift
        self.RSize = RSize
        self.GShift = GShift
        self.GSize = GSize
        self.BShift = BShift
        self.BSize = BSize

ColorFormat.ARGB8888 = ColorFormat(24, 8, 16, 8, 8, 8, 0, 8)

MaxInt = 2**31 - 1
MinInt = -(2**32)

ETC1Modifiers = [
    [2, 8],
    [5, 17],
    [9, 29],
    [13, 42],
    [18, 60],
    [24, 80],
    [33, 106],
    [47, 183]
]


def ToColorFormat(A, R, G, B, OutputFormat):
    result = 0
    if (OutputFormat.ASize != 0):
        mask = ~(0xFFFFFFFF << OutputFormat.ASize) & 0xFFFFFFFF
        result |= ((A * mask + 127) / 255) << OutputFormat.AShift

    mask = ~(0xFFFFFFFF << OutputFormat.RSize) & 0xFFFFFFFF
    result |= ((R * mask + 127) / 255) << OutputFormat.RShift
    mask = ~(0xFFFFFFFF << OutputFormat.GSize) & 0xFFFFFFFF
    result |= ((G * mask + 127) / 255) << OutputFormat.GShift
    mask = ~(0xFFFFFFFF << OutputFormat.BSize) & 0xFFFFFFFF
    result |= ((B * mask + 127) / 255) << OutputFormat.BShift

    return result & 0xFFFFFFFF


def GenModifier(Pixels):
    Max = Color.White
    Min = Color.Black

    MinY = MaxInt
    MaxY = MinInt
    for i in xrange(8):
        # if Pixels[i].A == 0:
        #     continue
        Y = (Pixels[i].R + Pixels[i].G + Pixels[i].B) / 3
        if Y > MaxY:
            MaxY = Y
            Max = Pixels[i]
        if Y < MinY:
            MinY = Y
            Min = Pixels[i]
    DiffMean = ((Max.R - Min.R) + (Max.G - Min.G) + (Max.B - Min.B)) / 3

    ModDiff = MaxInt
    Modifier = -1
    Mode = -1

    for i in range(8):
        SS = ETC1Modifiers[i][0] * 2
        SB = ETC1Modifiers[i][0] + ETC1Modifiers[i][1]
        BB = ETC1Modifiers[i][1] * 2
        if (SS > 255):
            SS = 255
        if (SB > 255):
            SB = 255
        if (BB > 255):
            BB = 255

        if abs(DiffMean - SS) < ModDiff:
            ModDiff = abs(DiffMean - SS)
            Modifier = i
            Mode = 0
        if abs(DiffMean - SB) < ModDiff:
            ModDiff = abs(DiffMean - SB)
            Modifier = i
            Mode = 1
        if abs(DiffMean - BB) < ModDiff:
            ModDiff = abs(DiffMean - BB)
            Modifier = i
            Mode = 2

    if Mode == 1:
        div1 = float(ETC1Modifiers[Modifier][0]) / float(ETC1Modifiers[Modifier][1])
        div2 = 1.0 - div1
        BaseColor = Color(int(Min.R * div1 + Max.R * div2), int(Min.G * div1 + Max.G * div2), int(Min.B * div1 + Max.B * div2))
    else:
        BaseColor = Color((Min.R + Max.R) / 2, (Min.G + Max.G) / 2, (Min.B + Max.B) / 2)

    return Modifier, BaseColor


def GenHorizontal(Colors):
    data = 0
    data = SetFlipMode(data, False)
    # Left
    Left = GetLeftColors(Colors)
    mod, basec1 = GenModifier(Left)
    data = SetTable1(data, mod)
    data = GenPixDiff(data, Left, basec1, mod, 0, 2, 0, 4)
    # Right
    Right = GetRightColors(Colors)
    mod, basec2 = GenModifier(Right)
    data = SetTable2(data, mod)
    data = GenPixDiff(data, Right, basec2, mod, 2, 4, 0, 4)
    data = SetBaseColors(data, basec1, basec2)
    return data


def GenVertical(Colors):
    data = 0
    data = SetFlipMode(data, True)
    # Top
    Top = GetTopColors(Colors)
    mod, basec1 = GenModifier(Top)
    data = SetTable1(data, mod)
    data = GenPixDiff(data, Top, basec1, mod, 0, 4, 0, 2)
    # Bottom
    Bottom = GetBottomColors(Colors)
    mod, basec2 = GenModifier(Bottom)
    data = SetTable2(data, mod)
    data = GenPixDiff(data, Bottom, basec2, mod, 0, 4, 2, 4)
    data = SetBaseColors(data, basec1, basec2)
    return data


def GetScore(Original, Encode):
    Diff = 0
    for i in range(4 * 4):
        Diff += abs(Encode[i].R - Original[i].R)
        Diff += abs(Encode[i].G - Original[i].G)
        Diff += abs(Encode[i].B - Original[i].B)
    return Diff


def GenETC1(Colors):
    Horizontal = GenHorizontal(Colors)
    Vertical = GenVertical(Colors)
    HorizontalScore = GetScore(Colors, DecodeETC1(Horizontal))
    VerticalScore = GetScore(Colors, DecodeETC1(Vertical))
    return Horizontal if HorizontalScore < VerticalScore else Vertical


def GenPixDiff(Data, Pixels, BaseColor, Modifier, XOffs, XEnd, YOffs, YEnd):
    BaseMean = (BaseColor.R + BaseColor.G + BaseColor.B) / 3
    i = 0
    for yy in range(YOffs, YEnd):
        for xx in range(XOffs, XEnd):
            Diff = ((Pixels[i].R + Pixels[i].G + Pixels[i].B) / 3) - BaseMean

            if Diff < 0:
                Data |= 1 << (xx * 4 + yy + 16)
            tbldiff1 = abs(Diff) - ETC1Modifiers[Modifier][0]
            tbldiff2 = abs(Diff) - ETC1Modifiers[Modifier][1]

            if abs(tbldiff2) < abs(tbldiff1):
                Data |= 1 << (xx * 4 + yy)
            i += 1
    return Data


def GetLeftColors(Pixels):
    Left = [Color() for i in range(4 * 2)]
    for y in range(0, 4):
        for x in range(0, 2):
            Left[y * 2 + x] = Pixels[y * 4 + x]
    return Left


def GetRightColors(Pixels):
    Right = [Color() for i in range(4 * 2)]
    for y in range(0, 4):
        for x in range(2, 4):
            Right[y * 2 + x - 2] = Pixels[y * 4 + x]
    return Right


def GetTopColors(Pixels):
    Top = [Color() for i in range(4 * 2)]
    for y in range(0, 2):
        for x in range(0, 4):
            Top[y * 4 + x] = Pixels[y * 4 + x]
    return Top


def GetBottomColors(Pixels):
    Bottom = [Color() for i in range(4 * 2)]
    for y in range(2, 4):
        for x in range(0, 4):
            Bottom[(y - 2) * 4 + x] = Pixels[y * 4 + x]
    return Bottom


def SetFlipMode(Data, Mode):
    Data &= (~(1 << 32))
    Data |= (1 if Mode else 0) << 32
    return Data


def SetDiffMode(Data, Mode):
    Data &= ~(1 << 33) & 0xFFFFFFFFFFFFFFFF
    Data |= (1 if Mode else 0) << 33
    return Data


def SetTable1(Data, Table):
    Data &= ~(7 << 37) & 0xFFFFFFFFFFFFFFFF
    Data |= (Table & 0x7) << 37
    return Data


def SetTable2(Data, Table):
    Data &= ~(7 << 34) & 0xFFFFFFFFFFFFFFFF
    Data |= (Table & 0x7) << 34
    return Data


def SetBaseColors(Data, Color1, Color2):
    R1 = Color1.R
    G1 = Color1.G
    B1 = Color1.B
    R2 = Color2.R
    G2 = Color2.G
    B2 = Color2.B
    # First look if differencial is possible.
    RDiff = (R2 - R1) / 8
    GDiff = (G2 - G1) / 8
    BDiff = (B2 - B1) / 8
    if (RDiff > -4 and RDiff < 3 and GDiff > -4 and GDiff < 3 and BDiff > -4 and BDiff < 3):
        Data = SetDiffMode(Data, True)
        R1 /= 8
        G1 /= 8
        B1 /= 8
        Data |= R1 << 59
        Data |= G1 << 51
        Data |= B1 << 43
        Data |= (RDiff & 0x7) << 56
        Data |= (GDiff & 0x7) << 48
        Data |= (BDiff & 0x7) << 40
    else:
        Data |= (R1 / 0x11) << 60
        Data |= (G1 / 0x11) << 52
        Data |= (B1 / 0x11) << 44

        Data |= (R2 / 0x11) << 56
        Data |= (G2 / 0x11) << 48
        Data |= (B2 / 0x11) << 40
    return Data


def DecodeETC1(Data, Alpha=0xFFFFFFFFFFFFFFFF):
    Result = [Color() for i in range(4 * 4)]
    diffbit = ((Data >> 33) & 1) == 1
    flipbit = ((Data >> 32) & 1) == 1

    if diffbit:  # 'differential' mode
        r = (Data >> 59) & 0x1F
        g = (Data >> 51) & 0x1F
        b = (Data >> 43) & 0x1F
        r1 = (r << 3) | ((r & 0x1C) >> 2)
        g1 = (g << 3) | ((g & 0x1C) >> 2)
        b1 = (b << 3) | ((b & 0x1C) >> 2)
        r += ((((Data >> 56) & 0x7) << 29) & 0x7FFFFFFF) >> 29
        g += ((((Data >> 48) & 0x7) << 29) & 0x7FFFFFFF) >> 29
        b += ((((Data >> 40) & 0x7) << 29) & 0x7FFFFFFF) >> 29
        r2 = (r << 3) | ((r & 0x1C) >> 2)
        g2 = (g << 3) | ((g & 0x1C) >> 2)
        b2 = (b << 3) | ((b & 0x1C) >> 2)
    else:  # 'individual' mode
        r1 = ((Data >> 60) & 0xF) * 0x11
        g1 = ((Data >> 52) & 0xF) * 0x11
        b1 = ((Data >> 44) & 0xF) * 0x11
        r2 = ((Data >> 56) & 0xF) * 0x11
        g2 = ((Data >> 48) & 0xF) * 0x11
        b2 = ((Data >> 40) & 0xF) * 0x11
    Table1 = ((Data >> 37) & 0x7)
    Table2 = ((Data >> 34) & 0x7)

    for y3 in range(4):
        for x3 in range(4):
            val = ((Data >> (x3 * 4 + y3)) & 0x1)
            neg = ((Data >> (x3 * 4 + y3 + 16)) & 0x1) == 1

            if ((flipbit and y3 < 2) or (not flipbit and x3 < 2)):
                add = ETC1Modifiers[Table1][val] * (-1 if neg else 1)
                c = ToColorFormat(((Alpha >> ((x3 * 4 + y3) * 4)) & 0xF) * 0x11, ColorClamp(r1 + add), ColorClamp(g1 + add), ColorClamp(b1 + add), ColorFormat.ARGB8888)
            else:
                add = ETC1Modifiers[Table2][val] * (-1 if neg else 1)
                c = ToColorFormat(((Alpha >> ((x3 * 4 + y3) * 4)) & 0xF) * 0x11, ColorClamp(r2 + add), ColorClamp(g2 + add), ColorClamp(b2 + add), ColorFormat.ARGB8888)
            Result[y3 * 4 + x3] = Color().FromArgbInt(c)
            # res[(i + y3) * stride + x + j + x3] = c;
    return Result

# Copyright 2015 Seth VanHeulen
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

def packpixel(px):
    return (px[0] & 255) + ((px[1] & 255) << 8) + ((px[2] & 255) << 16) + ((px[3] & 255) << 24)

etc1_mod_table = (
    (2, 8, -2, -8),
    (5, 17, -5, -17),
    (9, 29, -9, -29),
    (13, 42, -13, -42),
    (18, 60, -18, -60),
    (24, 80, -24, -80),
    (33, 106, -33, -106),
    (47, 183, -47, -183)
)

def decode_etc1(data, width, height, alpha=False):
    data = array.array('I', data)
    block_index = 0
    pixel_count = len(data) * 8 if not alpha else len(data) * 4
    rgba = array.array('I', [0]) * pixel_count

    while len(data) != 0:
        alpha_part1   = 0 if not alpha else data.pop(0)
        alpha_part2   = 0 if not alpha else data.pop(0)
        pixel_indices = data.pop(0)
        block_info    = data.pop(0)
        bc1 = [0, 0, 0]
        bc2 = [0, 0, 0]
        if block_info & 2 == 0:
            bc1[0] = block_info >> 28 & 15
            bc1[1] = block_info >> 20 & 15
            bc1[2] = block_info >> 12 & 15
            bc1 = [(x << 4) + x for x in bc1]
            bc2[0] = block_info >> 24 & 15
            bc2[1] = block_info >> 16 & 15
            bc2[2] = block_info >> 8 & 15
            bc2 = [(x << 4) + x for x in bc2]
        else:
            bc1[0] = block_info >> 27 & 31
            bc1[1] = block_info >> 19 & 31
            bc1[2] = block_info >> 11 & 31
            bc2[0] = block_info >> 24 & 7
            bc2[1] = block_info >> 16 & 7
            bc2[2] = block_info >> 8 & 7
            bc2 = [x + ((y > 3) and (y - 8) or y) for x, y in zip(bc1, bc2)]
            bc1 = [(x >> 2) + (x << 3) for x in bc1]
            bc2 = [(x >> 2) + (x << 3) for x in bc2]
        flip = block_info & 1
        tcw1 = block_info >> 5 & 7
        tcw2 = block_info >> 2 & 7

        for i in range(16):
            mi = ((pixel_indices >> i) & 1) + ((pixel_indices >> (i + 15)) & 2)
            c = None
            if flip == 0 and i < 8 or flip != 0 and (i // 2 % 2) == 0:
                m = etc1_mod_table[tcw1][mi]
                c = [max(0, min(255, x + m)) for x in bc1]
            else:
                m = etc1_mod_table[tcw2][mi]
                c = [max(0, min(255, x + m)) for x in bc2]
            if alpha:
                if i < 8:
                    px_alpha = alpha_part1 >> (4 * i) & 0xF
                else:
                    px_alpha = alpha_part2 >> (4 * (i - 8)) & 0xF

                px_alpha = px_alpha << 4 | px_alpha
                c.append(px_alpha)
            else:
                c.append(255)

            offset = block_index % 4
            x = (block_index - offset) % (width // 2) * 2
            y = (block_index - offset) // (width // 2) * 8

            if offset & 1:
                x += 4
            if offset & 2:
                y += 4
            x += i // 4
            y += i % 4

            rgba[x + y * width] = packpixel(c)
        block_index += 1
    return rgba.tostring()