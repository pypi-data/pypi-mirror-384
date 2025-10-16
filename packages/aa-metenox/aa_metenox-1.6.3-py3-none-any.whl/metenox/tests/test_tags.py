from django.test import TestCase

from metenox.models import MetenoxTag
from metenox.tests.testdata.load_eveuniverse import load_eveuniverse

from .utils import create_test_metenox


class TestTags(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    def test_get_holding_tags(self):
        tag1 = MetenoxTag.objects.create(name="Tag1")
        tag2 = MetenoxTag.objects.create(name="Tag2")

        metenox = create_test_metenox()
        holding = metenox.corporation

        self.assertEqual([], holding.get_holding_tags())

        metenox.tags.add(tag1)

        tag_list = holding.get_holding_tags()

        self.assertIn(tag1, tag_list)
        self.assertNotIn(tag2, tag_list)

    def test_count_metenox_tags(self):
        tag1 = MetenoxTag.objects.create(name="Tag1")
        tag2 = MetenoxTag.objects.create(name="Tag2")

        metenox = create_test_metenox()
        holding = metenox.corporation

        self.assertEqual(0, holding.count_metenoxes_with_tag(tag1))
        self.assertEqual(0, holding.count_metenoxes_with_tag(tag2))

        metenox.tags.add(tag1)

        self.assertEqual(1, holding.count_metenoxes_with_tag(tag1))
        self.assertEqual(0, holding.count_metenoxes_with_tag(tag2))
