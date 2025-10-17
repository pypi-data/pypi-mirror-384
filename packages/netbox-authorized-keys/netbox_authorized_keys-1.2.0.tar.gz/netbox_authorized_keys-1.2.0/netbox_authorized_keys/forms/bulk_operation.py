from dcim.models import Device
from django import forms
from django.utils.translation import gettext_lazy as _
from utilities.forms.widgets import APISelectMultiple
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import AuthorizedKey


class AuthorizedKeyAddForm(forms.Form):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure widget with dynamic API URL based on object type
        api_url = "api/plugins/authorized-keys/authorized-keys/?"
        if isinstance(obj, Device):
            api_url += f"unassigned_to_device={obj.id}"
        elif isinstance(obj, VirtualMachine):
            api_url += f"unassigned_to_virtual_machine={obj.id}"

        self.fields["authorized_keys"] = forms.ModelMultipleChoiceField(
            queryset=AuthorizedKey.objects.all(),
            widget=APISelectMultiple(api_url=api_url),
            required=True,
            label=_("Authorized Keys"),
        )


class AuthorizedKeyRemoveForm(forms.Form):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure widget with dynamic API URL based on object type
        api_url = "api/plugins/authorized-keys/authorized-keys/?"
        if isinstance(obj, Device):
            api_url += f"assigned_to_device={obj.id}"
        elif isinstance(obj, VirtualMachine):
            api_url += f"assigned_to_virtual_machine={obj.id}"

        self.fields["authorized_keys"] = forms.ModelMultipleChoiceField(
            queryset=AuthorizedKey.objects.all(),
            widget=APISelectMultiple(api_url=api_url),
            required=True,
            label=_("Authorized Keys"),
        )
