from django.test import TestCase
from eveuniverse.tools.testdata import ModelSpec, create_testdata

from . import test_data_filename


class CreateEveuniverseTestData(TestCase):
    def test_create_testdata(self):
        test_data_spec = [
            ModelSpec(
                "EveType",
                ids=[
                    28352,  # Rorqual
                    19720,  # Revelation
                    11567,  # Avatar
                    621,  # Caracal
                    585,  # Slasher
                ],
            )
        ]
        create_testdata(test_data_spec, test_data_filename())
