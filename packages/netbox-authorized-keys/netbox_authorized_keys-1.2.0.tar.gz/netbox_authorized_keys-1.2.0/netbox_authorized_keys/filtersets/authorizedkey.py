import django_filters
from dcim.models import Device
from django.db.models import Q
from extras.filters import TagFilter
from netbox.filtersets import BaseFilterSet, NetBoxModelFilterSet
from virtualization.models import VirtualMachine

from netbox_authorized_keys.models import AuthorizedKey, AuthorizedKeyDevice, AuthorizedKeyVirtualMachine


class AuthorizedKeyFilterSet(NetBoxModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    public_key = django_filters.CharFilter()
    username = django_filters.CharFilter()
    full_name = django_filters.CharFilter()
    description = django_filters.CharFilter()
    tag = TagFilter()

    devices = django_filters.ModelMultipleChoiceFilter(
        field_name="devices", queryset=Device.objects.all(), label="Devices"
    )
    virtual_machines = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machines", queryset=VirtualMachine.objects.all(), label="Virtual Machines"
    )

    assigned_to_device = django_filters.ModelChoiceFilter(
        queryset=Device.objects.all(), method="filter_assigned_to_device", label="Assigned to Device"
    )

    unassigned_to_device = django_filters.ModelChoiceFilter(
        queryset=Device.objects.all(), method="filter_unassigned_to_device", label="Unassigned from Device"
    )

    assigned_to_virtual_machine = django_filters.ModelChoiceFilter(
        queryset=VirtualMachine.objects.all(),
        method="filter_assigned_to_virtual_machine",
        label="Assigned to Virtual Machine",
    )

    unassigned_to_virtual_machine = django_filters.ModelChoiceFilter(
        queryset=VirtualMachine.objects.all(),
        method="filter_unassigned_to_virtual_machine",
        label="Unassigned from Virtual Machine",
    )

    def filter_assigned_to_device(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(devices=value)

    def filter_unassigned_to_device(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.exclude(devices=value)

    def filter_assigned_to_virtual_machine(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(virtual_machines=value)

    def filter_unassigned_to_virtual_machine(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.exclude(virtual_machines=value)

    class Meta:
        model = AuthorizedKey
        fields = ["id", "public_key", "username", "full_name", "description", "comments", "devices", "virtual_machines"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        filters = (
            Q(username__icontains=value)
            | Q(full_name__icontains=value)
            | Q(description__icontains=value)
            | Q(comments__icontains=value)
        )
        return queryset.filter(filters)


class AuthorizedKeyDeviceFilterSet(BaseFilterSet):
    authorized_key = django_filters.ModelMultipleChoiceFilter(
        field_name="authorized_key", queryset=AuthorizedKey.objects.all(), label="Authorized Key"
    )

    device = django_filters.ModelMultipleChoiceFilter(
        field_name="device", queryset=Device.objects.all(), label="Device"
    )

    class Meta:
        model = AuthorizedKeyDevice
        fields = ["id", "authorized_key", "device"]


class AuthorizedKeyVirtualMachineFilterSet(BaseFilterSet):
    authorized_key = django_filters.ModelMultipleChoiceFilter(
        field_name="authorized_key", queryset=AuthorizedKey.objects.all(), label="Authorized Key"
    )

    virtual_machine = django_filters.ModelMultipleChoiceFilter(
        field_name="virtual_machine", queryset=VirtualMachine.objects.all(), label="Virtual Machine"
    )

    class Meta:
        model = AuthorizedKeyVirtualMachine
        fields = ["id", "authorized_key", "virtual_machine"]
