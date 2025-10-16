from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.enums.unit_format import UnitFormat
from mixam_sdk.item_specification.enums.simple_fold import SimpleFold


# Constants
MM_IN_INCH = 25.4
MM_IN_POINT = 2.8346456693
MM_IN_300_DPI_PIXEL = 11.811023622
INCH_IN_POINT = 72.0
INCH_IN_300_DPI_PIXEL = 300.0

PAGE_SIZE_UNKNOWN = -1
PAGE_SIZE_SPINE = -99
PAGE_SIZE_JACKET = -98
PAGE_SIZE_TOLERANCE = 20  # percent
SECONDARY_SIZE_TOLERANCE = 10.0  # mm
PAGE_HEIGHT_TOLERANCE = 40  # percent
INACCURACY = 0.5
FLAPS_SIZE = 80
NARROW_FLAPS_SIZE = 40
GLUE_TRAP_SIZE = 7
HEIGHT_ADDITION_SIZE = 3
DUST_JACKET_THRESHOLD = 2.0
DEFAULT_BLEED = 3.0

# DIN A sizes (mm) A0..A8
DIN_SIZES: Tuple[Tuple[int, int], ...] = (
    (841, 1189),  # A0
    (594, 841),   # A1
    (420, 594),   # A2
    (297, 420),   # A3
    (210, 297),   # A4
    (148, 210),   # A5
    (105, 148),   # A6
    (74, 105),    # A7
    (52, 74),     # A8
)

# B sizes (mm) B0..B9
B_SIZES: Tuple[Tuple[int, int], ...] = (
    (1000, 1414),
    (707, 1000),
    (500, 707),
    (353, 500),
    (250, 353),
    (176, 250),
    (125, 176),
    (88, 125),
    (62, 88),
    (44, 62),
)


@dataclass(frozen=True)
class SecondarySizeInfo:
    id: int
    name: str
    width: float
    height: float
    imperial_width: float | None = None
    imperial_height: float | None = None

    def get_dims(self, unit: UnitFormat) -> Tuple[float, float]:
        if unit == UnitFormat.METRIC:
            return float(self.width), float(self.height)
        if self.imperial_width is not None and self.imperial_height is not None:
            return float(self.imperial_width), float(self.imperial_height)
        return mm_to_inch(self.width), mm_to_inch(self.height)


