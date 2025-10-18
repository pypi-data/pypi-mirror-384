from typing import Any

from deprecated import deprecated
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from happy_condo.condo_management.models import CondoManager
from happy_condo.condos.managers import LivingUnitQuerySet
from happy_condo.core.models import AuditableModel, Country
from model_utils.models import TimeStampedModel
from slugify import slugify

User = get_user_model()


class Condominium(AuditableModel, TimeStampedModel):
    """Model representing a condominium.

    Attributes:
        name (str): Name of the condominium.
        country (ForeignKey): Country where the condominium is located.
        slug (str): Unique slug for the condominium.
        status (str): Current status of the condominium.
    """

    STATUS_CHOICES = [
        ("ACTIVE", _("Active")),
        ("ARCHIVED", _("Archived")),
        ("FROZEN", _("Frozen")),
    ]

    name = models.CharField(max_length=255, verbose_name=_("Name"), help_text=_("Name of the condominium"))
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        verbose_name=_("Country"),
        help_text=_("Country where the condominium is located"),
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("Unique slug for the condominium"),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name=_("Status"),
        help_text=_("Current status of the condominium"),
    )
    condo_manager = models.ForeignKey(
        CondoManager,
        on_delete=models.PROTECT,
        verbose_name=_("Condo Manager"),
        null=True,
        related_name="condos",
    )

    def get_living_units(self) -> QuerySet["LivingUnit"]:
        """Return all living units in the condominium."""
        return LivingUnit.objects.filter(parcel__condominium=self)

    class Meta:  # noqa: D106
        ordering = ["name"]
        verbose_name = _("Condominium")
        verbose_name_plural = _("Condominiums")

    def __str__(self) -> str:  # noqa: D105
        return self.name

    def save(self, *args, **kwargs):  # noqa: ANN002 ANN003 ANN201
        """Override the save method to generate a slug."""
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Parcel(AuditableModel, TimeStampedModel):
    """Model representing a parcel within a condominium.

    Attributes:
        name (str): Name of the parcel.
        condominium (ForeignKey): Condominium to which the parcel belongs.
    """

    TOWER = "TOWER"
    LOT = "LOT"
    PARCEL_TYPE_CHOICES = [
        (TOWER, _("Tower")),
        (LOT, _("Lot")),
    ]
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the parcel, e.g., Tower 1 or Sunset Tower"),
    )
    parcel_type = models.CharField(
        max_length=12,
        choices=PARCEL_TYPE_CHOICES,
        verbose_name=_("Parcel Type"),
        help_text=_("Type of parcel, e.g., tower or lot"),
    )
    condominium = models.ForeignKey(
        Condominium,
        on_delete=models.PROTECT,
        related_name="parcels",
        verbose_name=_("Condominium"),
        help_text=_("Condominium to which the parcel belongs"),
    )

    class Meta:  # noqa: D106
        unique_together = ("condominium", "name")
        verbose_name = _("Parcel")
        verbose_name_plural = _("Parcels")

    def __str__(self) -> str:  # noqa: D105
        return self.name


