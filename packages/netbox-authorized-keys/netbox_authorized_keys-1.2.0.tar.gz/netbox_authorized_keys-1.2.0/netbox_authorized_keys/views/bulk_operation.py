from dcim.models import Device
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from netbox.views import generic
from virtualization.models import VirtualMachine

from netbox_authorized_keys import forms, models


class AuthorizedKeyBulkActionView(generic.object_views.BaseObjectView):
    queryset = models.AuthorizedKey.objects.all()
    default_return_url = "plugins:netbox_authorized_keys:authorizedkey_list"
    form_class = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("device_id"):
            self.object = get_object_or_404(Device, pk=kwargs.get("device_id"))
        elif kwargs.get("virtual_machine_id"):
            self.object = get_object_or_404(VirtualMachine, pk=kwargs.get("virtual_machine_id"))

        return super().dispatch(request, *args, **kwargs)

    def get_extra_context(self, request, instance):
        return_url = request.GET.get("return_url", reverse(self.default_return_url))

        params = {"obj": self.object, "instance": instance} if instance else {"obj": self.object}
        form = self.form_class(**params)
        return {
            "form": form,
            "object": self.object,
            "return_url": return_url,  # Add return_url to context
        }

    def get(self, request, *args, **kwargs):
        context = self.get_extra_context(request, instance=None)
        return render(request, self.template_name, context)

    def perform_action(self, key, object):
        raise NotImplementedError("Subclasses must implement perform_action")

    def post(self, request, *args, **kwargs):
        return_url = request.GET.get("return_url", reverse(self.default_return_url))
        form = self.form_class(request.POST)

        if form.is_valid():
            authorized_keys = form.cleaned_data["authorized_keys"]

            for key in authorized_keys:
                self.perform_action(key, self.object)

            return redirect(return_url)

        context = self.get_extra_context(request, instance=None)
        context.update({"form": form})
        return render(request, self.template_name, context)


class AuthorizedKeyBulkAddView(AuthorizedKeyBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.AuthorizedKeyAddForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Add", "preposition": "to", "button_class": "success"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.add_authorizedkey"

    def perform_action(self, key, object):
        if isinstance(object, Device):
            key.devices.add(object)
        elif isinstance(object, VirtualMachine):
            key.virtual_machines.add(object)


class AuthorizedKeyBulkRemoveView(AuthorizedKeyBulkActionView):
    template_name = "netbox_authorized_keys/bulk_authorized_keys.html"
    form_class = forms.AuthorizedKeyRemoveForm

    def get_extra_context(self, request, instance):
        context = super().get_extra_context(request, instance)
        context.update({"action_text": "Remove", "preposition": "from", "button_class": "danger"})
        return context

    def get_required_permission(self):
        return "netbox_authorized_keys.delete_authorizedkey"

    def perform_action(self, key, object):
        if isinstance(object, Device):
            key.devices.remove(object)
        elif isinstance(object, VirtualMachine):
            key.virtual_machines.remove(object)
