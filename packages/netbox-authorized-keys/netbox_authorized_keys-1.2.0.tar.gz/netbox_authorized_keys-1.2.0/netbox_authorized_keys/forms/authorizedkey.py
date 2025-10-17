from dcim.models import Device
from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import NetBoxModelBulkEditForm, NetBoxModelFilterSetForm, NetBoxModelForm, NetBoxModelImportForm
from utilities.forms.fields import (
    CommentField,
    CSVModelMultipleChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import AuthorizedKey


class AuthorizedKeyForm(NetBoxModelForm):
    public_key = forms.CharField(
        label=_("Public Key"), widget=forms.Textarea, required=True, help_text=_("Enter the public key (unique)")
    )
    username = forms.CharField(label=_("Username"), required=True)
    full_name = forms.CharField(label=_("Full Name"), required=False, help_text=_("Owner's Full Name"))

    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label=_("Devices"), required=False)
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), label=_("Virtual Machines"), required=False
    )

    fieldsets = (
        FieldSet("public_key", "username", "full_name", "description", name=_("Base")),
        FieldSet("devices", "virtual_machines", name=_("Host Assignment")),
        FieldSet("tags", name=_("Misc")),
    )

    class Meta:
        comments = CommentField()
        model = AuthorizedKey
        fields = [
            "public_key",
            "username",
            "full_name",
            "description",
            "devices",
            "virtual_machines",
            "comments",
            "tags",
        ]


class AuthorizedKeyFilterForm(NetBoxModelFilterSetForm):
    model = AuthorizedKey
    public_key__ic = forms.CharField(
        label=_("Public Key (contains)"),
        required=False,
        widget=forms.widgets.Textarea(attrs={"placeholder": _("Public Key")}),
        help_text="Public Key | Treated as CharField => contains",
    )

    username = forms.CharField(required=False)
    full_name = forms.CharField(required=False)
    description = forms.CharField(required=False)

    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label=_("Devices"), required=False)
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), label=_("Virtual Machines"), required=False
    )

    tag = TagFilterField(model)


class AuthorizedKeyBulkImportForm(NetBoxModelImportForm):
    devices = CSVModelMultipleChoiceField(
        queryset=Device.objects.all(),
        to_field_name="name",
        required=False,
        help_text=_('Comma-separated list of devices, encased with double quotes (e.g. "Router1,Switch2")'),
    )

    virtual_machines = CSVModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        to_field_name="name",
        required=False,
        help_text=_('Comma-separated list of virtual machines, encased with double quotes (e.g. "VM1,VM2")'),
    )

    class Meta:
        model = AuthorizedKey
        fields = [
            "public_key",
            "username",
            "full_name",
            "description",
            "devices",
            "virtual_machines",
            "comments",
            "tags",
        ]


class AuthorizedKeyBulkEditForm(NetBoxModelBulkEditForm):
    username = forms.CharField(label=_("Username"), required=False)
    full_name = forms.CharField(label=_("Full Name"), required=False, help_text=_("Owner's Full Name"))
    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label=_("Devices"), required=False)
    virtual_machines = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(), label=_("Virtual Machines"), required=False
    )
    comments = CommentField()

    model = AuthorizedKey

    fieldsets = (
        FieldSet("public_key", "username", "full_name", "description", name=_("Base")),
        FieldSet("devices", "virtual_machines", name=_("Host Assignment")),
        FieldSet("tags", name=_("Misc")),
    )

    nullable_fields = ("devices", "virtual_machines", "tags", "comments")
