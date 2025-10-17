from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from netbox.models.features import (
    BookmarksMixin,
    # ChangeLoggingMixin,
    CloningMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    EventRulesMixin,
    ExportTemplatesMixin,
    JournalingMixin,
    NotificationsMixin,
    TagsMixin,
)
from utilities.querysets import RestrictedQuerySet


class AuthorizedKey(NetBoxModel):
    public_key = models.TextField(verbose_name=_("Public Key"), null=False, blank=False, unique=True)
    username = models.CharField(max_length=200, blank=False, null=False, verbose_name=_("Username"))
    full_name = models.CharField(max_length=200, blank=True, null=False, verbose_name=_("Full Name"))

    description = models.CharField(max_length=255, verbose_name=_("description"), blank=True, default="", null=False)
    comments = models.TextField(blank=True, default="", null=False, verbose_name=_("Comments"))

    devices = models.ManyToManyField(
        to="dcim.device",
        related_name="authorized_keys",
        blank=True,
        through="netbox_authorized_keys.AuthorizedKeyDevice",
        verbose_name=_("Devices"),
    )

    virtual_machines = models.ManyToManyField(
        to="virtualization.virtualmachine",
        related_name="authorized_keys",
        blank=True,
        through="netbox_authorized_keys.AuthorizedKeyVirtualMachine",
        verbose_name=_("Virtual Machines"),
    )

    objects = RestrictedQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse("plugins:netbox_authorized_keys:authorizedkey", args=[self.pk])

    def serialize_object(self, *, exclude=None):
        data = super().serialize_object(exclude=exclude or [])
        data["devices"] = list(self.devices.values_list("pk", flat=True))
        data["virtual_machines"] = list(self.virtual_machines.values_list("pk", flat=True))
        return data

    def __str__(self):
        if self.username and self.full_name:
            return f"{self.username} - {self.full_name} - {self.rendered_key}"
        return f"{self.username} - {self.rendered_key}"
    
    class Meta:
        ordering = ["id"]

    @property
    def rendered_key(self) -> str:
        """
        Returns a shortened version of the public key in format: "<key_type> ...<last_8_chars_of_key>"
        Example: "ssh-rsa ...Kj38dK2p"
        """
        try:
            # Unpack key parts (type, key, optional comment)
            key_type, key, *_ = self.public_key.split()
            return f"{key_type} ...{key[-8:]}"
        except (ValueError, IndexError):
            return "Invalid key format"


class NetBoxModelWithoutChangelog(
    BookmarksMixin,
    # ChangeLoggingMixin,
    CloningMixin,
    CustomFieldsMixin,
    CustomLinksMixin,
    CustomValidationMixin,
    ExportTemplatesMixin,
    JournalingMixin,
    NotificationsMixin,
    TagsMixin,
    EventRulesMixin,
    models.Model,
):
    class Meta:
        abstract = True


class AuthorizedKeyDevice(NetBoxModelWithoutChangelog):
    authorized_key = models.ForeignKey(to="netbox_authorized_keys.AuthorizedKey", on_delete=models.CASCADE)
    device = models.ForeignKey(to="dcim.Device", on_delete=models.CASCADE)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        unique_together = ("authorized_key", "device")
        ordering = ["id"]

    def __str__(self):
        return f"{self.authorized_key} - {self.device}"


class AuthorizedKeyVirtualMachine(NetBoxModelWithoutChangelog):
    authorized_key = models.ForeignKey(to="netbox_authorized_keys.AuthorizedKey", on_delete=models.CASCADE)
    virtual_machine = models.ForeignKey(to="virtualization.VirtualMachine", on_delete=models.CASCADE)

    objects = RestrictedQuerySet.as_manager()

    class Meta:
        unique_together = ("authorized_key", "virtual_machine")
        ordering = ["id"]

    def __str__(self):
        return f"{self.authorized_key} - {self.virtual_machine}"
