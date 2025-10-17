"""NetBox Authorized Keys Plugin - Manage SSH authorized keys for devices and virtual machines."""

from netbox.plugins import PluginConfig

from netbox_authorized_keys.version import __author__, __email__, __version__


class NetBoxAuthorizeKeysConfig(PluginConfig):
    name = "netbox_authorized_keys"
    verbose_name = "NetBox Authorized Keys Plugin"
    description = "NetBox plugin to store and manage SSH authorized keys for devices and virtual machines"
    version = __version__
    author = __author__
    author_email = __email__
    base_url = "authorized-keys"
    min_version = "4.0.0"
    max_version = "4.9.99"


config = NetBoxAuthorizeKeysConfig