_secondary_info_map: Dict[int, SecondarySizeInfo] = {
    1: SecondarySizeInfo(1, "Novel (127mm x 203mm)", 127, 203, 5, 8),
    2: SecondarySizeInfo(2, "Standard (132mm x 197mm)", 132, 197, 5.2, 7.76),
    3: SecondarySizeInfo(3, "Demy (138mm x 216mm)", 138, 216, 5.43, 8.5),
    4: SecondarySizeInfo(4, "US Royal (152mm x 229mm)", 152, 229, 6, 8.98),
    5: SecondarySizeInfo(5, "Royal (156mm x 234mm)", 156, 234, 6.14, 9.21),
    6: SecondarySizeInfo(6, "210mm Square", 210, 210, 8.27, 8.27),
    7: SecondarySizeInfo(7, "Large Format Portrait (210mm x 280mm)", 210, 280, 8.27, 11),
    8: SecondarySizeInfo(8, "Dl Small 100", 100, 210, 3.94, 8.27),
    9: SecondarySizeInfo(9, "DL 105mm x 210mm", 105, 210, 4.13, 8.27),
    10: SecondarySizeInfo(10, "A5 Long (105mm x 297mm)", 105, 297, 4.13, 11.69),
    11: SecondarySizeInfo(11, "148mm Square", 148, 148, 5.82, 5.82),
    12: SecondarySizeInfo(12, "105mm Square", 105, 105, 4.13, 4.13),
    13: SecondarySizeInfo(13, "120mm Square", 120, 120),
    14: SecondarySizeInfo(14, "A1 Long", 420, 1188),
    15: SecondarySizeInfo(15, "A2 Long", 297, 840),
    16: SecondarySizeInfo(16, "DL Small", 99, 210),
    17: SecondarySizeInfo(17, "B1", 707, 1000),
    18: SecondarySizeInfo(18, "B2", 500, 707),
    19: SecondarySizeInfo(19, "183mm x 273mm", 183, 273),
    20: SecondarySizeInfo(20, "150mm x 265mm", 150, 265),
    21: SecondarySizeInfo(21, "100mm Square", 100, 100),
    22: SecondarySizeInfo(22, "55mm x 85mm", 55, 85),
    23: SecondarySizeInfo(23, "DL", 110, 220),
    24: SecondarySizeInfo(24, "C5", 162, 229),
    25: SecondarySizeInfo(25, "C4", 229, 324),
    26: SecondarySizeInfo(26, "C6", 162, 114),
    27: SecondarySizeInfo(27, "Square 155", 155, 155),
    28: SecondarySizeInfo(28, "Square 170", 170, 170),
    29: SecondarySizeInfo(29, "DL large", 229, 114),
    30: SecondarySizeInfo(30, "50mm x 90mm", 50, 90),
    31: SecondarySizeInfo(31, "54mm x 86mm", 54, 86),
    32: SecondarySizeInfo(32, "55mm Square", 55, 55),
    33: SecondarySizeInfo(33, "B5", 175, 245),
    34: SecondarySizeInfo(34, "B4", 248, 346),
    35: SecondarySizeInfo(35, "98mm Square", 98, 98),
    36: SecondarySizeInfo(36, "A6 Long", 74, 210),
    37: SecondarySizeInfo(37, "A7 Long", 52, 148),
    38: SecondarySizeInfo(38, "B0", 1000, 1414),
    39: SecondarySizeInfo(39, "170mm x 590mm", 170, 590),
    40: SecondarySizeInfo(40, "Large format", 1185, 1750),
    41: SecondarySizeInfo(41, "A7 mini", 74, 98),
    42: SecondarySizeInfo(42, "Large Format Trade (170mm x 240mm)", 170, 240),
    43: SecondarySizeInfo(43, "508mm x 762mm", 508, 762, 20, 30),
    44: SecondarySizeInfo(44, "762mm x 1016mm", 762, 1016, 30, 40),
    45: SecondarySizeInfo(45, "1016mm x 1524mm", 1016, 1524, 40, 60),
    46: SecondarySizeInfo(46, "5.5\" x 8.5\"", 140, 216, 5.5, 8.5),
    47: SecondarySizeInfo(47, "8.5\" x 11\"", 216, 279, 8.5, 11),
    48: SecondarySizeInfo(48, "8.5\" x 22\"", 216, 559, 8.5, 22),
    49: SecondarySizeInfo(49, "4.25\" x 5.5\"", 108, 140, 4.25, 5.5),
    50: SecondarySizeInfo(50, "4\" x 6\"", 102, 152, 4, 6),
    51: SecondarySizeInfo(51, "5\" x 7\"", 127, 178, 5, 7),
    52: SecondarySizeInfo(52, "6\" x 9\"", 152, 229, 6, 9),
    53: SecondarySizeInfo(53, "8\" x 10\"", 203, 254, 8, 10),
    54: SecondarySizeInfo(54, "6\" x 11\"", 152, 279, 6, 11),
    55: SecondarySizeInfo(55, "11\" x 17\"", 279, 432, 11, 17),
    56: SecondarySizeInfo(56, "6\" x 6\"", 152, 152, 6, 6),
    57: SecondarySizeInfo(57, "12\" x 12\"", 305, 305, 12, 12),
    58: SecondarySizeInfo(58, "4.75\" x 4.75\"", 121, 121, 4.75, 4.75),
    59: SecondarySizeInfo(59, "12\" x 18\"", 305, 457, 12, 18),
    60: SecondarySizeInfo(60, "13\" x 19\"", 330, 483, 13, 19),
    61: SecondarySizeInfo(61, "18\" x 24\"", 457, 610, 18, 24),
    62: SecondarySizeInfo(62, "19\" x 27\"", 483, 686, 19, 27),
    63: SecondarySizeInfo(63, "24\" x 36\"", 610, 914, 24, 36),
    64: SecondarySizeInfo(64, "26\" x 39\"", 660, 991, 26, 39),
    65: SecondarySizeInfo(65, "8.5\" x 14\"", 216, 356, 8.5, 14),
    66: SecondarySizeInfo(66, "UK Standard", 157, 240, 6.18, 9.45),
    67: SecondarySizeInfo(67, "US Standard", 170, 260),
    68: SecondarySizeInfo(68, "Manga Standard", 127, 191),
    69: SecondarySizeInfo(69, "5\" x 8\"", 127, 203, 5, 8),
    70: SecondarySizeInfo(70, "5.06\" x 7.81\"", 129, 198, 5.06, 7.81),
    71: SecondarySizeInfo(71, "5.25\" x 8\"", 133, 203, 5.25, 8),
    72: SecondarySizeInfo(72, "6.14\" x 9.21\"", 156, 234, 6.14, 9.21),
    73: SecondarySizeInfo(73, "6.69\" x 9.61\"", 170, 244, 6.69, 9.61),
    74: SecondarySizeInfo(74, "7\" x 10\"", 178, 254, 7, 10),
    75: SecondarySizeInfo(75, "7.44\" x 9.69\"", 189, 246, 7.44, 9.69),
    76: SecondarySizeInfo(76, "7.5\" x 9.25\"", 191, 235, 7.5, 9.25),
    77: SecondarySizeInfo(77, "6\" x 8.25\"", 152, 210, 6, 8.25),
    78: SecondarySizeInfo(78, "8.25\" Square", 210, 210, 8.25, 8.25),
    79: SecondarySizeInfo(79, "8.5\" Square", 216, 216, 8.5, 8.5),
    80: SecondarySizeInfo(80, "7\" Square", 178, 178, 7, 7),
    81: SecondarySizeInfo(81, "140mm Square", 140, 140),
    82: SecondarySizeInfo(82, "B6", 125, 176),
    83: SecondarySizeInfo(83, "US Trade", 152, 229, 6, 9),
    84: SecondarySizeInfo(84, "Business card", 51, 89),
    85: SecondarySizeInfo(85, "Postcard", 89, 140),
    86: SecondarySizeInfo(86, "Postcard", 108, 152),
    87: SecondarySizeInfo(87, "8\" x 11\"", 203, 279, 8, 11),
    88: SecondarySizeInfo(88, "11\" x 14\"", 279, 356, 11, 14),
    89: SecondarySizeInfo(89, "8\" x Square", 203, 203, 8, 8),
    90: SecondarySizeInfo(90, "B format UK", 129, 198),
    91: SecondarySizeInfo(91, "Pinched Crown Quarto", 171, 246, 6.73, 9.65),
    92: SecondarySizeInfo(92, "Crown Quarto", 189, 246, 7.44, 9.68),
    93: SecondarySizeInfo(93, "280 Square", 280, 280),
    94: SecondarySizeInfo(94, "7.25\" x 9.5\"", 184, 241, 7.25, 9.5),
    95: SecondarySizeInfo(95, "Pocket Book 4.25\" x 6.87\"", 108, 174, 4.25, 6.87),
    96: SecondarySizeInfo(96, "Small Square 7.5\"", 191, 191, 7.5, 7.5),
    97: SecondarySizeInfo(97, "Quarto 9.5\" x 12\"", 241, 305, 9.5, 12),
    98: SecondarySizeInfo(98, "7\" x 9\"", 178, 229, 7, 9),
    99: SecondarySizeInfo(99, "200mm x 200mm", 200, 200),
    100: SecondarySizeInfo(100, "200mm x 250mm", 200, 250),
    101: SecondarySizeInfo(101, "200mm x 300mm", 200, 300),
    102: SecondarySizeInfo(102, "200mm x 600mm", 200, 600),
    103: SecondarySizeInfo(103, "300mm x 300mm", 300, 300),
    104: SecondarySizeInfo(104, "300mm x 400mm", 300, 400),
    105: SecondarySizeInfo(105, "300mm x 600mm", 300, 600),
    106: SecondarySizeInfo(106, "300mm x 1000mm", 300, 1000),
    107: SecondarySizeInfo(107, "400mm x 400mm", 400, 400),
    108: SecondarySizeInfo(108, "400mm x 500mm", 400, 500),
    109: SecondarySizeInfo(109, "400mm x 600mm", 400, 600),
    110: SecondarySizeInfo(110, "500mm x 500mm", 500, 500),
    111: SecondarySizeInfo(111, "500mm x 600mm", 500, 600),
    112: SecondarySizeInfo(112, "500mm x 700mm", 500, 700),
    113: SecondarySizeInfo(113, "500mm x 750mm", 500, 750),
    114: SecondarySizeInfo(114, "500mm x 1000mm", 500, 1000),
    115: SecondarySizeInfo(115, "600mm x 600mm", 600, 600),
    116: SecondarySizeInfo(116, "600mm x 750mm", 600, 750),
    117: SecondarySizeInfo(117, "600mm x 800mm", 600, 800),
    118: SecondarySizeInfo(118, "750mm x 1000mm", 750, 1000),
    119: SecondarySizeInfo(119, "10\" x Square", 254, 254, 10, 10),
    120: SecondarySizeInfo(120, "11.8\" x Square", 300, 300, 11.8, 11.8),
    121: SecondarySizeInfo(121, "3.5\" x 8.5\"", 89, 216, 3.5, 8.5),
    122: SecondarySizeInfo(122, "4.25\" x 11\"", 108, 280, 4.25, 11),
    123: SecondarySizeInfo(123, "7\" x 8.5\"", 178, 216, 7, 8.5),
    124: SecondarySizeInfo(124, "7.5\" x 8.5\"", 191, 216, 7.5, 8.5),
    125: SecondarySizeInfo(125, "9\" x 12\"", 229, 305, 9, 12),
    126: SecondarySizeInfo(126, "9\" x 16\"", 229, 406, 9, 16),
    127: SecondarySizeInfo(127, "8.5\" x 17\"", 216, 432, 8.5, 17),
    128: SecondarySizeInfo(128, "11.5\" x 17.5\"", 292, 445, 11.5, 17.5),
    129: SecondarySizeInfo(129, "17\" x 22\"", 432, 559, 17, 22),
    130: SecondarySizeInfo(130, "11\" x 25.5\"", 279, 648, 11, 25.5),
    131: SecondarySizeInfo(131, "8\" x 12\"", 203, 305, 8, 12),
    132: SecondarySizeInfo(132, "10\" x 15\"", 254, 381, 10, 15),
    133: SecondarySizeInfo(133, "5.5\" x 8.5\"", 140, 216, 5.5, 8.5),
    134: SecondarySizeInfo(134, "3.5\" x 8.5\"", 89, 216, 3.5, 8.5),
    135: SecondarySizeInfo(135, "4\" x 9\"", 102, 229, 4, 9),
    136: SecondarySizeInfo(136, "2\" x 8\"", 51, 203, 2, 8),
    137: SecondarySizeInfo(137, "3.66\" x 4.25\"", 93, 108, 3.66, 4.25),
    138: SecondarySizeInfo(138, "3\" x 4\"", 76, 102, 3, 4),
    139: SecondarySizeInfo(139, "4\" x 4\"", 102, 102, 4, 4),
    140: SecondarySizeInfo(140, "5.8\" x 9.25\"", 147, 235, 5.8, 9.25),
    141: SecondarySizeInfo(141, "8.375\" x 10.875\"", 213, 276, 8.375, 10.875),
    142: SecondarySizeInfo(142, "5.375\" x 8.375\"", 137, 213, 5.375, 8.375),
    143: SecondarySizeInfo(143, "5.25\" x 8.375\"", 133, 213, 5.25, 8.375),
    144: SecondarySizeInfo(144, "10mm x 10mm", 10, 10),
    145: SecondarySizeInfo(145, "15mm x 15mm", 15, 15),
    146: SecondarySizeInfo(146, "20mm x 20mm", 20, 20),
    147: SecondarySizeInfo(147, "21mm x 21mm", 21, 21),
    148: SecondarySizeInfo(148, "25mm x 25mm", 25, 25),
    149: SecondarySizeInfo(149, "10mm x 30mm", 10, 30),
    150: SecondarySizeInfo(150, "30mm x 30mm", 30, 30),
    151: SecondarySizeInfo(151, "15mm x 35mm", 15, 35),
    152: SecondarySizeInfo(152, "35mm x 35mm", 35, 35),
    153: SecondarySizeInfo(153, "35mm x 105mm", 35, 105),
    154: SecondarySizeInfo(154, "35mm x 210mm", 35, 210),
    155: SecondarySizeInfo(155, "35mm x 316mm", 35, 316),
    156: SecondarySizeInfo(156, "20mm x 40mm", 20, 40),
    157: SecondarySizeInfo(157, "40mm x 40mm", 40, 40),
    158: SecondarySizeInfo(158, "15mm x 45mm", 15, 45),
    159: SecondarySizeInfo(159, "45mm x 45mm", 45, 45),
    160: SecondarySizeInfo(160, "48mm x 70mm", 48, 70),
    161: SecondarySizeInfo(161, "20mm x 50mm", 20, 50),
    162: SecondarySizeInfo(162, "25mm x 50mm", 25, 50),
    163: SecondarySizeInfo(163, "40mm x 50mm", 40, 50),
    164: SecondarySizeInfo(164, "50mm x 50mm", 50, 50),
    165: SecondarySizeInfo(165, "51mm x 298mm", 51, 298),
    166: SecondarySizeInfo(166, "51mm x 420mm", 51, 420),
    167: SecondarySizeInfo(167, "55mm x 85mm", 55, 85),
    168: SecondarySizeInfo(168, "60mm x 60mm", 60, 60),
    169: SecondarySizeInfo(169, "21mm x 68mm", 21, 68),
    170: SecondarySizeInfo(170, "70mm x 70mm", 70, 70),
    171: SecondarySizeInfo(171, "71mm x 96mm", 71, 96),
    172: SecondarySizeInfo(172, "80mm x 80mm", 80, 80),
    173: SecondarySizeInfo(173, "45mm x 95mm", 45, 95),
    174: SecondarySizeInfo(174, "95mm x 95mm", 95, 95),
    175: SecondarySizeInfo(175, "95mm x 145mm", 95, 145),
    176: SecondarySizeInfo(176, "98mm x 420mm", 98, 420),
    177: SecondarySizeInfo(177, "120mm x 125mm", 120, 125),
    178: SecondarySizeInfo(178, "140mm x 297mm", 140, 297),
    179: SecondarySizeInfo(179, "124mm x 140mm", 124, 140),
    180: SecondarySizeInfo(180, "98mm x 210mm", 98, 210),
    181: SecondarySizeInfo(181, "Silver Age (6.875\" x 10.25\")", 175, 260, 6.875, 10.25),
    182: SecondarySizeInfo(182, "Golden Age (7.375\" x 10.25\")", 187, 260, 7.375, 10.25),
    183: SecondarySizeInfo(183, "8.75\" x 11\"", 222, 279, 8.75, 11),
    184: SecondarySizeInfo(184, "6.63\" x 10.25\"", 168, 260, 6.63, 10.25),
    185: SecondarySizeInfo(185, "5.125\" x 7\"", 130, 178, 5.125, 7),
    186: SecondarySizeInfo(186, "4.125\" x 5.875\"", 105, 149, 4.125, 5.875),
    187: SecondarySizeInfo(187, "895mm x 1280mm", 895, 1280),
    188: SecondarySizeInfo(188, "700mm x 1000mm", 700, 1000),
    189: SecondarySizeInfo(189, "1000mm x 1400mm", 1000, 1400),
    190: SecondarySizeInfo(190, "130mm x 150mm", 130, 150),
    191: SecondarySizeInfo(191, "138mm x 297mm", 138, 297),
    192: SecondarySizeInfo(192, "30mm x 70mm", 30, 70),
    193: SecondarySizeInfo(193, "199mm x 210mm", 199, 210),
    194: SecondarySizeInfo(194, "130mm x 190mm", 130, 190),
    195: SecondarySizeInfo(195, "297mm Square", 297, 297),
    196: SecondarySizeInfo(196, "240mm x 340mm", 240, 340),
    197: SecondarySizeInfo(197, "300mm x 800mm", 300, 800),
    198: SecondarySizeInfo(198, "400mm x 1500mm", 400, 1500),
    199: SecondarySizeInfo(199, "750mm x 750mm", 750, 750),
    200: SecondarySizeInfo(200, "1000mm x 1000mm", 1000, 1000),
    201: SecondarySizeInfo(201, "1000mm x 1500mm", 1000, 1500),
    202: SecondarySizeInfo(202, "1000mm x 2000mm", 1000, 2000),
    203: SecondarySizeInfo(203, "800mm x 1200mm", 800, 1200),
    204: SecondarySizeInfo(204, "1000mm x 1200mm", 1000, 1200),
    205: SecondarySizeInfo(205, "2\" x 3.5\"", 51, 89, 2, 3.5),
    206: SecondarySizeInfo(206, "2\" x 6\"", 51, 152, 2, 6),
    207: SecondarySizeInfo(207, "55mm x 148mm", 55, 148),
    208: SecondarySizeInfo(208, "55mm x 173mm", 55, 173),
    209: SecondarySizeInfo(209, "52mm x 210mm", 52, 210),
    210: SecondarySizeInfo(210, "Kitchen", 210, 420),
    211: SecondarySizeInfo(211, "135mm x 205mm", 135, 205, 5.315, 8.071),
    212: SecondarySizeInfo(212, "125mm x 190mm", 125, 190, 4.921, 7.480),
    213: SecondarySizeInfo(213, "115mm x 185mm", 115, 185, 4.528, 7.283),
    214: SecondarySizeInfo(214, "114mm x 172mm", 114, 172, 4.488, 6.772),
    215: SecondarySizeInfo(215, "148mm x 156mm", 148, 156, 5.827, 6.142),
    216: SecondarySizeInfo(216, "294mm x 300mm", 294, 300, 11.575, 11.811),
    217: SecondarySizeInfo(217, "120mm x 190mm", 120, 190, 4.724, 7.480),
    218: SecondarySizeInfo(218, "5.5\" x 10\"", 139.7, 254, 5.5, 10),
    219: SecondarySizeInfo(219, "6\" x 8\"", 152.4, 203.2, 6, 8),
    220: SecondarySizeInfo(220, "12\" x 16\"", 304.8, 406.4, 12, 16),
    221: SecondarySizeInfo(221, "135mm x 210mm", 135, 210, 5.32, 8.27),
    222: SecondarySizeInfo(222, "160mm x 240mm", 160, 240, 6.30, 9.45),
    223: SecondarySizeInfo(223, "Royal+ (168mm x 240mm)", 168, 240, 6.61, 9.45),
    224: SecondarySizeInfo(224, "193mm x 260mm", 193, 260, 7.60, 10.24),
    225: SecondarySizeInfo(225, "AB (210mm x 257mm)", 210, 257, 8.26, 10.11),
    226: SecondarySizeInfo(226, "B5 (182mm x 257mm)", 182, 257, 7.16, 10.11),
    227: SecondarySizeInfo(227, "JIS B5 (179mm x 252mm)", 179, 252, 7.04, 9.92),
    228: SecondarySizeInfo(228, "JIS B40 (103mm x 182mm)", 103, 182, 4.05, 7.16),
    229: SecondarySizeInfo(229, "Han 46 (128mm x 188mm)", 128, 188, 5.03, 7.40),
    230: SecondarySizeInfo(230, "Hobonichi (110mm x 148mm)", 110, 148, 4.33, 5.82),
    231: SecondarySizeInfo(231, "95mm x 210mm", 95, 210, 3.74, 8.27),
}


