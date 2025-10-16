from eveuniverse.models import EveMoon

from allianceauth.eveonline.models import EveCorporationInfo

from metenox.models import HoldingCorporation, Metenox
from metenox.tasks import create_metenox

MOON_ID = 40178441


def create_test_holding(holding_id: int = 1) -> HoldingCorporation:
    """Creates a template holding corporation"""

    corporation = EveCorporationInfo.objects.create(
        corporation_id=holding_id,
        corporation_name="corporation1",
        corporation_ticker="CORP1",
        member_count=1,
    )
    holding = HoldingCorporation(corporation=corporation)
    holding.save()

    return holding


def create_test_metenox() -> Metenox:
    """
    Creates a basic metenox for testing purpose
    """

    corporation = EveCorporationInfo.objects.create(
        corporation_id=1,
        corporation_name="corporation1",
        corporation_ticker="CORP1",
        member_count=1,
    )
    holding = HoldingCorporation(corporation=corporation)
    holding.save()
    eve_moon = EveMoon.objects.get(id=MOON_ID)

    structure_info = {
        "name": "Metenox1",
        "structure_id": 1,
    }

    location_info = {
        "position": {
            "x": eve_moon.position_x,
            "y": eve_moon.position_y,
            "z": eve_moon.position_z,
        },
        "solar_system_id": eve_moon.eve_planet.eve_solar_system.id,
    }

    create_metenox(holding.corporation.corporation_id, structure_info, location_info)

    metenox = Metenox.objects.get(structure_id=1)

    return metenox
