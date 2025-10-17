from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_authorized_keys import views

urlpatterns = [
    # Authorized Keys
    path("authorized-keys/", views.AuthorizedKeyListView.as_view(), name="authorizedkey_list"),
    path("authorized-keys/add/", views.AuthorizedKeyEditView.as_view(), name="authorizedkey_add"),
    path("authorized-keys/import/", views.AuthorizedKeyBulkImportView.as_view(), name="authorizedkey_import"),
    path("authorized-keys/edit/", views.AuthorizedKeyBulkEditView.as_view(), name="authorizedkey_bulk_edit"),
    path("authorized-keys/delete/", views.AuthorizedKeyBulkDeleteView.as_view(), name="authorizedkey_bulk_delete"),
    path("authorized-keys/<int:pk>/", views.AuthorizedKeyView.as_view(), name="authorizedkey"),
    path("authorized-keys/<int:pk>/edit/", views.AuthorizedKeyEditView.as_view(), name="authorizedkey_edit"),
    path("authorized-keys/<int:pk>/delete/", views.AuthorizedKeyDeleteView.as_view(), name="authorizedkey_delete"),
    path(
        "authorized-keys/",
        include(get_model_urls("netbox_authorized_keys", "authorizedkey", detail=False)),
    ),
    path(
        "authorized-keys/<int:pk>/",
        include(get_model_urls("netbox_authorized_keys", "authorizedkey")),
    ),
    # Authorized Key Devices
    path("authorized-keys/devices/", views.AuthorizedKeyDeviceListView.as_view(), name="authorizedkeydevice_list"),
    path(
        "authorized-keys/devices/<int:device_id>/add/",
        views.AuthorizedKeyBulkAddView.as_view(),
        name="authorizedkeydevice_add",
    ),
    path(
        "authorized-keys/devices/<int:device_id>/remove/",
        views.AuthorizedKeyBulkRemoveView.as_view(),
        name="authorizedkeydevice_remove",
    ),
    # Authorized Key Virtual Machines
    path(
        "authorized-keys/virtual-machines/",
        views.AuthorizedKeyVirtualMachineListView.as_view(),
        name="authorizedkeyvirtualmachine_list",
    ),
    path(
        "authorized-keys/virtual-machines/<int:virtual_machine_id>/add/",
        views.AuthorizedKeyBulkAddView.as_view(),
        name="authorizedkeyvirtualmachine_add",
    ),
    path(
        "authorized-keys/virtual-machines/<int:virtual_machine_id>/remove/",
        views.AuthorizedKeyBulkRemoveView.as_view(),
        name="authorizedkeyvirtualmachine_remove",
    ),
]