def get_din_sizes() -> Tuple[Tuple[int, int], ...]:
    return DIN_SIZES


def get_b_sizes() -> Tuple[Tuple[int, int], ...]:
    return B_SIZES


def _is_landscape_from_orientation(width: float, height: float, orientation: Orientation | None) -> bool:
    return (orientation is None and width > height) or (orientation is not None and orientation == Orientation.LANDSCAPE)


def get_din_size_index(
    w: float,
    h: float,
    orientation: Orientation | None = None,
) -> int:
    is_landscape = _is_landscape_from_orientation(w, h, orientation)
    width_index = 1 if is_landscape else 0
    height_index = 0 if is_landscape else 1

    for i in range(len(DIN_SIZES) - 1, -1, -1):
        p_w, p_h = DIN_SIZES[i][width_index], DIN_SIZES[i][height_index]
        w_ratio = abs((p_w - w) / p_w * 100)
        h_ratio = (p_h - h) / p_h * 100
        if w_ratio <= PAGE_SIZE_TOLERANCE:
            if abs(h_ratio) <= PAGE_SIZE_TOLERANCE:
                return i
            if 0 <= h_ratio <= PAGE_HEIGHT_TOLERANCE:
                return i

    # spine detection
    if (h / w) > 8 or (w / h) > 8:
        return PAGE_SIZE_SPINE

    return PAGE_SIZE_UNKNOWN


