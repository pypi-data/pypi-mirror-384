import django_tables2 as tables
from django.utils.html import format_html
from netbox.tables import NetBoxTable, columns

from netbox_authorized_keys.models import AuthorizedKey, AuthorizedKeyDevice, AuthorizedKeyVirtualMachine


class AuthorizedKeyTable(NetBoxTable):
    id = tables.Column(linkify=True, verbose_name="ID")
    public_key = tables.Column(verbose_name="Public Key")
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = AuthorizedKey
        fields = ("id", "public_key", "username", "full_name", "description", "comments", "tags")
        default_columns = ("id", "username", "full_name", "description")

    def render_public_key(self, value, record):
        return format_html('<span title="{}">{}</span>', value, record.rendered_key)


class AuthorizedKeyDeviceTable(NetBoxTable):
    id = tables.Column(linkify=False, verbose_name="ID")

    authorized_key = tables.Column(linkify=True)
    device = tables.Column(linkify=True)
    actions = columns.ActionsColumn(
        actions=(),
    )

    class Meta(NetBoxTable.Meta):
        model = AuthorizedKeyDevice
        fields = ("authorized_key", "device")


class AuthorizedKeyVirtualMachineTable(NetBoxTable):
    id = tables.Column(linkify=False, verbose_name="ID")

    authorized_key = tables.Column(linkify=True)
    virtual_machine = tables.Column(linkify=True)
    actions = columns.ActionsColumn(
        actions=(),
    )

    class Meta(NetBoxTable.Meta):
        model = AuthorizedKeyVirtualMachine
        fields = ("authorized_key", "virtual_machine")
