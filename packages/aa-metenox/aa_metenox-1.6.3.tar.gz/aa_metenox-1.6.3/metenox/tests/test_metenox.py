from unittest.mock import MagicMock

from moonmining.models import Moon as MoonMiningMoon
from moonmining.models import MoonProduct

from django.test import TestCase
from eveuniverse.models import EveType

from metenox.models import (
    EveTypePrice,
    HoldingCorporation,
    MetenoxStoredMoonMaterials,
    MetenoxTag,
)
from metenox.tasks import update_moons_from_moonmining
from metenox.tests.testdata.load_eveuniverse import load_eveuniverse
from metenox.tests.utils import MOON_ID, create_test_metenox


class TestMetenoxes(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()

    def test_moon_update_when_metenox_created_on_empty_moon(self):
        """
        Check that when a metenox is created on a moon that isn't present in moonmining an update will happen
        if the moon appears in moonmining
        """

        metenox = create_test_metenox()

        self.assertEqual(
            len(metenox.moon.hourly_pull), 0
        )  # checks that the moon is empty
        self.assertEqual(metenox.moon.moonmining_moon, None)

        moon_scan = {
            45490: 0.2809781134,
            45491: 0.2083230466,
            45493: 0.5106988549,
        }

        moonmining_moon, _ = MoonMiningMoon.objects.get_or_create(eve_moon_id=MOON_ID)

        moon_products = [
            MoonProduct(
                moon=moonmining_moon, ore_type_id=ore_type_id, amount=ore_type_amount
            )
            for ore_type_id, ore_type_amount in moon_scan.items()
        ]
        moonmining_moon.update_products(moon_products)

        update_moons_from_moonmining()

        self.assertEqual(
            len(metenox.moon.hourly_pull), 3
        )  # checks that  the moon was updated

    def test_total_stored_volume(self):
        """Checks the volume stored in a metenox"""

        metenox = create_test_metenox()

        atmospheric_gases = EveType.objects.get(id=16634)
        hydrocarbons = EveType.objects.get(id=16633)

        stored_atmospheric_gases = MetenoxStoredMoonMaterials(
            metenox=metenox, product=atmospheric_gases, amount=50
        )
        stored_atmospheric_gases.save()
        stored_hydrocarbons = MetenoxStoredMoonMaterials(
            metenox=metenox, product=hydrocarbons, amount=200
        )
        stored_hydrocarbons.save()

        self.assertEqual(
            metenox.get_stored_moon_materials_volume(), 50 * 0.05 + 200 * 0.05
        )

    def test_total_stored_value(self):
        """Checks the value stored in a metenox"""

        metenox = create_test_metenox()
        hydrocarbon = EveType.objects.get(id=16633)
        atmospheric_gases = EveType.objects.get(id=16634)
        EveTypePrice.objects.create(eve_type=hydrocarbon, price=2000)
        EveTypePrice.objects.create(eve_type=atmospheric_gases, price=1000)

        MetenoxStoredMoonMaterials.objects.create(
            metenox=metenox, product=atmospheric_gases, amount=50
        )
        MetenoxStoredMoonMaterials.objects.create(
            metenox=metenox, product=hydrocarbon, amount=200
        )

        self.assertEqual(
            2000 * 200 + 1000 * 50, metenox.get_stored_moon_materials_value()
        )

    def test_set_fuel_blocks(self):
        """Test the set_fuel_blocks command"""

        metenox = create_test_metenox()
        holding = metenox.corporation
        holding.ping_on_remaining_fuel_days = (
            1  # 120 fuel blocks being a daily consumption
        )
        holding.save()

        self.assertEqual(metenox.fuel_blocks_count, 0)

        metenox.set_fuel_blocs(1400)

        self.assertEqual(metenox.fuel_blocks_count, 1400)
        self.assertFalse(metenox.was_fuel_pinged)  # enough fuel to last longer

        metenox.set_fuel_blocs(20)

        self.assertEqual(metenox.fuel_blocks_count, 20)
        self.assertTrue(metenox.was_fuel_pinged)

        metenox.set_fuel_blocs(1500)

        self.assertEqual(metenox.fuel_blocks_count, 1500)
        self.assertFalse(metenox.was_fuel_pinged)

    def test_set_magmatic(self):
        """Test the set_magmatic command"""

        metenox = create_test_metenox()
        holding = metenox.corporation
        holding.ping_on_remaining_magmatic_days = (
            1  # 4800 magmatic gases being a daily consumption
        )
        holding.save()

        self.assertEqual(metenox.fuel_blocks_count, 0)

        metenox.set_magmatic_gases(5000)

        self.assertEqual(metenox.magmatic_gas_count, 5000)
        self.assertFalse(metenox.was_magmatic_pinged)

        metenox.set_magmatic_gases(1000)

        self.assertEqual(metenox.magmatic_gas_count, 1000)
        self.assertTrue(metenox.was_magmatic_pinged)

        metenox.set_magmatic_gases(5000)

        self.assertEqual(metenox.magmatic_gas_count, 5000)
        self.assertFalse(metenox.was_magmatic_pinged)

    def test_default_tags(self):
        """
        Checks that on metenox creation the default tags are correctly added
        """

        tag1 = MetenoxTag.objects.create(name="tag1", default=True)
        tag2 = MetenoxTag.objects.create(name="tag2", default=True)
        tag3 = MetenoxTag.objects.create(name="tag3")

        metenox = create_test_metenox()

        self.assertIn(tag1, metenox.tags.all())
        self.assertIn(tag2, metenox.tags.all())
        self.assertNotIn(tag3, metenox.tags.all())

    def test_check_moon_material_bay(self):
        HoldingCorporation.ping_metenox_value = MagicMock()
        HoldingCorporation.ping_metenox_volume = MagicMock()

        metenox = create_test_metenox()
        holding = metenox.corporation
        scandium = EveType.objects.get(id=16639)  # volume = 0.05

        scandium_price = EveTypePrice.objects.create(eve_type=scandium, price=100)
        holding.ping_on_value_in_moongoo_bay = 1000
        holding.save()

        MetenoxStoredMoonMaterials.objects.create(
            metenox=metenox,
            product=scandium,
            amount=1,
        )

        # nothing should ping
        metenox.check_moon_material_bay()

        HoldingCorporation.ping_metenox_value.assert_not_called()
        HoldingCorporation.ping_metenox_volume.assert_not_called()

        metenox.last_moongoo_bay_ping = None  # Resets timer
        metenox.save()

        MetenoxStoredMoonMaterials.objects.update_or_create(
            metenox=metenox, product=scandium, defaults={"amount": 100}
        )

        # value should ping
        metenox.check_moon_material_bay()

        HoldingCorporation.ping_metenox_value.assert_called_once()
        HoldingCorporation.ping_metenox_volume.assert_not_called()

        HoldingCorporation.ping_metenox_value = MagicMock()  # Resets call count
        metenox.last_moongoo_bay_ping = None  # Resets timer
        metenox.save()

        holding.ping_on_volume_in_moongoo_bay = 1  # volume should be 2 so ping

        # value and volume should ping
        metenox.check_moon_material_bay()

        HoldingCorporation.ping_metenox_value.assert_called_once()
        HoldingCorporation.ping_metenox_volume.assert_called_once()

        # resets calls
        HoldingCorporation.ping_metenox_value = MagicMock()
        HoldingCorporation.ping_metenox_volume = MagicMock()
        metenox.last_moongoo_bay_ping = None  # Resets timer
        metenox.save()

        scandium_price.price = 0  # value shouldn't ping
        scandium_price.save()

        # volume should ping
        metenox.check_moon_material_bay()

        HoldingCorporation.ping_metenox_value.assert_not_called()
        HoldingCorporation.ping_metenox_volume.assert_called_once()