def get_din_size_from_layout(
    sides: int,
    simple_fold: SimpleFold,
    w: float,
    h: float,
    orientation: Orientation | None = None,
) -> int:
    fold_factor_w = 4 if simple_fold == SimpleFold.CROSS else 2
    fold_factor_h = 2 if simple_fold == SimpleFold.CROSS else 1
    adj_w = w / sides * fold_factor_w
    adj_h = h / fold_factor_h
    return get_din_size_index(adj_w, adj_h, orientation)


def get_din_dimensions(size_idx: int, orientation: Orientation = Orientation.PORTRAIT) -> Tuple[float, float]:
    o = orientation
    return float(DIN_SIZES[size_idx][o.value]), float(DIN_SIZES[size_idx][o.value ^ 1])

def validate_secondary_size(
    secondary_id: int,
    w: float,
    h: float,
    orientation: Orientation | None = None,
) -> bool:
    is_landscape = _is_landscape_from_orientation(w, h, orientation)
    width_index = 1 if is_landscape else 0
    height_index = 0 if is_landscape else 1

    info = _secondary_info_map[secondary_id]
    p = (info.width, info.height)
    type_width = p[width_index]
    type_height = p[height_index]
    return abs(type_width - w) < SECONDARY_SIZE_TOLERANCE and abs(type_height - h) < SECONDARY_SIZE_TOLERANCE


