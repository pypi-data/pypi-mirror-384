from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.substrate_weight import SubstrateWeight, SubstrateWeightType


class SubstrateWeights:
    class Uk:
        class Silk(Enum):
            GSM_90 = SubstrateWeight(0, 90, 78.0)
            GSM_110 = SubstrateWeight(18, 110, 92.0)
            GSM_115 = SubstrateWeight(2, 115, 97.0)
            GSM_130 = SubstrateWeight(3, 130, 109.0)
            GSM_150 = SubstrateWeight(4, 150, 126.0)
            GSM_170 = SubstrateWeight(5, 170, 145.0)
            GSM_200 = SubstrateWeight(14, 200, 172.0)
            GSM_250 = SubstrateWeight(7, 250, 225.0)
            GSM_240 = SubstrateWeight(16, 240, 200.0)
            GSM_300 = SubstrateWeight(8, 300, 282.0)
            GSM_350 = SubstrateWeight(9, 350, 347.0)
            GSM_400 = SubstrateWeight(13, 400, 412.0)
            GSM_450 = SubstrateWeight(15, 450, 477.0)
            GSM_100 = SubstrateWeight(1, 100, 85.0)
            GSM_70 = SubstrateWeight(17, 70, 61.0)
            GSM_80 = SubstrateWeight(19, 80, 69.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            GSM_74 = SubstrateWeight(11, 74, 50.0)
            GSM_104 = SubstrateWeight(12, 104, 70.0)
            GSM_90 = SubstrateWeight(0, 90, 70.0)
            GSM_115 = SubstrateWeight(2, 115, 85.0)
            GSM_130 = SubstrateWeight(3, 130, 94.0)
            GSM_150 = SubstrateWeight(4, 150, 110.0)
            GSM_170 = SubstrateWeight(5, 170, 128.0)
            GSM_200 = SubstrateWeight(14, 200, 152.0)
            GSM_250 = SubstrateWeight(7, 250, 190.0)
            GSM_300 = SubstrateWeight(8, 300, 234.0)
            GSM_350 = SubstrateWeight(9, 350, 280.0)
            GSM_400 = SubstrateWeight(13, 400, 326.0)
            GSM_70 = SubstrateWeight(17, 70, 54.0)
            GSM_80 = SubstrateWeight(19, 80, 62.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            GSM_80 = SubstrateWeight(116, 80, 54.0)
            GSM_90 = SubstrateWeight(100, 90, 97.0)
            GSM_100 = SubstrateWeight(111, 100, 115.0)
            GSM_110 = SubstrateWeight(119, 110, 127.0)
            GSM_120 = SubstrateWeight(112, 120, 138.0)
            GSM_150 = SubstrateWeight(104, 150, 173.0)
            GSM_170 = SubstrateWeight(105, 170, 196.0)
            GSM_200 = SubstrateWeight(113, 200, 230.0)
            GSM_250 = SubstrateWeight(107, 250, 287.0)
            GSM_300 = SubstrateWeight(108, 300, 345.0)
            GSM_350 = SubstrateWeight(109, 350, 403.0)
            GSM_60 = SubstrateWeight(117, 60, 64.0)
            GSM_400 = SubstrateWeight(118, 400, 451.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PostcardBoard(Enum):
            GSM_280 = SubstrateWeight(11001, 280, 375.0)
            GSM_300 = SubstrateWeight(11003, 300, 438.0)
            GSM_350 = SubstrateWeight(11002, 350, 438.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            GSM_80 = SubstrateWeight(7001, 80, 100.0)
            GSM_100 = SubstrateWeight(7006, 100, 125.0)
            GSM_120 = SubstrateWeight(7007, 120, 150.0)
            GSM_135 = SubstrateWeight(7008, 135, 175.0)
            GSM_150 = SubstrateWeight(7009, 150, 188.0)
            GSM_170 = SubstrateWeight(7002, 170, 213.0)
            GSM_190 = SubstrateWeight(7010, 190, 237.0)
            GSM_250 = SubstrateWeight(7003, 250, 288.0)
            GSM_300 = SubstrateWeight(7005, 300, 345.0)
            GSM_350 = SubstrateWeight(7004, 350, 403.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledNatural(Enum):
            GSM_80 = SubstrateWeight(8001, 80, 103.0)
            GSM_100 = SubstrateWeight(8007, 100, 134.0)
            GSM_115 = SubstrateWeight(8006, 115, 154.0)
            GSM_135 = SubstrateWeight(8008, 135, 173.0)
            GSM_170 = SubstrateWeight(8002, 170, 212.0)
            GSM_250 = SubstrateWeight(8003, 250, 325.0)
            GSM_300 = SubstrateWeight(8005, 300, 390.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledSilk(Enum):
            GSM_100 = SubstrateWeight(45003, 100, 88.0)
            GSM_115 = SubstrateWeight(45004, 115, 90.0)
            GSM_130 = SubstrateWeight(45005, 130, 103.0)
            GSM_150 = SubstrateWeight(45006, 150, 118.0)
            GSM_170 = SubstrateWeight(45007, 170, 135.0)
            GSM_200 = SubstrateWeight(45008, 200, 165.0)
            GSM_250 = SubstrateWeight(45009, 250, 215.0)
            GSM_300 = SubstrateWeight(45010, 300, 275.0)
            GSM_350 = SubstrateWeight(45011, 350, 325.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Polyester(Enum):
            GSM_260 = SubstrateWeight(55000, 260, 220.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class MattePaper(Enum):
            GSM_74 = SubstrateWeight(62000, 74, 3.8)
            GSM_104 = SubstrateWeight(62001, 104, 3.8)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PremiumWhite(Enum):
            GSM_80 = SubstrateWeight(63000, 80, 3.9)
            GSM_90 = SubstrateWeight(63001, 90, 4.2)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Creme(Enum):
            GSM_70 = SubstrateWeight(60002, 70, 50.0)
            GSM_74 = SubstrateWeight(60000, 74, 50.0)
            GSM_80 = SubstrateWeight(60001, 80, 54.0)
            GSM_90 = SubstrateWeight(60003, 90, 58.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class EPhotoSilkLustre(Enum):
            GSM_190 = SubstrateWeight(78001, 190, 170.0)
            GSM_260 = SubstrateWeight(78002, 260, 225.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalTexturedMatt(Enum):
            GSM_240 = SubstrateWeight(81001, 240, 200.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalUncoated(Enum):
            GSM_300 = SubstrateWeight(80001, 300, 282.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalMatt(Enum):
            GSM_240 = SubstrateWeight(79001, 240, 200.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class WrappedGreyboard(Enum):
            GSM_650 = SubstrateWeight(83000, 650, 880000.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Linen(Enum):
            GSM_115 = SubstrateWeight(12000, 115, 160.0)
            GSM_125 = SubstrateWeight(12001, 125, 180.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PearlPolar(Enum):
            GSM_125 = SubstrateWeight(16000, 125, 150.0)
            GSM_300 = SubstrateWeight(16001, 300, 360.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PearlOyster(Enum):
            GSM_125 = SubstrateWeight(17000, 125, 150.0)
            GSM_300 = SubstrateWeight(17001, 300, 360.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class IceGold(Enum):
            GSM_300 = SubstrateWeight(41000, 300, 400.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class TintorettoGesso(Enum):
            GSM_140 = SubstrateWeight(36000, 140, 196.0)
            GSM_150 = SubstrateWeight(36001, 150, 210.0)
            GSM_250 = SubstrateWeight(36002, 250, 358.0)
            GSM_300 = SubstrateWeight(36003, 300, 429.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RivesShetland(Enum):
            GSM_250 = SubstrateWeight(43000, 250, 357.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Aquerello(Enum):
            GSM_160 = SubstrateWeight(86000, 160, 232.0)
            GSM_280 = SubstrateWeight(86001, 280, 406.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class FrescoGesso(Enum):
            GSM_300 = SubstrateWeight(42000, 300, 435.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Nettuno(Enum):
            GSM_140 = SubstrateWeight(87000, 140, 210.0)
            GSM_280 = SubstrateWeight(87001, 280, 420.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class LuxLayeredKraft(Enum):
            GSM_810 = SubstrateWeight(88000, 810, 1000.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class LuxLayeredWhite(Enum):
            GSM_810 = SubstrateWeight(89000, 810, 1000.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Kraft(Enum):
            GSM_120 = SubstrateWeight(39000, 120, 170.0)
            GSM_300 = SubstrateWeight(39001, 300, 380.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Laid(Enum):
            GSM_120 = SubstrateWeight(85000, 120, 171.0)
            GSM_300 = SubstrateWeight(85001, 300, 430.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Etching(Enum):
            GSM_300 = SubstrateWeight(90000, 300, 500.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RagPearl(Enum):
            GSM_320 = SubstrateWeight(91000, 320, 480.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class Us:
        class Silk(Enum):
            LBS_80_COVER = SubstrateWeight(1, 216, 8.00, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(2, 271, 10.00, 100, SubstrateWeightType.COVER)
            LBS_110_COVER = SubstrateWeight(3, 297, 12.00, 110, SubstrateWeightType.COVER)
            LBS_130_COVER = SubstrateWeight(5, 350, 16.00, 130, SubstrateWeightType.COVER)
            LBS_70_TEXT = SubstrateWeight(7, 104, 3.50, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(8, 118, 4.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(9, 148, 5.00, 100, SubstrateWeightType.TEXT)
            LBS_60_TEXT = SubstrateWeight(17, 104, 3.10, 60, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            LBS_50_COVER = SubstrateWeight(11, 74, 50.00, 50, SubstrateWeightType.COVER)
            LBS_70_COVER = SubstrateWeight(12, 104, 70.00, 70, SubstrateWeightType.COVER)
            LBS_80_COVER = SubstrateWeight(1, 216, 8.00, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(2, 271, 10.00, 100, SubstrateWeightType.COVER)
            LBS_110_COVER = SubstrateWeight(3, 297, 12.00, 110, SubstrateWeightType.COVER)
            LBS_130_COVER = SubstrateWeight(5, 350, 16.00, 130, SubstrateWeightType.COVER)
            LBS_70_TEXT = SubstrateWeight(7, 104, 3.50, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(8, 118, 4.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(9, 148, 5.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            LBS_65_COVER = SubstrateWeight(101, 176, 9.50, 65, SubstrateWeightType.COVER)
            LBS_80_COVER = SubstrateWeight(102, 216, 11.50, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(103, 270, 14.00, 100, SubstrateWeightType.COVER)
            LBS_120_COVER = SubstrateWeight(104, 325, 17.00, 120, SubstrateWeightType.COVER)
            LBS_40_TEXT = SubstrateWeight(117, 60, 3.4, 40, SubstrateWeightType.TEXT)
            LBS_50_TEXT = SubstrateWeight(105, 74, 4.00, 50, SubstrateWeightType.TEXT)
            LBS_60_TEXT = SubstrateWeight(106, 89, 4.50, 60, SubstrateWeightType.TEXT)
            LBS_70_TEXT = SubstrateWeight(107, 104, 5.00, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(108, 118, 6.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(109, 148, 7.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class MattePaper(Enum):
            LBS_50_TEXT = SubstrateWeight(62000, 74, 50.00, 50, SubstrateWeightType.TEXT)
            LBS_70_TEXT = SubstrateWeight(62001, 104, 70.00, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(62002, 120, 80.00, 80, SubstrateWeightType.TEXT)
            LBS_80_COVER = SubstrateWeight(62003, 216, 9.20, 80, SubstrateWeightType.COVER)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class None_(Enum):
            LBS_0_TEXT = SubstrateWeight(0, 0, 0.00, 0, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PolyfillBag(Enum):
            LBS_1_TEXT = SubstrateWeight(76001, 1, 0.10, 1, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PremiumWhite(Enum):
            LBS_54_TEXT = SubstrateWeight(63000, 80, 3.80, 54, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            LBS_60_TEXT = SubstrateWeight(7001, 89, 4.50, 60, SubstrateWeightType.TEXT)
            LBS_70_TEXT = SubstrateWeight(7002, 104, 5.00, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(7003, 118, 6.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(7004, 148, 7.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class UncoatedCremePaper(Enum):
            LBS_60_TEXT = SubstrateWeight(35000, 89, 4.00, 60, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class EPhotoPaper(Enum):
            LBS_110_COVER = SubstrateWeight(77000, 222, 8.35, 110, SubstrateWeightType.COVER)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class Ca:
        class Silk(Enum):
            LBS_80_COVER = SubstrateWeight(1, 216, 8.00, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(2, 271, 10.00, 100, SubstrateWeightType.COVER)
            LBS_110_COVER = SubstrateWeight(3, 297, 12.00, 110, SubstrateWeightType.COVER)
            LBS_130_COVER = SubstrateWeight(5, 350, 16.00, 130, SubstrateWeightType.COVER)
            LBS_70_TEXT = SubstrateWeight(7, 104, 3.50, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(8, 118, 4.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(9, 148, 5.00, 100, SubstrateWeightType.TEXT)
            LBS_60_TEXT = SubstrateWeight(17, 104, 3.10, 60, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            LBS_50_COVER = SubstrateWeight(11, 74, 50.00, 50, SubstrateWeightType.COVER)
            LBS_70_COVER = SubstrateWeight(12, 104, 70.00, 70, SubstrateWeightType.COVER)
            LBS_80_COVER = SubstrateWeight(1, 216, 8.00, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(2, 271, 10.00, 100, SubstrateWeightType.COVER)
            LBS_110_COVER = SubstrateWeight(3, 297, 12.00, 110, SubstrateWeightType.COVER)
            LBS_130_COVER = SubstrateWeight(5, 350, 16.00, 130, SubstrateWeightType.COVER)
            LBS_70_TEXT = SubstrateWeight(7, 104, 3.50, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(8, 118, 4.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(9, 148, 5.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            LBS_65_COVER = SubstrateWeight(101, 176, 9.50, 65, SubstrateWeightType.COVER)
            LBS_80_COVER = SubstrateWeight(102, 216, 11.50, 80, SubstrateWeightType.COVER)
            LBS_100_COVER = SubstrateWeight(103, 270, 14.00, 100, SubstrateWeightType.COVER)
            LBS_120_COVER = SubstrateWeight(104, 325, 17.00, 120, SubstrateWeightType.COVER)
            LBS_50_TEXT = SubstrateWeight(105, 74, 4.00, 50, SubstrateWeightType.TEXT)
            LBS_60_TEXT = SubstrateWeight(106, 89, 4.50, 60, SubstrateWeightType.TEXT)
            LBS_70_TEXT = SubstrateWeight(107, 104, 5.00, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(108, 118, 6.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(109, 148, 7.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PhotoLustre(Enum):
            LBS_110_COVER = SubstrateWeight(82000, 222, 8.35, 110, SubstrateWeightType.COVER)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            LBS_60_TEXT = SubstrateWeight(7001, 89, 4.50, 60, SubstrateWeightType.TEXT)
            LBS_70_TEXT = SubstrateWeight(7002, 104, 5.00, 70, SubstrateWeightType.TEXT)
            LBS_80_TEXT = SubstrateWeight(7003, 118, 6.00, 80, SubstrateWeightType.TEXT)
            LBS_100_TEXT = SubstrateWeight(7004, 148, 7.00, 100, SubstrateWeightType.TEXT)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class Au:
        class Silk(Enum):
            GSM_90 = SubstrateWeight(0, 90, 78.0)
            GSM_115 = SubstrateWeight(2, 115, 97.0)
            GSM_130 = SubstrateWeight(3, 130, 109.0)
            GSM_150 = SubstrateWeight(4, 150, 126.0)
            GSM_170 = SubstrateWeight(5, 170, 145.0)
            GSM_200 = SubstrateWeight(14, 200, 172.0)
            GSM_250 = SubstrateWeight(7, 250, 225.0)
            GSM_300 = SubstrateWeight(8, 300, 282.0)
            GSM_350 = SubstrateWeight(9, 350, 347.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            GSM_90 = SubstrateWeight(0, 90, 70.0)
            GSM_115 = SubstrateWeight(2, 115, 85.0)
            GSM_130 = SubstrateWeight(3, 130, 94.0)
            GSM_150 = SubstrateWeight(4, 150, 110.0)
            GSM_170 = SubstrateWeight(5, 170, 128.0)
            GSM_200 = SubstrateWeight(14, 200, 152.0)
            GSM_250 = SubstrateWeight(7, 250, 190.0)
            GSM_300 = SubstrateWeight(8, 300, 234.0)
            GSM_350 = SubstrateWeight(9, 350, 280.0)
            GSM_74 = SubstrateWeight(11, 74, 50.0)
            GSM_104 = SubstrateWeight(12, 104, 70.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            GSM_90 = SubstrateWeight(100, 90, 97.0)
            GSM_100 = SubstrateWeight(111, 100, 115.0)
            GSM_120 = SubstrateWeight(112, 120, 138.0)
            GSM_150 = SubstrateWeight(104, 150, 173.0)
            GSM_170 = SubstrateWeight(105, 170, 196.0)
            GSM_200 = SubstrateWeight(113, 200, 230.0)
            GSM_250 = SubstrateWeight(107, 250, 287.0)
            GSM_300 = SubstrateWeight(108, 300, 345.0)
            GSM_350 = SubstrateWeight(109, 350, 403.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Creme(Enum):
            GSM_70 = SubstrateWeight(60002, 70, 50.0)
            GSM_74 = SubstrateWeight(60000, 74, 50.0)
            GSM_80 = SubstrateWeight(60001, 80, 54.0)
            GSM_90 = SubstrateWeight(60003, 90, 58.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class MattePaper(Enum):
            GSM_74 = SubstrateWeight(62000, 74, 3.8)
            GSM_104 = SubstrateWeight(62001, 104, 3.8)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledSilk(Enum):
            GSM_100 = SubstrateWeight(45003, 100, 88.0)
            GSM_115 = SubstrateWeight(45004, 115, 90.0)
            GSM_130 = SubstrateWeight(45005, 130, 103.0)
            GSM_150 = SubstrateWeight(45006, 150, 118.0)
            GSM_170 = SubstrateWeight(45007, 170, 135.0)
            GSM_200 = SubstrateWeight(45008, 200, 165.0)
            GSM_250 = SubstrateWeight(45009, 250, 215.0)
            GSM_300 = SubstrateWeight(45010, 300, 275.0)
            GSM_350 = SubstrateWeight(45011, 350, 325.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            GSM_90 = SubstrateWeight(7001, 90, 113.0)
            GSM_100 = SubstrateWeight(7006, 100, 125.0)
            GSM_120 = SubstrateWeight(7007, 120, 150.0)
            GSM_135 = SubstrateWeight(7008, 135, 175.0)
            GSM_150 = SubstrateWeight(7009, 150, 188.0)
            GSM_160 = SubstrateWeight(7011, 160, 201.0)
            GSM_170 = SubstrateWeight(7002, 170, 213.0)
            GSM_190 = SubstrateWeight(7010, 190, 237.0)
            GSM_250 = SubstrateWeight(7003, 250, 288.0)
            GSM_300 = SubstrateWeight(7005, 300, 345.0)
            GSM_350 = SubstrateWeight(7004, 350, 403.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class De:
        class Silk(Enum):
            GSM_90 = SubstrateWeight(0, 90, 78.0)
            GSM_110 = SubstrateWeight(18, 110, 92.0)
            GSM_115 = SubstrateWeight(2, 115, 97.0)
            GSM_135 = SubstrateWeight(3, 135, 109.0)
            GSM_150 = SubstrateWeight(4, 150, 126.0)
            GSM_170 = SubstrateWeight(5, 170, 145.0)
            GSM_200 = SubstrateWeight(14, 200, 172.0)
            GSM_250 = SubstrateWeight(7, 250, 225.0)
            GSM_240 = SubstrateWeight(16, 240, 200.0)
            GSM_300 = SubstrateWeight(8, 300, 282.0)
            GSM_350 = SubstrateWeight(9, 350, 347.0)
            GSM_400 = SubstrateWeight(13, 400, 412.0)
            GSM_450 = SubstrateWeight(15, 450, 477.0)
            GSM_100 = SubstrateWeight(1, 100, 85.0)
            GSM_70 = SubstrateWeight(19, 70, 60.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            GSM_74 = SubstrateWeight(11, 74, 50.0)
            GSM_104 = SubstrateWeight(12, 104, 70.0)
            GSM_90 = SubstrateWeight(0, 90, 70.0)
            GSM_115 = SubstrateWeight(2, 115, 85.0)
            GSM_135 = SubstrateWeight(3, 135, 94.0)
            GSM_150 = SubstrateWeight(4, 150, 110.0)
            GSM_170 = SubstrateWeight(5, 170, 128.0)
            GSM_200 = SubstrateWeight(14, 200, 152.0)
            GSM_250 = SubstrateWeight(7, 250, 190.0)
            GSM_300 = SubstrateWeight(8, 300, 234.0)
            GSM_350 = SubstrateWeight(9, 350, 280.0)
            GSM_400 = SubstrateWeight(13, 400, 326.0)
            GSM_100 = SubstrateWeight(1, 100, 77.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            GSM_80 = SubstrateWeight(116, 80, 100.0)
            GSM_90 = SubstrateWeight(100, 90, 110.0)
            GSM_100 = SubstrateWeight(111, 100, 115.0)
            GSM_110 = SubstrateWeight(119, 110, 127.0)
            GSM_120 = SubstrateWeight(112, 120, 138.0)
            GSM_150 = SubstrateWeight(104, 150, 173.0)
            GSM_170 = SubstrateWeight(105, 170, 196.0)
            GSM_200 = SubstrateWeight(113, 200, 230.0)
            GSM_250 = SubstrateWeight(107, 250, 287.0)
            GSM_300 = SubstrateWeight(108, 300, 345.0)
            GSM_350 = SubstrateWeight(109, 350, 403.0)
            GSM_400 = SubstrateWeight(110, 400, 453.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledNatural(Enum):
            GSM_80 = SubstrateWeight(8001, 80, 103.0)
            GSM_90 = SubstrateWeight(8004, 90, 118.0)
            GSM_100 = SubstrateWeight(8007, 100, 134.0)
            GSM_120 = SubstrateWeight(8006, 120, 154.0)
            GSM_135 = SubstrateWeight(8008, 135, 173.0)
            GSM_160 = SubstrateWeight(8002, 160, 212.0)
            GSM_250 = SubstrateWeight(8003, 250, 325.0)
            GSM_300 = SubstrateWeight(8005, 300, 390.0)
            GSM_400 = SubstrateWeight(8009, 400, 450.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            GSM_80 = SubstrateWeight(7001, 80, 100.0)
            GSM_100 = SubstrateWeight(7006, 100, 125.0)
            GSM_120 = SubstrateWeight(7007, 120, 150.0)
            GSM_135 = SubstrateWeight(7008, 135, 175.0)
            GSM_150 = SubstrateWeight(7009, 150, 188.0)
            GSM_170 = SubstrateWeight(7002, 170, 213.0)
            GSM_400 = SubstrateWeight(7010, 400, 450.0)
            GSM_250 = SubstrateWeight(7003, 250, 288.0)
            GSM_300 = SubstrateWeight(7005, 300, 345.0)
            GSM_350 = SubstrateWeight(7004, 350, 403.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Polyester(Enum):
            GSM_190 = SubstrateWeight(56000, 190, 150.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Creme(Enum):
            GSM_70 = SubstrateWeight(60002, 70, 50.0)
            GSM_74 = SubstrateWeight(60000, 74, 50.0)
            GSM_80 = SubstrateWeight(60001, 80, 54.0)
            GSM_90 = SubstrateWeight(60003, 90, 58.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PostcardBoard(Enum):
            GSM_280 = SubstrateWeight(11001, 280, 375.0)
            GSM_300 = SubstrateWeight(11003, 300, 438.0)
            GSM_350 = SubstrateWeight(11002, 350, 438.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Affiche(Enum):
            GSM_115 = SubstrateWeight(10001, 115, 97.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class Ie:
        class Silk(Enum):
            GSM_90 = SubstrateWeight(0, 90, 78.0)
            GSM_110 = SubstrateWeight(18, 110, 92.0)
            GSM_115 = SubstrateWeight(2, 115, 97.0)
            GSM_135 = SubstrateWeight(3, 135, 109.0)
            GSM_150 = SubstrateWeight(4, 150, 126.0)
            GSM_170 = SubstrateWeight(5, 170, 145.0)
            GSM_200 = SubstrateWeight(14, 200, 172.0)
            GSM_250 = SubstrateWeight(7, 250, 225.0)
            GSM_240 = SubstrateWeight(16, 240, 200.0)
            GSM_300 = SubstrateWeight(8, 300, 282.0)
            GSM_350 = SubstrateWeight(9, 350, 347.0)
            GSM_400 = SubstrateWeight(13, 400, 412.0)
            GSM_450 = SubstrateWeight(15, 450, 477.0)
            GSM_100 = SubstrateWeight(1, 100, 85.0)
            GSM_70 = SubstrateWeight(19, 70, 60.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            GSM_74 = SubstrateWeight(11, 74, 50.0)
            GSM_104 = SubstrateWeight(12, 104, 70.0)
            GSM_90 = SubstrateWeight(0, 90, 70.0)
            GSM_115 = SubstrateWeight(2, 115, 85.0)
            GSM_135 = SubstrateWeight(3, 135, 94.0)
            GSM_150 = SubstrateWeight(4, 150, 110.0)
            GSM_170 = SubstrateWeight(5, 170, 128.0)
            GSM_200 = SubstrateWeight(14, 200, 152.0)
            GSM_250 = SubstrateWeight(7, 250, 190.0)
            GSM_300 = SubstrateWeight(8, 300, 234.0)
            GSM_350 = SubstrateWeight(9, 350, 280.0)
            GSM_400 = SubstrateWeight(13, 400, 326.0)
            GSM_100 = SubstrateWeight(1, 100, 77.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            GSM_80 = SubstrateWeight(116, 80, 54.0)
            GSM_90 = SubstrateWeight(100, 90, 97.0)
            GSM_100 = SubstrateWeight(111, 100, 115.0)
            GSM_110 = SubstrateWeight(119, 110, 127.0)
            GSM_120 = SubstrateWeight(112, 120, 138.0)
            GSM_150 = SubstrateWeight(104, 150, 173.0)
            GSM_170 = SubstrateWeight(105, 170, 196.0)
            GSM_200 = SubstrateWeight(113, 200, 230.0)
            GSM_250 = SubstrateWeight(107, 250, 287.0)
            GSM_300 = SubstrateWeight(108, 300, 345.0)
            GSM_350 = SubstrateWeight(109, 350, 403.0)
            GSM_400 = SubstrateWeight(110, 400, 453.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledNatural(Enum):
            GSM_80 = SubstrateWeight(8001, 80, 103.0)
            GSM_90 = SubstrateWeight(8004, 90, 118.0)
            GSM_100 = SubstrateWeight(8007, 100, 134.0)
            GSM_120 = SubstrateWeight(8006, 120, 154.0)
            GSM_135 = SubstrateWeight(8008, 135, 173.0)
            GSM_160 = SubstrateWeight(8002, 160, 212.0)
            GSM_250 = SubstrateWeight(8003, 250, 325.0)
            GSM_300 = SubstrateWeight(8005, 300, 390.0)
            GSM_400 = SubstrateWeight(8009, 400, 450.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            GSM_80 = SubstrateWeight(7001, 80, 100.0)
            GSM_100 = SubstrateWeight(7006, 100, 125.0)
            GSM_120 = SubstrateWeight(7007, 120, 150.0)
            GSM_135 = SubstrateWeight(7008, 135, 175.0)
            GSM_150 = SubstrateWeight(7009, 150, 188.0)
            GSM_170 = SubstrateWeight(7002, 170, 213.0)
            GSM_190 = SubstrateWeight(7010, 190, 237.0)
            GSM_250 = SubstrateWeight(7003, 250, 288.0)
            GSM_300 = SubstrateWeight(7005, 300, 345.0)
            GSM_350 = SubstrateWeight(7004, 350, 403.0)
            GSM_400 = SubstrateWeight(7010, 400, 450.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Polyester(Enum):
            GSM_190 = SubstrateWeight(56000, 190, 150.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Creme(Enum):
            GSM_70 = SubstrateWeight(60002, 70, 50.0)
            GSM_74 = SubstrateWeight(60000, 74, 50.0)
            GSM_80 = SubstrateWeight(60001, 80, 54.0)
            GSM_90 = SubstrateWeight(60003, 90, 58.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PostcardBoard(Enum):
            GSM_280 = SubstrateWeight(11001, 280, 375.0)
            GSM_300 = SubstrateWeight(11003, 300, 438.0)
            GSM_350 = SubstrateWeight(11002, 350, 438.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Affiche(Enum):
            GSM_115 = SubstrateWeight(10001, 115, 97.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

    class Jp:
        class Silk(Enum):
            GSM_110 = SubstrateWeight(18, 110, 92.0)
            GSM_115 = SubstrateWeight(2, 115, 97.0)
            GSM_130 = SubstrateWeight(3, 130, 109.0)
            GSM_150 = SubstrateWeight(4, 150, 126.0)
            GSM_170 = SubstrateWeight(5, 170, 145.0)
            GSM_200 = SubstrateWeight(14, 200, 172.0)
            GSM_250 = SubstrateWeight(7, 250, 225.0)
            GSM_240 = SubstrateWeight(16, 240, 200.0)
            GSM_300 = SubstrateWeight(8, 300, 282.0)
            GSM_350 = SubstrateWeight(9, 350, 347.0)
            GSM_400 = SubstrateWeight(13, 400, 412.0)
            GSM_450 = SubstrateWeight(15, 450, 477.0)
            GSM_100 = SubstrateWeight(1, 100, 85.0)
            GSM_128 = SubstrateWeight(19, 128, 109.0)
            GSM_105 = SubstrateWeight(20, 105, 92.0)
            GSM_157 = SubstrateWeight(21, 157, 126.0)
            GSM_186 = SubstrateWeight(22, 186, 172.0)
            GSM_209 = SubstrateWeight(23, 209, 180.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Gloss(Enum):
            GSM_74 = SubstrateWeight(11, 74, 50.0)
            GSM_104 = SubstrateWeight(12, 104, 70.0)
            GSM_115 = SubstrateWeight(2, 115, 85.0)
            GSM_130 = SubstrateWeight(3, 130, 94.0)
            GSM_150 = SubstrateWeight(4, 150, 110.0)
            GSM_170 = SubstrateWeight(5, 170, 128.0)
            GSM_200 = SubstrateWeight(14, 200, 152.0)
            GSM_250 = SubstrateWeight(7, 250, 190.0)
            GSM_300 = SubstrateWeight(8, 300, 234.0)
            GSM_350 = SubstrateWeight(9, 350, 280.0)
            GSM_400 = SubstrateWeight(13, 400, 326.0)
            GSM_105 = SubstrateWeight(15, 105, 85.0)
            GSM_128 = SubstrateWeight(16, 128, 94.0)
            GSM_157 = SubstrateWeight(17, 157, 110.0)
            GSM_186 = SubstrateWeight(18, 186, 128.0)
            GSM_209 = SubstrateWeight(19, 209, 152.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Uncoated(Enum):
            GSM_80 = SubstrateWeight(116, 80, 54.0)
            GSM_90 = SubstrateWeight(100, 90, 97.0)
            GSM_100 = SubstrateWeight(111, 100, 115.0)
            GSM_110 = SubstrateWeight(119, 110, 127.0)
            GSM_120 = SubstrateWeight(112, 120, 138.0)
            GSM_150 = SubstrateWeight(104, 150, 173.0)
            GSM_170 = SubstrateWeight(105, 170, 196.0)
            GSM_200 = SubstrateWeight(113, 200, 230.0)
            GSM_250 = SubstrateWeight(107, 250, 287.0)
            GSM_300 = SubstrateWeight(108, 300, 345.0)
            GSM_350 = SubstrateWeight(109, 350, 403.0)
            GSM_81 = SubstrateWeight(120, 81, 97.0)
            GSM_105 = SubstrateWeight(121, 105, 127.0)
            GSM_128 = SubstrateWeight(122, 128, 138.0)
            GSM_157 = SubstrateWeight(123, 157, 173.0)
            GSM_209 = SubstrateWeight(124, 209, 230.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PostcardBoard(Enum):
            GSM_280 = SubstrateWeight(11001, 280, 375.0)
            GSM_300 = SubstrateWeight(11003, 300, 438.0)
            GSM_350 = SubstrateWeight(11002, 350, 438.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledUncoated(Enum):
            GSM_80 = SubstrateWeight(7001, 80, 100.0)
            GSM_100 = SubstrateWeight(7006, 100, 125.0)
            GSM_120 = SubstrateWeight(7007, 120, 150.0)
            GSM_135 = SubstrateWeight(7008, 135, 175.0)
            GSM_150 = SubstrateWeight(7009, 150, 188.0)
            GSM_170 = SubstrateWeight(7002, 170, 213.0)
            GSM_190 = SubstrateWeight(7010, 190, 237.0)
            GSM_250 = SubstrateWeight(7003, 250, 288.0)
            GSM_300 = SubstrateWeight(7005, 300, 345.0)
            GSM_350 = SubstrateWeight(7004, 350, 403.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledNatural(Enum):
            GSM_80 = SubstrateWeight(8001, 80, 103.0)
            GSM_100 = SubstrateWeight(8007, 100, 134.0)
            GSM_115 = SubstrateWeight(8006, 115, 154.0)
            GSM_135 = SubstrateWeight(8008, 135, 173.0)
            GSM_170 = SubstrateWeight(8002, 170, 212.0)
            GSM_250 = SubstrateWeight(8003, 250, 325.0)
            GSM_300 = SubstrateWeight(8005, 300, 390.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class RecycledSilk(Enum):
            GSM_100 = SubstrateWeight(45003, 100, 88.0)
            GSM_115 = SubstrateWeight(45004, 115, 90.0)
            GSM_130 = SubstrateWeight(45005, 130, 103.0)
            GSM_150 = SubstrateWeight(45006, 150, 118.0)
            GSM_170 = SubstrateWeight(45007, 170, 135.0)
            GSM_200 = SubstrateWeight(45008, 200, 165.0)
            GSM_250 = SubstrateWeight(45009, 250, 215.0)
            GSM_300 = SubstrateWeight(45010, 300, 275.0)
            GSM_350 = SubstrateWeight(45011, 350, 325.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Polyester(Enum):
            GSM_260 = SubstrateWeight(55000, 260, 220.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class MattePaper(Enum):
            GSM_74 = SubstrateWeight(62000, 74, 3.8)
            GSM_104 = SubstrateWeight(62001, 104, 3.8)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class PremiumWhite(Enum):
            GSM_80 = SubstrateWeight(63000, 80, 3.9)
            GSM_90 = SubstrateWeight(63001, 90, 4.2)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Creme(Enum):
            GSM_70 = SubstrateWeight(60002, 70, 50.0)
            GSM_74 = SubstrateWeight(60000, 74, 50.0)
            GSM_80 = SubstrateWeight(60001, 80, 54.0)
            GSM_90 = SubstrateWeight(60003, 90, 58.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class EPhotoSilkLustre(Enum):
            GSM_190 = SubstrateWeight(78001, 190, 170.0)
            GSM_260 = SubstrateWeight(78002, 260, 225.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalTexturedMatt(Enum):
            GSM_240 = SubstrateWeight(81001, 240, 200.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalUncoated(Enum):
            GSM_300 = SubstrateWeight(80001, 300, 282.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class ArchivalMatt(Enum):
            GSM_240 = SubstrateWeight(79001, 240, 200.0)

            def get_values(self) -> SubstrateWeight:
                return self.value

        class Buckram(Enum):
            GSM_115 = SubstrateWeight(84000, 115, 185.0)

            def get_values(self) -> SubstrateWeight:
                return self.value
