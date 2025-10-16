from django.core.management.base import BaseCommand
from eveuniverse.models import EveSolarSystem

from allianceauth.services.hooks import get_extension_logger

from metenox.esi import esi
from metenox.models import MoonTag
from metenox.tasks import tag_moons_in_range

logger = get_extension_logger(__name__)


class Command(BaseCommand):
    help = "Tag moons in a given range of the base system"

    def add_arguments(self, parser):
        parser.add_argument("base_system", type=str, help="Base system to tag from")
        parser.add_argument("range", type=float, help="Range from the base system")
        parser.add_argument("tag", type=str, help="Tag name to add to the moons")

    def handle(self, *args, **options):
        eve_solar_system = find_solar_system_from_str(options["base_system"])
        range = options["range"]
        tag_name = options["tag"]
        tag = MoonTag.objects.get_or_create(name=tag_name)[0]
        tag_moons_in_range.delay(eve_solar_system.id, range, tag.id)


def find_solar_system_from_str(solar_system_name: str) -> EveSolarSystem | None:
    """
    Will attempt to load a system from it's string
    """
    logger.debug("Trying to find solar system for name %s", solar_system_name)
    try:
        solar_system = EveSolarSystem.objects.get(name=solar_system_name)
        return solar_system
    except EveSolarSystem.DoesNotExist:
        logger.debug(
            "Couldn't find %s in database, trying to find the id from esi",
            solar_system_name,
        )
        solar_system_id_result = esi.client.Universe.post_universe_ids(
            names=[solar_system_name]
        ).result()
        if id_list := solar_system_id_result["systems"]:
            solar_system_id = id_list[0]["id"]
            solar_system, _ = EveSolarSystem.objects.get_or_create_esi(
                id=solar_system_id
            )
            logger.info(
                "Created system id %s matching name %s",
                solar_system.id,
                solar_system_name,
            )
            return solar_system

    logger.error("Couldn't find a matching id for %s", solar_system_name)
    return