def validate_secondary_size_from_layout(
    secondary_id: int,
    sides: int,
    simple_fold: SimpleFold,
    w: float,
    h: float,
    orientation: Orientation | None = None,
) -> bool:
    fold_factor_w = 4 if simple_fold == SimpleFold.CROSS else 2
    fold_factor_h = 2 if simple_fold == SimpleFold.CROSS else 1
    adj_w = w / sides * fold_factor_w
    adj_h = h / fold_factor_h
    return validate_secondary_size(secondary_id, adj_w, adj_h, orientation)


def get_secondary_name(secondary_id: int) -> str:
    return _secondary_info_map[secondary_id].name


def get_secondary_size(
    secondary_id: int,
    orientation: Orientation | None = None,
    size_format: UnitFormat = UnitFormat.METRIC,
) -> Tuple[float, float]:
    if orientation is None:
        orientation = Orientation.PORTRAIT
    info = _secondary_info_map[secondary_id]
    w, h = info.get_dims(size_format)
    p = (w, h)
    return float(p[orientation.value]), float(p[orientation.value ^ 1])


def is_dim_of_size(size_idx: int, w: float, h: float, orientation: Orientation) -> bool:
    dw, dh = get_din_dimensions(size_idx, orientation)
    return abs(w - dw) < INACCURACY and abs(h - dh) < INACCURACY

