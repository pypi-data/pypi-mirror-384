from netbox.api.viewsets import NetBoxModelViewSet

from netbox_authorized_keys.api.serializers import (
    AuthorizedKeyDeviceSerializer,
    AuthorizedKeySerializer,
    AuthorizedKeyVirtualMachineSerializer,
)
from netbox_authorized_keys.models import AuthorizedKey, AuthorizedKeyDevice, AuthorizedKeyVirtualMachine
from netbox_authorized_keys.filtersets import AuthorizedKeyFilterSet, AuthorizedKeyDeviceFilterSet, AuthorizedKeyVirtualMachineFilterSet


class AuthorizedKeyViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKey.objects.all()
    serializer_class = AuthorizedKeySerializer
    filterset_class = AuthorizedKeyFilterSet


class AuthorizedKeyDeviceViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKeyDevice.objects.all()
    serializer_class = AuthorizedKeyDeviceSerializer
    filterset_class = AuthorizedKeyDeviceFilterSet


class AuthorizedKeyVirtualMachineViewSet(NetBoxModelViewSet):
    queryset = AuthorizedKeyVirtualMachine.objects.all()
    serializer_class = AuthorizedKeyVirtualMachineSerializer
    filterset_class = AuthorizedKeyVirtualMachineFilterSet