class LivingUnitType(AuditableModel, TimeStampedModel):
    """Model representing a type of living unit.

    Attributes:
        name (str): Name of the living unit type.
        area (Decimal): Area of the living unit type in square meters.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the living unit type"),
    )
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Area"),
        help_text=_("Area of the living unit type in square meters"),
    )
    area_unit = models.CharField(
        max_length=50,
        verbose_name=_("Area Unit"),
        help_text=_("Unit of area measurement, e.g., square meters"),
    )

    class Meta:  # noqa: D106
        verbose_name = _("Living Unit Type")
        verbose_name_plural = _("Living Unit Types")

    def __str__(self) -> str:  # noqa: D105
        return self.name


class Member(AuditableModel, TimeStampedModel):
    """Model representing a member of a condominium."""

    class OwnerType(models.TextChoices):
        """TextChoices representing the type of owner."""

        NATURAL_ENTITY = "NATURAL_ENTITY", _("Person")
        LEGAL_ENTITY = "LEGAL_ENTITY", _("Company")

    class NationalIdType(models.TextChoices):
        """TextChoices representing the type of national identification."""

        NATIONAL_ID = "NATIONAL_ID", _("National ID")
        FOREIGN_ID = "FOREIGN_ID", _("Foreign ID")
        COMPANY_ID = "COMPANY_ID", _("Company ID")
        PASSPORT = "PASSPORT", _("Passport")

    name = models.CharField(max_length=255, verbose_name=_("Name"), help_text=_("Full name."))
    email = models.EmailField(verbose_name=_("Email"), help_text=_("Email address of the owner"), blank=True)
    last_name = models.CharField(
        max_length=64,
        verbose_name=_("Last Name"),
        help_text=_("Last name."),
        blank=True,
    )
    first_name = models.CharField(
        max_length=64,
        verbose_name=_("First Name"),
        help_text=_("First name."),
        blank=True,
    )
    second_name = models.CharField(
        max_length=64,
        verbose_name=_("Second Name"),
        help_text=_("Second name."),
        blank=True,
    )
    entity_type = models.CharField(
        max_length=20,
        choices=OwnerType.choices,
        default=OwnerType.LEGAL_ENTITY,
        verbose_name=_("Entity type"),
        help_text=_("Entity type"),
    )
    national_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("National ID"),
        help_text=_("National identification number"),
    )
    national_id_type = models.CharField(
        max_length=50,
        choices=NationalIdType.choices,
        default=NationalIdType.NATIONAL_ID,
        blank=True,
        verbose_name=_("National ID Type"),
        help_text=_("National identification type"),
    )
    verification_digit = models.CharField(
        _("Verification digit"),
        blank=True,
        max_length=4,
        help_text=_("Verification digit"),
    )
    phone1 = models.CharField(
        max_length=32,
        verbose_name=_("Phone 1"),
        help_text=_("Phone 1"),
        blank=True,
    )
    phone2 = models.CharField(
        max_length=32,
        verbose_name=_("Phone 2"),
        help_text=_("Phone 2"),
        blank=True,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_("User"),
        help_text=_("User account associated with the member"),
        related_name="member",
        blank=True,
        null=True,
    )

    condominium = models.ForeignKey(
        Condominium,
        on_delete=models.PROTECT,
        verbose_name=_("Condominium"),
        help_text=_("Condominium associated with the member"),
        related_name="member",
    )

    class Meta:  # noqa D106
        verbose_name = _("Member")
        verbose_name_plural = _("Members")
        ordering = ["last_name", "first_name", "name"]

    def __str__(self) -> str:  # noqa: D105
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Override the save method to generate a full name."""
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)


class LivingUnit(AuditableModel, TimeStampedModel):
    """Model representing a living unit within a parcel.

    Attributes:
        unit_number (str): Unit number of the living unit. e.g., 101, 102A, 201B.
        floor (int): Floor where the living unit is located. 0 for parcels Lot parcels.
        parcel (ForeignKey): Parcel where the living unit is located.
        living_unit_type (ForeignKey): Type of the living unit.
        area (Decimal): Area of the living unit.
        area_unit (str): Unit of area measurement.
    """

    members = models.ManyToManyField(
        Member,
        verbose_name=_("Members"),
        through="LivingUnitMember",
        related_name="living_units",
        help_text=_("Members of the living unit"),
        blank=True,
    )
    # @deprecated(reason="This field will be removed in the next version.", version="0.11.0")
    unit_number = models.CharField(_("Unit Number"), max_length=255, help_text=_("Unit number of the living"))
    floor = models.CharField(_("Floor"), max_length=6, help_text=_("Floor where the living unit is located"))
    parcel = models.ForeignKey(
        Parcel,
        related_name="living_units",
        on_delete=models.PROTECT,
        verbose_name=_("Parcel"),
        help_text=_("Parcel where the living unit is located"),
    )
    living_unit_type = models.ForeignKey(
        LivingUnitType,
        on_delete=models.PROTECT,
        verbose_name=_("Living Unit Type"),
        help_text=_("Type of the living unit"),
    )
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Area"),
        help_text=_("Area of the living unit"),
    )
    area_unit = models.CharField(
        max_length=50,
        verbose_name=_("Area Unit"),
        help_text=_("Unit of area measurement, e.g., square meters"),
    )

    class Meta:  # noqa: D106
        verbose_name = _("Living Unit")
        verbose_name_plural = _("Living Units")
        ordering = ["floor", "unit_number"]

    def __str__(self) -> str:  # noqa: D105
        return f"{self.parcel} - {self.unit_number}"

    objects = LivingUnitQuerySet.as_manager()


class LivingUnitMember(AuditableModel, TimeStampedModel):
    """Model representing a member of a living unit."""  # noqa: D210

    class MemberRoleType(models.TextChoices):
        """TextChoices representing the type of Member Role."""

        OWNER = "OWNER", _("Owner")
        TENANT = "TENANT", _("Tenant")
        RESIDENT = "RESIDENT", _("Resident")

    living_unit = models.ForeignKey(
        LivingUnit, verbose_name=_("Living Unit"), on_delete=models.PROTECT, related_name="living_unit_members"
    )
    member = models.ForeignKey(
        Member, verbose_name=_("Member"), on_delete=models.PROTECT, related_name="living_unit_members"
    )
    member_type = models.CharField(
        _("Member type"),
        max_length=20,
        choices=MemberRoleType.choices,
        default=MemberRoleType.RESIDENT,
    )

    class Meta:  # noqa: D106
        unique_together = ("living_unit", "member", "member_type")