def mm_to_inch(size: float) -> float:
    return size / MM_IN_INCH


def mm_to_point(size: float) -> float:
    return size * MM_IN_POINT


def mm_to_300dpi_pixel(size: float) -> int:
    return int(size * MM_IN_300_DPI_PIXEL)


def inch_to_mm(size: float) -> float:
    return size * MM_IN_INCH


def inch_to_point(size: float) -> float:
    return size * INCH_IN_POINT


def inch_to_300dpi_pixel(size: float) -> int:
    return int(size * INCH_IN_300_DPI_PIXEL)

def calculate_max_vertical_items_per_plate(machine_width: float, job_width: float) -> int:
    return int(machine_width / (job_width + (DEFAULT_BLEED * 2)))


def calculate_max_horizontal_items_per_plate(machine_height: float, job_height: float) -> int:
    return int(machine_height / (job_height + (DEFAULT_BLEED * 2)))

def get_b_format_from_custom_size(
    width: float,
    height: float,
    size_format: UnitFormat,
    is_offset_optimized: bool,
    is_perfect_bound: bool,
) -> int:
    # Convert to MM & Switch Orientation To Portrait
    w = min(width, height) * (MM_IN_INCH if size_format == UnitFormat.IMPERIAL else 1.0)
    h = max(width, height) * (MM_IN_INCH if size_format == UnitFormat.IMPERIAL else 1.0)

    printable_w_desc = [125, 150, 217, 353, 500, 707, 1000]
    printable_h_desc = [176, 214, 300, 500, 707, 1000, 1414]

    if is_offset_optimized:
        printable_w_desc = [125, 170, 245, 348, 495, 702, 995]
        if is_perfect_bound:
            printable_h_desc = [172, 240, 304, 495, 702, 995, 1409]
        else:
            printable_h_desc = [172, 240, 348, 495, 702, 995, 1409]

    for i in range(7):
        if printable_w_desc[i] > w and printable_h_desc[i] > h:
            return 6 - i

    return 0
