from rest_framework.routers import DefaultRouter

from netbox_authorized_keys.api.views import (
    AuthorizedKeyDeviceViewSet,
    AuthorizedKeyViewSet,
    AuthorizedKeyVirtualMachineViewSet,
)

router = DefaultRouter()
router.register(r"authorized-keys", AuthorizedKeyViewSet)
router.register(r"devices", AuthorizedKeyDeviceViewSet)
router.register(r"virtual-machines", AuthorizedKeyVirtualMachineViewSet)

urlpatterns = router.urls
