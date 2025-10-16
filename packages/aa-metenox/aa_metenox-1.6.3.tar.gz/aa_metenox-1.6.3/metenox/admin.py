"""Admin site."""

from celery import group

from django.contrib import admin
from django.db.models import QuerySet

from metenox.models import (
    EveTypePrice,
    HoldingCorporation,
    Metenox,
    MetenoxHourlyProducts,
    MetenoxStoredMoonMaterials,
    MetenoxTag,
    Moon,
    MoonTag,
    Owner,
    Webhook,
)
from metenox.tasks import update_holding
from metenox.templatetags.metenox import formatisk


class MetenoxHourlyHarvestInline(admin.TabularInline):
    model = MetenoxHourlyProducts

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Moon)
class MoonAdmin(admin.ModelAdmin):
    list_display = ["name", "moon_value", "tag_display", "value_updated_at"]
    fields = [("eve_moon", "moonmining_moon"), ("value", "value_updated_at"), ("tags",)]
    search_fields = ["eve_moon__name"]
    readonly_fields = ["eve_moon", "moonmining_moon"]
    inlines = (MetenoxHourlyHarvestInline,)

    @admin.display(description="value")
    def moon_value(self, moon: Moon):
        return f"{formatisk(moon.value)} ISK"

    @admin.display(description="Tags attached to the moon")
    def tag_display(self, moon: Moon):
        return " ,".join([tag.name for tag in moon.tags.all()])

    def has_add_permission(self, request):
        return False


@admin.action(description="Reset the metenox ping status")
def reset_pings(modeladmin, request, queryset):
    """Resets the ping status of the selected metenoxes for them to be pinged again"""
    queryset.update(
        was_magmatic_pinged=False, was_fuel_pinged=False, last_moongoo_bay_ping=None
    )


class MetenoxMoonMaterialBayInline(admin.TabularInline):
    model = MetenoxStoredMoonMaterials

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Metenox)
class MetenoxAdmin(admin.ModelAdmin):
    list_display = [
        "structure_name",
        "corporation",
        "alliance",
        "tag_display",
        "metenox_value",
        "fuel_blocks_count",
        "magmatic_gas_count",
        "was_fuel_pinged",
        "was_magmatic_pinged",
        "last_moongoo_bay_ping",
        "last_updated",
    ]
    list_filter = ["corporation", "corporation__corporation__alliance", "tags"]
    search_fields = ["structure_name"]
    actions = [reset_pings]
    fields = [
        ("structure_id", "structure_name"),
        "moon",
        "corporation",
        "tags",
        ("fuel_blocks_count", "magmatic_gas_count"),
        ("was_fuel_pinged", "was_magmatic_pinged", "last_moongoo_bay_ping"),
        "last_updated",
    ]
    readonly_fields = [
        "structure_id",
        "moon",
        "corporation",
        "was_fuel_pinged",
        "was_magmatic_pinged",
        "last_moongoo_bay_ping",
        "last_updated",
    ]
    inlines = (MetenoxMoonMaterialBayInline,)

    @admin.display(description="Value", ordering="moon__value")
    def metenox_value(self, metenox: Metenox):
        return f"{formatisk(metenox.moon.value)} ISK"

    @admin.display(
        description="Corporation alliance",
        ordering="corporation__corporation__alliance",
    )
    def alliance(self, metenox: Metenox):
        return metenox.corporation.alliance

    @admin.display(description="Tags attached to the metenox")
    def tag_display(self, metenox: Metenox):
        return " ,".join([tag.name for tag in metenox.tags.all()])

    def has_add_permission(self, request):
        return False


@admin.action(description="Enable selected owners")
def enable_owners(modeladmin, request, queryset):
    """Enable all owners of the received queryset"""
    Owner.enable_owners(queryset)


