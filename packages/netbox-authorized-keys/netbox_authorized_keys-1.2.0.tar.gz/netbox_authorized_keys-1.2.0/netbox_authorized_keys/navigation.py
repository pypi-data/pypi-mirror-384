from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Authorized Keys",
    icon_class="mdi mdi-key",
    groups=(
        (
            "SSH Public Keys",
            (
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkey_list",
                    link_text="Authorized Keys",
                    permissions=["netbox_authorized_keys.view_authorizedkey"],
                ),
            ),
        ),
        (
            "Assignments",
            (
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkeydevice_list",
                    link_text="Devices",
                    permissions=["netbox_authorized_keys.view_authorizedkeydevice"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_authorized_keys:authorizedkeyvirtualmachine_list",
                    link_text="Virtual Machines",
                    permissions=["netbox_authorized_keys.view_authorizedkeyvirtualmachine"],
                ),
            ),
        ),
    ),
)
