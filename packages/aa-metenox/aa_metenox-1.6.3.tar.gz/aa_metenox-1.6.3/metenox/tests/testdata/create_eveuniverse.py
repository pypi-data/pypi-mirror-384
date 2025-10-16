from django.test import TestCase
from eveuniverse.models import EveType
from eveuniverse.tools.testdata import ModelSpec, create_testdata

from . import test_data_filename


class CreateEveUniverseTestData(TestCase):
    def test_create_testdata(self):
        moon_goo_id_range = [i for i in range(16633, 16654)]
        moon_goo_id_range.remove(16645)  # why does this one not exists? #CCPLZ
        testdata_spec = [
            ModelSpec(
                "EveMoon",
                ids=[
                    40178441,  # Loads Tama
                    40178267,  # Eranakko
                    40178195,  # Sujarento
                    40178312,  # Onatoh x
                    40178362,  # Tannolen
                    40178073,  # Nagamanen
                    40471667,  # Some wh system
                ],
            ),
            ModelSpec("EveType", ids=moon_goo_id_range),  # all moon goo
            ModelSpec("EveType", ids=[81143]),  # Magmatic gases
            ModelSpec(
                "EveType",
                ids=[
                    45490,
                    45491,
                    45492,
                    45493,
                    46280,
                    46281,
                    46282,
                    46283,
                    46284,
                    46285,
                    46286,
                    46287,
                    62454,
                    62455,
                    62456,
                    62457,
                    62458,
                    62459,
                    62460,
                    62461,
                    62463,
                    62464,
                    62466,
                    62467,
                ],
                enabled_sections=[EveType.Section.TYPE_MATERIALS],
            ),  # Ubiquitous Moon Asteroids
            ModelSpec(
                "EveType",
                ids=[
                    45494,
                    45495,
                    45496,
                    45497,
                    46288,
                    46289,
                    46290,
                    46291,
                    46292,
                    46293,
                    46294,
                    46295,
                    62468,
                    62469,
                    62470,
                    62471,
                    62472,
                    62473,
                    62474,
                    62475,
                    62476,
                    62477,
                    62478,
                    62479,
                ],
                enabled_sections=[EveType.Section.TYPE_MATERIALS],
            ),  # Common Moon Asteroids.Section.TYPE_MATERIALS
            ModelSpec(
                "EveType",
                ids=[
                    45498,
                    45499,
                    45500,
                    45501,
                    46296,
                    46297,
                    46298,
                    46299,
                    46300,
                    46301,
                    46302,
                    46303,
                    62480,
                    62481,
                    62482,
                    62483,
                    62484,
                    62485,
                    62486,
                    62487,
                    62488,
                    62489,
                    62490,
                    62491,
                ],
                enabled_sections=[EveType.Section.TYPE_MATERIALS],
            ),  # Uncommon Moon Asteroids.Section.TYPE_MATERIALS
            ModelSpec(
                "EveType",
                ids=[
                    45510,
                    45511,
                    45512,
                    45513,
                    46312,
                    46313,
                    46314,
                    46315,
                    46316,
                    46317,
                    46318,
                    46319,
                    62504,
                    62505,
                    62506,
                    62507,
                    62508,
                    62509,
                    62510,
                    62511,
                    62512,
                    62513,
                    62514,
                    62515,
                ],
                enabled_sections=[EveType.Section.TYPE_MATERIALS],
            ),  # Exceptional Moon Asteroids
        ]
        create_testdata(testdata_spec, test_data_filename())