@admin.action(description="Disable selected owners")
def disable_owners(modeladmin, request, queryset):
    """Disable all owners of the received queryset"""
    Owner.disable_owners(queryset)


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = [
        "char_name",
        "is_enabled",
        "corporation",
        "ally_name",
        "character_ownership",
    ]
    list_filter = ["is_enabled", "corporation", "corporation__corporation__alliance"]
    readonly_fields = ["character_ownership", "corporation"]
    actions = [enable_owners, disable_owners]

    @admin.display(
        description="Character name", ordering="character_ownership__character"
    )
    def char_name(self, owner: Owner) -> str:
        return owner.character_name

    @admin.display(
        description="Alliance name", ordering="corporation__corporation__alliance"
    )
    def ally_name(self, owner: Owner) -> str:
        return owner.alliance_name

    def has_add_permission(self, request):
        return False


@admin.action(description="Update the selected holding corporations")
def update_holdings(modeladmin, request, queryset: QuerySet[HoldingCorporation]):
    """Update the selected holding corporations"""
    tasks = [
        update_holding.si(id)
        for id in queryset.values_list("corporation__corporation_id", flat=True)
    ]
    group(tasks).delay()


@admin.action(description="Enable all owners of the corporations")
def enable_all_owners(modeladmin, request, queryset):
    """Enable all owners part of the corporations listed"""
    HoldingCorporation.enable_all_owners(queryset)


@admin.action(description="Disable all owners of the corporations")
def disable_all_owners(modeladmin, request, queryset):
    """Disable all owners part of the corporations listed"""
    HoldingCorporation.disable_all_owners(queryset)


class OwnerCharacterAdminInline(admin.TabularInline):
    model = Owner
    readonly_fields = ["character_ownership"]

    fields = ["character_ownership", "is_enabled"]

    def has_add_permission(self, request, obj):
        return False


@admin.register(HoldingCorporation)
class HoldingCorporationAdmin(admin.ModelAdmin):
    list_display = [
        "corporation",
        "alliance",
        "is_active",
        "count_metenox",
        "count_owners",
        "last_updated",
    ]
    list_filter = ["corporation__alliance", "is_active"]
    sortable_by = ["is_active"]
    actions = [update_holdings, enable_all_owners, disable_all_owners]
    readonly_fields = ["corporation", "last_updated", "count_metenox"]
    inlines = (OwnerCharacterAdminInline,)

    @admin.display(description="Number metenoxes")
    def count_metenox(self, holding: HoldingCorporation) -> int:
        return holding.count_metenoxes

    @admin.display(
        description="Number of owners / active owners", ordering="owners__count"
    )
    def count_owners(self, holding: HoldingCorporation) -> str:
        return f"{holding.owners.count()} / {holding.active_owners().count()}"

    def has_add_permission(self, request):
        return False


@admin.register(EveTypePrice)
class EveTypePriceAdmin(admin.ModelAdmin):
    list_display = ["eve_type", "eve_group", "type_price"]
    readonly_fields = ["eve_type", "last_update"]

    @admin.display(description="Price", ordering="price")
    def type_price(self, type_price: EveTypePrice):
        return f"{formatisk(type_price.price)} ISK"

    @admin.display(description="Eve Group", ordering="eve_type__eve_group")
    def eve_group(self, type_price: EveTypePrice):
        return type_price.eve_type.eve_group

    def has_add_permission(self, request):
        return False


@admin.register(MoonTag)
class MoonTagAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.action(description="Add the tags to every metenoxes")
def add_tag_all_metenoxes(modeladmin, request, queryset):
    for metenox in Metenox.objects.all():
        metenox.tags.add(*queryset)


@admin.register(MetenoxTag)
class MetenoxTagAdmin(admin.ModelAdmin):
    list_display = ["name", "default"]
    actions = [add_tag_all_metenoxes]


@admin.action(description="Send a test message to the selected webhooks")
def test_webhooks(modeladmin, request, queryset):
    """Test the selected webhooks"""
    for webhook in queryset:
        webhook.send_info(
            "Test notification",
            "This is a webhook test send from the aa-metenox application",
        )


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ["name", "webhook_id", "count_holdings", "default"]
    list_filter = ["holding_corporations", "default"]
    actions = [test_webhooks]
    readonly_fields = ["webhook_id", "webhook_token"]

    @admin.display(
        description="Number of corporations attached to this webhook",
        ordering="webhooks__count",
    )
    def count_holdings(self, webhook: Webhook):
        return webhook.holding_corporations.count()