class Amenity(AuditableModel, TimeStampedModel):
    """Model representing an amenity.

    Attributes:
        name (str): Name of the amenity.
        is_closed (bool): Indicates if the amenity is currently closed.
        can_be_reserved (bool): Indicates if the amenity can be reserved.
    """

    condominium = models.ForeignKey(Condominium, related_name="amenities", on_delete=models.PROTECT)
    parcel = models.ForeignKey(
        Parcel,
        related_name="amenities",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"), help_text=_("Name of the amenity"))
    is_closed = models.BooleanField(
        default=False,
        verbose_name=_("Is Closed"),
        help_text=_("Indicates if the amenity is currently closed"),
    )
    can_be_reserved = models.BooleanField(
        default=True,
        verbose_name=_("Can Be Reserved"),
        help_text=_("Indicates if the amenity can be reserved"),
    )

    class Meta:  # noqa: D106
        verbose_name = _("Amenity")
        verbose_name_plural = _("Amenities")

    def __str__(self) -> str:  # noqa: D105
        return self.name


@deprecated(version="0.11.0", reason="This model will be implemented in another app.")
class Reservation(AuditableModel, TimeStampedModel):
    """Model representing a reservation for an amenity.

    Attributes:
        amenity (ForeignKey): Amenity being reserved.
        user (ForeignKey): User making the reservation.
        start_time (DateTimeField): Start time of the reservation.
        end_time (DateTimeField): End time of the reservation.
    """

    amenity = models.ForeignKey(
        Amenity,
        related_name="reservations",
        on_delete=models.PROTECT,
        verbose_name=_("Amenity"),
        help_text=_("Amenity being reserved"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_("User"),
        help_text=_("User making the reservation"),
    )
    start_time = models.DateTimeField(verbose_name=_("Start Time"), help_text=_("Start time of the reservation"))
    end_time = models.DateTimeField(verbose_name=_("End Time"), help_text=_("End time of the reservation"))

    class Meta:  # noqa: D106
        verbose_name = _("Reservation")
        verbose_name_plural = _("_Reservations DEPRECATED")

    def __str__(self) -> str:  # noqa: D105
        return f"{self.amenity} - {self.user}"


class CondoSpace(models.Model):
    """Abstract condo space.

    Attributes:
        name (str): Name of the parking space.
        condominium (ForeignKey): Condominium to which the parking space belongs.
        living_unit: (ForeignKey): Living unit which owns the parking space.
    """

    name = models.CharField(max_length=64, verbose_name=_("Name"), help_text=_("Name of the parking space"))
    condominium = models.ForeignKey(
        Condominium,
        on_delete=models.PROTECT,
        related_name="%(class)s_condo",
        verbose_name=_("Condominium"),
        help_text=_("Condominium to which the parking space belongs"),
    )
    living_unit = models.ForeignKey(
        LivingUnit,
        related_name="%(class)s_living_unit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    usage_type = models.CharField(
        max_length=50,
        verbose_name=_("Usage Type. Private or Public"),
        help_text=_("Usage Type. Private or Shared."),
    )
    floor = models.CharField(max_length=16, help_text=_("Floor where the parking spaces is."))

    class Meta:  # noqa: D106
        unique_together = ("condominium", "name")
        abstract = True


class ParkingSpace(CondoSpace, AuditableModel, TimeStampedModel):
    """Model representing a parking space within a condominium."""

    class Meta:  # noqa: D106
        verbose_name = _("Parking Space")
        verbose_name_plural = _("Parking Spaces")

    def __str__(self) -> str:  # noqa: D105
        return self.name


class StorageSpace(CondoSpace, AuditableModel, TimeStampedModel):
    """Model representing a storage space within a condominium."""

    class Meta:  # noqa: D106
        verbose_name = _("Storage Space")
        verbose_name_plural = _("Storage Spaces")

    def __str__(self) -> str:  # noqa: D105
        return self.name


class CommonElement(CondoSpace, AuditableModel, TimeStampedModel):
    """Common elements and spaces, like elevators and lobbies."""

    parcel = models.ForeignKey(
        Parcel,
        related_name="common_elements",
        verbose_name=_("Common elements"),
        help_text=_("Parcel location"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:  # noqa: D106
        verbose_name = _("Common Element")
        verbose_name_plural = _("Common Elements")

    def __str__(self) -> str:  # noqa: D105
        return self.name
