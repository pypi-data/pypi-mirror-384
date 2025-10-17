from netbox.views import generic

from netbox_authorized_keys.filtersets import (
    AuthorizedKeyDeviceFilterSet,
    AuthorizedKeyVirtualMachineFilterSet,
)
from netbox_authorized_keys.forms import (
    AuthorizedKeyDeviceFilterForm,
    AuthorizedKeyVirtualMachineFilterForm,
)
from netbox_authorized_keys.models import AuthorizedKeyDevice, AuthorizedKeyVirtualMachine
from netbox_authorized_keys.tables import AuthorizedKeyDeviceTable, AuthorizedKeyVirtualMachineTable


# Authorized Key Devices
class AuthorizedKeyDeviceListView(generic.ObjectListView):
    queryset = AuthorizedKeyDevice.objects.all()
    table = AuthorizedKeyDeviceTable
    filterset = AuthorizedKeyDeviceFilterSet
    filterset_form = AuthorizedKeyDeviceFilterForm


# Authorized Key Virtual Machines
class AuthorizedKeyVirtualMachineListView(generic.ObjectListView):
    queryset = AuthorizedKeyVirtualMachine.objects.all()
    table = AuthorizedKeyVirtualMachineTable
    filterset = AuthorizedKeyVirtualMachineFilterSet
    filterset_form = AuthorizedKeyVirtualMachineFilterForm
